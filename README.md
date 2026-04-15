# Retention Optimization System

Musteri sadakati optimizasyon sistemi. RFM analizi, K-Means segmentasyon ve XGBoost churn tahmini ile musterilerin elde tutulmasini optimize eder.

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

### Sprint 1 - Altyapi (Tamamlandi)
- Proje iskeleti ve klasor yapisi
- SQLAlchemy ORM ile veritabani katmani (customers, transactions, rfm_scores, segments)
- Excel/CSV veri import servisi (5 asamali pipeline: okuma → temizleme → DB → RFM → skorlama)
- PyQt6 ana pencere iskeleti, ozel NavButton ve SplashScreen

### Sprint 2 - Analiz, ML ve Tam Uygulama (Tamamlandi)
- Progress bar ile veri yukleme (animasyonlu 5-adim ilerleme cubugu)
- RFM analizi (Recency, Frequency, Monetary) ve 1-5 skorlama
- Loyalty score hesaplama (agirlikli formul, 0-100 olcek)
- Dashboard: 4 istatistik karti, sadakat histogram, RFM scatter plot, segment pie chart
- Musteri listesi: arama, filtreleme, sayfalama (100 satir/sayfa), detay karti
- K-Means musteri segmentasyonu (k=4): Low Engagement / At Risk / Active / High Value Loyal
- XGBoost churn tahmin modeli: risk skorlama, feature importance, model metrikleri
- Segmentasyon gorunumu: pasta grafigi, RFM cubuk grafigi, scatter plot, filtreleme
- Tahminleme gorunumu: model metrikleri, feature importance, renk kodlu risk tablosu
- Excel export (openpyxl ile stilize edilmis rapor)
- PDF export (matplotlib ile dashboard ozeti)
- Splash screen ve Hakkinda dialog'u
- pytest test suite (17 test: RFM, skorlama, segmentasyon)
- PyInstaller ile Windows exe paketleme

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

Agile (Sprint tabanli) gelistirme ile 2 sprint boyunca insa edilmistir.
