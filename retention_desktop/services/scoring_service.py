import pandas as pd
from sqlalchemy import text

from config import RFM_WEIGHTS
from data.database import engine, get_session


class ScoringService:
    """Calculates loyalty scores from RFM scores using weighted formula."""

    def compute(self) -> pd.DataFrame:
        """Load RFM scores and compute loyalty score.

        Formula: Loyalty = (R_score * w_r + F_score * w_f + M_score * w_m)
                 normalized to 0-100 scale.
        """
        with engine.connect() as conn:
            df = pd.read_sql(text("SELECT * FROM rfm_scores"), conn)

        if df.empty:
            return pd.DataFrame()

        w_r = RFM_WEIGHTS["recency"]
        w_f = RFM_WEIGHTS["frequency"]
        w_m = RFM_WEIGHTS["monetary"]

        # Raw weighted score (scores are 1-5)
        df["raw_score"] = (
            df["r_score"] * w_r
            + df["f_score"] * w_f
            + df["m_score"] * w_m
        )

        # Min possible = 1*(w_r+w_f+w_m) = 1.0, Max = 5*(w_r+w_f+w_m) = 5.0
        min_possible = 1.0 * (w_r + w_f + w_m)
        max_possible = 5.0 * (w_r + w_f + w_m)

        # Normalize to 0-100
        df["loyalty_score"] = (
            (df["raw_score"] - min_possible) / (max_possible - min_possible) * 100
        ).round(2)

        df.drop(columns=["raw_score"], inplace=True)
        return df

    def save_to_db(self, df: pd.DataFrame) -> int:
        """Update loyalty_score column in rfm_scores table."""
        if df.empty:
            return 0

        session = get_session()
        try:
            for _, row in df.iterrows():
                session.execute(
                    text("""
                        UPDATE rfm_scores
                        SET loyalty_score = :loyalty_score
                        WHERE customer_id = :customer_id
                    """),
                    {
                        "customer_id": int(row["customer_id"]),
                        "loyalty_score": float(row["loyalty_score"]),
                    },
                )
            session.commit()
            return len(df)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def run(self) -> pd.DataFrame:
        """Compute and save loyalty scores."""
        df = self.compute()
        self.save_to_db(df)
        return df
