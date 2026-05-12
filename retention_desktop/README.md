# retention_desktop

PyQt6 admin dashboard with ML-powered customer segmentation and coupon management.

## What it does

- Loads the Online Retail II dataset (Excel) and stores transactions in SQLite
- Runs RFM analysis → K-Means clustering (4 segments) → XGBoost churn prediction
- Displays results in tabbed dashboards with charts
- Sends segment-targeted coupon campaigns via the backend API (which triggers FCM push)

## Requirements

- Python 3.9+
- Shared SQLite database (`data/retention.db`) — created on first run

## Setup

```bash
cd retention_desktop
pip install -r requirements.txt
python main.py
```

## Usage

1. **Veri Analizi tab** — import dataset, run RFM + clustering
2. **Müşteri Segmentleri tab** — view cluster summaries and churn scores
3. **Kupon Yönetimi tab** — pick a segment, choose a template, send campaign

The backend must be running (`scripts\start_backend.bat`) for coupon dispatch and FCM push to work.

## Build (optional)

```bash
pyinstaller retention.spec
```

Output: `dist/RetentionOptimizer/`
