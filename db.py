"""
db.py  —  Ava Serene Hospital
PostgreSQL connection layer with auto-config saving.

First run: a dialog asks for your credentials and saves them to db_config.json
Subsequent runs: credentials loaded automatically from db_config.json
"""

import sys
import os
import json
import bcrypt
import psycopg2
from datetime import datetime


# ─────────────────────────────────────────
#  CONFIG FILE — saved next to db.py
# ─────────────────────────────────────────
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db_config.json")

DEFAULT_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "ava_serene_hospital",
    "user":     "postgres",
    "password": "",
}

# Runtime cache — loaded once per session
_config: dict = {}


def load_config() -> dict:
    """Load credentials from db_config.json, or return defaults."""
    global _config
    if _config:
        return _config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                _config = json.load(f)
            return _config
        except Exception:
            pass
    _config = DEFAULT_CONFIG.copy()
    return _config


def save_config(cfg: dict):
    """Persist credentials to db_config.json."""
    global _config
    _config = cfg
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def get_connection():
    """Return a live psycopg2 connection using saved config."""
    cfg = load_config()
    return psycopg2.connect(
        host=cfg["host"],
        port=int(cfg["port"]),
        dbname=cfg["dbname"],
        user=cfg["user"],
        password=cfg["password"],
    )


