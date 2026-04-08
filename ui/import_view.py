import os

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QProgressBar,
    QFileDialog,
    QGroupBox,
    QGridLayout,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from services.import_service import ImportService, ImportResult
from services.rfm_service import RFMService
from services.scoring_service import ScoringService
from services.segmentation_service import SegmentationService
from services.churn_service import ChurnService


class ImportWorker(QThread):
    """Background thread for full pipeline: import -> RFM -> scoring -> segmentation -> churn."""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(object, object)  # (ImportResult, ChurnMetrics or None)
    error = pyqtSignal(str)

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            # Phase 1: Import (0-40%)
            self.status.emit("Dosya okunuyor...")
            service = ImportService(self.file_path)
            df = service.read_file()

            self.status.emit("Veri temizleniyor...")
            df, result = service.clean(df)

            self.status.emit("Veritabanina kaydediliyor...")
            def db_progress(pct):
                self.progress.emit(int(pct * 0.4))
            service.load_to_db(df, result, progress_callback=db_progress)

            # Phase 2: RFM (40-55%)
            self.progress.emit(42)
            self.status.emit("RFM analizi hesaplaniyor...")
            RFMService().run()

            # Phase 3: Scoring (55-65%)
            self.progress.emit(57)
            self.status.emit("Loyalty score hesaplaniyor...")
            ScoringService().run()

            # Phase 4: Segmentation (65-80%)
            self.progress.emit(67)
            self.status.emit("K-Means segmentasyon calistiriliyor...")
            SegmentationService().run()

            # Phase 5: Churn prediction (80-100%)
            self.progress.emit(82)
            self.status.emit("Churn modeli egitiliyor ve tahmin yapiliyor...")
            churn_metrics = ChurnService().run()

            self.progress.emit(100)
            self.status.emit(
                f"Tamamlandi! {result.customer_count:,} musteri yuklendi, "
                f"segmentasyon ve churn analizi yapildi"
            )
            self.finished.emit(result, churn_metrics)
        except Exception as e:
            self.error.emit(str(e))


class AnalysisWorker(QThread):
    """Background thread for running only segmentation + churn (no import)."""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(object)  # ChurnMetrics
    error = pyqtSignal(str)

    def run(self):
        try:
            self.progress.emit(10)
            self.status.emit("K-Means segmentasyon calistiriliyor...")
            SegmentationService().run()

            self.progress.emit(50)
            self.status.emit("Churn modeli egitiliyor ve tahmin yapiliyor...")
            churn_metrics = ChurnService().run()

            self.progress.emit(100)
            self.status.emit("Analiz tamamlandi!")
            self.finished.emit(churn_metrics)
        except Exception as e:
            self.error.emit(str(e))


class ImportView(QWidget):
    import_completed = pyqtSignal(object)  # emits ChurnMetrics or None

    def __init__(self):
        super().__init__()
        self._worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title
        title = QLabel("Veri Yukleme")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # File selection
        file_group = QGroupBox("Dosya Secimi")
        file_layout = QHBoxLayout(file_group)

        self.file_label = QLabel("Henuz dosya secilmedi")
        self.file_label.setObjectName("fileLabel")
        file_layout.addWidget(self.file_label, stretch=1)

        self.browse_btn = QPushButton("Dosya Sec")
        self.browse_btn.setFixedWidth(120)
        self.browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(self.browse_btn)

        layout.addWidget(file_group)

        # Import button and progress
        action_layout = QHBoxLayout()

        self.import_btn = QPushButton("Import Baslat")
        self.import_btn.setObjectName("importButton")
        self.import_btn.setFixedHeight(40)
        self.import_btn.setFixedWidth(160)
        self.import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.import_btn.setEnabled(False)
        self.import_btn.clicked.connect(self._start_import)
        action_layout.addWidget(self.import_btn)

        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setFont(QFont("Segoe UI", 10))
        progress_layout.addWidget(self.status_label)

        action_layout.addLayout(progress_layout, stretch=1)
        layout.addLayout(action_layout)

        # Summary group
        self.summary_group = QGroupBox("Import Ozeti")
        self.summary_group.setVisible(False)
        summary_grid = QGridLayout(self.summary_group)

        self._summary_labels = {}
        fields = [
            ("total_raw", "Toplam Satir (Ham)"),
            ("removed_null_customer", "Silinen: Null Customer ID"),
            ("removed_negative_qty", "Silinen: Negatif Miktar"),
            ("removed_cancelled", "Silinen: Iptal Faturalar (C*)"),
            ("removed_bad_date", "Silinen: Gecersiz Tarih"),
            ("removed_duplicates", "Silinen: Tekrar Eden"),
            ("total_clean", "Temiz Satir Sayisi"),
            ("customer_count", "Benzersiz Musteri Sayisi"),
            ("transaction_count", "Yuklenen Islem Sayisi"),
        ]

        for i, (key, label_text) in enumerate(fields):
            label = QLabel(label_text + ":")
            label.setFont(QFont("Segoe UI", 10))
            label.setObjectName("summaryLabel")
            value = QLabel("-")
            value.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            value.setObjectName("summaryValue")
            value.setAlignment(Qt.AlignmentFlag.AlignRight)
            summary_grid.addWidget(label, i, 0)
            summary_grid.addWidget(value, i, 1)
            self._summary_labels[key] = value

        layout.addWidget(self.summary_group)
        layout.addStretch()

        self._selected_path = None

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Veri Dosyasi Sec",
            "",
            "Veri Dosyalari (*.xlsx *.csv);;Excel (*.xlsx);;CSV (*.csv)",
        )
        if path:
            self._selected_path = path
            self.file_label.setText(os.path.basename(path))
            self.import_btn.setEnabled(True)
            self.summary_group.setVisible(False)
            self.progress_bar.setValue(0)
            self.status_label.setText("")

    def _set_busy(self, busy: bool):
        self.import_btn.setEnabled(not busy and self._selected_path is not None)
        self.browse_btn.setEnabled(not busy)

    def _start_import(self):
        if not self._selected_path:
            return

        self._set_busy(True)
        self.progress_bar.setValue(0)
        self.summary_group.setVisible(False)
        self.status_label.setText("Baslatiliyor...")

        self._worker = ImportWorker(self._selected_path)
        self._worker.progress.connect(self.progress_bar.setValue)
        self._worker.status.connect(self.status_label.setText)
        self._worker.finished.connect(self._on_import_done)
        self._worker.error.connect(self._on_import_error)
        self._worker.start()

    def _on_import_done(self, result: ImportResult, churn_metrics):
        self.progress_bar.setValue(100)
        self._set_busy(False)

        for key, label in self._summary_labels.items():
            label.setText(f"{getattr(result, key):,}")
        self.summary_group.setVisible(True)

        self.import_completed.emit(churn_metrics)

    def _on_import_error(self, error_msg: str):
        self.progress_bar.setValue(0)
        self.status_label.setText("Hata olustu!")
        self._set_busy(False)
        QMessageBox.critical(self, "Import Hatasi", f"Veri yuklenirken hata olustu:\n{error_msg}")
