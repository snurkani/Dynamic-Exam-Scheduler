import os, sys
from pathlib import Path
import PyQt5
from app.ui.search_sql import StudentSearchPage
from app.ui.courses_sql import CoursesPage
from app.ui.seating_sql import SeatingPage


def _fix_qt_paths():
    base = Path(PyQt5.__file__).parent
    plugin_candidates = [base / "Qt5" / "plugins" / "platforms", base / "Qt" / "plugins" / "platforms"]
    bin_candidates = [base / "Qt5" / "bin", base / "Qt" / "bin"]
    for p in bin_candidates:
        if p.exists():
            try:
                os.add_dll_directory(str(p))
            except Exception:
                os.environ["PATH"] = str(p) + os.pathsep + os.environ.get("PATH", "")
            break
    for p in plugin_candidates:
        if p.exists():
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(p)
            break
_fix_qt_paths()

from PyQt5 import QtWidgets
from app.ui.login import LoginWindow
from app.ui.classroom import ClassroomPage
from app.ui.users_sql import UsersPage
from app.ui.importer import ImporterPage
from app.ui.scheduler_sql import SchedulerPage

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user or {}
        role = self.current_user.get("role", "?")
        email = self.current_user.get("email", "")
        self.setWindowTitle(f"Dinamik Sinav Takvimi - {role} - {email}")
        self.resize(1100, 700)

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(ClassroomPage(current_user=self.current_user), "Derslikler")
        tabs.addTab(ImporterPage(current_user=self.current_user), "Icer Aktar (Excel)")
        tabs.addTab(SchedulerPage(current_user=self.current_user), "Program (MVP)")
        tabs.addTab(SeatingPage(current_user=self.current_user), "Oturma Planı")
        tabs.addTab(StudentSearchPage(current_user=self.current_user), "Öğrenci Ara")
        tabs.addTab(CoursesPage(current_user=self.current_user), "Dersler")


        if (self.current_user.get("role") or "").lower() == "admin":
            tabs.addTab(UsersPage(), "Kullanicilar")
        self.setCentralWidget(tabs)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    login = LoginWindow()
    if login.exec_() != QtWidgets.QDialog.Accepted:
        sys.exit(0)
    w = MainWindow(current_user=login.current_user)
    w.show()
    sys.exit(app.exec_())

