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
from PyQt6.QtGui import QFont, QPainter, QPen, QColor, QPainterPath, QLinearGradient, QRadialGradient, QBrush

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

        # Pre-compute everything once — nothing is created during paintEvent
        sz = float(size)
        r  = sz / 2.0

        grad = QRadialGradient(r * 0.55, r * 0.45, r * 1.1)
        grad.setColorAt(0.0, QColor("#9333EA"))
        grad.setColorAt(0.5, QColor("#7C3AED"))
        grad.setColorAt(1.0, QColor("#5B21B6"))
        self._grad_brush = QBrush(grad)

        shine = QRadialGradient(r * 0.38, r * 0.30, r * 0.65)
        shine.setColorAt(0.0, QColor(255, 255, 255, 55))
        shine.setColorAt(1.0, QColor(255, 255, 255, 0))
        self._shine_brush = QBrush(shine)

        self._circle_rect = QRectF(0, 0, sz, sz)
        self._font        = QFont("Bahnschrift", int(r * 0.46), QFont.Weight.Bold)
        self._text_color  = QColor(255, 255, 255, 235)
        self._no_pen      = Qt.PenStyle.NoPen

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        p.setPen(self._no_pen)
        p.setBrush(self._grad_brush)
        p.drawEllipse(self._circle_rect)

        p.setBrush(self._shine_brush)
        p.drawEllipse(self._circle_rect)

        p.setFont(self._font)
        p.setPen(self._text_color)
        p.drawText(self._circle_rect, Qt.AlignmentFlag.AlignCenter, "ROS")


# ---------------------------------------------------------------------------
# Segmented progress bar — five pill shapes, fills left to right smoothly
# ---------------------------------------------------------------------------

class SegmentedProgress(QWidget):
    def __init__(self, segments: int = 5, parent=None):
        super().__init__(parent)
        self._segments  = segments
        self._val       = 0.0
        self._anim      = None
        self._built     = False
        # Caches filled by _rebuild() on first resize
        self._pill_paths:  list[QPainterPath] = []
        self._grad_brushes: list[QBrush]      = []
        self._shine_brushes: list[QBrush]     = []
        self._seg_xs:  list[float]            = []
        self._seg_w    = 0.0
        self._h        = 0.0
        self._bg_color = QColor(180, 180, 185, 120)
        self.setFixedHeight(8)

    # ── Qt property (needed by QPropertyAnimation) ────────────
    @pyqtProperty(float)
    def value(self):
        return self._val

    @value.setter
    def value(self, v: float):
        self._val = v
        self.update()

    # ── Cache rebuild — called once when the widget gets its size
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.width() > 0:
            self._rebuild()

    def _rebuild(self):
        w      = float(self.width())
        h      = float(self.height())
        gap    = 7.0
        seg_w  = (w - gap * (self._segments - 1)) / self._segments
        radius = h / 2.0

        self._seg_w = seg_w
        self._h     = h
        self._seg_xs.clear()
        self._pill_paths.clear()
        self._grad_brushes.clear()
        self._shine_brushes.clear()

        for i in range(self._segments):
            x = i * (seg_w + gap)
            self._seg_xs.append(x)

            path = QPainterPath()
            path.addRoundedRect(QRectF(x, 0.0, seg_w, h), radius, radius)
            self._pill_paths.append(path)

            grad = QLinearGradient(x, 0.0, x + seg_w, 0.0)
            grad.setColorAt(0.0, QColor("#6D28D9"))
            grad.setColorAt(0.5, QColor("#7C3AED"))
            grad.setColorAt(1.0, QColor("#8B5CF6"))
            self._grad_brushes.append(QBrush(grad))

            shine = QLinearGradient(x, 0.0, x, h)
            shine.setColorAt(0.0, QColor(255, 255, 255, 70))
            shine.setColorAt(0.5, QColor(255, 255, 255, 0))
            self._shine_brushes.append(QBrush(shine))

        self._built = True

    # ── Animation ─────────────────────────────────────────────
    def animateTo(self, target: float):
        if self._anim is not None:
            self._anim.stop()
        self._anim = QPropertyAnimation(self, b"value")
        self._anim.setDuration(260)
        self._anim.setStartValue(self._val)
        self._anim.setEndValue(float(min(target, self._segments)))
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    # ── Paint — uses only pre-built objects ───────────────────
    def paintEvent(self, event):
        if not self._built:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        seg_w = self._seg_w
        h     = self._h

        for i in range(self._segments):
            x    = self._seg_xs[i]
            fill = max(0.0, min(1.0, self._val - i))

            p.fillPath(self._pill_paths[i], self._bg_color)

            if fill > 0.001:
                p.save()
                p.setClipRect(QRectF(x, 0.0, seg_w * fill, h))
                p.fillPath(self._pill_paths[i], self._grad_brushes[i])
                p.fillPath(self._pill_paths[i], self._shine_brushes[i])
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
