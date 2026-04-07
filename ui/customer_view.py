import pandas as pd
from sqlalchemy import text

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QGridLayout,
    QGroupBox,
    QPushButton,
    QComboBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from data.database import engine


class CustomerDetailCard(QFrame):
    """Card showing selected customer details."""

    def __init__(self):
        super().__init__()
        self.setObjectName("detailCard")
        self.setStyleSheet("""
            #detailCard {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        self.setFixedHeight(180)

        layout = QGridLayout(self)
        layout.setSpacing(8)

        self.title_label = QLabel("Musteri Detayi")
        self.title_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(self.title_label, 0, 0, 1, 4)

        self._fields = {}
        fields = [
            ("customer_id", "Musteri ID", 1, 0),
            ("country", "Ulke", 1, 2),
            ("recency", "Recency (gun)", 2, 0),
            ("frequency", "Frequency", 2, 2),
            ("monetary", "Monetary", 3, 0),
            ("loyalty_score", "Loyalty Score", 3, 2),
            ("r_score", "R Score", 4, 0),
            ("f_score", "F Score", 4, 2),
            ("m_score", "M Score", 5, 0),
        ]

        for key, label_text, row, col in fields:
            lbl = QLabel(f"{label_text}:")
            lbl.setFont(QFont("Segoe UI", 9))
            lbl.setStyleSheet("color: #7f8c8d;")
            val = QLabel("-")
            val.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            layout.addWidget(lbl, row, col)
            layout.addWidget(val, row, col + 1)
            self._fields[key] = val

    def update_data(self, row_data: dict):
        for key, val_label in self._fields.items():
            value = row_data.get(key, "-")
            if isinstance(value, float):
                val_label.setText(f"{value:,.2f}")
            else:
                val_label.setText(str(value))

    def clear(self):
        for val_label in self._fields.values():
            val_label.setText("-")


class CustomerView(QWidget):
    def __init__(self):
        super().__init__()
        self._df = pd.DataFrame()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # Title
        title_row = QHBoxLayout()
        title = QLabel("Musteri Listesi")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title_row.addWidget(title)
        title_row.addStretch()

        self.refresh_btn = QPushButton("Yenile")
        self.refresh_btn.setFixedHeight(35)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.refresh)
        title_row.addWidget(self.refresh_btn)

        layout.addLayout(title_row)

        # Search & Filter bar
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        filter_layout.addWidget(QLabel("Ara:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Musteri ID girin...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.search_input)

        filter_layout.addWidget(QLabel("Score Araligi:"))
        self.score_filter = QComboBox()
        self.score_filter.addItems([
            "Tumu",
            "0 - 25 (Dusuk)",
            "25 - 50 (Orta)",
            "50 - 75 (Iyi)",
            "75 - 100 (Harika)",
        ])
        self.score_filter.setFixedWidth(160)
        self.score_filter.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.score_filter)

        self.count_label = QLabel("")
        self.count_label.setStyleSheet("color: #7f8c8d;")
        filter_layout.addStretch()
        filter_layout.addWidget(self.count_label)

        layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Musteri ID", "Ulke", "Recency", "Frequency",
            "Monetary", "R Score", "F Score", "Loyalty Score",
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.clicked.connect(self._on_row_clicked)

        layout.addWidget(self.table, stretch=1)

        # Detail card
        self.detail_card = CustomerDetailCard()
        layout.addWidget(self.detail_card)

    def refresh(self):
        """Reload data from database."""
        try:
            with engine.connect() as conn:
                query = text("""
                    SELECT
                        c.customer_id, c.country,
                        r.recency, r.frequency, r.monetary,
                        r.r_score, r.f_score, r.m_score,
                        r.loyalty_score
                    FROM customers c
                    LEFT JOIN rfm_scores r ON c.customer_id = r.customer_id
                    ORDER BY r.loyalty_score DESC
                """)
                self._df = pd.read_sql(query, conn)
        except Exception:
            self._df = pd.DataFrame()

        self._apply_filters()

    def _apply_filters(self):
        """Filter the dataframe and populate the table."""
        if self._df.empty:
            self.table.setRowCount(0)
            self.count_label.setText("0 musteri")
            return

        filtered = self._df.copy()

        # Search by customer ID
        search_text = self.search_input.text().strip()
        if search_text:
            filtered = filtered[
                filtered["customer_id"].astype(str).str.contains(search_text)
            ]

        # Filter by score range
        score_idx = self.score_filter.currentIndex()
        if score_idx > 0 and "loyalty_score" in filtered.columns:
            ranges = [(0, 25), (25, 50), (50, 75), (75, 100)]
            low, high = ranges[score_idx - 1]
            filtered = filtered[
                (filtered["loyalty_score"] >= low) & (filtered["loyalty_score"] <= high)
            ]

        self._populate_table(filtered)
        self.count_label.setText(f"{len(filtered):,} musteri")

    def _populate_table(self, df: pd.DataFrame):
        self.table.setRowCount(len(df))

        columns = [
            "customer_id", "country", "recency", "frequency",
            "monetary", "r_score", "f_score", "loyalty_score",
        ]

        for row_idx, (_, row) in enumerate(df.iterrows()):
            for col_idx, col_name in enumerate(columns):
                value = row.get(col_name, "")
                if pd.isna(value):
                    text = "-"
                elif isinstance(value, float):
                    text = f"{value:,.2f}"
                else:
                    text = str(int(value)) if col_name in ("customer_id", "recency", "frequency", "r_score", "f_score") else str(value)

                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # Store full row data for detail card
                item.setData(Qt.ItemDataRole.UserRole, row.to_dict())
                self.table.setItem(row_idx, col_idx, item)

    def _on_row_clicked(self, index):
        item = self.table.item(index.row(), 0)
        if item:
            row_data = item.data(Qt.ItemDataRole.UserRole)
            if row_data:
                self.detail_card.update_data(row_data)
