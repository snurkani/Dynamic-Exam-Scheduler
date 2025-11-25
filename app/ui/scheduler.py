# app/ui/scheduler.py
from PyQt5 import QtWidgets
from app.db import SessionLocal
from app.models import Department, Course, Classroom, ExamSlot, ExamAssignment
import os, pandas as pd
from datetime import datetime, timedelta

# Kısıt penceresi ve ham SQL yardımcıları
from app.ui.constraints import ConstraintsDialog
from app.db_sql import execute


class SchedulerPage(QtWidgets.QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user or {}
        lay = QtWidgets.QVBoxLayout(self)

        # -------- Bölüm seçimi --------
        row_dep = QtWidgets.QHBoxLayout()
        row_dep.addWidget(QtWidgets.QLabel("Bölüm:"))
        self.dept = QtWidgets.QComboBox()
        row_dep.addWidget(self.dept)
        lay.addLayout(row_dep)

        self._load_departments()
        # Koordinatör ise bölüm seçimi kilitlenir
        if (self.current_user.get("role") or "").lower() == "coordinator":
            dep_id = self.current_user.get("department_id")
            i = self.dept.findData(dep_id)
            if i >= 0:
                self.dept.setCurrentIndex(i)
            self.dept.setEnabled(False)

        # -------- Butonlar --------
        row_btn = QtWidgets.QHBoxLayout()
        self.btn_build        = QtWidgets.QPushButton("Planı Oluştur (MVP)")
        self.btn_clear        = QtWidgets.QPushButton("Planı Temizle")
        self.btn_export       = QtWidgets.QPushButton("Excel'e Aktar")
        self.btn_constraints  = QtWidgets.QPushButton("Kısıtlar...")

        # Sıra: Kısıtlar... | Planı Oluştur | Temizle | Excel'e Aktar
        row_btn.addWidget(self.btn_constraints)
        row_btn.addWidget(self.btn_build)
        row_btn.addWidget(self.btn_clear)
        row_btn.addWidget(self.btn_export)
        lay.addLayout(row_btn)

        # -------- Sinyaller --------
        # MVP butonunu da kısıt akışına bağlıyoruz: gerçek takvimle plan üret
        self.btn_build.clicked.connect(self.open_constraints)
        self.btn_clear.clicked.connect(self.clear_plan)
        self.btn_export.clicked.connect(self.export_excel)
        self.btn_constraints.clicked.connect(self.open_constraints)

        # -------- Tablo --------
        # İstersen 4 kolona düşürüp "Slot"u kaldırabilirsin.
        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["course_id", "Ders", "Derslik", "Slot", "Saat"])
        self.table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.table)

        self.load_plan()

    # ================= helpers =================

    def _load_departments(self):
        self.dept.clear()
        with SessionLocal() as db:
            for d in db.query(Department).order_by(Department.id):
                self.dept.addItem(d.name, d.id)

    def current_department_id(self):
        return self.dept.currentData()

    # ================= core actions =================

    def clear_plan(self):
        dep = self.current_department_id()
        with SessionLocal() as db:
            db.query(ExamAssignment).filter_by(department_id=dep).delete()
            db.commit()
        self.load_plan()
        QtWidgets.QMessageBox.information(self, "OK", "Plan temizlendi.")

    def load_plan(self):
        """Tabloyu DB'den doldurur. 'Saat' sütununda sadece HH:MM - HH:MM gösterilir."""
        self.table.setRowCount(0)
        dep = self.current_department_id()
        with SessionLocal() as db:
            rows = (
                db.query(ExamAssignment, Course, Classroom, ExamSlot)
                .join(Course, Course.id == ExamAssignment.course_id)
                .join(Classroom, Classroom.id == ExamAssignment.classroom_id)
                .join(ExamSlot, ExamSlot.id == ExamAssignment.slot_id)
                .filter(ExamAssignment.department_id == dep)
                .order_by(ExamSlot.starts_at, Course.code)
                .all()
            )
            for r, (a, course, room, slot) in enumerate(rows):
                self.table.insertRow(r)
                start_txt = slot.starts_at.strftime('%d.%m %H:%M')
                end_txt   = slot.ends_at.strftime('%H:%M')
                vals = [
                    course.id,
                    f"{course.code} - {course.name}",
                    f"{room.code} ({room.name})",
                    slot.name,
                    f"{start_txt} - {end_txt}",
                ]
                for c, v in enumerate(vals):
                    self.table.setItem(r, c, QtWidgets.QTableWidgetItem(str(v)))

    # ============ constraints-based planning ============

    def open_constraints(self):
        """Kısıtlar penceresini açar, takvimi üretir ve atamayı yapar."""
        dlg = ConstraintsDialog(self)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return
        opts = dlg.values()

        # 1) exam_slots takvimini (uniq slotlar) yeniden kur
        self._rebuild_calendar_sql(opts)

        dep_id = self.current_department_id()

        # 2) Var olan atamaları (bu bölüm) temizle
        with SessionLocal() as db:
            db.query(ExamAssignment).filter_by(department_id=dep_id).delete()
            db.commit()

        # 3) Atama stratejisi
        if opts.get("unique_all", True):
            self._assign_unique_one_per_course(dep_id, opts)
        else:
            self._assign_sequential(dep_id, opts)

        # 4) Tür & varsayılan süre uygula (ek kolonlar varsa)
        execute(
            "UPDATE exam_assignments SET exam_type=?, duration_min=? WHERE department_id=?",
            (opts.get("exam_type", "Vize"), int(opts.get("duration", 75)), dep_id)
        )

        self.load_plan()
        QtWidgets.QMessageBox.information(self, "OK", "Program oluşturuldu.")

    def _rebuild_calendar_sql(self, opts: dict):
        """
        opts:
          start: 'yyyy-MM-dd HH:mm'
          end:   'yyyy-MM-dd HH:mm'
          skip_sat/sun: bool
          day_start/day_end: 'HH:mm'
          duration: int (dk)
          break_min: int (dk)
        """
        # Var olan uniq slotları temizle (sabit slotlara dokunma)
        execute("DELETE FROM exam_slots WHERE name LIKE 'Uniq %'")

        dt_start = datetime.strptime(opts["start"], "%Y-%m-%d %H:%M")
        dt_end   = datetime.strptime(opts["end"],   "%Y-%m-%d %H:%M")
        ds_h, ds_m = map(int, opts["day_start"].split(":"))
        de_h, de_m = map(int, opts["day_end"].split(":"))
        dur   = int(opts["duration"])
        gap   = int(opts["break_min"])

        # Gün gün, gün içi slotları üret
        cur_day = dt_start.date()
        count = 0
        while cur_day <= dt_end.date():
            wd = cur_day.weekday()  # 0=Mon .. 6=Sun
            if (opts.get("skip_sat") and wd == 5) or (opts.get("skip_sun") and wd == 6):
                cur_day = cur_day + timedelta(days=1)
                continue

            day_start = datetime(cur_day.year, cur_day.month, cur_day.day, ds_h, ds_m)
            day_end   = datetime(cur_day.year, cur_day.month, cur_day.day, de_h, de_m)

            t = max(day_start, dt_start)
            while t + timedelta(minutes=dur) <= day_end and t + timedelta(minutes=dur) <= dt_end:
                s = t
                e = t + timedelta(minutes=dur)
                name = f"Uniq {count+1:03d}"
                execute(
                    "INSERT OR IGNORE INTO exam_slots(name, starts_at, ends_at) VALUES(?,?,?)",
                    (name, s.strftime("%Y-%m-%d %H:%M"), e.strftime("%Y-%m-%d %H:%M"))
                )
                count += 1
                t = e + timedelta(minutes=gap)

            cur_day = cur_day + timedelta(days=1)

    def _assign_unique_one_per_course(self, dep_id: int, opts: dict):
        """Her derse sıradaki uniq slotu ver (çakışmasız). Derslikleri kapasiteye göre döndür."""
        with SessionLocal() as db:
            slots = (
                db.query(ExamSlot)
                .filter(ExamSlot.name.like("Uniq %"))
                .order_by(ExamSlot.starts_at)
                .all()
            )
            if not slots:
                raise RuntimeError("Uniq slot bulunamadı. Lütfen kısıtlardan takvim üretin.")

            courses = db.query(Course).filter_by(department_id=dep_id).order_by(Course.id).all()
            if not courses:
                return

            # Önce bu bölümün derslikleri, yoksa tüm derslikler
            rooms = (
                db.query(Classroom)
                .filter_by(department_id=dep_id)
                .order_by(Classroom.capacity.desc())
                .all()
            )
            if not rooms:
                rooms = db.query(Classroom).order_by(Classroom.capacity.desc()).all()
            if not rooms:
                raise RuntimeError("Derslik yok.")

            si = 0
            ri = 0
            exam_type   = opts.get("exam_type", "Vize")
            duration_min= int(opts.get("duration", 75))

            for c in courses:
                slot = slots[si % len(slots)]
                room = rooms[ri % len(rooms)]
                db.add(ExamAssignment(
                    department_id=dep_id,
                    course_id=c.id,
                    classroom_id=room.id,
                    slot_id=slot.id,
                    exam_type=exam_type,
                    duration_min=duration_min,
                ))
                si += 1
                ri += 1

            db.commit()

    def _assign_sequential(self, dep_id: int, opts: dict):
        """Alternatif eski yöntem: tüm slotları sırayla doldurur (benzersiz garantisi yok)."""
        with SessionLocal() as db:
            slots = db.query(ExamSlot).order_by(ExamSlot.starts_at).all()
            rooms = (
                db.query(Classroom)
                .filter_by(department_id=dep_id)
                .order_by(Classroom.capacity.desc())
                .all()
            )
            if not rooms:
                rooms = db.query(Classroom).order_by(Classroom.capacity.desc()).all()
            courses = db.query(Course).filter_by(department_id=dep_id).order_by(Course.id).all()

            si = ri = 0
            exam_type   = opts.get("exam_type", "Vize")
            duration_min= int(opts.get("duration", 75))

            for c in courses:
                slot = slots[si % len(slots)]
                room = rooms[ri % len(rooms)]
                db.add(ExamAssignment(
                    department_id=dep_id,
                    course_id=c.id,
                    classroom_id=room.id,
                    slot_id=slot.id,
                    exam_type=exam_type,
                    duration_min=duration_min,
                ))
                si += 1
                ri += 1

            db.commit()

    # ================= export =================

    def export_excel(self):
        dep = self.current_department_id()
        with SessionLocal() as db:
            rows = (
                db.query(ExamAssignment, Course, Classroom, ExamSlot, Department)
                .join(Course, Course.id == ExamAssignment.course_id)
                .join(Classroom, Classroom.id == ExamAssignment.classroom_id)
                .join(ExamSlot, ExamSlot.id == ExamAssignment.slot_id)
                .join(Department, Department.id == ExamAssignment.department_id)
                .filter(ExamAssignment.department_id == dep)
                .order_by(ExamSlot.starts_at, Classroom.code, Course.code)
                .all()
            )
            data = []
            for a, course, room, slot, depobj in rows:
                data.append({
                    "Bölüm": depobj.name,
                    "Ders Kodu": course.code,
                    "Ders Adı": course.name,
                    "Derslik": f"{room.code} ({room.name})",
                    "Slot": slot.name,
                    "Başlangıç": slot.starts_at.strftime('%Y-%m-%d %H:%M'),
                    "Bitiş": slot.ends_at.strftime('%Y-%m-%d %H:%M'),
                })

        if not data:
            QtWidgets.QMessageBox.information(self, "Boş", "Önce bir plan oluştur.")
            return

        os.makedirs("exports", exist_ok=True)
        fname = f"exports/plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        pd.DataFrame(data).to_excel(fname, index=False)
        QtWidgets.QMessageBox.information(self, "OK", f"Excel kaydedildi:\n{fname}")
