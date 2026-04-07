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

# App settings
APP_NAME = "Retention Optimization System"
APP_VERSION = "0.1.0"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
