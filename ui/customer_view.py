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
    QPushButton,
    QComboBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from data.database import engine

ROWS_PER_PAGE = 100


class CustomerDetailCard(QFrame):
    """Card showing selected customer details."""

    def __init__(self):
        super().__init__()
        self.setObjectName("detailCard")
        self.setFixedHeight(180)

        layout = QGridLayout(self)
        layout.setSpacing(8)

        self.title_label = QLabel("Musteri Detayi")
        self.title_label.setObjectName("detailCardTitle")
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
            lbl.setObjectName("detailLabel")
            lbl.setFont(QFont("Segoe UI", 10))
            val = QLabel("-")
            val.setObjectName("detailValue")
            val.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
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
        self._filtered_df = pd.DataFrame()
        self._current_page = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # Title
        title_row = QHBoxLayout()
        title = QLabel("Musteri Listesi")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setObjectName("pageTitle")
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

        ara_label = QLabel("Ara:")
        ara_label.setObjectName("filterLabel")
        ara_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        filter_layout.addWidget(ara_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Musteri ID girin...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.search_input)

        score_label = QLabel("Score Araligi:")
        score_label.setObjectName("filterLabel")
        score_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        filter_layout.addWidget(score_label)

        self.score_filter = QComboBox()
        self.score_filter.addItems([
            "Tumu",
            "0 - 25 (Dusuk)",
            "25 - 50 (Orta)",
            "50 - 75 (Iyi)",
            "75 - 100 (Harika)",
        ])
        self.score_filter.setFixedWidth(160)
        self.score_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.score_filter)

        self.count_label = QLabel("")
        self.count_label.setObjectName("filterLabel")
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

        # Pagination bar
        page_layout = QHBoxLayout()
        page_layout.setSpacing(10)

        self.btn_first = QPushButton("<<")
        self.btn_prev = QPushButton("< Onceki")
        self.page_label = QLabel("Sayfa 1 / 1")
        self.page_label.setObjectName("filterLabel")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_next = QPushButton("Sonraki >")
        self.btn_last = QPushButton(">>")

        for btn in (self.btn_first, self.btn_prev, self.btn_next, self.btn_last):
            btn.setFixedWidth(90)
            btn.setFixedHeight(30)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_first.clicked.connect(lambda: self._go_to_page(0))
        self.btn_prev.clicked.connect(lambda: self._go_to_page(self._current_page - 1))
        self.btn_next.clicked.connect(lambda: self._go_to_page(self._current_page + 1))
        self.btn_last.clicked.connect(lambda: self._go_to_page(self._total_pages() - 1))

        page_layout.addStretch()
        page_layout.addWidget(self.btn_first)
        page_layout.addWidget(self.btn_prev)
        page_layout.addWidget(self.page_label)
        page_layout.addWidget(self.btn_next)
        page_layout.addWidget(self.btn_last)
        page_layout.addStretch()

        layout.addLayout(page_layout)

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

        self._on_filter_changed()

    def _on_filter_changed(self):
        """Reapply filters and reset to page 0."""
        self._apply_filters()
        self._current_page = 0
        self._show_current_page()

    def _apply_filters(self):
        """Filter the dataframe."""
        if self._df.empty:
            self._filtered_df = pd.DataFrame()
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

        self._filtered_df = filtered.reset_index(drop=True)

    def _total_pages(self) -> int:
        if self._filtered_df.empty:
            return 1
        return max(1, -(-len(self._filtered_df) // ROWS_PER_PAGE))  # ceil division

    def _go_to_page(self, page: int):
        page = max(0, min(page, self._total_pages() - 1))
        self._current_page = page
        self._show_current_page()

    def _show_current_page(self):
        """Populate the table with only the current page's rows."""
        total = len(self._filtered_df)
        total_pages = self._total_pages()
        self.count_label.setText(f"{total:,} musteri")
        self.page_label.setText(f"Sayfa {self._current_page + 1} / {total_pages}")

        # Enable/disable buttons
        self.btn_first.setEnabled(self._current_page > 0)
        self.btn_prev.setEnabled(self._current_page > 0)
        self.btn_next.setEnabled(self._current_page < total_pages - 1)
        self.btn_last.setEnabled(self._current_page < total_pages - 1)

        if self._filtered_df.empty:
            self.table.setRowCount(0)
            return

        start = self._current_page * ROWS_PER_PAGE
        end = min(start + ROWS_PER_PAGE, total)
        page_df = self._filtered_df.iloc[start:end]

        self._populate_table(page_df)

    def _populate_table(self, df: pd.DataFrame):
        self.table.setRowCount(len(df))

        columns = [
            "customer_id", "country", "recency", "frequency",
            "monetary", "r_score", "f_score", "loyalty_score",
        ]
        int_cols = {"customer_id", "recency", "frequency", "r_score", "f_score"}

        # Zebra colors
        color_even = QColor("#ffffff")
        color_odd = QColor("#f0f3f7")

        for row_idx, (_, row) in enumerate(df.iterrows()):
            bg = color_even if row_idx % 2 == 0 else color_odd
            for col_idx, col_name in enumerate(columns):
                value = row.get(col_name, "")
                if pd.isna(value):
                    display = "-"
                elif isinstance(value, float):
                    if col_name in int_cols:
                        display = str(int(value))
                    else:
                        display = f"{value:,.2f}"
                else:
                    display = str(value)

                item = QTableWidgetItem(display)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(bg)
                item.setForeground(QColor("#2c3e50"))
                # Store full row data for detail card
                item.setData(Qt.ItemDataRole.UserRole, row.to_dict())
                self.table.setItem(row_idx, col_idx, item)

    def _on_row_clicked(self, index):
        item = self.table.item(index.row(), 0)
        if item:
            row_data = item.data(Qt.ItemDataRole.UserRole)
            if row_data:
                self.detail_card.update_data(row_data)
