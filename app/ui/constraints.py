from PyQt5 import QtWidgets, QtCore

class ConstraintsDialog(QtWidgets.QDialog):
    """
    Kısıtlar penceresi: takvim + atama ayarlarını toplar.
    values() ile tüm ayarları basit bir dict olarak döndürür.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kısıtlar")
        self.setMinimumWidth(520)

        # === Takvim ===
        g_cal = QtWidgets.QGroupBox("Takvim")
        self.start = QtWidgets.QDateTimeEdit(
            QtCore.QDateTime.fromString("2025-11-03 09:00", "yyyy-MM-dd HH:mm")
        )
        self.end = QtWidgets.QDateTimeEdit(
            QtCore.QDateTime.fromString("2025-11-07 18:00", "yyyy-MM-dd HH:mm")
        )
        for w in (self.start, self.end):
            w.setDisplayFormat("yyyy-MM-dd HH:mm")
            w.setCalendarPopup(True)

        self.skip_sat = QtWidgets.QCheckBox("Cumartesi hariç")
        self.skip_sun = QtWidgets.QCheckBox("Pazar hariç")
        self.skip_sat.setChecked(True)
        self.skip_sun.setChecked(True)

        self.day_start = QtWidgets.QTimeEdit(QtCore.QTime(9, 0))
        self.day_end = QtWidgets.QTimeEdit(QtCore.QTime(18, 0))
        self.day_start.setDisplayFormat("HH:mm")
        self.day_end.setDisplayFormat("HH:mm")

        lay_cal = QtWidgets.QFormLayout()
        lay_cal.addRow("Başlangıç", self.start)
        lay_cal.addRow("Bitiş", self.end)
        lay_cal.addRow(self.skip_sat)
        lay_cal.addRow(self.skip_sun)
        lay_cal.addRow("Gün başlangıcı", self.day_start)
        lay_cal.addRow("Gün bitişi", self.day_end)
        g_cal.setLayout(lay_cal)

        # === Sınav Ayarları ===
        g_exam = QtWidgets.QGroupBox("Sınav Ayarları")
        self.exam_type = QtWidgets.QComboBox()
        self.exam_type.addItems(["Vize", "Final", "Bütünleme"])

        self.duration = QtWidgets.QSpinBox()
        self.duration.setRange(30, 240)
        self.duration.setValue(75)

        self.break_min = QtWidgets.QSpinBox()
        self.break_min.setRange(0, 60)
        self.break_min.setValue(15)

        self.unique_all = QtWidgets.QCheckBox("Her ders için benzersiz slot üret (çakışma olmaz)")
        self.use_all_rooms = QtWidgets.QCheckBox("Tüm derslikleri kapasite sırasıyla kullan")
        self.use_all_rooms.setChecked(True)

        lay_exam = QtWidgets.QFormLayout()
        lay_exam.addRow("Sınav türü", self.exam_type)
        lay_exam.addRow("Süre (dk)", self.duration)
        lay_exam.addRow("Mola (dk)", self.break_min)
        lay_exam.addRow(self.unique_all)
        lay_exam.addRow(self.use_all_rooms)
        g_exam.setLayout(lay_exam)

        # === Alt butonlar ===
        btn_ok = QtWidgets.QPushButton("Programı Oluştur")
        btn_cancel = QtWidgets.QPushButton("Vazgeç")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        row.addWidget(btn_cancel)
        row.addWidget(btn_ok)

        main = QtWidgets.QVBoxLayout(self)
        main.addWidget(g_cal)
        main.addWidget(g_exam)
        main.addLayout(row)

    def values(self) -> dict:
        """Form değerlerini döndür."""
        return {
            "start": self.start.dateTime().toString("yyyy-MM-dd HH:mm"),
            "end": self.end.dateTime().toString("yyyy-MM-dd HH:mm"),
            "skip_sat": self.skip_sat.isChecked(),
            "skip_sun": self.skip_sun.isChecked(),
            "day_start": self.day_start.time().toString("HH:mm"),
            "day_end": self.day_end.time().toString("HH:mm"),
            "exam_type": self.exam_type.currentText(),
            "duration": int(self.duration.value()),
            "break_min": int(self.break_min.value()),
            "unique_all": self.unique_all.isChecked(),
            "use_all_rooms": self.use_all_rooms.isChecked(),
        }