# ─────────────────────────────────────────
#  CONFIG DIALOG  (PyQt5)
# ─────────────────────────────────────────
def show_config_dialog(error_message: str = "") -> bool:
    """
    Show a GUI dialog to enter PostgreSQL credentials.
    Returns True if user saved and connection works, False if they cancelled.
    """
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
        QLabel, QLineEdit, QPushButton, QSpinBox, QMessageBox, QApplication
    )
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont

    # ensure a QApplication exists
    app = QApplication.instance()
    _app_created = False
    if app is None:
        app = QApplication(sys.argv)
        _app_created = True

    cfg = load_config()

    dlg = QDialog()
    dlg.setWindowTitle("Database Configuration — Ava Serene Hospital")
    dlg.setMinimumWidth(440)
    dlg.setStyleSheet("""
        QDialog  { background:#F0F4F8; font-family:'Segoe UI'; font-size:13px; }
        QLabel   { color:#2D3748; background:transparent; border:none; }
        QLineEdit, QSpinBox {
            background:#FFFFFF; border:1.5px solid #CBD5E0;
            border-radius:7px; padding:7px 12px; min-height:32px;
        }
        QLineEdit:focus, QSpinBox:focus { border-color:#0D7377; background:#F0FFFE; }
        QPushButton {
            background:#0D7377; color:#FFFFFF; border:none; border-radius:7px;
            padding:8px 20px; font-weight:600; min-height:36px;
        }
        QPushButton:hover { background:#0A5F63; }
        #btnGray { background:#718096; }
        #btnGray:hover { background:#4A5568; }
        #errorBox {
            background:#FFF5F5; border:1px solid #FC8181; border-radius:8px;
            padding:10px 14px; color:#C53030;
        }
        #infoBox {
            background:#EBF8FF; border:1px solid #90CDF4; border-radius:8px;
            padding:10px 14px; color:#2C5282;
        }
    """)

    root = QVBoxLayout(dlg)
    root.setContentsMargins(24, 24, 24, 24)
    root.setSpacing(14)

    # title
    title = QLabel("PostgreSQL Connection Setup")
    title.setFont(QFont("Segoe UI", 14, QFont.Bold))
    title.setStyleSheet("color:#0D7377; background:transparent; border:none;")
    root.addWidget(title)

    # error banner (shown only if there was a previous failure)
    if error_message:
        err_lbl = QLabel(f"Connection failed:\n{error_message}")
        err_lbl.setObjectName("errorBox")
        err_lbl.setWordWrap(True)
        root.addWidget(err_lbl)

    # info
    info = QLabel(
        "Enter your PostgreSQL credentials.\n"
        "These will be saved to  db_config.json  in the project folder."
    )
    info.setObjectName("infoBox")
    info.setWordWrap(True)
    root.addWidget(info)

    # form fields
    host_input = QLineEdit(cfg.get("host", "localhost"))
    port_input = QSpinBox()
    port_input.setRange(1, 65535)
    port_input.setValue(int(cfg.get("port", 5432)))
    dbname_input = QLineEdit(cfg.get("dbname", "ava_serene_hospital"))
    user_input   = QLineEdit(cfg.get("user", "postgres"))
    pass_input   = QLineEdit(cfg.get("password", ""))
    pass_input.setEchoMode(QLineEdit.Password)
    pass_input.setPlaceholderText("Your PostgreSQL password")

    form = QFormLayout()
    form.setSpacing(10)
    form.setLabelAlignment(Qt.AlignRight)
    form.addRow("Host :",      host_input)
    form.addRow("Port :",      port_input)
    form.addRow("Database :",  dbname_input)
    form.addRow("Username :",  user_input)
    form.addRow("Password :",  pass_input)
    root.addLayout(form)

    # status label
    status_lbl = QLabel("")
    status_lbl.setStyleSheet("color:#E53E3E; font-size:12px; background:transparent; border:none;")
    status_lbl.setWordWrap(True)
    root.addWidget(status_lbl)

    # buttons
    test_btn   = QPushButton("Test Connection")
    save_btn   = QPushButton("Save & Connect")
    cancel_btn = QPushButton("Cancel")
    cancel_btn.setObjectName("btnGray")

    btn_row = QHBoxLayout()
    btn_row.addWidget(cancel_btn)
    btn_row.addWidget(test_btn)
    btn_row.addWidget(save_btn)
    root.addLayout(btn_row)

    result = {"ok": False}

    def get_form_config():
        return {
            "host":     host_input.text().strip(),
            "port":     port_input.value(),
            "dbname":   dbname_input.text().strip(),
            "user":     user_input.text().strip(),
            "password": pass_input.text(),
        }

    def do_test():
        fc = get_form_config()
        try:
            conn = psycopg2.connect(**fc)
            conn.close()
            status_lbl.setStyleSheet(
                "color:#38A169; font-size:12px; background:transparent; border:none;"
            )
            status_lbl.setText("Connection successful!")
            return True
        except Exception as e:
            status_lbl.setStyleSheet(
                "color:#E53E3E; font-size:12px; background:transparent; border:none;"
            )
            status_lbl.setText(f"Failed: {e}")
            return False

    def do_save():
        fc = get_form_config()
        if not fc["host"] or not fc["dbname"] or not fc["user"]:
            status_lbl.setText("Host, database, and username are required.")
            return
        try:
            conn = psycopg2.connect(**fc)
            conn.close()
            save_config(fc)
            result["ok"] = True
            dlg.accept()
        except Exception as e:
            status_lbl.setStyleSheet(
                "color:#E53E3E; font-size:12px; background:transparent; border:none;"
            )
            status_lbl.setText(f"Connection failed: {e}")

    test_btn.clicked.connect(do_test)
    save_btn.clicked.connect(do_save)
    cancel_btn.clicked.connect(dlg.reject)

    dlg.exec_()
    return result["ok"]


