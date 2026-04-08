from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QStackedWidget,
    QLabel,
    QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT
from ui.dashboard_view import DashboardView
from ui.import_view import ImportView
from ui.customer_view import CustomerView
from ui.segmentation_view import SegmentationView
from ui.prediction_view import PredictionView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left sidebar
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

        # App title
        title = QLabel("Retention\nOptimization System")
        title.setObjectName("sidebarTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setFixedHeight(60)
        title.setWordWrap(True)
        sidebar_layout.addWidget(title)

        # Menu items
        menu_items = [
            ("Dashboard", 0),
            ("Veri Yukle", 1),
            ("Musteriler", 2),
            ("Segmentasyon", 3),
            ("Tahminleme", 4),
        ]

        self.menu_buttons: list[QPushButton] = []
        for label, index in menu_items:
            btn = QPushButton(label)
            btn.setObjectName("menuButton")
            btn.setFixedHeight(45)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=index: self._switch_page(idx))
            sidebar_layout.addWidget(btn)
            self.menu_buttons.append(btn)

        sidebar_layout.addStretch()

        # Version label
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setObjectName("versionLabel")
        sidebar_layout.addWidget(version_label)

        # Set first button active
        if self.menu_buttons:
            self.menu_buttons[0].setChecked(True)

        return sidebar

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
