import pandas as pd
from sqlalchemy import text

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from data.database import engine
from utils.charts import (
    create_canvas,
    loyalty_histogram,
    rfm_scatter,
    segment_pie,
)

LOYALTY_BINS = [0, 25, 50, 75, 100]
LOYALTY_LABELS = ["Dusuk (0-25)", "Orta (25-50)", "Iyi (50-75)", "Harika (75-100)"]


class AnalysisWorker(QThread):
    """Runs segmentation + churn in background."""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(object)  # ChurnMetrics
    error = pyqtSignal(str)

    def run(self):
        try:
            from services.segmentation_service import SegmentationService
            from services.churn_service import ChurnService

            self.progress.emit(10)
            self.status.emit("K-Means segmentasyon calistiriliyor...")
            SegmentationService().run()

            self.progress.emit(50)
            self.status.emit("Churn modeli egitiliyor...")
            churn_metrics = ChurnService().run()

            self.progress.emit(100)
            self.status.emit("Analiz tamamlandi!")
            self.finished.emit(churn_metrics)
        except Exception as e:
            self.error.emit(str(e))


class StatCard(QFrame):
    def __init__(self, title: str, value: str, color: str = "#7C3AED"):
        super().__init__()
        self.setObjectName("statCard")
        self.setFixedHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 10))
        title_label.setStyleSheet("color: #6B7280;")
        layout.addWidget(title_label)

        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(self.value_label)

    def set_value(self, value: str):
        self.value_label.setText(value)


