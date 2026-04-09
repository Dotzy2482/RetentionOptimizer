# Retention Optimization System

Musteri sadakati optimizasyon sistemi. RFM analizi, K-Means segmentasyon ve XGBoost churn tahmini ile musterilerin elde tutulmasini optimize eder.

## Gelistiriciler

- **Gamze Bargan**
- **Erva**

## Teknolojiler

- Python 3.11+
- PyQt6 (masaustu arayuz)
- SQLAlchemy + SQLite (veritabani)
- Scikit-learn (K-Means segmentasyon)
- XGBoost (churn tahmini)
- Matplotlib (grafikler)
- Pandas / NumPy (veri isleme)

## Kurulum

```bash
# Bagimliliklari yukle
pip install -r requirements.txt

# Uygulamayi calistir
python main.py
```

## Ozellikler

### Sprint 1 - Altyapi
- Proje iskeleti ve klasor yapisi
- SQLAlchemy ORM ile veritabani katmani (customers, transactions, rfm_scores, segments)
- Excel/CSV veri import servisi
- PyQt6 ana pencere iskeleti

### Sprint 2 - Analiz ve Dashboard
- Progress bar ile veri yukleme
- RFM analizi (Recency, Frequency, Monetary) ve 1-5 skorlama
- Loyalty score hesaplama (agirlikli formul, 0-100 olcek)
- Dashboard: istatistik kartlari, histogram, scatter plot, pie chart
- Musteri listesi: arama, filtreleme, sayfalama, detay karti

### Sprint 3 - ML ve Segmentasyon
- K-Means musteri segmentasyonu (k=4)
- XGBoost churn tahmin modeli
- Segmentasyon gorunumu: ozet tablo, 3 grafik, filtreleme
- Tahminleme gorunumu: model metrikleri, feature importance, risk tablosu
- Tam pipeline entegrasyonu (QThread ile arka plan isleme)

### Sprint 4 - Export, Polish ve Paketleme
- iOS 26 Liquid Glass tasarim dili (tamamen yeni UI temasi)
- Excel export (openpyxl ile stilize edilmis rapor)
- PDF export (matplotlib ile dashboard ozeti)
- Bos veritabani, tekrar import, bozuk dosya edge case'leri
- Hakkinda dialog'u
- Splash screen
- pytest test suite (17 test)
- PyInstaller ile exe paketleme

## Kullanim

1. **Veri Yukle**: Sol menudan "Veri Yukle" sekmesine git, Excel/CSV dosyasi sec ve import baslat
2. **Dashboard**: Otomatik olarak istatistikler ve grafikler guncellenir
3. **Musteriler**: Tum musterileri listele, ara, filtrele
4. **Segmentasyon**: K-Means segmentlerini ve RFM dagilimlari incele
5. **Tahminleme**: Churn risk skorlarini ve model performansini gor
6. **Export**: Her sayfadaki "Excel Export" veya "PDF Export" butonlari ile raporla

## Test

```bash
python -m pytest tests/ -v
```

## Paketleme (EXE)

```bash
pyinstaller retention.spec
```

Olusturulan exe `dist/RetentionOptimizer/` klasorunde bulunur.

## Proje Yapisi

```
RetentionOptimizer/
  main.py               # Uygulama giris noktasi
  config.py             # Yapilandirma sabitleri
  requirements.txt      # Bagimliliklar
  retention.spec        # PyInstaller yapilandirma
  assets/
    styles.qss          # Liquid Glass QSS temasi
  data/
    database.py          # SQLAlchemy ORM modelleri
    repository.py        # CRUD islemleri
  services/
    import_service.py    # Veri import pipeline
    rfm_service.py       # RFM analizi
    scoring_service.py   # Loyalty skorlama
    segmentation_service.py  # K-Means segmentasyon
    churn_service.py     # XGBoost churn tahmini
  ui/
    main_window.py       # Ana pencere + Hakkinda dialog
    dashboard_view.py    # Dashboard sayfasi
    import_view.py       # Veri yukleme sayfasi
    customer_view.py     # Musteri listesi sayfasi
    segmentation_view.py # Segmentasyon sayfasi
    prediction_view.py   # Tahminleme sayfasi
  utils/
    charts.py            # Matplotlib grafik fonksiyonlari
    export.py            # Excel/PDF export
  tests/
    test_rfm.py          # RFM servis testleri
    test_scoring.py      # Skorlama servis testleri
    test_segmentation.py # Segmentasyon servis testleri
```

## Metodoloji

Agile (Sprint tabanli) gelistirme ile 4 sprint boyunca insa edilmistir.
