import os
import sys


def _get_app_dir() -> str:
    """Return the directory that should be used for writable app data (db, models).

    * When running as a PyInstaller bundle  → directory that contains the .exe
    * When running from source              → directory that contains this file
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _get_resource_dir() -> str:
    """Return the directory where read-only bundled assets live.

    * PyInstaller extracts assets to sys._MEIPASS at runtime.
    * In source mode this is the same as the project root.
    """
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.abspath(__file__))


APP_DIR = _get_app_dir()
RESOURCE_DIR = _get_resource_dir()

# Ensure writable data sub-directory exists
_data_dir = os.path.join(APP_DIR, "data")
os.makedirs(_data_dir, exist_ok=True)

# Database  (written next to the exe so it persists across runs)
DB_PATH = os.path.join(_data_dir, "retention.db")
DB_URL = f"sqlite:///{DB_PATH}"

# Dataset  (read-only; bundled inside the exe or in the source tree)
DATASET_PATH = os.path.join(RESOURCE_DIR, "datasets", "online_retail_II.xlsx")

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

# Churn model  (written next to the exe so trained models persist)
MODEL_DIR = os.path.join(APP_DIR, "models", "trained")
os.makedirs(MODEL_DIR, exist_ok=True)
CHURN_MODEL_PATH = os.path.join(MODEL_DIR, "churn_model.joblib")

# App settings
APP_NAME = "Retention Optimization System"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