class DashboardView(QWidget):
    analysis_completed = pyqtSignal(object)  # ChurnMetrics

    def __init__(self):
        super().__init__()
        self._worker = None
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(28, 24, 28, 28)
        self.main_layout.setSpacing(16)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setObjectName("pageTitle")
        title_row.addWidget(title)
        title_row.addStretch()

        self.export_pdf_btn = QPushButton("PDF Export")
        self.export_pdf_btn.setObjectName("exportButton")
        self.export_pdf_btn.setFixedHeight(35)
        self.export_pdf_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_pdf_btn.clicked.connect(self._export_pdf)
        title_row.addWidget(self.export_pdf_btn)

        self.analysis_btn = QPushButton("Analiz Calistir")
        self.analysis_btn.setObjectName("importButton")
        self.analysis_btn.setFixedHeight(35)
        self.analysis_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.analysis_btn.clicked.connect(self._run_analysis)
        title_row.addWidget(self.analysis_btn)

        self.refresh_btn = QPushButton("Yenile")
        self.refresh_btn.setFixedHeight(35)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.refresh)
        title_row.addWidget(self.refresh_btn)

        self.main_layout.addLayout(title_row)

        # Status label for analysis
        self.analysis_status = QLabel("")
        self.analysis_status.setObjectName("statusLabel")
        self.analysis_status.setFont(QFont("Segoe UI", 10))
        self.main_layout.addWidget(self.analysis_status)

        # Stat cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.card_customers = StatCard("Toplam Musteri", "-", "#7C3AED")
        self.card_avg_loyalty = StatCard("Ort. Loyalty Score", "-", "#059669")
        self.card_best_segment = StatCard("En Iyi Segment", "-", "#7C3AED")
        self.card_worst_segment = StatCard("En Dusuk Segment", "-", "#DC2626")

        cards_layout.addWidget(self.card_customers)
        cards_layout.addWidget(self.card_avg_loyalty)
        cards_layout.addWidget(self.card_best_segment)
        cards_layout.addWidget(self.card_worst_segment)

        self.main_layout.addLayout(cards_layout)

        # Charts - row 1: histogram + scatter (equal width)
        charts_row1 = QHBoxLayout()
        charts_row1.setSpacing(12)
        self.hist_fig, self.hist_canvas = create_canvas(6, 3.8)
        self.scatter_fig, self.scatter_canvas = create_canvas(6, 3.8)
        charts_row1.addWidget(self.hist_canvas)
        charts_row1.addWidget(self.scatter_canvas)
        self.main_layout.addLayout(charts_row1)

        # Charts - row 2: pie (wider canvas so external legend fits)
        self.pie_fig, self.pie_canvas = create_canvas(9, 4.2)
        self.pie_canvas.setMinimumHeight(360)
        self.main_layout.addWidget(self.pie_canvas)
        self.main_layout.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "PDF Raporu Kaydet", "dashboard_raporu.pdf", "PDF Dosyasi (*.pdf)"
        )
        if not path:
            return
        try:
            from utils.export import export_dashboard_pdf
            export_dashboard_pdf(path)
            QMessageBox.information(self, "Export Basarili", f"PDF raporu kaydedildi:\n{path}")
        except PermissionError:
            QMessageBox.warning(self, "Hata", "Dosya acik. Lutfen kapatip tekrar deneyin.")
        except Exception as e:
            QMessageBox.critical(self, "Export Hatasi", str(e))

    def _run_analysis(self):
        """Run segmentation + churn in background thread."""
        self.analysis_btn.setEnabled(False)
        self.analysis_status.setText("Analiz calistiriliyor...")

        self._worker = AnalysisWorker()
        self._worker.status.connect(self.analysis_status.setText)
        self._worker.finished.connect(self._on_analysis_done)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.start()

    def _on_analysis_done(self, churn_metrics):
        self.analysis_btn.setEnabled(True)
        self.analysis_status.setText("Analiz tamamlandi!")
        self.refresh()
        self.analysis_completed.emit(churn_metrics)

    def _on_analysis_error(self, error_msg: str):
        self.analysis_btn.setEnabled(True)
        self.analysis_status.setText(f"Hata: {error_msg}")

    def refresh(self):
        """Reload data from database and update all visuals."""
        try:
            with engine.connect() as conn:
                rfm_df = pd.read_sql(text("SELECT * FROM rfm_scores"), conn)
                seg_df = pd.read_sql(text("SELECT * FROM segments"), conn)
        except Exception:
            return

        if rfm_df.empty:
            self.card_customers.set_value("0")
            self.card_avg_loyalty.set_value("-")
            self.card_best_segment.set_value("-")
            self.card_worst_segment.set_value("-")
            # Show empty-state hint on histogram area
            self.hist_fig.clear()
            ax = self.hist_fig.add_subplot(111)
            ax.set_facecolor("#F2F2F7")
            ax.text(0.5, 0.5, "Henuz veri yuklenmedi.\nVeri Yukle sayfasindan baslayabilirsiniz.",
                    ha="center", va="center", fontsize=12, color="#9CA3AF",
                    transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)
            self.hist_canvas.draw()
            return

        # Update stat cards
        total = len(rfm_df)
        avg_loyalty = rfm_df["loyalty_score"].mean()
        self.card_customers.set_value(f"{total:,}")
        self.card_avg_loyalty.set_value(f"{avg_loyalty:.1f}")

        # Segment cards - use real segments if available, fallback to loyalty-based
        if not seg_df.empty:
            seg_avg = seg_df.merge(rfm_df[["customer_id", "loyalty_score"]], on="customer_id")
            seg_stats = seg_avg.groupby("segment_label")["loyalty_score"].mean()
        else:
            rfm_df["_group"] = pd.cut(
                rfm_df["loyalty_score"], bins=LOYALTY_BINS, labels=LOYALTY_LABELS, include_lowest=True
            )
            seg_stats = rfm_df.groupby("_group")["loyalty_score"].mean()

        if not seg_stats.empty:
            self.card_best_segment.set_value(str(seg_stats.idxmax()))
            self.card_worst_segment.set_value(str(seg_stats.idxmin()))

        # Loyalty histogram
        loyalty_histogram(rfm_df["loyalty_score"].values, self.hist_fig)
        self.hist_canvas.draw()

        # RFM scatter
        rfm_scatter(
            rfm_df["frequency"].values,
            rfm_df["monetary"].values,
            rfm_df["recency"].values,
            self.scatter_fig,
        )
        self.scatter_canvas.draw()

        # Segment pie - use real segments if available
        if not seg_df.empty:
            counts = seg_df["segment_label"].value_counts()
        else:
            rfm_df["_group"] = pd.cut(
                rfm_df["loyalty_score"], bins=LOYALTY_BINS, labels=LOYALTY_LABELS, include_lowest=True
            )
            counts = rfm_df["_group"].value_counts().sort_index()
        segment_pie(counts.index.tolist(), counts.values.tolist(), self.pie_fig)
        self.pie_canvas.draw()
