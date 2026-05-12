# retention_mobile

Flutter mobile app — customer-facing loyalty and coupon viewer with real-time FCM push notifications.

## Features

- 5 demo users (each maps to a real customer_id from the dataset)
- Loyalty score gauge driven by live RFM data from the backend
- Segment-based personalized tips
- Coupon listing with swipe-to-delete
- FCM push notifications (foreground + background)
- Persistent login via `shared_preferences`
- Native Android splash screen with app branding

## Requirements

- Flutter 3.x
- Android emulator or physical device (API 21+)
- Backend running at `http://10.0.2.2:8000` (emulator) or your machine's IP (physical device)

## Setup

```bash
cd retention_mobile
flutter pub get
```

### Firebase Setup

Copy the example files and fill in your project values:
```bash
copy android\app\google-services.json.example android\app\google-services.json
copy lib\firebase_options.dart.example lib\firebase_options.dart
```

Get the real files from Firebase Console → your project → Project Settings.

### API URL

The base URL is set in `lib/services/api_service.dart`. Change it if using a physical device:
```dart
// Emulator (default)
static const String baseUrl = 'http://10.0.2.2:8000';

// Physical device — use your PC's local IP
static const String baseUrl = 'http://192.168.1.X:8000';
```

## Run

```bash
flutter run
```

## Demo Credentials

| Username | Password | Segment |
|----------|----------|---------|
| sarp | 1234 | Champions |
| ali | 1234 | At Risk |
| ayse | 1234 | Loyal |
| mehmet | 1234 | New Customer |
| fatma | 1234 | Hibernating |