# ─────────────────────────────────────────
#  INIT DB  (tables + seed admin)
# ─────────────────────────────────────────
def init_db():
    """
    Create all tables, triggers, and seed default admin.
    Called at startup by login_window.py.
    If connection fails, shows the config dialog.
    """
    # Try connection — if it fails, prompt for credentials
    try:
        conn = get_connection()
    except Exception as e:
        ok = show_config_dialog(str(e))
        if not ok:
            return
        try:
            conn = get_connection()
        except Exception as e2:
            return  # login_window will show the error

    cur = conn.cursor()

    # ── tables ────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          SERIAL      PRIMARY KEY,
            username    VARCHAR(100) UNIQUE NOT NULL,
            password    BYTEA        NOT NULL,
            role        VARCHAR(10)  NOT NULL
                        CHECK (role IN ('admin','worker')),
            created_at  TIMESTAMP    DEFAULT NOW(),
            last_login  TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id          SERIAL       PRIMARY KEY,
            name        VARCHAR(150) UNIQUE NOT NULL,
            specialty   VARCHAR(150),
            created_at  TIMESTAMP    DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id          SERIAL        PRIMARY KEY,
            code        VARCHAR(20)   UNIQUE NOT NULL,
            name        VARCHAR(150)  NOT NULL,
            age         INTEGER       NOT NULL
                        CHECK (age > 0 AND age <= 100),
            gender      VARCHAR(10)   CHECK (gender IN ('Male','Female','Other')),
            area        VARCHAR(150),
            doctor      VARCHAR(150),
            fee         NUMERIC(10,2) NOT NULL DEFAULT 0
                        CHECK (fee >= 0),
            visit_date  TIMESTAMP     DEFAULT NOW(),
            status      VARCHAR(20)   DEFAULT 'waiting'
                        CHECK (status IN ('waiting','in_consultation','completed'))
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id          SERIAL      PRIMARY KEY,
            user_id     INTEGER     REFERENCES users(id) ON DELETE SET NULL,
            username    VARCHAR(100),
            action      TEXT        NOT NULL,
            timestamp   TIMESTAMP   DEFAULT NOW()
        )
    """)

    # ── indexes ───────────────────────────
    for stmt in [
        "CREATE INDEX IF NOT EXISTS idx_patients_doctor     ON patients(doctor)",
        "CREATE INDEX IF NOT EXISTS idx_patients_visit_date ON patients(visit_date)",
        "CREATE INDEX IF NOT EXISTS idx_patients_status     ON patients(status)",
        "CREATE INDEX IF NOT EXISTS idx_audit_ts            ON audit_logs(timestamp)",
    ]:
        cur.execute(stmt)

    # ── triggers ──────────────────────────

    # TRIGGER 1 — Validate fee >= 0 on INSERT
    cur.execute("""
        CREATE OR REPLACE FUNCTION validate_fee_insert()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.fee < 0 THEN
                RAISE EXCEPTION 'Fee cannot be negative. You entered: Rs. %', NEW.fee;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    cur.execute("DROP TRIGGER IF EXISTS trg_fee_insert ON patients")
    cur.execute("""
        CREATE TRIGGER trg_fee_insert
        BEFORE INSERT ON patients
        FOR EACH ROW EXECUTE FUNCTION validate_fee_insert();
    """)

    # TRIGGER 2 — Validate fee >= 0 on UPDATE
    cur.execute("""
        CREATE OR REPLACE FUNCTION validate_fee_update()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.fee < 0 THEN
                RAISE EXCEPTION 'Fee cannot be negative. You entered: Rs. %', NEW.fee;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    cur.execute("DROP TRIGGER IF EXISTS trg_fee_update ON patients")
    cur.execute("""
        CREATE TRIGGER trg_fee_update
        BEFORE UPDATE ON patients
        FOR EACH ROW EXECUTE FUNCTION validate_fee_update();
    """)

    # TRIGGER 3 — Validate age 1-100 on INSERT
    cur.execute("""
        CREATE OR REPLACE FUNCTION validate_age_insert()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.age <= 0 OR NEW.age > 100 THEN
                RAISE EXCEPTION 'Age must be between 1 and 100. You entered: %', NEW.age;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    cur.execute("DROP TRIGGER IF EXISTS trg_age_insert ON patients")
    cur.execute("""
        CREATE TRIGGER trg_age_insert
        BEFORE INSERT ON patients
        FOR EACH ROW EXECUTE FUNCTION validate_age_insert();
    """)

    # TRIGGER 4 — Validate age 1-100 on UPDATE
    cur.execute("""
        CREATE OR REPLACE FUNCTION validate_age_update()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.age <= 0 OR NEW.age > 100 THEN
                RAISE EXCEPTION 'Age must be between 1 and 100. You entered: %', NEW.age;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    cur.execute("DROP TRIGGER IF EXISTS trg_age_update ON patients")
    cur.execute("""
        CREATE TRIGGER trg_age_update
        BEFORE UPDATE ON patients
        FOR EACH ROW EXECUTE FUNCTION validate_age_update();
    """)

    # TRIGGER 5 — Auto audit log on patient INSERT
    cur.execute("""
        CREATE OR REPLACE FUNCTION audit_patient_insert()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO audit_logs (username, action)
            VALUES ('system',
                'Patient registered: ' || NEW.code || ' — ' || NEW.name ||
                ' (Age: ' || NEW.age ||
                ', Doctor: ' || COALESCE(NEW.doctor, 'N/A') ||
                ', Fee: Rs.' || NEW.fee || ')'
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    cur.execute("DROP TRIGGER IF EXISTS trg_audit_patient_insert ON patients")
    cur.execute("""
        CREATE TRIGGER trg_audit_patient_insert
        AFTER INSERT ON patients
        FOR EACH ROW EXECUTE FUNCTION audit_patient_insert();
    """)

    # TRIGGER 6 — Auto audit log on patient status UPDATE
    cur.execute("""
        CREATE OR REPLACE FUNCTION audit_patient_status()
        RETURNS TRIGGER AS $$
        BEGIN
            IF OLD.status IS DISTINCT FROM NEW.status THEN
                INSERT INTO audit_logs (username, action)
                VALUES ('system',
                    'Patient ' || NEW.code || ' status: ' ||
                    COALESCE(OLD.status, '?') || ' → ' || NEW.status
                );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    cur.execute("DROP TRIGGER IF EXISTS trg_audit_patient_status ON patients")
    cur.execute("""
        CREATE TRIGGER trg_audit_patient_status
        AFTER UPDATE ON patients
        FOR EACH ROW EXECUTE FUNCTION audit_patient_status();
    """)

    # TRIGGER 7 — Auto audit log on patient DELETE
    cur.execute("""
        CREATE OR REPLACE FUNCTION audit_patient_delete()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO audit_logs (username, action)
            VALUES ('system',
                'Patient deleted: ' || OLD.code || ' — ' || OLD.name ||
                ' (Doctor: ' || COALESCE(OLD.doctor, 'N/A') || ')'
            );
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)
    cur.execute("DROP TRIGGER IF EXISTS trg_audit_patient_delete ON patients")
    cur.execute("""
        CREATE TRIGGER trg_audit_patient_delete
        AFTER DELETE ON patients
        FOR EACH ROW EXECUTE FUNCTION audit_patient_delete();
    """)

    # TRIGGER 8 — Doctor name trim on INSERT
    cur.execute("""
        CREATE OR REPLACE FUNCTION trim_doctor_name()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.name := TRIM(NEW.name);
            IF LENGTH(NEW.name) < 3 THEN
                RAISE EXCEPTION 'Doctor name is too short: "%"', NEW.name;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    cur.execute("DROP TRIGGER IF EXISTS trg_trim_doctor_name ON doctors")
    cur.execute("""
        CREATE TRIGGER trg_trim_doctor_name
        BEFORE INSERT ON doctors
        FOR EACH ROW EXECUTE FUNCTION trim_doctor_name();
    """)

    conn.commit()

    # ── default admin ────────────────────
    cur.execute("SELECT id FROM users WHERE username = 'admin'")
    if cur.fetchone() is None:
        pw_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt())
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            ("admin", pw_hash, "admin"),
        )
        conn.commit()
        print("Default admin created  →  username: admin  |  password: admin123")

    cur.close()
    conn.close()


# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────
def update_last_login(username: str):
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("UPDATE users SET last_login = NOW() WHERE username = %s", (username,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[last_login] {e}")


def log_action(user_id, username: str, action: str):
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO audit_logs (user_id, username, action) VALUES (%s, %s, %s)",
            (user_id, username, action),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[log_action] {e}")


# ─────────────────────────────────────────
#  DIRECT RUN  — test connection
# ─────────────────────────────────────────
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    print("Testing PostgreSQL connection …")
    try:
        conn = get_connection()
        conn.close()
        print("Connection OK.")
        init_db()
        print("All tables and triggers ready.")
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Opening config dialog …")
        ok = show_config_dialog(str(e))
        if ok:
            init_db()
            print("Done.")
        else:
            print("Cancelled.")