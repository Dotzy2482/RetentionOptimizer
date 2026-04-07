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

from config import APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT


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
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # App title
        title = QLabel(APP_NAME)
        title.setObjectName("sidebarTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title.setFixedHeight(60)
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
        from config import APP_VERSION
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setObjectName("versionLabel")
        sidebar_layout.addWidget(version_label)

        # Set first button active
        if self.menu_buttons:
            self.menu_buttons[0].setChecked(True)

        return sidebar

    def _create_pages(self):
        """Create placeholder pages. Will be replaced with actual views in Sprint 2."""
        page_names = ["Dashboard", "Veri Yukle", "Musteriler", "Segmentasyon", "Tahminleme"]
        for name in page_names:
            page = QWidget()
            page_layout = QVBoxLayout(page)
            label = QLabel(f"{name} sayfasi - Sprint 2'de gelecek")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFont(QFont("Segoe UI", 16))
            page_layout.addWidget(label)
            self.stack.addWidget(page)

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.menu_buttons):
            btn.setChecked(i == index)
