# app/ui/scheduler_sql.py
from PyQt5 import QtWidgets, QtCore
import os
from datetime import datetime, timedelta
import pandas as pd

from app.ui.constraints import ConstraintsDialog
from app.db_sql import query_all, query_one, execute


# --- yardımcılar -------------------------------------------------------------

def _parse_dt(v):
    """SQLite'tan gelen DATETIME text'ini güvenle datetime'a çevirir."""
    if isinstance(v, datetime):
        return v
    s = str(v)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    # son çare
    return datetime.fromisoformat(s)


# --- ana sayfa ---------------------------------------------------------------

class SchedulerPage(QtWidgets.QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user or {}

        main = QtWidgets.QVBoxLayout(self)

        # Bölüm seçimi
        row_dep = QtWidgets.QHBoxLayout()
        row_dep.addWidget(QtWidgets.QLabel("Bölüm:"))
        self.dept = QtWidgets.QComboBox()
        row_dep.addWidget(self.dept)
        main.addLayout(row_dep)

        self._load_departments()

        # koordinatör ise bölüm kilitli
        role = (self.current_user.get("role") or "").lower()
        if role == "coordinator":
            dep_id = self.current_user.get("department_id")
            i = self.dept.findData(dep_id)
            if i >= 0:
                self.dept.setCurrentIndex(i)
            self.dept.setEnabled(False)

        # Butonlar
        row_btn = QtWidgets.QHBoxLayout()
        self.btn_constraints = QtWidgets.QPushButton("Kısıtlar…")
        self.btn_build = QtWidgets.QPushButton("Planı Oluştur (MVP)")
        self.btn_clear = QtWidgets.QPushButton("Planı Temizle")
        self.btn_export = QtWidgets.QPushButton("Excel'e Aktar")
        for b in (self.btn_constraints, self.btn_build, self.btn_clear, self.btn_export):
            row_btn.addWidget(b)
        main.addLayout(row_btn)

        # MVP butonunu da kısıt akışına bağladım (tek tıkla gerçek takvimle üretir)
        self.btn_constraints.clicked.connect(self.open_constraints)
        self.btn_build.clicked.connect(self.open_constraints)
        self.btn_clear.clicked.connect(self.clear_plan)
        self.btn_export.clicked.connect(self.export_excel)

        # Tablo
        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["course_id", "Ders", "Derslik", "Slot", "Saat"])
        self.table.horizontalHeader().setStretchLastSection(True)
        main.addWidget(self.table)

        self.load_plan()

    # ---------------- helpers ----------------

    def _load_departments(self):
        self.dept.clear()
        rows = query_all("SELECT id, name FROM departments ORDER BY id")
        for r in rows:
            self.dept.addItem(r["name"], r["id"])

    def current_department_id(self):
        return self.dept.currentData()

    # ---------------- actions ----------------

    def clear_plan(self):
        dep = self.current_department_id()
        execute("DELETE FROM exam_assignments WHERE department_id=?", (dep,))
        self.load_plan()
        QtWidgets.QMessageBox.information(self, "OK", "Plan temizlendi.")

    def load_plan(self):
        """Tabloyu DB'den doldurur. 'Saat'te sadece dd.mm HH:MM - HH:MM görünür."""
        self.table.setRowCount(0)
        dep = self.current_department_id()

        rows = query_all(
            """
            SELECT
              c.id             AS cid,
              c.code           AS ccode,
              c.name           AS cname,
              cr.code          AS rcode,
              cr.name          AS rname,
              s.name           AS sname,
              s.starts_at      AS starts_at,
              s.ends_at        AS ends_at
            FROM exam_assignments ea
            JOIN courses     c  ON c.id  = ea.course_id
            JOIN classrooms  cr ON cr.id = ea.classroom_id
            JOIN exam_slots  s  ON s.id  = ea.slot_id
            WHERE ea.department_id = ?
            ORDER BY s.starts_at, c.code
            """,
            (dep,),
        )

        for r, row in enumerate(rows):
            self.table.insertRow(r)
            st = _parse_dt(row["starts_at"])
            en = _parse_dt(row["ends_at"])
            start_txt = st.strftime("%d.%m %H:%M")
            end_txt = en.strftime("%H:%M")
            vals = [
                row["cid"],
                f"{row['ccode']} - {row['cname']}",
                f"{row['rcode']} ({row['rname']})",
                row["sname"],
                f"{start_txt} - {end_txt}",
            ]
            for c, v in enumerate(vals):
                self.table.setItem(r, c, QtWidgets.QTableWidgetItem(str(v)))

    # ---------------- constraints-based planning ----------------

    def open_constraints(self):
        """Kısıtlar penceresini aç, takvimi üret, atamayı yap."""
        dlg = ConstraintsDialog(self)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return
        opts = dlg.values()

        # 1) uniq takvim oluştur
        self._rebuild_calendar_sql(opts)

        dep_id = self.current_department_id()

        # 2) mevcut atamaları temizle
        execute("DELETE FROM exam_assignments WHERE department_id=?", (dep_id,))

        # 3) atama stratejisi
        if opts.get("unique_all", True):
            self._assign_unique_one_per_course(dep_id, opts)
        else:
            self._assign_sequential(dep_id, opts)

        # 4) exam_type & duration_min uygula
        execute(
            "UPDATE exam_assignments SET exam_type=?, duration_min=? WHERE department_id=?",
            (opts["exam_type"], int(opts["duration"]), dep_id),
        )

        self.load_plan()
        QtWidgets.QMessageBox.information(self, "OK", "Program oluşturuldu.")

    def _rebuild_calendar_sql(self, opts: dict):
        """
        opts:
          start/end: 'yyyy-MM-dd HH:mm'
          skip_sat/sun: bool
          day_start/day_end: 'HH:mm'
          duration: int (dk)
          break_min: int (dk)
        """
        # Önce uniq slotları temizle (sabit slotlara dokunma)
        execute("DELETE FROM exam_slots WHERE name LIKE 'Uniq %'")

        dt_start = datetime.strptime(opts["start"], "%Y-%m-%d %H:%M")
        dt_end = datetime.strptime(opts["end"], "%Y-%m-%d %H:%M")
        ds_h, ds_m = map(int, opts["day_start"].split(":"))
        de_h, de_m = map(int, opts["day_end"].split(":"))
        dur = int(opts["duration"])
        gap = int(opts["break_min"])

        cur = dt_start
        count = 0
        while cur <= dt_end:
            # hafta sonu atla
            if (opts.get("skip_sat") and cur.weekday() == 5) or (opts.get("skip_sun") and cur.weekday() == 6):
                cur = datetime(cur.year, cur.month, cur.day) + timedelta(days=1, hours=ds_h, minutes=ds_m)
                continue

            day_start = cur.replace(hour=ds_h, minute=ds_m, second=0, microsecond=0)
            day_end = cur.replace(hour=de_h, minute=de_m, second=0, microsecond=0)
            t = max(cur, day_start)

            while t + timedelta(minutes=dur) <= day_end and t + timedelta(minutes=dur) <= dt_end:
                s = t
                e = t + timedelta(minutes=dur)
                name = f"Uniq {count + 1:03d}"
                execute(
                    "INSERT OR IGNORE INTO exam_slots(name, starts_at, ends_at) VALUES(?,?,?)",
                    (name, s.strftime("%Y-%m-%d %H:%M"), e.strftime("%Y-%m-%d %H:%M")),
                )
                count += 1
                t = e + timedelta(minutes=gap)

            # sonraki gün
            cur = datetime(cur.year, cur.month, cur.day) + timedelta(days=1, hours=ds_h, minutes=ds_m)

    def _assign_unique_one_per_course(self, dep_id: int, opts: dict):
        """Her derse sıradaki uniq slotu ver; sınıfı kapasiteye göre sıradan döndür."""
        slots = query_all(
            "SELECT id FROM exam_slots WHERE name LIKE 'Uniq %' ORDER BY starts_at"
        )
        if not slots:
            raise RuntimeError("Uniq slot bulunamadı. Önce kısıtlardan takvim üretin.")

        courses = query_all(
            "SELECT id FROM courses WHERE department_id=? ORDER BY id", (dep_id,)
        )
        if not courses:
            return

        rooms = query_all(
            "SELECT id FROM classrooms WHERE department_id=? ORDER BY capacity DESC",
            (dep_id,),
        )
        if not rooms:
            rooms = query_all("SELECT id FROM classrooms ORDER BY capacity DESC")
        if not rooms:
            raise RuntimeError("Derslik yok.")

        si = ri = 0
        for c in courses:
            slot_id = slots[si % len(slots)]["id"]
            room_id = rooms[ri % len(rooms)]["id"]
            execute(
                """
                INSERT INTO exam_assignments(department_id, course_id, classroom_id, slot_id, exam_type, duration_min)
                VALUES(?,?,?,?,?,?)
                """,
                (dep_id, c["id"], room_id, slot_id, opts.get("exam_type", "Vize"), int(opts.get("duration", 75))),
            )
            si += 1
            ri += 1

    def _assign_sequential(self, dep_id: int, opts: dict):
        """Alternatif: tüm slotları sırayla dolaş (benzersiz garanti etmez)."""
        slots = query_all("SELECT id FROM exam_slots ORDER BY starts_at")
        rooms = query_all(
            "SELECT id FROM classrooms WHERE department_id=? ORDER BY capacity DESC",
            (dep_id,),
        )
        if not rooms:
            rooms = query_all("SELECT id FROM classrooms ORDER BY capacity DESC")
        courses = query_all(
            "SELECT id FROM courses WHERE department_id=? ORDER BY id", (dep_id,)
        )
        si = ri = 0
        for c in courses:
            slot_id = slots[si % len(slots)]["id"]
            room_id = rooms[ri % len(rooms)]["id"]
            execute(
                """
                INSERT INTO exam_assignments(department_id, course_id, classroom_id, slot_id, exam_type, duration_min)
                VALUES(?,?,?,?,?,?)
                """,
                (dep_id, c["id"], room_id, slot_id, opts.get("exam_type", "Vize"), int(opts.get("duration", 75))),
            )
            si += 1
            ri += 1

    # ---------------- export ----------------

    def export_excel(self):
        dep = self.current_department_id()
        rows = query_all(
            """
            SELECT
              d.name      AS dep_name,
              c.code      AS ccode,
              c.name      AS cname,
              cr.code     AS rcode,
              cr.name     AS rname,
              s.name      AS sname,
              s.starts_at AS starts_at,
              s.ends_at   AS ends_at
            FROM exam_assignments ea
            JOIN departments d ON d.id = ea.department_id
            JOIN courses     c ON c.id = ea.course_id
            JOIN classrooms  cr ON cr.id = ea.classroom_id
            JOIN exam_slots  s ON s.id = ea.slot_id
            WHERE ea.department_id = ?
            ORDER BY s.starts_at, cr.code, c.code
            """,
            (dep,),
        )

        if not rows:
            QtWidgets.QMessageBox.information(self, "Boş", "Önce bir plan oluştur.")
            return

        data = []
        for r in rows:
            st = _parse_dt(r["starts_at"])
            en = _parse_dt(r["ends_at"])
            data.append({
                "Bölüm": r["dep_name"],
                "Ders Kodu": r["ccode"],
                "Ders Adı": r["cname"],
                "Derslik": f"{r['rcode']} ({r['rname']})",
                "Slot": r["sname"],
                "Başlangıç": st.strftime("%Y-%m-%d %H:%M"),
                "Bitiş": en.strftime("%Y-%m-%d %H:%M"),
            })

        os.makedirs("exports", exist_ok=True)
        fname = f"exports/plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        pd.DataFrame(data).to_excel(fname, index=False)
        QtWidgets.QMessageBox.information(self, "OK", f"Excel kaydedildi:\n{fname}")
