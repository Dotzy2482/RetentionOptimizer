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
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from data.database import engine
from utils.charts import (
    create_canvas,
    segment_pie,
    segment_rfm_bar,
    segment_scatter,
    SEGMENT_COLORS,
)

ROWS_PER_PAGE = 100


class SegmentationView(QWidget):
    def __init__(self):
        super().__init__()
        self._seg_df = pd.DataFrame()
        self._filtered_df = pd.DataFrame()
        self._current_page = 0
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.verticalScrollBar().setSingleStep(24)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(28, 24, 28, 28)
        main_layout.setSpacing(16)

        # Title
        title_row = QHBoxLayout()
        title = QLabel("Musteri Segmentasyonu")
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

        # Summary table
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(5)
        self.summary_table.setHorizontalHeaderLabels([
            "Segment", "Musteri Sayisi", "Yuzde (%)", "Ort. Loyalty", "Ort. Churn Risk",
        ])
        self.summary_table.setFixedHeight(170)
        self.summary_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.summary_table.verticalHeader().setVisible(False)
        self.summary_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.summary_table)

        # Charts — stacked vertically, each large and readable.
        # Fixed vertical size policy ensures QScrollArea can compute the
        # total content height deterministically (prevents scroll jitter).
        main_layout.addSpacing(8)

        chart_policy = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        self.pie_fig, self.pie_canvas = create_canvas(10, 5)
        self.pie_canvas.setFixedHeight(500)
        self.pie_canvas.setSizePolicy(chart_policy)
        main_layout.addWidget(self.pie_canvas)

        main_layout.addSpacing(12)

        self.bar_fig, self.bar_canvas = create_canvas(11, 8.5)
        self.bar_canvas.setFixedHeight(720)
        self.bar_canvas.setSizePolicy(chart_policy)
        main_layout.addWidget(self.bar_canvas)

        main_layout.addSpacing(12)

        self.scatter_fig, self.scatter_canvas = create_canvas(12, 5.5)
        self.scatter_canvas.setFixedHeight(540)
        self.scatter_canvas.setSizePolicy(chart_policy)
        main_layout.addWidget(self.scatter_canvas)

        main_layout.addSpacing(8)

        # Segment filter + customer table
        filter_row = QHBoxLayout()
        seg_label = QLabel("Segment Filtrele:")
        seg_label.setObjectName("filterLabel")
        seg_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        filter_row.addWidget(seg_label)

        self.seg_filter = QComboBox()
        self.seg_filter.addItem("Tumu")
        self.seg_filter.setFixedWidth(200)
        self.seg_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.seg_filter)

        self.cust_count_label = QLabel("")
        self.cust_count_label.setObjectName("filterLabel")
        filter_row.addStretch()
        filter_row.addWidget(self.cust_count_label)
        main_layout.addLayout(filter_row)

        # Customer detail table
        self.cust_table = QTableWidget()
        self.cust_table.setColumnCount(6)
        self.cust_table.setHorizontalHeaderLabels([
            "Musteri ID", "Segment", "Recency", "Frequency", "Monetary", "Loyalty Score",
        ])
        self.cust_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cust_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cust_table.verticalHeader().setVisible(False)
        self.cust_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.cust_table.setMinimumHeight(250)
        main_layout.addWidget(self.cust_table)

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

    def refresh(self):
        """Reload segment data from database."""
        try:
            with engine.connect() as conn:
                self._seg_df = pd.read_sql(text("""
                    SELECT s.customer_id, s.segment_label, s.churn_probability,
                           r.recency, r.frequency, r.monetary, r.loyalty_score
                    FROM segments s
                    JOIN rfm_scores r ON s.customer_id = r.customer_id
                    ORDER BY r.loyalty_score DESC
                """), conn)
        except Exception:
            self._seg_df = pd.DataFrame()
            return

        if self._seg_df.empty:
            return

        self._update_summary()
        self._update_charts()
        self._update_filter_combo()
        self._on_filter_changed()

    def _update_summary(self):
        df = self._seg_df
        total = len(df)
        stats = df.groupby("segment_label").agg(
            count=("customer_id", "count"),
            avg_loyalty=("loyalty_score", "mean"),
            avg_churn=("churn_probability", "mean"),
        ).reset_index()

        self.summary_table.setRowCount(len(stats))
        for i, (_, row) in enumerate(stats.iterrows()):
            label = row["segment_label"]
            color = QColor(SEGMENT_COLORS.get(label, "#7f8c8d"))

            items = [
                label,
                f"{int(row['count']):,}",
                f"{row['count'] / total * 100:.1f}%",
                f"{row['avg_loyalty']:.1f}",
                f"{row['avg_churn']:.2%}" if pd.notna(row['avg_churn']) else "-",
            ]
            for j, text_val in enumerate(items):
                item = QTableWidgetItem(text_val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if j == 0:
                    item.setForeground(color)
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self.summary_table.setItem(i, j, item)

    def _update_charts(self):
        df = self._seg_df

        # Pie chart
        counts = df["segment_label"].value_counts()
        segment_pie(counts.index.tolist(), counts.values.tolist(), self.pie_fig)
        self.pie_canvas.draw()

        # RFM bar chart
        stats = df.groupby("segment_label").agg(
            avg_recency=("recency", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
        ).reset_index()
        segment_rfm_bar(stats, self.bar_fig)
        self.bar_canvas.draw()

        # Scatter
        segment_scatter(
            df["frequency"].tolist(),
            df["monetary"].tolist(),
            df["segment_label"].tolist(),
            self.scatter_fig,
        )
        self.scatter_canvas.draw()

    def _update_filter_combo(self):
        current = self.seg_filter.currentText()
        self.seg_filter.blockSignals(True)
        self.seg_filter.clear()
        self.seg_filter.addItem("Tumu")
        for label in sorted(self._seg_df["segment_label"].unique()):
            self.seg_filter.addItem(label)
        # Restore selection
        idx = self.seg_filter.findText(current)
        self.seg_filter.setCurrentIndex(max(0, idx))
        self.seg_filter.blockSignals(False)

    def _on_filter_changed(self):
        selected = self.seg_filter.currentText()
        if selected == "Tumu":
            self._filtered_df = self._seg_df.reset_index(drop=True)
        else:
            self._filtered_df = self._seg_df[
                self._seg_df["segment_label"] == selected
            ].reset_index(drop=True)
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
        self.cust_count_label.setText(f"{total:,} musteri")
        self.page_label.setText(f"Sayfa {self._current_page + 1} / {total_pages}")
        self.btn_prev.setEnabled(self._current_page > 0)
        self.btn_next.setEnabled(self._current_page < total_pages - 1)

        if self._filtered_df.empty:
            self.cust_table.setRowCount(0)
            return

        start = self._current_page * ROWS_PER_PAGE
        end = min(start + ROWS_PER_PAGE, total)
        page_df = self._filtered_df.iloc[start:end]

        self.cust_table.setRowCount(len(page_df))
        cols = ["customer_id", "segment_label", "recency", "frequency", "monetary", "loyalty_score"]
        int_cols = {"customer_id", "recency", "frequency"}
        color_even = QColor("#FFFFFF")
        color_odd = QColor("#FAFAFA")

        for row_idx, (_, row) in enumerate(page_df.iterrows()):
            bg = color_even if row_idx % 2 == 0 else color_odd
            for col_idx, col_name in enumerate(cols):
                val = row.get(col_name, "")
                if pd.isna(val):
                    display = "-"
                elif isinstance(val, float) and col_name in int_cols:
                    display = str(int(val))
                elif isinstance(val, float):
                    display = f"{val:,.2f}"
                else:
                    display = str(val)
                item = QTableWidgetItem(display)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(bg)
                item.setForeground(QColor("#1C1C1E"))
                self.cust_table.setItem(row_idx, col_idx, item)
