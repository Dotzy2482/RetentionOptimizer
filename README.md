# Retention Optimizer

> Data-driven customer retention and loyalty optimization system for e-commerce platforms

## Project Overview

This is an Agile university project (Piri Reis University) that combines machine learning, REST APIs, and cross-platform development to build an end-to-end customer retention system.

### Architecture

```
+-----------------+     HTTP      +-----------------+     SQLite     +--------------+
|  Desktop App    | ------------> |   Backend API   | ------------> |   Database   |
|  (PyQt6)        |              |   (FastAPI)     |                |  5878 rows   |
+-----------------+              +--------+--------+                +--------------+
                                          | FCM Push
                                          v
                                 +-----------------+     HTTP      +-----------------+
                                 |    Firebase     | ------------> |   Mobile App    |
                                 | Cloud Messaging |              |   (Flutter)     |
                                 +-----------------+              +-----------------+
```

### Components

| Component | Tech Stack | Purpose |
|-----------|-----------|---------|
| **retention_desktop/** | Python, PyQt6, scikit-learn, XGBoost | Admin dashboard, ML pipeline (RFM + K-Means + churn prediction), coupon management |
| **retention_backend/** | Python, FastAPI, SQLAlchemy, Firebase Admin | REST API layer, FCM push trigger |
| **retention_mobile/** | Flutter, Dart, Provider, FCM | Customer-facing mobile app: loyalty score, coupons, push notifications |

## Features

### Desktop (Admin)
- Import e-commerce transaction data (Excel)
- RFM analysis (Recency, Frequency, Monetary)
- K-Means clustering into 4 customer segments
- XGBoost churn prediction
- Visual dashboards
- Segment-based coupon campaigns with template library

### Mobile (Customer)
- Demo login (5 personas representing different segments)
- Loyalty score gauge with real RFM data
- Personalized tips by segment
- Coupon listing with swipe-to-delete
- Real-time push notifications via Firebase

### Backend (Bridge)
- 8 REST endpoints
- Auto-generated OpenAPI docs (Swagger UI at /docs)
- Firebase Cloud Messaging integration
- Shared SQLite database with desktop app

## Setup

See [docs/SETUP.md](docs/SETUP.md) for detailed setup instructions.

### Quick Start

```bash
git clone https://github.com/Dotzy2482/RetentionOptimizer.git
cd RetentionOptimizer

cd retention_backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

cd retention_desktop
pip install -r requirements.txt
python main.py

cd retention_mobile
flutter pub get
flutter run
```

### Firebase Setup

You need to create your own Firebase project and provide:
1. retention_backend/firebase_credentials.json - Service Account key
2. retention_mobile/android/app/google-services.json - Android config
3. retention_mobile/lib/firebase_options.dart - Flutter config

See the .example files in each location for the expected format.

### Launch Scripts (Windows)

scripts\start_backend.bat   - starts FastAPI server
scripts\start_desktop.bat   - starts PyQt6 desktop app
scripts\start_all.bat       - starts both (mobile emulator separate)

## Academic Context

- Course: Software Engineering Agile Project - Piri Reis University
- Methodology: Scrum (3 sprints)
- Sprint 1: Data ingestion + RFM analysis
- Sprint 2: Clustering + churn prediction
- Sprint 3: Mobile app + Backend API + FCM integration

## License

MIT - see LICENSE
