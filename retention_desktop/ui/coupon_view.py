from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QLineEdit, QTextEdit, QSpinBox, QGroupBox, QFormLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QSplitter,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime

from services.backend_client import BackendClient
from services.coupon_templates import COUPON_TEMPLATES


class SendCouponWorker(QThread):
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, params: dict):
        super().__init__()
        self.params = params

    def run(self):
        try:
            result = BackendClient.send_coupon(**self.params)
            self.success.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class BackendStatusWorker(QThread):
    """UI thread'i bloklamadan backend durumunu kontrol eder."""
    result = pyqtSignal(bool, str, str, dict)  # connected, text, style, segment_counts

    def run(self):
        try:
            if not BackendClient.is_alive():
                self.result.emit(
                    False,
                    "Backend bağlı değil. uvicorn'u başlatıp bekleyin...",
                    "color: #DC2626; font-size: 12px;",
                    {},
                )
                return
            segments = BackendClient.list_segments()
            total = sum(s["user_count"] for s in segments)
            counts = {s["segment"]: s["user_count"] for s in segments}
            self.result.emit(
                True,
                f"✓ Backend bağlı (localhost:8000) — {total} kayıtlı mobile müşteri",
                "color: #059669; font-size: 12px;",
                counts,
            )
        except Exception as e:
            self.result.emit(
                False,
                f"Backend bağlandı ama veri alınamadı: {e}",
                "color: #D97706; font-size: 12px;",
                {},
            )


