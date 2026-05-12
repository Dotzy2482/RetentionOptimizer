# Demo Guide

Step-by-step walkthrough for presenting the system.

## Before the Demo

1. Start backend: `scripts\start_backend.bat`
2. Open desktop app: `scripts\start_desktop.bat`
3. Start Android emulator from Android Studio
4. Run mobile app: `flutter run` in `retention_mobile/`
5. The database must already be populated (run analysis at least once)

## Demo Flow

### Scene 1 — Data & ML (Desktop)

1. Open the **Veri Analizi** tab
2. Show the loaded dataset stats (5878 customers, transaction history)
3. Click **Analiz Et** — watch RFM scores calculate
4. Switch to **Müşteri Segmentleri** tab
5. Point out the 4 segments: Champions, Loyal, At Risk, Hibernating
6. Show churn probability column — "these are customers about to leave"

### Scene 2 — Coupon Campaign (Desktop → Mobile)

1. Switch to **Kupon Yönetimi** tab
2. Select segment: **At Risk**
3. Pick template: **Geri Kazan** (Winback — 25% discount)
4. Click **Gönder**
5. Watch the send history table update
6. _Simultaneously_ — on the mobile emulator, a push notification arrives

### Scene 3 — Customer View (Mobile)

1. On the emulator, tap the notification → app opens to Coupons screen
2. Show the coupon card with discount and expiry
3. Navigate to **Profilim** tab — show loyalty gauge (e.g. 42/100 for At Risk)
4. Show personalized tip: "Son alışverişiniz uzun süre önce..."
5. Swipe a coupon left to delete it — confirm it disappears

### Scene 4 — Different Segment (Optional)

1. Log out on mobile
2. Log in as **sarp** (Champions segment)
3. Show loyalty score ~85/100, different tip text
4. Back in desktop — send a **VIP Ödül** coupon to Champions
5. Notification arrives on mobile again

## Key Talking Points

- **End-to-end**: one action in the admin dashboard reaches the customer's phone in seconds
- **ML-driven**: segments are computed from real purchase data, not hardcoded
- **Real data**: 5878 customers from UCI Online Retail II dataset
- **Production-like stack**: FastAPI + SQLAlchemy + Firebase Admin, not a toy demo
- **Three platforms**: desktop (PyQt6), API (FastAPI), mobile (Flutter) — all integrated

## Demo Credentials

| Username | Segment | Loyalty Score |
|----------|---------|--------------|
| sarp | Champions | ~85 |
| ayse | Loyal | ~70 |
| ali | At Risk | ~42 |
| fatma | Hibernating | ~20 |
| mehmet | New Customer | ~55 |

Password for all: `1234`
