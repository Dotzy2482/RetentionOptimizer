from datetime import datetime

import pandas as pd
import numpy as np
from sqlalchemy import text

from config import RFM_SCORE_BINS
from data.database import get_session, init_db, engine


class RFMService:
    """Computes Recency, Frequency, Monetary values and quantile-based scores."""

    def compute(self, reference_date: datetime | None = None) -> pd.DataFrame:
        """Calculate RFM metrics from the transactions table.

        Returns a DataFrame with columns:
            customer_id, recency, frequency, monetary, r_score, f_score, m_score
        """
        query = text("""
            SELECT
                customer_id,
                invoice_no,
                invoice_date,
                quantity,
                price
            FROM transactions
        """)

        with engine.connect() as conn:
            df = pd.read_sql(query, conn)

        if df.empty:
            return pd.DataFrame()

        df["invoice_date"] = pd.to_datetime(df["invoice_date"])
        df["revenue"] = df["quantity"] * df["price"]

        if reference_date is None:
            reference_date = df["invoice_date"].max() + pd.Timedelta(days=1)

        # Aggregate per customer
        rfm = df.groupby("customer_id").agg(
            recency=("invoice_date", lambda x: (reference_date - x.max()).days),
            frequency=("invoice_no", "nunique"),
            monetary=("revenue", "sum"),
        ).reset_index()

        rfm["monetary"] = rfm["monetary"].round(2)

        # Quantile-based scoring (1-5)
        # Recency: lower is better -> reverse labels
        rfm["r_score"] = pd.qcut(
            rfm["recency"], q=RFM_SCORE_BINS, labels=False, duplicates="drop"
        )
        rfm["r_score"] = rfm["r_score"].max() - rfm["r_score"] + 1

        # Frequency: higher is better
        rfm["f_score"] = pd.qcut(
            rfm["frequency"], q=RFM_SCORE_BINS, labels=False, duplicates="drop"
        ) + 1

        # Monetary: higher is better
        rfm["m_score"] = pd.qcut(
            rfm["monetary"], q=RFM_SCORE_BINS, labels=False, duplicates="drop"
        ) + 1

        # Ensure scores are int
        for col in ["r_score", "f_score", "m_score"]:
            rfm[col] = rfm[col].astype(int)

        return rfm

    def save_to_db(self, rfm_df: pd.DataFrame) -> int:
        """Save RFM results to rfm_scores table. Returns row count."""
        if rfm_df.empty:
            return 0

        session = get_session()
        try:
            # Clear old scores
            session.execute(text("DELETE FROM rfm_scores"))
            session.flush()

            records = rfm_df.to_dict("records")
            for rec in records:
                session.execute(
                    text("""
                        INSERT INTO rfm_scores
                            (customer_id, recency, frequency, monetary,
                             r_score, f_score, m_score, loyalty_score)
                        VALUES
                            (:customer_id, :recency, :frequency, :monetary,
                             :r_score, :f_score, :m_score, 0)
                    """),
                    rec,
                )
            session.commit()
            return len(records)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def run(self, reference_date: datetime | None = None) -> pd.DataFrame:
        """Compute RFM and save to database."""
        rfm_df = self.compute(reference_date)
        self.save_to_db(rfm_df)
        return rfm_df
