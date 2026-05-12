# Retention Backend (FastAPI)

Bu backend, RetentionOptimizer ekosisteminin API katmanıdır. Mobil ve masaüstü uygulamalar arasında veri köprüsü kurar.

## Tech Stack
- Python 3.11+
- FastAPI (REST API)
- SQLAlchemy 2.0 (ORM)
- Pydantic v2 (validation)
- SQLite (mevcut retention.db'yi paylaşır)
- Uvicorn (ASGI server)

## Veritabanı
Path: ../RetentionOptimizer/data/retention.db
Bu veritabanı RetentionOptimizer (PyQt6 masaüstü) tarafından doldurulur. 
Backend'in EKLEDİĞİ tablolar: users, coupons, notification_logs.
Backend'in OKUDUĞU tablolar: customers, rfm_scores, segments, transactions.

## Klasör Yapısı
- main.py: FastAPI app entry, router include
- database.py: SQLAlchemy engine, SessionLocal, Base
- models.py: ORM modelleri (User, Coupon, NotificationLog)
- schemas.py: Pydantic request/response şemaları
- routers/auth.py: POST /api/login
- routers/users.py: GET /api/users/{id}/profile, GET /api/users/{id}/coupons
- routers/admin.py: POST /api/admin/send-coupon
- seed.py: 5 demo user'ı yazan script
- requirements.txt

## Demo User Listesi (Sabit)
| Name           | customer_id | Email             | Avatar |
|----------------|-------------|-------------------|--------|
| Selin Aydın    | 12380       | selin@demo.com    | S      |
| Ayşe Yılmaz    | 12348       | ayse@demo.com     | A      |
| Can Öztürk     | 12372       | can@demo.com      | C      |
| Mehmet Demir   | 12385       | mehmet@demo.com   | M      |
| Zeynep Kaya    | 12353       | zeynep@demo.com   | Z      |

Bu customer_id'ler RetentionOptimizer veritabanındaki gerçek müşterilere karşılık geliyor. Profil endpoint'i bu ID'ler üzerinden rfm_scores ve segments tablolarına JOIN yapar.

## Network Konfigürasyonu
- Server: 0.0.0.0:8000 (her ağ arayüzünden erişilebilir)
- Android emülatör erişimi: http://10.0.2.2:8000
- Aynı Wi-Fi'daki cihazlar: http://<host_ip>:8000
- CORS: tüm originlere izin (akademik proje)

## Geliştirme Sırası
1. ⬜ Bağımlılıklar kurulumu, FastAPI iskelet
2. ⬜ Database connection + ORM modelleri
3. ⬜ Pydantic schemas
4. ⬜ Auth endpoint (login)
5. ⬜ Users endpoints (profile, coupons)
6. ⬜ Admin endpoint (send-coupon)
7. ⬜ Seed script (demo users + sample coupons)

## Önemli Kurallar
- Türkçe mesajlar/error string'leri
- Mevcut RetentionOptimizer veritabanına ZARAR VERMEK YASAK (sadece okuma + yeni tablolar ekleme)
- Yeni tablolar IF NOT EXISTS ile oluşturulmalı, idempotent olmalı
- Her endpoint'te try/except + uygun HTTP statüsü dön
