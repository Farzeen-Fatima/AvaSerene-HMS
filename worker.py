""" worker.py — Ava Serene Hospital Worker Dashboard Fully PostgreSQL-native using psycopg2 """

import sys
import random
import string
import csv
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox,
    QTableWidget, QTableWidgetItem, QComboBox,
    QHeaderView, QFrame, QSplitter, QListWidget,
    QListWidgetItem, QFileDialog, QDialog,
    QFormLayout, QSpinBox, QDoubleSpinBox,
    QApplication, QScrollArea, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon

from db import get_connection, log_action

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────
def get_doctors_from_db():
    """Load doctor names from the doctors table (managed by Admin Dashboard)."""
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT name FROM doctors ORDER BY name")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        names = [r[0] for r in rows]
        return names if names else ["No doctors added yet — ask Admin"]
    except Exception:
        return ["No doctors added yet — ask Admin"]

def generate_code():
    return "P-" + "".join(random.choices(string.digits, k=4))

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
#card {
    background: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
}
#sectionTitle {
    font-size: 11px;
    font-weight: 700;
    color: #718096;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
#statBox {
    background: #FFFFFF;
    border-radius: 10px;
    border-left: 4px solid #319795;
    padding: 10px 16px;
}
#statNumber {
    font-size: 28px;
    font-weight: 700;
    color: #2D3748;
}
#statLabel {
    font-size: 11px;
    color: #718096;
    font-weight: 600;
    letter-spacing: 0.5px;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background: #FFFFFF;
    border: 1.5px solid #CBD5E0;
    border-radius: 7px;
    padding: 7px 12px;
    font-size: 13px;
    color: #2D3748;
    min-height: 32px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #319795;
    background: #F0FFFE;
}
QComboBox::drop-down { border: none; width: 24px; }
QPushButton {
    background: #319795;
    color: #FFFFFF;
    border: none;
    border-radius: 7px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 12px;
    min-height: 34px;
}
QPushButton:hover   { background: #2C7A7B; }
QPushButton:pressed { background: #285E61; }
#btnDanger  { background: #E53E3E; }
#btnDanger:hover { background: #C53030; }
#btnWarn    { background: #DD6B20; }
#btnWarn:hover { background: #C05621; }
#btnGreen   { background: #38A169; }
#btnGreen:hover { background: #2F855A; }
#btnGray    { background: #718096; }
#btnGray:hover { background: #4A5568; }
#btnPrimary { background: #3182CE; font-size: 13px; padding: 10px 22px; }
#btnPrimary:hover { background: #2B6CB0; }
QTableWidget {
    background: #FFFFFF;
    border: none;
    border-radius: 10px;
    gridline-color: #EDF2F7;
    font-size: 13px;
}
QTableWidget::item {
    padding: 8px 10px;
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
    font-size: 12px;
    padding: 8px 10px;
    border: none;
    border-right: 1px solid #E2E8F0;
    letter-spacing: 0.5px;
}
QListWidget {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    font-size: 12px;
}
QListWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid #EDF2F7;
}
QListWidget::item:selected {
    background: #E6FFFA;
    color: #234E52;
}
#searchBar {
    background: #FFFFFF;
    border: 1.5px solid #CBD5E0;
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 13px;
}
#searchBar:focus { border-color: #319795; }
#clock {
    font-size: 18px;
    font-weight: 700;
    color: #319795;
    letter-spacing: 1px;
}
#dateLabel {
    font-size: 11px;
    color: #718096;
    letter-spacing: 0.5px;
}
QScrollBar:vertical {
    background: #F7FAFC;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #CBD5E0;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #A0AEC0; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

# ─────────────────────────────────────────
#  STAT CARD
# ─────────────────────────────────────────
class StatCard(QFrame):
    def __init__(self, label: str, value: str = "0", accent: str = "#319795"):
        super().__init__()
        self.setObjectName("statBox")
        self.setStyleSheet(f"#statBox {{ border-left: 4px solid {accent}; background:#FFFFFF; "
                           f"border-radius:10px; padding:10px 16px; }}")
        self.num_lbl = QLabel(value)
        self.num_lbl.setObjectName("statNumber")
        self.num_lbl.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.num_lbl.setStyleSheet(f"color: {accent};")
        
        lbl = QLabel(label.upper())
        lbl.setObjectName("statLabel")
        lbl.setStyleSheet("color: #718096; font-size:11px; font-weight:600; letter-spacing:0.5px;")
        
        v = QVBoxLayout(self)
        v.setContentsMargins(12, 10, 12, 10)
        v.setSpacing(2)
        v.addWidget(self.num_lbl)
        v.addWidget(lbl)

    def set_value(self, val: str):
        self.num_lbl.setText(val)

# ─────────────────────────────────────────
#  ADD PATIENT DIALOG
# ─────────────────────────────────────────
class AddPatientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register New Patient")
        self.setMinimumWidth(420)
        self.setStyleSheet(STYLE)
        
        self.name_input   = QLineEdit()
        self.name_input.setPlaceholderText("Full name")
        
        self.age_input    = QSpinBox()
        self.age_input.setRange(1, 120)
        self.age_input.setValue(25)
        
        self.gender_input = QComboBox()
        self.gender_input.addItems(["Male", "Female", "Other"])
        
        self.area_input   = QLineEdit()
        self.area_input.setPlaceholderText("City / Area")
        
        self.doctor_input = QComboBox()
        self.doctor_input.addItems(get_doctors_from_db())
        
        self.fee_input    = QDoubleSpinBox()
        self.fee_input.setRange(0, 99999)
        self.fee_input.setPrefix("Rs. ")
        self.fee_input.setValue(500)
        
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)
        form.addRow("Patient Name :", self.name_input)
        form.addRow("Age :",          self.age_input)
        form.addRow("Gender :",       self.gender_input)
        form.addRow("Area :",         self.area_input)
        form.addRow("Doctor :",       self.doctor_input)
        form.addRow("Fee Paid :",     self.fee_input)
        
        ok_btn = QPushButton("Register Patient")
        ok_btn.setObjectName("btnPrimary")
        ok_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btnGray")
        cancel_btn.clicked.connect(self.reject)
        
        btns = QHBoxLayout()
        btns.addWidget(cancel_btn)
        btns.addWidget(ok_btn)
        
        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(24, 24, 24, 24)
        root.addLayout(form)
        root.addLayout(btns)

    def get_data(self):
        return {
            "name":   self.name_input.text().strip(),
            "age":    self.age_input.value(),
            "gender": self.gender_input.currentText(),
            "area":   self.area_input.text().strip(),
            "doctor": self.doctor_input.currentText(),
            "fee":    self.fee_input.value(),
        }

