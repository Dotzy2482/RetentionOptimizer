import sys
import os
import traceback

# In source mode, ensure the project root is importable.
# PyInstaller bundles all modules itself, so we skip this when frozen.
if not getattr(sys, "frozen", False):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QMessageBox
from PyQt6.QtCore import (QFile, QTextStream, Qt, QTimer, QPropertyAnimation,
                          QEasingCurve, QRectF, pyqtProperty)
from PyQt6.QtGui import QFont, QPainter, QColor, QPainterPath, QLinearGradient, QRadialGradient, QBrush

from data.database import init_db
from config import APP_NAME, APP_VERSION, RESOURCE_DIR


def load_stylesheet(app: QApplication):
    style_path = os.path.join(RESOURCE_DIR, "assets", "styles.qss")
    file = QFile(style_path)
    if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
        stream = QTextStream(file)
        app.setStyleSheet(stream.readAll())
        file.close()


# ---------------------------------------------------------------------------
# Logo widget — gradient circle with "ROS" and a glass shine
# ---------------------------------------------------------------------------

class LogoWidget(QWidget):
    def __init__(self, size: int = 70, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._sz = size

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        sz = float(self._sz)
        r = sz / 2.0

        # Main gradient fill — top-left light, bottom-right deep
        grad = QRadialGradient(r * 0.55, r * 0.45, r * 1.1)
        grad.setColorAt(0.0, QColor("#9333EA"))
        grad.setColorAt(0.5, QColor("#7C3AED"))
        grad.setColorAt(1.0, QColor("#5B21B6"))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawEllipse(QRectF(0, 0, sz, sz))

        # Glass shine — top-left quarter highlight
        shine = QRadialGradient(r * 0.38, r * 0.30, r * 0.65)
        shine.setColorAt(0.0, QColor(255, 255, 255, 55))
        shine.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(shine))
        p.drawEllipse(QRectF(0, 0, sz, sz))

        # "ROS" text
        font = QFont("Bahnschrift", int(r * 0.46), QFont.Weight.Bold)
        p.setFont(font)
        p.setPen(QColor(255, 255, 255, 235))
        p.drawText(QRectF(0, 0, sz, sz), Qt.AlignmentFlag.AlignCenter, "ROS")


# ---------------------------------------------------------------------------
# Segmented progress bar — five pill shapes, fills left to right smoothly
# ---------------------------------------------------------------------------

class SegmentedProgress(QWidget):
    def __init__(self, segments: int = 5, parent=None):
        super().__init__(parent)
        self._segments = segments
        self._val = 0.0
        self._anim = None
        self.setFixedHeight(8)

    @pyqtProperty(float)
    def value(self):
        return self._val

    @value.setter
    def value(self, v: float):
        self._val = v
        self.update()

    def animateTo(self, target: float):
        self._anim = QPropertyAnimation(self, b"value")
        self._anim.setDuration(260)
        self._anim.setStartValue(self._val)
        self._anim.setEndValue(float(min(target, self._segments)))
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        gap = 7.0
        seg_w = (w - gap * (self._segments - 1)) / self._segments
        radius = h / 2.0

        for i in range(self._segments):
            x = i * (seg_w + gap)
            fill = max(0.0, min(1.0, self._val - i))

            # Inactive pill — light gray
            bg = QPainterPath()
            bg.addRoundedRect(QRectF(x, 0.0, seg_w, h), radius, radius)
            p.fillPath(bg, QColor(180, 180, 185, 120))

            if fill > 0.001:
                # Clip to filled width, draw full pill shape so edges stay round
                p.save()
                p.setClipRect(QRectF(x, 0.0, seg_w * fill, h))

                grad = QLinearGradient(x, 0.0, x + seg_w, 0.0)
                grad.setColorAt(0.0, QColor("#6D28D9"))
                grad.setColorAt(0.5, QColor("#7C3AED"))
                grad.setColorAt(1.0, QColor("#8B5CF6"))

                pill = QPainterPath()
                pill.addRoundedRect(QRectF(x, 0.0, seg_w, h), radius, radius)
                p.fillPath(pill, QBrush(grad))

                # Subtle top-edge shine
                shine = QLinearGradient(x, 0.0, x, h)
                shine.setColorAt(0.0, QColor(255, 255, 255, 70))
                shine.setColorAt(0.5, QColor(255, 255, 255, 0))
                p.fillPath(pill, QBrush(shine))

                p.restore()


# ---------------------------------------------------------------------------
# Splash screen — original white design with new segmented progress bar
# ---------------------------------------------------------------------------

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

        # Gradient logo circle
        icon = LogoWidget(70)
        icon_row = QVBoxLayout()
        icon_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_row.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(icon_row)

        layout.addSpacing(12)

        title = QLabel("Retention Optimization System")
        title.setObjectName("splashTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Bahnschrift", 20, QFont.Weight.Bold))
        layout.addWidget(title)

        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("splashSubtitle")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setFont(QFont("Bahnschrift", 11))
        layout.addWidget(version)

        layout.addStretch()

        # Segmented progress bar
        self._bar = SegmentedProgress(segments=5)
        layout.addWidget(self._bar)

        self._status = QLabel("Yukleniyor...")
        self._status.setObjectName("splashSubtitle")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self._status)

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
        """)

        # Advance one segment every ~275 ms (5 × 275 = 1375 ms, finishes just before show_main)
        self._seg = 0
        self._seg_timer = QTimer(self)
        self._seg_timer.timeout.connect(self._tick)
        self._seg_timer.start(275)

    def _tick(self):
        self._seg += 1
        self._bar.animateTo(self._seg)
        if self._seg >= 5:
            self._seg_timer.stop()


def _get_log_path():
    """Return a log file path next to the exe (or source file in dev mode)."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "startup_error.log")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    load_stylesheet(app)

    # Show splash screen immediately
    splash = SplashScreen()
    screen = app.primaryScreen().geometry()
    splash.move(
        (screen.width() - splash.width()) // 2,
        (screen.height() - splash.height()) // 2,
    )
    splash.show()
    app.processEvents()

    def show_main():
        """Initialize DB and launch the main window; always closes the splash."""
        try:
            init_db()

            from ui.main_window import MainWindow
            window = MainWindow()
            window.show()
            # Keep a strong reference on the app so the GC cannot collect the window.
            app._main_window = window
        except Exception:
            err = traceback.format_exc()
            # Write error to log file so we can diagnose EXE issues
            try:
                with open(_get_log_path(), "w", encoding="utf-8") as f:
                    f.write(err)
            except Exception:
                pass
            QMessageBox.critical(
                None,
                "Baslatma Hatasi",
                f"Uygulama baslatilirken beklenmeyen bir hata olustu:\n\n{err}",
            )
            app.quit()
        finally:
            # Splash must always close regardless of success or failure.
            splash.close()

    QTimer.singleShot(1500, show_main)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
