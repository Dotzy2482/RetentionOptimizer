# Setup Guide

## Prerequisites

| Tool | Version | Required for |
|------|---------|-------------|
| Python | 3.9+ | desktop + backend |
| pip | latest | Python packages |
| Flutter SDK | 3.x | mobile |
| Android Studio | latest | emulator |
| Git | any | cloning |

## 1. Clone

```bash
git clone https://github.com/Dotzy2482/RetentionOptimizer.git
cd RetentionOptimizer
```

## 2. Firebase Project

You need a Firebase project with Cloud Messaging enabled.

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create a project (or use existing)
3. Enable **Cloud Messaging** in project settings

### Backend credentials

- Firebase Console → Project Settings → Service Accounts → **Generate new private key**
- Save as `retention_backend/firebase_credentials.json`

### Mobile credentials

- Firebase Console → Project Settings → Your apps → Add Android app
  - Package name: `com.example.retention_mobile`
  - Download `google-services.json` → save to `retention_mobile/android/app/`
- Run: `flutterfire configure` (or manually create `lib/firebase_options.dart`)

See `.example` files for the expected structure.

## 3. Backend

```bash
cd retention_backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Verify: open `http://localhost:8000/docs` — Swagger UI should appear.

## 4. Desktop App

```bash
cd retention_desktop
pip install -r requirements.txt
python main.py
```

**First run:**
1. Go to **Veri Analizi** tab
2. Click **Veri Yükle** and select `datasets/online_retail_II.xlsx`
3. Click **Analiz Et** — this runs RFM + clustering + churn prediction
4. The SQLite database is populated; backend can now serve real data

## 5. Mobile App

```bash
cd retention_mobile
flutter pub get
```

Start an Android emulator from Android Studio, then:

```bash
flutter run
```

**Default API URL** (emulator): `http://10.0.2.2:8000`

For a physical device, edit `lib/services/api_service.dart` and replace `10.0.2.2` with your PC's local IP address.

## 6. Windows Quick Launch

After setup, use the scripts:

```
scripts\start_backend.bat   — terminal 1
scripts\start_desktop.bat   — terminal 2
scripts\start_all.bat       — both at once
```

Mobile emulator is started separately from Android Studio.

## Troubleshooting

**Backend: `firebase_credentials.json` not found**
→ Copy and fill `firebase_credentials.json.example`

**Mobile: network error on login**
→ Check emulator is running, backend is on port 8000, and `baseUrl` in `api_service.dart` is correct

**Desktop: no data in Segments tab**
→ Run the analysis in Veri Analizi tab first to populate the database

**Flutter build fails on desugaring**
→ Ensure `compileOptions { coreLibraryDesugaringEnabled true }` is in `android/app/build.gradle`
