# retention_backend

FastAPI REST API — bridge between the desktop admin app and the Flutter mobile app, with Firebase Cloud Messaging push notification support.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/login` | Demo login (returns customer_id + token) |
| GET | `/users/me` | Current user profile + loyalty score |
| GET | `/users/me/coupons` | List user's coupons |
| DELETE | `/users/me/coupons/{id}` | Delete a coupon |
| POST | `/admin/send-coupon` | Send coupon to a segment (triggers FCM) |
| POST | `/admin/register-fcm-token` | Register device FCM token |
| GET | `/users` | List all demo users (admin) |
| GET | `/docs` | Swagger UI (auto-generated) |

## Setup

```bash
cd retention_backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Firebase Setup

Copy the example file and fill in your credentials:
```bash
copy firebase_credentials.json.example firebase_credentials.json
```

Get the real file from Firebase Console → Project Settings → Service Accounts → Generate new private key.

## Run

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at: `http://localhost:8000/docs`

## Database

Shares `retention_desktop/data/retention.db` (SQLite). The desktop app must run the ML pipeline at least once to populate the database before the backend can serve real data.