# ─────────────────────────────────────────
#  PDF SLIP GENERATION
# ─────────────────────────────────────────
def generate_pdf_slip(patient: dict, output_path: str):
    """Pixel-perfect 80mm thermal slip for Ava Serene Hospital."""
    try:
        from reportlab.lib.pagesizes import mm
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
    except ImportError:
        return False

    W = 80 * mm
    H = 160 * mm
    MX = 5 * mm
    CX = W / 2

    TEAL    = colors.HexColor("#0D7377")
    TEAL_LT = colors.HexColor("#E6FFFA")
    DARK    = colors.HexColor("#1A202C")
    GRAY    = colors.HexColor("#718096")
    WHITE   = colors.white
    RULE    = colors.HexColor("#CBD5E0")

    visit_dt = patient.get("visit_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if isinstance(visit_dt, str):
        date_str = visit_dt[:10]
        time_str = visit_dt[11:16]
    else:
        date_str = visit_dt.strftime("%Y-%m-%d")
        time_str = visit_dt.strftime("%H:%M")

    c = canvas.Canvas(output_path, pagesize=(W, H))

    # header
    c.setFillColor(TEAL)
    c.rect(0, H - 30*mm, W, 30*mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(CX, H - 10*mm, "AVA SERENE HOSPITAL")
    c.setFont("Helvetica", 8)
    c.drawCentredString(CX, H - 16*mm, "Patient Visit Receipt")
    c.setFont("Helvetica-Oblique", 7)
    c.drawCentredString(CX, H - 21.5*mm, "Compassionate Care, Always")

    def dashed_rule(y):
        c.setStrokeColor(RULE)
        c.setDash(2, 3)
        c.setLineWidth(0.4)
        c.line(MX, y, W - MX, y)
        c.setDash()
        c.setLineWidth(1)

    dashed_rule(H - 32*mm)

    # token box
    c.setFillColor(TEAL_LT)
    c.roundRect(MX, H - 52*mm, W - 2*MX, 17*mm, 2.5*mm, fill=1, stroke=0)
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 7)
    c.drawCentredString(CX, H - 37.5*mm, "TOKEN NUMBER")
    c.setFillColor(TEAL)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(CX, H - 49*mm, patient["code"])

    dashed_rule(H - 55*mm)

    # details
    LX = MX + 1*mm
    VX = MX + 24*mm

    def detail_row(label, value, y):
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 7.5)
        c.drawString(LX, y, label)
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(VX, y, str(value))

    ROW_H = 7.2*mm
    base  = H - 60*mm
    detail_row("Name",      patient["name"],                                     base)
    detail_row("Age / Sex", f"{patient['age']} yrs  /  {patient['gender']}",   base - ROW_H)
    detail_row("Area",      patient.get("area", "-") or "-",                     base - 2*ROW_H)
    detail_row("Doctor",    patient.get("doctor", "-") or "-",                   base - 3*ROW_H)
    detail_row("Fee Paid",  f"Rs. {float(patient.get('fee', 0)):.0f}",           base - 4*ROW_H)
    detail_row("Date",      date_str,                                            base - 5*ROW_H)
    detail_row("Time",      time_str,                                            base - 6*ROW_H)

    dashed_rule(base - 7.2*ROW_H)

    badge_y = base - 8.4*ROW_H
    c.setFillColor(TEAL_LT)
    c.roundRect(MX, badge_y - 1*mm, W - 2*MX, 7*mm, 2*mm, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(CX, badge_y + 1.5*mm, "STATUS:  WAITING FOR CONSULTATION")

    fy = badge_y - 9*mm
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 7)
    c.drawCentredString(CX, fy,          "Please keep this slip with you.")
    c.drawCentredString(CX, fy - 4.5*mm, "Show it when your token is called.")
    dashed_rule(fy - 9*mm)
    c.setFont("Helvetica-Oblique", 6.5)
    c.drawCentredString(CX, fy - 13*mm, "Ava Serene Hospital  —  Thank you for visiting")

    c.save()
    return True

