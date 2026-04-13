from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QStackedWidget,
    QLabel,
    QFrame,
    QDialog,
    QDialogButtonBox,
    QAbstractButton,
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QFont, QPainter, QColor, QPainterPath

from config import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT


# ---------------------------------------------------------------------------
# NavButton — icon + text sidebar button with left accent bar when active
# ---------------------------------------------------------------------------

class NavButton(QAbstractButton):
    """Custom sidebar nav item: Segoe MDL2 icon, label, hover fill, active accent."""

    def __init__(self, icon_char: str, label: str, checkable: bool = True, parent=None):
        super().__init__(parent)
        self._icon    = icon_char
        self._label   = label
        self._hovered = False
        self.setCheckable(checkable)
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Pre-build fonts (created once, reused every frame)
        self._font_normal = QFont("Segoe UI", 13)
        self._font_bold   = QFont("Segoe UI", 13)
        self._font_bold.setBold(True)
        self._font_icon   = QFont("Segoe MDL2 Assets", 13)

        # Pre-build colors
        self._col_purple     = QColor(124, 58, 237)
        self._col_bg_checked = QColor(124, 58, 237, 25)
        self._col_bg_hover   = QColor(124, 58, 237, 14)
        self._col_txt_active = QColor(124, 58, 237)
        self._col_txt_hover  = QColor(107, 114, 128)
        self._col_txt_normal = QColor(55, 65, 81)
        self._col_icn_active = QColor(124, 58, 237)
        self._col_icn_inact  = QColor(156, 163, 175)

        # Geometry paths — built in resizeEvent (size unknown at __init__)
        self._bg_path   = QPainterPath()
        self._bar_path  = QPainterPath()
        self._icon_rect = QRectF()
        self._text_rect = QRectF()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = float(self.width()), float(self.height())
        if w == 0 or h == 0:
            return
        mx, my = 10.0, 2.0

        self._bg_path = QPainterPath()
        self._bg_path.addRoundedRect(QRectF(mx, my, w - mx * 2, h - my * 2), 8, 8)

        self._bar_path = QPainterPath()
        self._bar_path.addRoundedRect(QRectF(mx, h * 0.22, 3, h * 0.56), 1.5, 1.5)

        self._icon_rect = QRectF(mx + 12, 0.0, 24.0, h)
        text_x          = mx + 12 + 24 + 10
        self._text_rect = QRectF(text_x, 0.0, w - text_x - mx, h)

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        checked = self.isChecked()

        # Background pill
        if checked:
            p.fillPath(self._bg_path, self._col_bg_checked)
        elif self._hovered:
            p.fillPath(self._bg_path, self._col_bg_hover)

        # Left accent bar when active
        if checked:
            p.fillPath(self._bar_path, self._col_purple)

        # Icon
        p.setPen(self._col_icn_active if (checked or self._hovered) else self._col_icn_inact)
        p.setFont(self._font_icon)
        p.drawText(self._icon_rect, Qt.AlignmentFlag.AlignCenter, self._icon)

        # Label
        p.setPen(self._col_txt_active if checked
                 else self._col_txt_hover if self._hovered
                 else self._col_txt_normal)
        p.setFont(self._font_bold if checked else self._font_normal)
        p.drawText(self._text_rect, Qt.AlignmentFlag.AlignVCenter, self._label)
