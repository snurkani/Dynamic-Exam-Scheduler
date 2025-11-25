from PyQt5 import QtWidgets, QtCore, QtGui
from datetime import datetime
import os, pandas as pd
from app.db_sql import query_all, query_one
from app.tools.build_seating_sql import build_for_exam

class GridPreview(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.rows=0; self.cols=0; self.labels={}
        self.setMinimumHeight(260)
    def set_layout(self, r,c): self.rows, self.cols = r,c; self.update()
    def set_labels(self, d): self.labels = d or {}; self.update()
    def paintEvent(self, _):
        p=QtGui.QPainter(self); p.setRenderHint(QtGui.QPainter.Antialiasing)
        if self.rows<=0 or self.cols<=0: return
        m=10; w=self.width()-m*2; h=self.height()-m*2; cw=w/self.cols; ch=h/self.rows
        p.setFont(QtGui.QFont("Helvetica",8))
        for r in range(self.rows):
            for k in range(self.cols):
                x=m+k*cw; y=m+r*ch
                p.setPen(QtGui.QPen(QtCore.Qt.black)); p.drawRect(QtCore.QRectF(x,y,cw-2,ch-2))
                txt=self.labels.get((r,k)); 
                if txt: p.drawText(QtCore.QRectF(x,y,cw-2,ch-2), QtCore.Qt.AlignCenter, txt)

class SeatingPage(QtWidgets.QWidget):
    def __init__(self, current_user=None):
        super().__init__(); self.current_user=current_user or {}
        lay=QtWidgets.QVBoxLayout(self)
        top=QtWidgets.QHBoxLayout(); top.addWidget(QtWidgets.QLabel("Bölüm:"))
        self.dept=QtWidgets.QComboBox(); top.addWidget(self.dept,1); lay.addLayout(top)
        for d in query_all('SELECT id,name FROM departments ORDER BY id'): self.dept.addItem(d['name'], d['id'])

        self.tbl=QtWidgets.QTableWidget(0,4)
        self.tbl.setHorizontalHeaderLabels(['ea_id','Ders','Derslik','Saat'])
        self.tbl.setColumnHidden(0,True); self.tbl.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.tbl)

        btnrow=QtWidgets.QHBoxLayout()
        self.btn_build=QtWidgets.QPushButton('Oturma Planını Oluştur')
        self.btn_pdf=QtWidgets.QPushButton('PDF İndir'); self.btn_xlsx=QtWidgets.QPushButton('Excel’e Aktar')
        btnrow.addWidget(self.btn_build); btnrow.addStretch(1); btnrow.addWidget(self.btn_pdf); btnrow.addWidget(self.btn_xlsx)
        lay.addLayout(btnrow)

        split=QtWidgets.QSplitter(); split.setOrientation(QtCore.Qt.Horizontal)
        self.grid=GridPreview(); split.addWidget(self.grid)
        self.list=QtWidgets.QTableWidget(0,4); self.list.setHorizontalHeaderLabels(['Öğrenci No','Ad Soyad','Sıra','Sütun'])
        self.list.horizontalHeader().setStretchLastSection(True); split.addWidget(self.list); split.setSizes([500,400])
        lay.addWidget(split)

        self.dept.currentIndexChanged.connect(self.load_exams)
        self.tbl.itemSelectionChanged.connect(self.load_preview)
        self.btn_build.clicked.connect(self.run_build_for_selected)
        self.btn_xlsx.clicked.connect(self.export_excel)
        self.btn_pdf.clicked.connect(self.export_pdf)
        self.load_exams()

    def _dep(self): return self.dept.currentData()
    def load_exams(self):
        self.tbl.setRowCount(0)
        rows=query_all("""
          SELECT ea.id ea_id, c.code||' - '||c.name ders, cr.code||' ('||cr.name||')' room,
                 s.starts_at st, s.ends_at et
          FROM exam_assignments ea
          JOIN courses c ON c.id=ea.course_id
          JOIN classrooms cr ON cr.id=ea.classroom_id
          JOIN exam_slots s ON s.id=ea.slot_id
          WHERE ea.department_id=? ORDER BY s.starts_at, c.code
        """,(self._dep(),))
        for r,row in enumerate(rows):
            self.tbl.insertRow(r)
            start=row['st'][:16].replace('-','.'); end=row['et'][11:16]
            vals=[row['ea_id'], row['ders'], row['room'], f"{start} - {end}"]
            for c,v in enumerate(vals): self.tbl.setItem(r,c,QtWidgets.QTableWidgetItem(str(v)))
        if rows: self.tbl.selectRow(0)

    def clear_preview(self):
        self.grid.set_layout(0,0); self.grid.set_labels({}); self.list.setRowCount(0)

    def load_preview(self):
        it=self.tbl.selectedItems(); 
        if not it: return
        ea_id=int(self.tbl.item(it[0].row(),0).text())
        cfg=query_one("""SELECT c.rows,c.cols FROM exam_assignments ea JOIN classrooms c ON c.id=ea.classroom_id WHERE ea.id=?""",(ea_id,))
        if not cfg: self.clear_preview(); return
        self.grid.set_layout(cfg['rows'], cfg['cols'])
        seats=query_all("""
          SELECT s.number num, s.name sname, sa.row_index r, sa.col_index k
          FROM seating_assignments sa JOIN students s ON s.id=sa.student_id
          WHERE sa.exam_assignment_id=? ORDER BY sa.row_index, sa.col_index
        """,(ea_id,))
        self.list.setRowCount(0); labels={}
        for i,row in enumerate(seats):
            self.list.insertRow(i)
            for c,v in enumerate([row['num'],row['sname'],row['r']+1,row['k']+1]):
                self.list.setItem(i,c,QtWidgets.QTableWidgetItem(str(v)))
            labels[(row['r'],row['k'])]=str(row['num'])[-4:]
        self.grid.set_labels(labels)

    def selected_ea(self):
        it=self.tbl.selectedItems(); 
        return None if not it else int(self.tbl.item(it[0].row(),0).text())

    def run_build_for_selected(self):
        ea=self.selected_ea()
        if not ea: QtWidgets.QMessageBox.information(self,'Bilgi','Önce bir sınav seç.'); return
        build_for_exam(ea); self.load_preview()
        QtWidgets.QMessageBox.information(self,'OK','Oturma planı oluşturuldu.')

    def export_excel(self):
        ea=self.selected_ea(); 
        if not ea: return
        rows=query_all("""
          SELECT d.name department, cr.code||' ('||cr.name||')' room,
                 c.code course_code, c.name course_name,
                 st.number student_number, st.name student_name,
                 sa.row_index+1 row_no, sa.col_index+1 col_no
          FROM seating_assignments sa
          JOIN exam_assignments ea ON ea.id=sa.exam_assignment_id
          JOIN courses c ON c.id=ea.course_id
          JOIN classrooms cr ON cr.id=sa.classroom_id
          JOIN departments d ON d.id=sa.department_id
          JOIN students st ON st.id=sa.student_id
          WHERE sa.exam_assignment_id=? ORDER BY row_no, col_no
        """,(ea,))
        if not rows: QtWidgets.QMessageBox.information(self,'Boş','Önce oturma planını oluştur.'); return
        os.makedirs('exports',exist_ok=True)
        fn=f"exports/seating_{ea}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        pd.DataFrame(rows).to_excel(fn,index=False)
        QtWidgets.QMessageBox.information(self,'OK',f'Excel kaydedildi:\n{fn}')

    def export_pdf(self):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except Exception:
            QtWidgets.QMessageBox.information(self,'Bilgi','PDF modülü yok. Excel’i kullanabilirsin.'); return
        ea=self.selected_ea(); 
        if not ea: return
        cfg=query_one("""
          SELECT c.rows,c.cols, cr.code room_code, cr.name room_name, cs.code course_code, cs.name course_name
          FROM exam_assignments ea
          JOIN classrooms cr ON cr.id=ea.classroom_id
          JOIN courses cs ON cs.id=ea.course_id
          JOIN classrooms c ON c.id=ea.classroom_id
          WHERE ea.id=?""",(ea,))
        seats=query_all("""
          SELECT st.number num, st.name sname, sa.row_index r, sa.col_index k
          FROM seating_assignments sa JOIN students st ON st.id=sa.student_id
          WHERE sa.exam_assignment_id=?""",(ea,))
        if not seats: QtWidgets.QMessageBox.information(self,'Boş','Önce oturma planını oluştur.'); return
        os.makedirs('exports',exist_ok=True)
        fn=f"exports/seating_{ea}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        c=canvas.Canvas(fn, pagesize=A4); W,H=A4
        c.setFont('Helvetica-Bold',12)
        c.drawString(40,H-40,f"Oturma Planı - {cfg['course_code']} {cfg['course_name']} - {cfg['room_code']} ({cfg['room_name']})")
        m=40; gw=W-m*2; gh=H-120; cw=gw/cfg['cols']; ch=gh/cfg['rows']
        c.setFont('Helvetica',8)
        for r in range(cfg['rows']):
            for k in range(cfg['cols']):
                x=m+k*cw; y=80+r*ch; c.rect(x,y,cw-2,ch-2)
        for s in seats:
            short=str(s['num'])[-4:]; x=m+s['k']*cw; y=80+s['r']*ch
            c.drawCentredString(x+cw/2,y+ch/2,short)
        c.showPage(); c.save()
        QtWidgets.QMessageBox.information(self,'OK',f'PDF kaydedildi:\n{fn}')
