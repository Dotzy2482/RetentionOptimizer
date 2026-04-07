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
)
from PyQt6.QtCore import Qt
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


class StatCard(QFrame):
    """A single summary statistic card."""

    def __init__(self, title: str, value: str, color: str = "#3498db"):
        super().__init__()
        self.setObjectName("statCard")
        self.setFixedHeight(100)
        self.setStyleSheet(f"""
            #statCard {{
                background-color: #ffffff;
                border-left: 4px solid {color};
                border-radius: 6px;
                padding: 10px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 9))
        title_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(title_label)

        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(self.value_label)

    def set_value(self, value: str):
        self.value_label.setText(value)


class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setObjectName("pageTitle")
        title_row.addWidget(title)
        title_row.addStretch()

        self.refresh_btn = QPushButton("Yenile")
        self.refresh_btn.setFixedHeight(35)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.refresh)
        title_row.addWidget(self.refresh_btn)

        self.main_layout.addLayout(title_row)

        # Stat cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)

        self.card_customers = StatCard("Toplam Musteri", "-", "#3498db")
        self.card_avg_loyalty = StatCard("Ort. Loyalty Score", "-", "#2ecc71")
        self.card_best_segment = StatCard("En Iyi Segment", "-", "#9b59b6")
        self.card_worst_segment = StatCard("En Dusuk Segment", "-", "#e74c3c")

        cards_layout.addWidget(self.card_customers)
        cards_layout.addWidget(self.card_avg_loyalty)
        cards_layout.addWidget(self.card_best_segment)
        cards_layout.addWidget(self.card_worst_segment)

        self.main_layout.addLayout(cards_layout)

        # Charts - row 1
        charts_row1 = QHBoxLayout()
        charts_row1.setSpacing(15)

        self.hist_fig, self.hist_canvas = create_canvas(5, 3.5)
        self.scatter_fig, self.scatter_canvas = create_canvas(5, 3.5)
        charts_row1.addWidget(self.hist_canvas)
        charts_row1.addWidget(self.scatter_canvas)

        self.main_layout.addLayout(charts_row1)

        # Charts - row 2
        charts_row2 = QHBoxLayout()
        charts_row2.setSpacing(15)

        self.pie_fig, self.pie_canvas = create_canvas(5, 3.5)
        charts_row2.addWidget(self.pie_canvas)
        charts_row2.addStretch()

        self.main_layout.addLayout(charts_row2)
        self.main_layout.addStretch()

        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _assign_segments(self, rfm_df: pd.DataFrame) -> pd.DataFrame:
        """Assign loyalty-based segments to customers."""
        rfm_df = rfm_df.copy()
        rfm_df["segment"] = pd.cut(
            rfm_df["loyalty_score"],
            bins=LOYALTY_BINS,
            labels=LOYALTY_LABELS,
            include_lowest=True,
        )
        return rfm_df

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
            return

        # Assign loyalty-based segments
        rfm_df = self._assign_segments(rfm_df)

        # Update stat cards
        total = len(rfm_df)
        avg_loyalty = rfm_df["loyalty_score"].mean()
        self.card_customers.set_value(f"{total:,}")
        self.card_avg_loyalty.set_value(f"{avg_loyalty:.1f}")

        # Segment stats - use DB segments if available, otherwise loyalty-based
        if not seg_df.empty:
            seg_avg = seg_df.merge(rfm_df[["customer_id", "loyalty_score"]], on="customer_id")
            seg_stats = seg_avg.groupby("segment_label")["loyalty_score"].mean()
        else:
            seg_stats = rfm_df.groupby("segment")["loyalty_score"].mean()

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

        # Segment pie
        if not seg_df.empty:
            counts = seg_df["segment_label"].value_counts()
        else:
            counts = rfm_df["segment"].value_counts().sort_index()
        segment_pie(counts.index.tolist(), counts.values.tolist(), self.pie_fig)
        self.pie_canvas.draw()
