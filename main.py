import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import QFile, QTextStream, Qt, QTimer
from PyQt6.QtGui import QFont

from data.database import init_db
from config import APP_NAME, APP_VERSION


def load_stylesheet(app: QApplication):
    style_path = os.path.join(os.path.dirname(__file__), "assets", "styles.qss")
    file = QFile(style_path)
    if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
        stream = QTextStream(file)
        app.setStyleSheet(stream.readAll())
        file.close()


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("splashWidget")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(480, 320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 50, 40, 30)
        layout.setSpacing(10)

        layout.addStretch()

        # Purple icon circle
        icon = QLabel("ROS")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedSize(70, 70)
        icon.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        icon.setStyleSheet("background-color: #7C3AED; color: white; border-radius: 35px;")
        icon_row = QVBoxLayout()
        icon_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_row.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(icon_row)

        layout.addSpacing(12)

        title = QLabel("Retention Optimization System")
        title.setObjectName("splashTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        layout.addWidget(title)

        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("splashSubtitle")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setFont(QFont("Segoe UI", 11))
        layout.addWidget(version)

        layout.addStretch()

        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 0)  # indeterminate
        layout.addWidget(self.progress)

        status = QLabel("Yukleniyor...")
        status.setObjectName("splashSubtitle")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setFont(QFont("Segoe UI", 10))
        layout.addWidget(status)

        # Center on screen
        self.setStyleSheet("""
            #splashWidget {
                background-color: #FFFFFF;
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 20px;
            }
            #splashWidget QLabel {
                background-color: transparent;
            }
            #splashWidget QWidget {
                background-color: transparent;
            }
            #splashWidget QProgressBar {
                background-color: rgba(120, 120, 128, 0.08);
            }
        """)


def main():
    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    load_stylesheet(app)

    # Show splash
    splash = SplashScreen()
    # Center on screen
    screen = app.primaryScreen().geometry()
    splash.move(
        (screen.width() - splash.width()) // 2,
        (screen.height() - splash.height()) // 2,
    )
    splash.show()
    app.processEvents()

    # Load main window after a short delay
    def show_main():
        from ui.main_window import MainWindow
        window = MainWindow()
        window.show()
        splash.close()
        # Keep reference so window isn't garbage collected
        app._main_window = window

    QTimer.singleShot(2000, show_main)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
