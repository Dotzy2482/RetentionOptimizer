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


class ImportWorker(QThread):
    """Background thread for data import."""
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)  # ImportResult
    error = pyqtSignal(str)

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            service = ImportService(self.file_path)
            result = service.run(progress_callback=self.progress.emit)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ImportView(QWidget):
    import_completed = pyqtSignal()

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

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(30)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        action_layout.addWidget(self.progress_bar, stretch=1)

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
            value = QLabel("-")
            value.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
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

    def _start_import(self):
        if not self._selected_path:
            return

        self.import_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.summary_group.setVisible(False)

        self._worker = ImportWorker(self._selected_path)
        self._worker.progress.connect(self.progress_bar.setValue)
        self._worker.finished.connect(self._on_import_done)
        self._worker.error.connect(self._on_import_error)
        self._worker.start()

    def _on_import_done(self, result: ImportResult):
        self.progress_bar.setValue(100)
        self.import_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)

        # Update summary
        for key, label in self._summary_labels.items():
            label.setText(f"{getattr(result, key):,}")
        self.summary_group.setVisible(True)

        self.import_completed.emit()

    def _on_import_error(self, error_msg: str):
        self.progress_bar.setValue(0)
        self.import_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        QMessageBox.critical(self, "Import Hatasi", f"Veri yuklenirken hata olustu:\n{error_msg}")
