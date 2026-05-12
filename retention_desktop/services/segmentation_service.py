from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sqlalchemy import text

from config import N_CLUSTERS, SEGMENT_LABELS
from data.database import engine, get_session


class SegmentationService:
    """K-Means customer segmentation based on RFM values."""

    def compute(self) -> pd.DataFrame:
        """Load RFM data, run K-Means, and assign segment labels."""
        with engine.connect() as conn:
            rfm_df = pd.read_sql(text("SELECT * FROM rfm_scores"), conn)

        if rfm_df.empty:
            return pd.DataFrame()

        features = rfm_df[["recency", "frequency", "monetary"]].copy()

        # Log-transform skewed features to reduce outlier influence
        features["frequency"] = np.log1p(features["frequency"])
        features["monetary"] = np.log1p(features["monetary"])

        # Normalize
        scaler = StandardScaler()
        scaled = scaler.fit_transform(features)

        # K-Means
        kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
        rfm_df["cluster"] = kmeans.fit_predict(scaled)

        # Determine which cluster is which by looking at cluster centers
        # Compute mean frequency+monetary per cluster to rank them
        cluster_stats = rfm_df.groupby("cluster").agg(
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
        )
        # Score = avg_frequency_rank + avg_monetary_rank (higher = better)
        cluster_stats["rank_score"] = (
            cluster_stats["avg_frequency"].rank() + cluster_stats["avg_monetary"].rank()
        )
        sorted_clusters = cluster_stats["rank_score"].sort_values().index.tolist()

        # Map: lowest rank -> Low Engagement, ..., highest -> High Value
        label_keys = ["low", "mid_low", "mid_high", "high"]
        cluster_to_label = {}
        for i, cluster_id in enumerate(sorted_clusters):
            cluster_to_label[cluster_id] = SEGMENT_LABELS[label_keys[i]]

        rfm_df["segment_label"] = rfm_df["cluster"].map(cluster_to_label)

        return rfm_df[["customer_id", "segment_label"]]

    def save_to_db(self, seg_df: pd.DataFrame) -> int:
        """Save segment labels to segments table."""
        if seg_df.empty:
            return 0

        session = get_session()
        now = datetime.now()
        try:
            session.execute(text("DELETE FROM segments"))
            session.flush()

            for _, row in seg_df.iterrows():
                session.execute(
                    text("""
                        INSERT INTO segments (customer_id, segment_label, churn_probability, prediction_date)
                        VALUES (:cid, :label, NULL, :pdate)
                    """),
                    {"cid": int(row["customer_id"]), "label": row["segment_label"], "pdate": now},
                )
            session.commit()
            return len(seg_df)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def run(self) -> pd.DataFrame:
        """Compute segments and save to database."""
        seg_df = self.compute()
        self.save_to_db(seg_df)
        return seg_df
