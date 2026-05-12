# RetentionOptimizer Mobile App

Bu, "Retention Optimization System" adlı bir Python masaüstü uygulamasının mobil eşlikçisidir. Müşteri sadakat puanlarını gösterir, kupon ve bildirimleri yönetir.

## Tech Stack
- Flutter 3.41+ / Dart 3.11+
- State management: Provider (basit tutuyoruz)
- HTTP: `http` paketi (sonradan eklenecek)
- Push notifications: Firebase Cloud Messaging (sonradan eklenecek)

## Mimari Kurallar
- Klasör yapısı: lib/screens, lib/models, lib/services, lib/widgets, lib/theme
- Her ekran kendi dosyasında, snake_case isim (örn. home_screen.dart)
- Widget'lar 300 satırı geçmemeli, geçerse parçala
- Mock data önce, gerçek API sonra

## Tasarım Sistemi (Masaüstü ile birebir aynı renkler)

### Renkler
- Background: #F2F2F7
- Surface: #FFFFFF
- Primary: #7C3AED (mor)
- Primary Dark: #6D28D9
- Primary Darker: #5B21B6
- Success: #059669
- Danger: #DC2626
- Text Primary: #1C1C1E
- Text Secondary: #6B7280
- Text Tertiary: #9CA3AF
- Border: rgba(0,0,0,0.08)

### Boyutlar
- Border radius card: 14
- Border radius button: 10
- Border radius input: 10

### Tipografi
- Font: Inter (Google Fonts)
- Page title: 20px bold
- Section title: 13px bold
- Body: 12px regular
- Caption: 11px regular

## Domain Modeli

### User
- customerId (int)
- name (String)
- email (String)
- loyaltyScore (int 0-100)
- segment (enum: lowEngagement, atRisk, active, highValueLoyal)
- fcmToken (String?, nullable)
- avatarInitial (String) - örn. "S", "A"
- segmentDescription (String) - segment için Türkçe açıklama

### Coupon
- couponId (int)
- customerId (int)
- code (String)
- discountPercent (int)
- title (String)
- message (String)
- isUsed (bool)
- createdAt (DateTime)
- expiresAt (DateTime)

## Segment Adlandırma (Türkçe Etiketler)
- lowEngagement → "Yeni Müşteri"
- atRisk → "Risk Altında"
- active → "Aktif Müşteri"
- highValueLoyal → "Sadık Müşteri"

## Backend Integration
- Base URL: http://10.0.2.2:8000 (Android emulator default)
- ApiService: lib/services/api_service.dart (singleton)
- Loading: skeleton (shimmer paketi) — lib/widgets/skeleton.dart
- Error: ErrorView widget + retry button — lib/widgets/error_view.dart
- Config: lib/config/api_config.dart (base URL, timeouts)
- Demo users API'den GELMEZ — login_screen'de MockData.demoUsers hardcoded liste, customer_id ile API'ye login isteği gider

## Geliştirme Sırası
1. ✅ Proje oluşturuldu
2. ✅ Tema dosyası ve mock data
3. ✅ Ana ekran (Profil + Loyalty Score)
4. ✅ Kuponlarım ekranı
5. ✅ Bottom navigation
6. ✅ Backend (FastAPI) entegrasyonu
7. ⬜ Firebase FCM

## Önemli Kurallar
- Türkçe arayüz metinleri kullan (kullanıcılar Türk)
- Hardcoded string'leri AppStrings sınıfına topla
- Animasyonlu loyalty gauge: TweenAnimationBuilder kullan
- Dark mode şu an YOK, sadece light tema
- Counter app artıkları lib/main.dart'ta, temizlenecek
