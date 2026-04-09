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
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QGridLayout,
    QComboBox,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from data.database import engine
from utils.charts import create_canvas, feature_importance_bar

ROWS_PER_PAGE = 100


def _risk_level(prob: float) -> tuple[str, QColor, QColor]:
    """Returns (label, text_color, row_background_color)."""
    if prob < 0.3:
        return "Dusuk", QColor("#059669"), QColor("#F0FDF4")
    elif prob < 0.7:
        return "Orta", QColor("#D97706"), QColor("#FFFBEB")
    else:
        return "Yuksek", QColor("#DC2626"), QColor("#FEF2F2")


class PredictionView(QWidget):
    def __init__(self):
        super().__init__()
        self._df = pd.DataFrame()
        self._filtered_df = pd.DataFrame()
        self._current_page = 0
        self._metrics = None
        self._feature_importances = None
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(28, 24, 28, 28)
        main_layout.setSpacing(16)

        # Title
        title_row = QHBoxLayout()
        title = QLabel("Churn Tahminleme")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setObjectName("pageTitle")
        title_row.addWidget(title)
        title_row.addStretch()

        self.export_btn = QPushButton("Excel Export")
        self.export_btn.setObjectName("exportButton")
        self.export_btn.setFixedHeight(35)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self._export_excel)
        title_row.addWidget(self.export_btn)

        self.refresh_btn = QPushButton("Yenile")
        self.refresh_btn.setFixedHeight(35)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.refresh)
        title_row.addWidget(self.refresh_btn)

        main_layout.addLayout(title_row)

        # Metrics card + Feature importance side by side
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(12)

        # Metrics group
        metrics_group = QGroupBox("Model Performansı")
        metrics_group.setMinimumWidth(280)
        metrics_grid = QGridLayout(metrics_group)
        self._metric_labels = {}
        metric_names = [
            ("accuracy", "Accuracy"),
            ("precision", "Precision"),
            ("recall", "Recall"),
            ("f1", "F1 Score"),
        ]
        for i, (key, display_name) in enumerate(metric_names):
            lbl = QLabel(f"{display_name}:")
            lbl.setFont(QFont("Segoe UI", 11))
            lbl.setObjectName("summaryLabel")
            val = QLabel("-")
            val.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            val.setObjectName("summaryValue")
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            metrics_grid.addWidget(lbl, i, 0)
            metrics_grid.addWidget(val, i, 1)
            self._metric_labels[key] = val

        metrics_row.addWidget(metrics_group)

        # Feature importance chart
        self.fi_fig, self.fi_canvas = create_canvas(6, 3.8)
        metrics_row.addWidget(self.fi_canvas)

        main_layout.addLayout(metrics_row)

        # Risk filter
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        risk_label = QLabel("Risk Seviyesi:")
        risk_label.setObjectName("filterLabel")
        risk_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        filter_row.addWidget(risk_label)

        self.risk_filter = QComboBox()
        self.risk_filter.addItems(["Tumu", "Yuksek Risk", "Orta Risk", "Dusuk Risk"])
        self.risk_filter.setFixedWidth(160)
        self.risk_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.risk_filter)

        self.count_label = QLabel("")
        self.count_label.setObjectName("filterLabel")
        filter_row.addStretch()
        filter_row.addWidget(self.count_label)

        main_layout.addLayout(filter_row)

        # Churn risk table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Musteri ID", "Segment", "Churn Olasiligi (%)", "Risk Seviyesi", "Loyalty Score",
        ])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setMinimumHeight(300)
        main_layout.addWidget(self.table)

        # Pagination
        page_layout = QHBoxLayout()
        self.btn_prev = QPushButton("< Onceki")
        self.page_label = QLabel("Sayfa 1 / 1")
        self.page_label.setObjectName("filterLabel")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_next = QPushButton("Sonraki >")

        for btn in (self.btn_prev, self.btn_next):
            btn.setFixedWidth(100)
            btn.setFixedHeight(30)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_prev.clicked.connect(lambda: self._go_to_page(self._current_page - 1))
        self.btn_next.clicked.connect(lambda: self._go_to_page(self._current_page + 1))

        page_layout.addStretch()
        page_layout.addWidget(self.btn_prev)
        page_layout.addWidget(self.page_label)
        page_layout.addWidget(self.btn_next)
        page_layout.addStretch()
        main_layout.addLayout(page_layout)

        main_layout.addStretch()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _export_excel(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Excel Raporu Kaydet", "musteri_raporu.xlsx", "Excel Dosyasi (*.xlsx)"
        )
        if not path:
            return
        try:
            from utils.export import export_customers_excel
            count = export_customers_excel(path)
            QMessageBox.information(self, "Export Basarili", f"{count:,} musteri kaydedildi:\n{path}")
        except PermissionError:
            QMessageBox.warning(self, "Hata", "Dosya acik. Lutfen kapatip tekrar deneyin.")
        except Exception as e:
            QMessageBox.critical(self, "Export Hatasi", str(e))

    def set_metrics(self, metrics):
        """Called after churn model training to display metrics."""
        self._metrics = metrics
        self._feature_importances = metrics.feature_importances
        self._update_metrics_display()

    def _update_metrics_display(self):
        if not self._metrics:
            return

        for key, label in self._metric_labels.items():
            val = getattr(self._metrics, key)
            label.setText(f"{val:.2%}")

        if self._feature_importances:
            feature_importance_bar(self._feature_importances, self.fi_fig)
            self.fi_canvas.draw()

    def refresh(self):
        """Reload churn data from database."""
        try:
            with engine.connect() as conn:
                self._df = pd.read_sql(text("""
                    SELECT s.customer_id, s.segment_label, s.churn_probability,
                           r.loyalty_score
                    FROM segments s
                    JOIN rfm_scores r ON s.customer_id = r.customer_id
                    WHERE s.churn_probability IS NOT NULL
                    ORDER BY s.churn_probability DESC
                """), conn)
        except Exception:
            self._df = pd.DataFrame()
            return

        self._update_metrics_display()
        self._on_filter_changed()

    def _on_filter_changed(self):
        if self._df.empty:
            self._filtered_df = pd.DataFrame()
        else:
            risk_idx = self.risk_filter.currentIndex()
            if risk_idx == 0:
                self._filtered_df = self._df.copy()
            elif risk_idx == 1:  # Yuksek
                self._filtered_df = self._df[self._df["churn_probability"] >= 0.7]
            elif risk_idx == 2:  # Orta
                self._filtered_df = self._df[
                    (self._df["churn_probability"] >= 0.3) & (self._df["churn_probability"] < 0.7)
                ]
            else:  # Dusuk
                self._filtered_df = self._df[self._df["churn_probability"] < 0.3]
            self._filtered_df = self._filtered_df.reset_index(drop=True)

        self._current_page = 0
        self._show_page()

    def _total_pages(self) -> int:
        if self._filtered_df.empty:
            return 1
        return max(1, -(-len(self._filtered_df) // ROWS_PER_PAGE))

    def _go_to_page(self, page: int):
        page = max(0, min(page, self._total_pages() - 1))
        self._current_page = page
        self._show_page()

    def _show_page(self):
        total = len(self._filtered_df)
        total_pages = self._total_pages()
        self.count_label.setText(f"{total:,} musteri")
        self.page_label.setText(f"Sayfa {self._current_page + 1} / {total_pages}")
        self.btn_prev.setEnabled(self._current_page > 0)
        self.btn_next.setEnabled(self._current_page < total_pages - 1)

        if self._filtered_df.empty:
            self.table.setRowCount(0)
            return

        start = self._current_page * ROWS_PER_PAGE
        end = min(start + ROWS_PER_PAGE, total)
        page_df = self._filtered_df.iloc[start:end]

        self.table.setRowCount(len(page_df))

        for row_idx, (_, row) in enumerate(page_df.iterrows()):
            churn_prob = row.get("churn_probability", 0) or 0
            risk_text, risk_color, risk_bg = _risk_level(churn_prob)

            values = [
                str(int(row["customer_id"])),
                str(row.get("segment_label", "-")),
                f"{churn_prob * 100:.1f}%",
                risk_text,
                f"{row.get('loyalty_score', 0):.2f}",
            ]

            for col_idx, val_text in enumerate(values):
                item = QTableWidgetItem(val_text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(risk_bg)

                if col_idx == 3:  # Risk level column
                    item.setForeground(risk_color)
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                elif col_idx == 2:  # Churn probability column
                    item.setForeground(risk_color)
                else:
                    item.setForeground(QColor("#1C1C1E"))

                self.table.setItem(row_idx, col_idx, item)
