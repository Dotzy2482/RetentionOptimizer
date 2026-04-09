import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database
DB_PATH = os.path.join(BASE_DIR, "data", "retention.db")
DB_URL = f"sqlite:///{DB_PATH}"

# Dataset
DATASET_PATH = os.path.join(BASE_DIR, "datasets", "online_retail_II.xlsx")

# RFM weights for loyalty score calculation
RFM_WEIGHTS = {
    "recency": 0.25,
    "frequency": 0.35,
    "monetary": 0.40,
}

# RFM score bins (1-5 scale)
RFM_SCORE_BINS = 5

# Churn threshold (days since last purchase)
CHURN_THRESHOLD_DAYS = 90

# Segmentation
N_CLUSTERS = 4
SEGMENT_LABELS = {
    "low": "Low Engagement",
    "mid_low": "At Risk",
    "mid_high": "Active Customer",
    "high": "High Value Loyal",
}

# Churn model
MODEL_DIR = os.path.join(BASE_DIR, "models", "trained")
CHURN_MODEL_PATH = os.path.join(MODEL_DIR, "churn_model.joblib")

# App settings
APP_NAME = "Retention Optimization System"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
