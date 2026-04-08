import os
from dataclasses import dataclass

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from xgboost import XGBClassifier
import joblib
from sqlalchemy import text

from config import CHURN_THRESHOLD_DAYS, CHURN_MODEL_PATH, MODEL_DIR
from data.database import engine, get_session


@dataclass
class ChurnMetrics:
    accuracy: float
    precision: float
    recall: float
    f1: float
    feature_importances: dict  # feature_name -> importance


class ChurnService:
    """XGBoost-based churn prediction model."""

    FEATURE_COLS = [
        "recency", "frequency", "monetary",
        "r_score", "f_score", "m_score",
        "loyalty_score", "aov", "unique_products",
    ]

    def _build_features(self) -> pd.DataFrame:
        """Build feature matrix from rfm_scores + transactions."""
        with engine.connect() as conn:
            rfm_df = pd.read_sql(text("SELECT * FROM rfm_scores"), conn)
            tx_df = pd.read_sql(text("""
                SELECT customer_id, invoice_no, stock_code, quantity, price
                FROM transactions
            """), conn)

        if rfm_df.empty or tx_df.empty:
            return pd.DataFrame()

        # AOV = total revenue / number of unique orders
        tx_df["revenue"] = tx_df["quantity"] * tx_df["price"]
        agg = tx_df.groupby("customer_id").agg(
            total_revenue=("revenue", "sum"),
            n_orders=("invoice_no", "nunique"),
            unique_products=("stock_code", "nunique"),
        ).reset_index()
        agg["aov"] = (agg["total_revenue"] / agg["n_orders"]).round(2)

        df = rfm_df.merge(agg[["customer_id", "aov", "unique_products"]], on="customer_id", how="left")
        df["aov"] = df["aov"].fillna(0)
        df["unique_products"] = df["unique_products"].fillna(0).astype(int)

        # Churn label: 1 if recency > threshold
        df["churn"] = (df["recency"] > CHURN_THRESHOLD_DAYS).astype(int)

        return df

    def train(self) -> ChurnMetrics:
        """Train the XGBoost model and return metrics."""
        df = self._build_features()
        if df.empty:
            raise ValueError("No data available for training")

        X = df[self.FEATURE_COLS]
        y = df["churn"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y,
        )

        model = XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            eval_metric="logloss",
        )
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        metrics = ChurnMetrics(
            accuracy=round(accuracy_score(y_test, y_pred), 4),
            precision=round(precision_score(y_test, y_pred, zero_division=0), 4),
            recall=round(recall_score(y_test, y_pred, zero_division=0), 4),
            f1=round(f1_score(y_test, y_pred, zero_division=0), 4),
            feature_importances=dict(zip(self.FEATURE_COLS, model.feature_importances_.round(4))),
        )

        # Save model
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(model, CHURN_MODEL_PATH)

        self._model = model
        return metrics

    def predict(self) -> pd.DataFrame:
        """Predict churn probability for all customers."""
        df = self._build_features()
        if df.empty:
            return pd.DataFrame()

        # Load model if not in memory
        if not hasattr(self, "_model"):
            if os.path.exists(CHURN_MODEL_PATH):
                self._model = joblib.load(CHURN_MODEL_PATH)
            else:
                raise FileNotFoundError("Model not trained yet. Call train() first.")

        X = df[self.FEATURE_COLS]
        proba = self._model.predict_proba(X)[:, 1]

        df["churn_probability"] = np.round(proba, 4)
        return df[["customer_id", "churn_probability"]]

    def save_predictions(self, pred_df: pd.DataFrame) -> int:
        """Update churn_probability in segments table."""
        if pred_df.empty:
            return 0

        session = get_session()
        try:
            for _, row in pred_df.iterrows():
                session.execute(
                    text("""
                        UPDATE segments
                        SET churn_probability = :prob
                        WHERE customer_id = :cid
                    """),
                    {"cid": int(row["customer_id"]), "prob": float(row["churn_probability"])},
                )
            session.commit()
            return len(pred_df)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def run(self) -> ChurnMetrics:
        """Full pipeline: train -> predict -> save."""
        metrics = self.train()
        pred_df = self.predict()
        self.save_predictions(pred_df)
        return metrics
