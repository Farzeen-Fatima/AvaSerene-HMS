"""
admin.py  —  Ava Serene Hospital Admin Dashboard
Fully PostgreSQL-native using psycopg2
"""

import sys
import bcrypt
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox,
    QTableWidget, QTableWidgetItem, QComboBox,
    QTabWidget, QDialog, QFormLayout, QInputDialog,
    QHeaderView, QFrame, QApplication, QSizePolicy,
    QScrollArea, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

from db import get_connection, log_action


# ─────────────────────────────────────────
#  SHARED STYLE
# ─────────────────────────────────────────
STYLE = """
QWidget {
    background-color: #F0F4F8;
    color: #1A202C;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QTabWidget::pane { border: none; background: #F0F4F8; }
QTabBar::tab {
    background: #E2E8F0;
    color: #4A5568;
    padding: 10px 26px;
    font-size: 12px;
    font-weight: 600;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 3px;
}
QTabBar::tab:selected {
    background: #0D7377;
    color: #FFFFFF;
}
QTabBar::tab:hover:!selected { background: #CBD5E0; }
QTableWidget {
    background: #FFFFFF;
    border: none;
    border-radius: 10px;
    gridline-color: #EDF2F7;
    font-size: 13px;
}
QTableWidget::item {
    padding: 9px 12px;
    border-bottom: 1px solid #EDF2F7;
}
QTableWidget::item:selected {
    background: #E6FFFA;
    color: #234E52;
}
QHeaderView::section {
    background: #EDF2F7;
    color: #4A5568;
    font-weight: 700;
    font-size: 11px;
    padding: 9px 12px;
    border: none;
    border-right: 1px solid #E2E8F0;
    letter-spacing: 0.6px;
}
QLineEdit, QComboBox {
    background: #FFFFFF;
    border: 1.5px solid #CBD5E0;
    border-radius: 7px;
    padding: 7px 12px;
    font-size: 13px;
    color: #2D3748;
    min-height: 32px;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #0D7377;
    background: #F0FFFE;
}
QComboBox::drop-down { border: none; width: 24px; }
QPushButton {
    background: #0D7377;
    color: #FFFFFF;
    border: none;
    border-radius: 7px;
    padding: 8px 20px;
    font-weight: 600;
    font-size: 12px;
    min-height: 36px;
}
QPushButton:hover   { background: #0A5F63; }
QPushButton:pressed { background: #084D50; }
#btnDanger { background: #E53E3E; }
#btnDanger:hover { background: #C53030; }
#btnWarn   { background: #DD6B20; }
#btnWarn:hover   { background: #C05621; }
#btnGray   { background: #718096; }
#btnGray:hover   { background: #4A5568; }
QScrollBar:vertical {
    background: #F7FAFC; width: 7px; border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #CBD5E0; border-radius: 4px; min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #A0AEC0; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


# ─────────────────────────────────────────
#  STAT CARD
# ─────────────────────────────────────────
class StatCard(QFrame):
    def __init__(self, label: str, value: str = "0", accent: str = "#0D7377"):
        super().__init__()
        self.setFixedHeight(90)
        self.setStyleSheet(
            f"QFrame {{ background:#FFFFFF; border-radius:10px; "
            f"border-left: 5px solid {accent}; }}"
        )
        self.num = QLabel(value)
        self.num.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.num.setStyleSheet(
            f"color:{accent}; background:transparent; border:none;"
        )
        lbl = QLabel(label.upper())
        lbl.setStyleSheet(
            "color:#718096; font-size:10px; font-weight:700; "
            "letter-spacing:0.8px; background:transparent; border:none;"
        )
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 10, 16, 10)
        v.setSpacing(2)
        v.addWidget(self.num)
        v.addWidget(lbl)

    def set_value(self, v: str):
        self.num.setText(v)


# ─────────────────────────────────────────
#  HEADER BANNER
# ─────────────────────────────────────────
class HeaderBanner(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(72)
        self.setStyleSheet(
            "QFrame { background: qlineargradient("
            "x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #0D7377, stop:1 #14B8A6); border-radius:0px; }"
        )
        self.clock_lbl = QLabel()
        self.clock_lbl.setStyleSheet(
            "color:rgba(255,255,255,0.85); font-size:13px; font-weight:600; "
            "background:transparent; border:none;"
        )
        title = QLabel("AVA SERENE HOSPITAL")
        title.setFont(QFont("Segoe UI", 17, QFont.Bold))
        title.setStyleSheet("color:#FFFFFF; background:transparent; border:none;")

        sub = QLabel("Admin Control Panel")
        sub.setStyleSheet(
            "color:rgba(255,255,255,0.75); font-size:11px; "
            "background:transparent; border:none;"
        )
        left = QVBoxLayout()
        left.setSpacing(1)
        left.addWidget(title)
        left.addWidget(sub)

        row = QHBoxLayout(self)
        row.setContentsMargins(20, 0, 20, 0)
        row.addLayout(left)
        row.addStretch()
        row.addWidget(self.clock_lbl)

        self._tick()
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(1000)

    def _tick(self):
        self.clock_lbl.setText(
            datetime.now().strftime("%A, %d %b %Y   %H:%M:%S")
        )


# ─────────────────────────────────────────
#  DOCTOR PERFORMANCE CARD
# ─────────────────────────────────────────
class DoctorCard(QFrame):
    def __init__(self, name, specialty, total, waiting, completed, fee):
        super().__init__()
        self.setStyleSheet(
            "QFrame { background:#FFFFFF; border-radius:12px; "
            "border: 1px solid #E2E8F0; }"
        )
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(148)

        av = QLabel(name[0].upper() if name else "?")
        av.setFixedSize(48, 48)
        av.setAlignment(Qt.AlignCenter)
        av.setStyleSheet(
            "background:#0D7377; color:#FFFFFF; border-radius:24px; "
            "font-size:20px; font-weight:700; border:none;"
        )
        name_lbl = QLabel(name)
        name_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        name_lbl.setStyleSheet("color:#1A202C; background:transparent; border:none;")

        spec_lbl = QLabel(specialty or "General")
        spec_lbl.setStyleSheet(
            "color:#718096; font-size:11px; background:transparent; border:none;"
        )

        left_col = QVBoxLayout()
        left_col.setSpacing(2)
        left_col.addWidget(av)
        left_col.addWidget(name_lbl)
        left_col.addWidget(spec_lbl)
        left_col.addStretch()

        def mini_stat(val, lbl_text, color):
            f = QFrame()
            f.setStyleSheet(
                f"QFrame {{ background:#F7FAFC; border-radius:8px; "
                f"border-left:3px solid {color}; }}"
            )
            vl = QLabel(str(val))
            vl.setFont(QFont("Segoe UI", 15, QFont.Bold))
            vl.setStyleSheet(f"color:{color}; background:transparent; border:none;")
            ll = QLabel(lbl_text)
            ll.setStyleSheet(
                "color:#A0AEC0; font-size:9px; font-weight:700; "
                "letter-spacing:0.5px; background:transparent; border:none;"
            )
            layout = QVBoxLayout(f)
            layout.setContentsMargins(10, 6, 10, 6)
            layout.setSpacing(0)
            layout.addWidget(vl)
            layout.addWidget(ll)
            return f

        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)
        stats_row.addWidget(mini_stat(total,              "TOTAL",   "#0D7377"))
        stats_row.addWidget(mini_stat(waiting,            "WAITING", "#D69E2E"))
        stats_row.addWidget(mini_stat(completed,          "DONE",    "#38A169"))
        stats_row.addWidget(mini_stat(f"Rs.{int(fee)}",  "FEE",     "#3182CE"))

        right_col = QVBoxLayout()
        right_col.addStretch()
        right_col.addLayout(stats_row)
        right_col.addStretch()

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 14, 16, 14)
        row.setSpacing(20)
        row.addLayout(left_col)
        row.addLayout(right_col, stretch=1)


# ─────────────────────────────────────────
#  DIALOGS
# ─────────────────────────────────────────
class UserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add User")
        self.setMinimumWidth(380)
        self.setStyleSheet(STYLE)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Enter username")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Enter password")
        self.password.setEchoMode(QLineEdit.Password)
        self.role = QComboBox()
        self.role.addItems(["admin", "worker"])

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)
        form.addRow("Username :", self.username)
        form.addRow("Password :", self.password)
        form.addRow("Role :",     self.role)

        ok_btn     = QPushButton("Add User")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btnGray")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        btns = QHBoxLayout()
        btns.addWidget(cancel_btn)
        btns.addWidget(ok_btn)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)
        root.addLayout(form)
        root.addLayout(btns)

    def get_data(self):
        return (
            self.username.text().strip(),
            self.password.text(),
            self.role.currentText(),
        )


class DoctorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Doctor")
        self.setMinimumWidth(380)
        self.setStyleSheet(STYLE)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Dr. Sara Malik")
        self.spec_input = QLineEdit()
        self.spec_input.setPlaceholderText("e.g. General Physician")

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)
        form.addRow("Full Name :",  self.name_input)
        form.addRow("Specialty :", self.spec_input)

        ok_btn     = QPushButton("Add Doctor")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btnGray")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        btns = QHBoxLayout()
        btns.addWidget(cancel_btn)
        btns.addWidget(ok_btn)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)
        root.addLayout(form)
        root.addLayout(btns)

    def get_data(self):
        return (
            self.name_input.text().strip(),
            self.spec_input.text().strip(),
        )


# ─────────────────────────────────────────
#  ADMIN DASHBOARD
# ─────────────────────────────────────────
class AdminDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ava Serene Hospital — Admin Dashboard")
        self.resize(1100, 720)
        self.setStyleSheet(STYLE)
        self._build_ui()
        self.refresh_all()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(HeaderBanner())

        self.stat_users    = StatCard("Total Users",    "0", "#0D7377")
        self.stat_workers  = StatCard("Workers",        "0", "#3182CE")
        self.stat_doctors  = StatCard("Doctors",        "0", "#38A169")
        self.stat_patients = StatCard("Patients Today", "0", "#D69E2E")

        stat_row = QHBoxLayout()
        stat_row.setContentsMargins(16, 14, 16, 6)
        stat_row.setSpacing(12)
        for s in [self.stat_users, self.stat_workers,
                  self.stat_doctors, self.stat_patients]:
            stat_row.addWidget(s)
        root.addLayout(stat_row)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._build_overview_tab(),  "Overview")
        self.tabs.addTab(self._build_users_tab(),     "Users")
        self.tabs.addTab(self._build_doctors_tab(),   "Doctors")
        self.tabs.addTab(self._build_patients_tab(),  "All Patients")

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(16, 8, 16, 16)
        cl.addWidget(self.tabs)
        root.addWidget(content)

    def _build_overview_tab(self):
        tab = QWidget()
        self._cards_grid = QGridLayout()
        self._cards_grid.setSpacing(12)
        self._cards_grid.setAlignment(Qt.AlignTop)

        inner = QWidget()
        inner.setLayout(self._cards_grid)
        inner.setStyleSheet("background:transparent;")

        scroll = QScrollArea()
        scroll.setWidget(inner)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background:transparent;")

        lbl = QLabel("DOCTOR PERFORMANCE — TODAY")
        lbl.setStyleSheet(
            "color:#718096; font-size:11px; font-weight:700; "
            "letter-spacing:1px; background:transparent;"
        )

        v = QVBoxLayout(tab)
        v.setContentsMargins(0, 8, 0, 0)
        v.setSpacing(10)
        v.addWidget(lbl)
        v.addWidget(scroll)
        return tab

    def _build_users_tab(self):
        tab = QWidget()
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(5)
        self.user_table.setHorizontalHeaderLabels(
            ["ID", "Username", "Role", "Created At", "Last Login"]
        )
        self.user_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.verticalHeader().setDefaultSectionSize(40)
        self.user_table.setAlternatingRowColors(True)
        self.user_table.setStyleSheet(
            "QTableWidget { alternate-background-color: #F7FAFC; }"
        )

        add_btn = QPushButton("Add User")
        del_btn = QPushButton("Delete User")
        rst_btn = QPushButton("Reset Password")
        del_btn.setObjectName("btnDanger")
        rst_btn.setObjectName("btnWarn")

        add_btn.clicked.connect(self.add_user)
        del_btn.clicked.connect(self.delete_user)
        rst_btn.clicked.connect(self.reset_password)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addWidget(rst_btn)
        btn_row.addStretch()

        v = QVBoxLayout(tab)
        v.setContentsMargins(0, 10, 0, 0)
        v.setSpacing(10)
        v.addWidget(self.user_table)
        v.addLayout(btn_row)
        return tab

    def _build_doctors_tab(self):
        tab = QWidget()
        self.doctor_table = QTableWidget()
        self.doctor_table.setColumnCount(3)
        self.doctor_table.setHorizontalHeaderLabels(["ID", "Name", "Specialty"])
        self.doctor_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.doctor_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.doctor_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.doctor_table.verticalHeader().setDefaultSectionSize(40)
        self.doctor_table.setAlternatingRowColors(True)
        self.doctor_table.setStyleSheet(
            "QTableWidget { alternate-background-color: #F7FAFC; }"
        )

        add_btn = QPushButton("Add Doctor")
        del_btn = QPushButton("Remove Doctor")
        del_btn.setObjectName("btnDanger")
        add_btn.clicked.connect(self.add_doctor)
        del_btn.clicked.connect(self.delete_doctor)

        note = QLabel(
            "Doctors added here automatically appear in the Worker Dashboard "
            "when registering patients."
        )
        note.setWordWrap(True)
        note.setStyleSheet(
            "background:#EBF8FF; color:#2C5282; border-radius:6px; "
            "padding:8px 12px; font-size:11px; border:1px solid #BEE3F8;"
        )

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()

        v = QVBoxLayout(tab)
        v.setContentsMargins(0, 10, 0, 0)
        v.setSpacing(10)
        v.addWidget(note)
        v.addWidget(self.doctor_table)
        v.addLayout(btn_row)
        return tab

    def _build_patients_tab(self):
        tab = QWidget()
        self.patient_table = QTableWidget()
        self.patient_table.setColumnCount(8)
        self.patient_table.setHorizontalHeaderLabels(
            ["Code", "Name", "Age", "Gender", "Doctor",
             "Fee", "Visit Date", "Status"]
        )
        self.patient_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.patient_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.patient_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.patient_table.verticalHeader().setDefaultSectionSize(38)
        self.patient_table.setAlternatingRowColors(True)
        self.patient_table.setStyleSheet(
            "QTableWidget { alternate-background-color: #F7FAFC; }"
        )

        v = QVBoxLayout(tab)
        v.setContentsMargins(0, 10, 0, 0)
        v.addWidget(self.patient_table)
        return tab

    # ── REFRESH ────────────────────────────
    def refresh_all(self):
        self._load_stats()
        self._load_users()
        self._load_doctors()
        self._load_patients()
        self._load_doctor_cards()

    def _load_stats(self):
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users")
            u = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE role = %s", ("worker",))
            w = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM doctors")
            d = cur.fetchone()[0]
            today = datetime.now().strftime("%Y-%m-%d")
            cur.execute(
                "SELECT COUNT(*) FROM patients WHERE DATE(visit_date) = %s::date",
                (today,)
            )
            p = cur.fetchone()[0]
            cur.close()
            conn.close()
            self.stat_users.set_value(str(u))
            self.stat_workers.set_value(str(w))
            self.stat_doctors.set_value(str(d))
            self.stat_patients.set_value(str(p))
        except Exception as e:
            print(f"[_load_stats] {e}")

    def _load_users(self):
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute(
                "SELECT id, username, role, created_at, last_login FROM users "
                "ORDER BY id"
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[_load_users] {e}")
            return

        ROLE_COLOR = {"admin": "#0D7377", "worker": "#3182CE"}
        self.user_table.setRowCount(0)
        for r in rows:
            idx = self.user_table.rowCount()
            self.user_table.insertRow(idx)
            for c, val in enumerate(r):
                text = str(val) if val is not None else "—"
                item = QTableWidgetItem(text)
                if c == 2:
                    item.setForeground(
                        QColor(ROLE_COLOR.get(str(val), "#718096"))
                    )
                    item.setFont(QFont("Segoe UI", 11, QFont.Bold))
                self.user_table.setItem(idx, c, item)

    def _load_doctors(self):
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("SELECT id, name, specialty FROM doctors ORDER BY name")
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[_load_doctors] {e}")
            return

        self.doctor_table.setRowCount(0)
        for r in rows:
            idx = self.doctor_table.rowCount()
            self.doctor_table.insertRow(idx)
            for c, val in enumerate(r):
                self.doctor_table.setItem(
                    idx, c,
                    QTableWidgetItem(str(val) if val else "—")
                )

    def _load_patients(self):
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("""
                SELECT code, name, age, gender, doctor, fee, visit_date, status
                FROM patients ORDER BY id DESC
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[_load_patients] {e}")
            return

        S_COLOR = {
            "waiting":         "#D69E2E",
            "in_consultation": "#3182CE",
            "completed":       "#38A169",
        }
        S_TEXT = {
            "waiting":         "Waiting",
            "in_consultation": "In Consult",
            "completed":       "Completed",
        }

        self.patient_table.setRowCount(0)
        for r in rows:
            idx = self.patient_table.rowCount()
            self.patient_table.insertRow(idx)
            for c, val in enumerate(r):
                if c == 7:
                    text  = S_TEXT.get(str(val), str(val))
                    color = S_COLOR.get(str(val), "#718096")
                    item  = QTableWidgetItem(text)
                    item.setForeground(QColor(color))
                    item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                elif c == 5:
                    item = QTableWidgetItem(
                        f"Rs. {float(val):.0f}" if val else "Rs. 0"
                    )
                else:
                    item = QTableWidgetItem(str(val) if val else "—")
                self.patient_table.setItem(idx, c, item)

    def _load_doctor_cards(self):
        while self._cards_grid.count():
            w = self._cards_grid.takeAt(0).widget()
            if w:
                w.deleteLater()

        try:
            conn  = get_connection()
            cur   = conn.cursor()
            cur.execute("SELECT name, specialty FROM doctors ORDER BY name")
            docs  = cur.fetchall()
            today = datetime.now().strftime("%Y-%m-%d")
            cards = []

            for name, spec in docs:
                cur.execute(
                    "SELECT COUNT(*) FROM patients "
                    "WHERE doctor = %s AND DATE(visit_date) = %s::date",
                    (name, today)
                )
                total = cur.fetchone()[0]

                cur.execute(
                    "SELECT COUNT(*) FROM patients "
                    "WHERE doctor = %s AND status = %s",
                    (name, "waiting")
                )
                waiting = cur.fetchone()[0]

                cur.execute(
                    "SELECT COUNT(*) FROM patients "
                    "WHERE doctor = %s AND status = %s AND DATE(visit_date) = %s::date",
                    (name, "completed", today)
                )
                completed = cur.fetchone()[0]

                cur.execute(
                    "SELECT COALESCE(SUM(fee), 0) FROM patients "
                    "WHERE doctor = %s AND DATE(visit_date) = %s::date",
                    (name, today)
                )
                fee = cur.fetchone()[0]

                cards.append(
                    DoctorCard(name, spec, total, waiting, completed, fee)
                )

            cur.close()
            conn.close()
        except Exception as e:
            print(f"[_load_doctor_cards] {e}")
            cards = []

        COLS = 2
        for i, card in enumerate(cards):
            self._cards_grid.addWidget(card, i // COLS, i % COLS)

        if not cards:
            empty = QLabel(
                "No doctors added yet.\n"
                "Go to the Doctors tab and add your first doctor."
            )
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(
                "color:#A0AEC0; font-size:14px; background:transparent;"
            )
            self._cards_grid.addWidget(empty, 0, 0)

    # ── USER ACTIONS ───────────────────────
    def add_user(self):
        dlg = UserDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        username, password, role = dlg.get_data()
        if not username or not password:
            QMessageBox.warning(self, "Error", "All fields are required.")
            return
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, pw_hash, role),
            )
            conn.commit()
            cur.close()
            conn.close()
            log_action(None, "admin", f"Created user '{username}' with role '{role}'")
            self.refresh_all()
            QMessageBox.information(
                self, "User Created", f"'{username}' has been added."
            )
        except Exception as e:
            if "unique constraint" in str(e).lower():
                QMessageBox.warning(self, "Error", "Username already exists.")
            else:
                QMessageBox.critical(self, "Database Error", str(e))

    def delete_user(self):
        rows = self.user_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Select a user", "Click on a row first.")
            return
        row   = rows[0].row()
        uid   = self.user_table.item(row, 0).text()
        uname = self.user_table.item(row, 1).text()
        if uname == "admin":
            QMessageBox.warning(self, "Denied", "Cannot delete the main admin account.")
            return
        reply = QMessageBox.question(
            self, "Confirm Delete", f"Delete user '{uname}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("DELETE FROM users WHERE id = %s", (int(uid),))
            conn.commit()
            cur.close()
            conn.close()
            log_action(None, "admin", f"Deleted user '{uname}'")
            self.refresh_all()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))

    def reset_password(self):
        rows = self.user_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Select a user", "Click on a row first.")
            return
        row   = rows[0].row()
        uid   = self.user_table.item(row, 0).text()
        uname = self.user_table.item(row, 1).text()
        new_pw, ok = QInputDialog.getText(
            self, "Reset Password",
            f"New password for '{uname}':", QLineEdit.Password
        )
        if not ok or not new_pw:
            return
        pw_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt())
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("UPDATE users SET password = %s WHERE id = %s", (pw_hash, int(uid)))
            conn.commit()
            cur.close()
            conn.close()
            log_action(None, "admin", f"Reset password for '{uname}'")
            QMessageBox.information(self, "Done", "Password has been reset.")
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))

    # ── DOCTOR ACTIONS ─────────────────────
    def add_doctor(self):
        dlg = DoctorDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        name, specialty = dlg.get_data()
        if not name:
            QMessageBox.warning(self, "Error", "Doctor name is required.")
            return
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute(
                "INSERT INTO doctors (name, specialty) VALUES (%s, %s)",
                (name, specialty),
            )
            conn.commit()
            cur.close()
            conn.close()
            log_action(None, "admin", f"Added doctor '{name}'")
            self.refresh_all()
            QMessageBox.information(
                self, "Doctor Added",
                f"'{name}' added.\n\n"
                "They now appear in the Worker Dashboard doctor list."
            )
        except Exception as e:
            if "unique constraint" in str(e).lower():
                QMessageBox.warning(self, "Error", "A doctor with that name already exists.")
            else:
                QMessageBox.critical(self, "Database Error", str(e))

    def delete_doctor(self):
        rows = self.doctor_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Select a doctor", "Click on a row first.")
            return
        row  = rows[0].row()
        did  = self.doctor_table.item(row, 0).text()
        name = self.doctor_table.item(row, 1).text()
        reply = QMessageBox.question(
            self, "Confirm", f"Remove '{name}' from the system?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("DELETE FROM doctors WHERE id = %s", (int(did),))
            conn.commit()
            cur.close()
            conn.close()
            log_action(None, "admin", f"Deleted doctor '{name}'")
            self.refresh_all()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = AdminDashboard()
    w.show()
    sys.exit(app.exec_())