# ─────────────────────────────────────────
#  WORKER DASHBOARD
# ─────────────────────────────────────────
class WorkerDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ava Serene Hospital — Worker Dashboard")
        self.resize(1200, 700)
        self.setStyleSheet(STYLE)
        self._build_ui()
        self._start_clock()
        self.load_patients()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)
        
        # ── LEFT PANEL ──────────────────────
        left = QVBoxLayout()
        left.setSpacing(14)
        
        # clock strip
        clock_row = QHBoxLayout()
        self.clock_lbl = QLabel("00:00:00")
        self.clock_lbl.setObjectName("clock")
        self.date_lbl  = QLabel("")
        self.date_lbl.setObjectName("dateLabel")
        clock_row.addWidget(self.clock_lbl)
        clock_row.addStretch()
        clock_row.addWidget(self.date_lbl)
        
        # stat row
        self.stat_waiting   = StatCard("Waiting",     "0", "#D69E2E")
        self.stat_consult   = StatCard("In Consult",  "0", "#3182CE")
        self.stat_done      = StatCard("Completed",   "0", "#38A169")
        self.stat_today     = StatCard("Today Total", "0", "#319795")
        
        stat_row = QHBoxLayout()
        stat_row.setSpacing(10)
        for s in [self.stat_waiting, self.stat_consult, self.stat_done, self.stat_today]:
            stat_row.addWidget(s)
            
        add_btn = QPushButton("Register New Patient")
        add_btn.setObjectName("btnPrimary")
        add_btn.setMinimumHeight(44)
        add_btn.clicked.connect(self.open_add_dialog)
        
        # queue
        queue_lbl = QLabel("PATIENT QUEUE")
        queue_lbl.setObjectName("sectionTitle")
        self.queue_list = QListWidget()
        self.queue_list.setMinimumHeight(180)
        
        left.addLayout(clock_row)
        left.addLayout(stat_row)
        left.addWidget(add_btn)
        left.addWidget(queue_lbl)
        left.addWidget(self.queue_list)
        
        # action buttons
        act_lbl = QLabel("ACTIONS")
        act_lbl.setObjectName("sectionTitle")
        left.addWidget(act_lbl)
        
        btn_consult = QPushButton("Mark In Consultation")
        btn_consult.setObjectName("btnWarn")
        btn_consult.clicked.connect(self.mark_in_consultation)
        
        btn_done = QPushButton("Mark Completed")
        btn_done.setObjectName("btnGreen")
        btn_done.clicked.connect(self.mark_completed)
        
        btn_next = QPushButton("Serve Next in Queue")
        btn_next.clicked.connect(self.serve_next)
        
        btn_slip = QPushButton("Print Slip (PDF)")
        btn_slip.clicked.connect(self.print_slip)
        
        btn_del = QPushButton("Delete Patient")
        btn_del.setObjectName("btnDanger")
        btn_del.clicked.connect(self.delete_patient)
        
        for btn in [btn_consult, btn_done, btn_next, btn_slip, btn_del]:
            btn.setMinimumHeight(36)
            left.addWidget(btn)
            
        # export row
        exp_lbl = QLabel("REPORTS")
        exp_lbl.setObjectName("sectionTitle")
        left.addWidget(exp_lbl)
        
        exp_row = QHBoxLayout()
        btn_daily   = QPushButton("Daily CSV")
        btn_monthly = QPushButton("Monthly CSV")
        btn_daily.setObjectName("btnGray")
        btn_monthly.setObjectName("btnGray")
        btn_daily.clicked.connect(self.export_daily)
        btn_monthly.clicked.connect(self.export_monthly)
        exp_row.addWidget(btn_daily)
        exp_row.addWidget(btn_monthly)
        left.addLayout(exp_row)
        left.addStretch()
        
        # ── RIGHT PANEL ─────────────────────
        right = QVBoxLayout()
        right.setSpacing(12)
        
        right_hdr = QHBoxLayout()
        title = QLabel("All Patients")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #2D3748;")
        
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchBar")
        self.search_input.setPlaceholderText("Search by name or code…")
        self.search_input.setMaximumWidth(260)
        self.search_input.textChanged.connect(self.filter_table)
        
        right_hdr.addWidget(title)
        right_hdr.addStretch()
        right_hdr.addWidget(self.search_input)
        
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            ["Code", "Name", "Age", "Gender", "Area", "Doctor", "Fee (Rs.)", "Date & Time", "Status"]
        )
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget { alternate-background-color: #F7FAFC; }"
        )
        
        right.addLayout(right_hdr)
        right.addWidget(self.table)
        
        left_w = QWidget()
        left_w.setLayout(left)
        left_w.setFixedWidth(300)
        
        root.addWidget(left_w)
        root.addLayout(right)

    def _start_clock(self):
        self._tick()
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(1000)

    def _tick(self):
        now = datetime.now()
        self.clock_lbl.setText(now.strftime("%H:%M:%S"))
        self.date_lbl.setText(now.strftime("%A, %d %B %Y"))

    # ── LOAD DATA ───────────────────────────
    def load_patients(self):
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("""
                SELECT code, name, age, gender, area, doctor, fee, visit_date, status
                FROM patients ORDER BY id DESC
            """)
            self._all_rows = cur.fetchall()
            
            today = datetime.now().strftime("%Y-%m-%d")
            cur.execute("SELECT COUNT(*) FROM patients WHERE status = %s", ("waiting",))
            w = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM patients WHERE status = %s", ("in_consultation",))
            c = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM patients WHERE status = %s", ("completed",))
            d = cur.fetchone()[0]
            cur.execute(
                "SELECT COUNT(*) FROM patients WHERE DATE(visit_date) = %s::date",
                (today,)
            )
            t = cur.fetchone()[0]
            
            cur.close()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))
            return
            
        self.stat_waiting.set_value(str(w))
        self.stat_consult.set_value(str(c))
        self.stat_done.set_value(str(d))
        self.stat_today.set_value(str(t))
        
        self._render_table(self._all_rows)
        self._refresh_queue()

    def _render_table(self, rows):
        STATUS_COLORS = {
            "waiting":         ("#D69E2E", "Waiting"),
            "in_consultation": ("#3182CE", "In Consult"),
            "completed":       ("#38A169", "Completed"),
        }
        
        self.table.setRowCount(0)
        for r in rows:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            for c, v in enumerate(r):
                if c == 8:
                    color, text = STATUS_COLORS.get(str(v), ("#718096", str(v)))
                    item = QTableWidgetItem(text)
                    item.setForeground(QColor(color))
                    item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                elif c == 6:
                    item = QTableWidgetItem(f"{float(v):.0f}")
                else:
                    item = QTableWidgetItem(str(v))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(row_idx, c, item)

    def _refresh_queue(self):
        self.queue_list.clear()
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("""
                SELECT code, name, age, doctor FROM patients
                WHERE status = %s ORDER BY id ASC
            """, ("waiting",))
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except Exception:
            return
            
        for i, (code, name, age, doctor) in enumerate(rows, 1):
            item = QListWidgetItem(f"  {i}.  {code}  —  {name} ({age})   {doctor}")
            self.queue_list.addItem(item)

    def filter_table(self, text):
        text = text.lower()
        filtered = [
            r for r in self._all_rows
            if text in str(r[0]).lower() or text in str(r[1]).lower()
        ]
        self._render_table(filtered)

    def _selected_code(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Select a Patient", "Please click on a patient row first.")
            return None
        return self.table.item(rows[0].row(), 0).text()

    def _get_patient(self, code):
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("""
                SELECT code, name, age, gender, area, doctor, fee, visit_date, status
                FROM patients WHERE code = %s
            """, (code,))
            row = cur.fetchone()
            cur.close()
            conn.close()
        except Exception:
            return None
        if not row:
            return None
        keys = ["code", "name", "age", "gender", "area", "doctor", "fee", "visit_date", "status"]
        return dict(zip(keys, row))

    def _update_status(self, code, status):
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("UPDATE patients SET status = %s WHERE code = %s", (status, code))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))
            return
        self.load_patients()

    # ── ACTIONS ─────────────────────────────
    def open_add_dialog(self):
        dlg = AddPatientDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_data()
        if not data["name"]:
            QMessageBox.warning(self, "Error", "Patient name is required.")
            return
            
        code = generate_code()
        now  = datetime.now()
        
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("""
                INSERT INTO patients (code, name, age, gender, area, doctor, fee, visit_date, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (code, data["name"], data["age"], data["gender"],
                  data["area"], data["doctor"], data["fee"], now, "waiting"))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))
            return
            
        self.load_patients()
        reply = QMessageBox.question(
            self, "Patient Registered",
            f"{data['name']} registered with token {code}\n\nPrint slip now?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._do_print_slip(code)

    def mark_in_consultation(self):
        code = self._selected_code()
        if code:
            self._update_status(code, "in_consultation")

    def mark_completed(self):
        code = self._selected_code()
        if code:
            self._update_status(code, "completed")

    def serve_next(self):
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("SELECT code FROM patients WHERE status = %s ORDER BY id ASC LIMIT 1",
                        ("waiting",))
            row = cur.fetchone()
            cur.close()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return
            
        if not row:
            QMessageBox.information(self, "Queue Empty", "No patients are currently waiting.")
            return
        self._update_status(row[0], "in_consultation")
        QMessageBox.information(self, "Next Patient", f"Token {row[0]} called in for consultation.")

    def delete_patient(self):
        code = self._selected_code()
        if not code:
            return
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete patient {code}? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("DELETE FROM patients WHERE code = %s", (code,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))
            return
        self.load_patients()

    def print_slip(self):
        code = self._selected_code()
        if code:
            self._do_print_slip(code)

    def _do_print_slip(self, code):
        patient = self._get_patient(code)
        if not patient:
            QMessageBox.warning(self, "Error", "Patient not found.")
            return
            
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Slip PDF", f"slip_{code}.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return
            
        ok = generate_pdf_slip(patient, path)
        if ok:
            QMessageBox.information(self, "Slip Saved",
                f"Slip saved to:\n{path}\n\nOpen and print from your PDF viewer.")
        else:
            QMessageBox.warning(self, "reportlab Missing",
                "Install reportlab to generate PDF slips:\n\n  pip install reportlab")

    # ── CSV EXPORTS ──────────────────────────
    def _export_csv(self, rows, filename_hint):
        if not rows:
            QMessageBox.information(self, "No Data", "No records found for this period.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", filename_hint, "CSV Files (*.csv)"
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Code", "Name", "Age", "Gender", "Area", "Doctor", "Fee", "Visit Date", "Status"])
            writer.writerows(rows)
        QMessageBox.information(self, "Exported", f"Report saved to:\n{path}")

    def export_daily(self):
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("""
                SELECT code, name, age, gender, area, doctor, fee, visit_date, status
                FROM patients WHERE DATE(visit_date) = %s::date
            """, (today,))
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))
            return
        self._export_csv(rows, f"daily_report_{today}.csv")

    def export_monthly(self):
        month = datetime.now().strftime("%Y-%m")
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("""
                SELECT code, name, age, gender, area, doctor, fee, visit_date, status
                FROM patients WHERE TO_CHAR(visit_date, 'YYYY-MM') = %s
            """, (month,))
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))
            return
        self._export_csv(rows, f"monthly_report_{month}.csv")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = WorkerDashboard()
    w.show()
    sys.exit(app.exec_())