from ui.dashboard_view import DashboardView
from ui.import_view import ImportView
from ui.customer_view import CustomerView
from ui.segmentation_view import SegmentationView
from ui.prediction_view import PredictionView


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hakkinda")
        self.setFixedSize(420, 340)
        self.setObjectName("aboutDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 20)
        layout.setSpacing(12)

        # App icon placeholder - purple circle
        icon_label = QLabel("ROS")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(60, 60)
        icon_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        icon_label.setStyleSheet("""
            background-color: #7C3AED;
            color: white;
            border-radius: 30px;
        """)
        icon_container = QHBoxLayout()
        icon_container.addStretch()
        icon_container.addWidget(icon_label)
        icon_container.addStretch()
        layout.addLayout(icon_container)

        title = QLabel("Retention Optimization System")
        title.setObjectName("aboutTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("aboutSubtitle")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setFont(QFont("Segoe UI", 11))
        layout.addWidget(version)

        layout.addSpacing(8)

        info_lines = [
            ("Teknolojiler:", "Python, PyQt6, Scikit-learn, XGBoost, SQLite"),
            ("Metodoloji:", "Agile (Sprint tabanli gelistirme)"),
        ]
        for label_text, value_text in info_lines:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            lbl.setStyleSheet("color: #8E8E93;")
            lbl.setFixedWidth(110)
            row.addWidget(lbl)
            val = QLabel(value_text)
            val.setObjectName("aboutDevLabel")
            val.setFont(QFont("Segoe UI", 10))
            val.setWordWrap(True)
            row.addWidget(val)
            layout.addLayout(row)

        layout.addSpacing(4)
        desc = QLabel("Musteri sadakati optimizasyon sistemi.\nRFM analizi, K-Means segmentasyon ve XGBoost churn tahmini.")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #8E8E93; font-size: 10px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addStretch()

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn_box.accepted.connect(self.accept)
        layout.addWidget(btn_box)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(12, 12, 0, 12)
        layout.setSpacing(12)

        # Left sidebar (floating)
        sidebar = self._create_sidebar()
        layout.addWidget(sidebar)

        # Right content area
        self.stack = QStackedWidget()
        self._create_pages()
        layout.addWidget(self.stack, stretch=1)

        # Default to dashboard
        self.stack.setCurrentIndex(0)

    def _create_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # ── Brand header ──────────────────────────────────────
        brand_container = QWidget()
        brand_container.setFixedHeight(80)
        brand_container.setStyleSheet("background: transparent;")
        brand_layout = QVBoxLayout(brand_container)
        brand_layout.setContentsMargins(0, 14, 0, 8)
        brand_layout.setSpacing(5)

        brand_icon = QLabel("ROS")
        brand_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_icon.setFixedSize(38, 38)
        brand_icon.setFont(QFont("Bahnschrift", 11, QFont.Weight.Bold))
        brand_icon.setStyleSheet("""
            background: qradialgradient(cx:0.4, cy:0.4, radius:0.9, fx:0.4, fy:0.4,
                stop:0 #9333EA, stop:0.5 #7C3AED, stop:1 #5B21B6);
            color: white;
            border-radius: 19px;
        """)
        icon_row = QHBoxLayout()
        icon_row.addStretch()
        icon_row.addWidget(brand_icon)
        icon_row.addStretch()
        brand_layout.addLayout(icon_row)

        brand_title = QLabel("Retention Optimizer")
        brand_title.setObjectName("sidebarTitle")
        brand_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_title.setFont(QFont("Bahnschrift", 10, QFont.Weight.Bold))
        brand_layout.addWidget(brand_title)

        sidebar_layout.addWidget(brand_container)

        # ── Nav items ─────────────────────────────────────────
        nav_items = [
            ("\uE80F", "Dashboard",    0),
            ("\uE896", "Veri Yukle",   1),
            ("\uE716", "Musteriler",   2),
            ("\uE9D2", "Segmentasyon", 3),
            ("\uE9F9", "Tahminleme",   4),
        ]

        self.menu_buttons: list[NavButton] = []
        for icon, label, index in nav_items:
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda checked, idx=index: self._switch_page(idx))
            sidebar_layout.addWidget(btn)
            self.menu_buttons.append(btn)

        sidebar_layout.addStretch()

        # ── Separator ─────────────────────────────────────────
        sep = QFrame()
        sep.setObjectName("sidebarSep")
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sidebar_layout.addWidget(sep)

        # ── About button ──────────────────────────────────────
        about_btn = NavButton("\uE946", "Hakkinda", checkable=False)
        about_btn.clicked.connect(self._show_about)
        sidebar_layout.addWidget(about_btn)

        # ── Version label ─────────────────────────────────────
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setObjectName("versionLabel")
        sidebar_layout.addWidget(version_label)

        # Set first button active
        if self.menu_buttons:
            self.menu_buttons[0].setChecked(True)

        return sidebar

    def _show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def _create_pages(self):
        # Dashboard
        self.dashboard_view = DashboardView()
        self.dashboard_view.analysis_completed.connect(self._on_analysis_done)
        self.stack.addWidget(self.dashboard_view)

        # Import
        self.import_view = ImportView()
        self.import_view.import_completed.connect(self._on_import_completed)
        self.stack.addWidget(self.import_view)

        # Customers
        self.customer_view = CustomerView()
        self.stack.addWidget(self.customer_view)

        # Segmentation
        self.segmentation_view = SegmentationView()
        self.stack.addWidget(self.segmentation_view)

        # Prediction
        self.prediction_view = PredictionView()
        self.stack.addWidget(self.prediction_view)

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.menu_buttons):
            btn.setChecked(i == index)

        # Auto-refresh data views when navigated to
        if index == 0:
            self.dashboard_view.refresh()
        elif index == 2:
            self.customer_view.refresh()
        elif index == 3:
            self.segmentation_view.refresh()
        elif index == 4:
            self.prediction_view.refresh()

    def _on_import_completed(self, churn_metrics):
        """Refresh all views after full import pipeline."""
        if churn_metrics:
            self.prediction_view.set_metrics(churn_metrics)
        self.dashboard_view.refresh()
        self.customer_view.refresh()
        self.segmentation_view.refresh()
        self.prediction_view.refresh()

    def _on_analysis_done(self, churn_metrics):
        """Refresh views after dashboard 'Analiz Calistir' button."""
        if churn_metrics:
            self.prediction_view.set_metrics(churn_metrics)
        self.segmentation_view.refresh()
        self.prediction_view.refresh()