class CouponView(QWidget):
    """Kupon Yönetimi sayfası — şablon seç, segment seç, gönder, geçmişi gör."""

    def __init__(self):
        super().__init__()
        self.sent_history: list[dict] = []
        self.worker: SendCouponWorker | None = None
        self._status_worker: BackendStatusWorker | None = None
        self._segment_user_counts: dict[str, int] = {}
        self._backend_connected = False

        self._build_ui()

        # Auto-refresh timer — 5s aralıkla backend kontrolü
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._start_status_check)
        self._timer.start(5000)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Kupon Yönetimi")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # Status satırı: etiket + refresh butonu
        status_row = QHBoxLayout()
        self.status_label = QLabel("Backend kontrol ediliyor…")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        status_row.addWidget(self.status_label)
        status_row.addStretch()

        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setFixedSize(28, 28)
        self.refresh_btn.setToolTip("Backend durumunu yenile")
        self.refresh_btn.setStyleSheet(
            "QPushButton { border: 1px solid #E5E7EB; border-radius: 6px; font-size: 14px; }"
            "QPushButton:hover { background: #F3F4F6; }"
            "QPushButton:pressed { background: #E5E7EB; }"
        )
        self.refresh_btn.clicked.connect(self._start_status_check)
        status_row.addWidget(self.refresh_btn)

        layout.addLayout(status_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_form_panel())
        splitter.addWidget(self._build_history_panel())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

    def showEvent(self, event):
        """Sayfa görünür olunca anında backend kontrolü tetikle."""
        super().showEvent(event)
        self._start_status_check()

    def _start_status_check(self):
        """Backend durumunu arka plan thread'inde kontrol et."""
        if self._status_worker and self._status_worker.isRunning():
            return
        self.status_label.setText("Backend kontrol ediliyor…")
        self.status_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        self._status_worker = BackendStatusWorker()
        self._status_worker.result.connect(self._on_status_result)
        self._status_worker.start()

    def _on_status_result(self, connected: bool, text: str, style: str, counts: dict):
        self._backend_connected = connected
        self.status_label.setText(text)
        self.status_label.setStyleSheet(style)
        self._segment_user_counts = counts
        self._update_target_info()

        # Backend bağlandıysa timer'ı 30s'ye çek, yoksa 5s'de bırak
        new_interval = 30_000 if connected else 5_000
        if self._timer.interval() != new_interval:
            self._timer.setInterval(new_interval)

    def _build_form_panel(self) -> QWidget:
        panel = QGroupBox("Yeni Kupon Oluştur")
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Şablon:", objectName="filterLabel"))
        self.template_combo = QComboBox()
        self.template_combo.addItem("— Manuel Giris —", None)
        for key, tmpl in COUPON_TEMPLATES.items():
            self.template_combo.addItem(tmpl["name"], key)
        self.template_combo.currentIndexChanged.connect(self._on_template_changed)
        layout.addWidget(self.template_combo)

        self.template_desc = QLabel("")
        self.template_desc.setWordWrap(True)
        self.template_desc.setObjectName("placeholderLabel")
        layout.addWidget(self.template_desc)

        form = QFormLayout()
        form.setSpacing(10)

        self.segment_combo = QComboBox()
        self.segment_combo.addItems(["High Value Loyal", "Active Customer", "At Risk", "Low Engagement"])
        form.addRow(QLabel("Hedef Segment:"), self.segment_combo)

        self.target_info = QLabel("")
        self.target_info.setObjectName("summaryLabel")
        form.addRow(QLabel(""), self.target_info)
        self.segment_combo.currentTextChanged.connect(self._update_target_info)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Örn: Seni Özledik!")
        form.addRow(QLabel("Başlık:"), self.title_input)

        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Kullanıcının göreceği mesaj...")
        self.message_input.setMaximumHeight(80)
        form.addRow(QLabel("Mesaj:"), self.message_input)

        self.discount_spin = QSpinBox()
        self.discount_spin.setRange(5, 70)
        self.discount_spin.setValue(20)
        self.discount_spin.setSuffix(" %")
        form.addRow(QLabel("İndirim:"), self.discount_spin)

        self.days_spin = QSpinBox()
        self.days_spin.setRange(1, 90)
        self.days_spin.setValue(7)
        self.days_spin.setSuffix(" gün")
        form.addRow(QLabel("Geçerlilik:"), self.days_spin)

        self.prefix_input = QLineEdit("PROMO")
        self.prefix_input.setMaxLength(10)
        form.addRow(QLabel("Kod Öneki:"), self.prefix_input)

        layout.addLayout(form)

        self.send_btn = QPushButton("Kupon Gönder")
        self.send_btn.setObjectName("importButton")
        self.send_btn.clicked.connect(self._on_send_clicked)
        layout.addWidget(self.send_btn)

        layout.addStretch()
        return panel

    def _build_history_panel(self) -> QWidget:
        panel = QGroupBox("Gönderim Geçmişi")
        layout = QVBoxLayout(panel)

        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(["Zaman", "Segment", "Başlık", "İndirim", "Etkilenen"])
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.hide()
        layout.addWidget(self.history_table)

        self.history_empty = QLabel("Henüz kupon gönderilmedi.\nSol panelden ilk kuponunu gönder.")
        self.history_empty.setObjectName("emptyStateLabel")
        self.history_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.history_empty)

        return panel

    def refresh(self):
        """main_window tarafından sayfa değiştirilince çağrılır."""
        self._start_status_check()

    def _update_target_info(self):
        segment = self.segment_combo.currentText()
        count = self._segment_user_counts.get(segment, 0)
        if count > 0:
            self.target_info.setText(f"Bu segmentte {count} kayıtlı mobile müşteri var.")
        else:
            self.target_info.setText("Bu segmentte kayıtlı mobile müşteri yok.")

    def _on_template_changed(self, index: int):
        key = self.template_combo.itemData(index)
        if key is None:
            self.template_desc.setText("Tüm alanları manuel olarak doldur.")
            return

        tmpl = COUPON_TEMPLATES[key]
        self.template_desc.setText(tmpl["description"])
        if tmpl["target_segment"]:
            idx = self.segment_combo.findText(tmpl["target_segment"])
            if idx >= 0:
                self.segment_combo.setCurrentIndex(idx)
        self.title_input.setText(tmpl["title"])
        self.message_input.setPlainText(tmpl["message"])
        self.discount_spin.setValue(tmpl["discount_percent"])
        self.days_spin.setValue(tmpl["days_valid"])
        self.prefix_input.setText(tmpl["code_prefix"])

    def _on_send_clicked(self):
        title = self.title_input.text().strip()
        message = self.message_input.toPlainText().strip()
        prefix = self.prefix_input.text().strip().upper()

        if not title:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen kupon başlığını gir.")
            return
        if not message:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen kupon mesajını gir.")
            return
        if not prefix:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen kod önekini gir.")
            return

        segment = self.segment_combo.currentText()
        params = {
            "segment": segment,
            "title": title,
            "message": message,
            "discount_percent": self.discount_spin.value(),
            "days_valid": self.days_spin.value(),
            "code_prefix": prefix,
        }

        reply = QMessageBox.question(
            self,
            "Kupon Gönderimini Onayla",
            f"'{segment}' segmentindeki tüm kayıtlı mobile kullanıcılara şu kupon gönderilecek:\n\n"
            f"Başlık: {title}\n"
            f"İndirim: %{self.discount_spin.value()}\n"
            f"Geçerlilik: {self.days_spin.value()} gün\n\n"
            "Devam edilsin mi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.send_btn.setEnabled(False)
        self.send_btn.setText("Gönderiliyor…")

        self.worker = SendCouponWorker(params)
        self.worker.success.connect(self._on_send_success)
        self.worker.error.connect(self._on_send_error)
        self.worker.start()

    def _on_send_success(self, result: dict):
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Kupon Gönder")
        affected = result.get("affected_users", 0)
        codes = result.get("coupon_codes", [])
        preview = "\n".join(codes[:5]) + ("\n…" if len(codes) > 5 else "")

        QMessageBox.information(
            self,
            "Başarılı",
            f"{affected} kullanıcıya kupon tanımlandı.\n\nKod örnekleri:\n{preview}",
        )

        self.sent_history.insert(0, {
            "time": datetime.now().strftime("%H:%M:%S"),
            "segment": self.segment_combo.currentText(),
            "title": self.title_input.text(),
            "discount": self.discount_spin.value(),
            "affected": affected,
        })
        self._refresh_history()
        self._start_status_check()

    def _on_send_error(self, error_msg: str):
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Kupon Gonder")
        QMessageBox.critical(self, "Gönderim Hatası", f"Kupon gönderilemedi:\n\n{error_msg}")

    def _refresh_history(self):
        if not self.sent_history:
            self.history_empty.show()
            self.history_table.hide()
            return

        self.history_empty.hide()
        self.history_table.show()
        self.history_table.setRowCount(len(self.sent_history))
        for row, item in enumerate(self.sent_history):
            self.history_table.setItem(row, 0, QTableWidgetItem(item["time"]))
            self.history_table.setItem(row, 1, QTableWidgetItem(item["segment"]))
            self.history_table.setItem(row, 2, QTableWidgetItem(item["title"]))
            self.history_table.setItem(row, 3, QTableWidgetItem(f"%{item['discount']}"))
            self.history_table.setItem(row, 4, QTableWidgetItem(str(item["affected"])))
