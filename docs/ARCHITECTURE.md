# Architecture

## System Overview

Retention Optimizer is a three-tier system: a Python desktop app (admin), a FastAPI backend (bridge), and a Flutter mobile app (customer).

```
retention_desktop  ──POST /admin/send-coupon──►  retention_backend  ──FCM──►  Firebase
      │                                                  │                         │
      └──────────────── shared SQLite ──────────────────►│                         │
                                                         │                         ▼
                                               GET /users/me/*       retention_mobile (Flutter)
```

## Component Details

### retention_desktop (PyQt6)

Entry point: `main.py` → `MainWindow`

| Module | Purpose |
|--------|---------|
| `ui/data_view.py` | Dataset import + RFM calculation |
| `ui/segments_view.py` | Cluster visualization, churn scores |
| `ui/coupon_view.py` | Coupon template selection + send |
| `services/ml_pipeline.py` | K-Means, XGBoost training |
| `services/backend_client.py` | HTTP calls to FastAPI |
| `services/coupon_templates.py` | 6 template definitions |
| `models/` | Serialized sklearn/XGBoost artifacts (gitignored) |
| `data/retention.db` | SQLite — shared with backend (gitignored) |

### retention_backend (FastAPI)

Entry point: `main.py` → FastAPI app

| Module | Purpose |
|--------|---------|
| `routers/auth.py` | POST /auth/login |
| `routers/users.py` | GET /me, GET /me/coupons, DELETE coupon |
| `routers/admin.py` | POST /admin/send-coupon, register-fcm-token |
| `database.py` | SQLAlchemy engine + session |
| `models.py` | ORM models: Customer, Coupon, FCMToken |
| `schemas.py` | Pydantic v2 request/response schemas |
| `firebase_service.py` | Firebase Admin SDK wrapper |

### retention_mobile (Flutter)

Entry point: `lib/main.dart` → `MyApp` → `Consumer<AuthProvider>`

| Path | Purpose |
|------|---------|
| `lib/screens/login_screen.dart` | Demo login form |
| `lib/screens/main_screen.dart` | Bottom nav shell |
| `lib/screens/profile_screen.dart` | Loyalty gauge + segment tips |
| `lib/screens/coupons_screen.dart` | Coupon list + swipe-to-delete |
| `lib/screens/splash_screen.dart` | Auth-wait splash |
| `lib/providers/auth_provider.dart` | Login state, auto-login, FCM token reg |
| `lib/providers/coupons_provider.dart` | Coupon list state |
| `lib/services/api_service.dart` | HTTP client (Dio/http) |
| `lib/services/fcm_service.dart` | Firebase Messaging setup |
| `lib/widgets/app_logo.dart` | Shared brand logo widget |
| `lib/theme/app_colors.dart` | Color tokens (primary: #7C3AED) |

## Database Schema

```sql
-- Populated by ML pipeline in retention_desktop
CREATE TABLE customers (
    customer_id   TEXT PRIMARY KEY,
    segment       TEXT,   -- Champions / Loyal / At Risk / Hibernating / New
    churn_prob    REAL,
    recency       INTEGER,
    frequency     INTEGER,
    monetary      REAL,
    loyalty_score INTEGER  -- 0-100 computed from RFM
);

CREATE TABLE coupons (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id   TEXT REFERENCES customers(customer_id),
    title         TEXT,
    description   TEXT,
    discount_pct  INTEGER,
    valid_until   TEXT,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fcm_tokens (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id   TEXT,
    token         TEXT UNIQUE,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## Request Flow: Coupon Campaign

```
Admin picks segment in coupon_view.py
  → BackendClient.send_coupon(segment, template)
    → POST /admin/send-coupon  {segment, title, description, discount_pct}
      → Query customers WHERE segment = ?
      → INSERT INTO coupons for each customer
      → Fetch FCM tokens for those customers
      → firebase_service.send_multicast(tokens, notification)
        → FCM delivers push to Flutter app
          → Flutter shows notification banner
          → On tap: navigate to CouponsScreen, reload list
```

## ML Pipeline

1. **Load** — `datasets/online_retail_II.xlsx` → pandas DataFrame
2. **Clean** — drop nulls, negative quantities, cancelled orders
3. **RFM** — compute Recency (days since last purchase), Frequency (order count), Monetary (total spend) per customer
4. **Normalize** — StandardScaler on RFM features
5. **Cluster** — KMeans(n_clusters=4), assign segment labels
6. **Churn** — XGBoostClassifier trained on RFM + segment features
7. **Persist** — write customers table to SQLite; save model artifacts to `models/`
