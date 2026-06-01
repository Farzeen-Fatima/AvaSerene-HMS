import sys
import bcrypt

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QComboBox, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from db import init_db, get_connection, update_last_login, show_config_dialog


STYLE = """
QWidget {
    background-color: #F0F4F8;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
    color: #1A202C;
}
#card {
    background-color: #FFFFFF;
    border-radius: 16px;
    border: 1px solid #E2E8F0;
}
QLineEdit, QComboBox {
    background-color: #FFFFFF;
    border: 1.5px solid #CBD5E0;
    border-radius: 7px;
    padding: 0px 12px;
    font-size: 14px;
    min-height: 42px;
    max-height: 42px; /* Forcing absolute height in CSS */
}
QLineEdit:focus, QComboBox:focus {
    border-color: #0D7377;
    background-color: #F0FFFE;
}
QComboBox::drop-down { 
    border: none; 
    padding-right: 10px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #718096;
    margin-right: 10px;
}
QPushButton {
    background-color: #0D7377;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 12px;
    font-weight: 700;
    font-size: 14px;
    min-height: 44px;
}
QPushButton:hover   { background-color: #0A5F63; }
QPushButton:pressed { background-color: #084D50; }
QPushButton:disabled { background-color: #A0AEC0; cursor: not-allowed; }
#btnConfig {
    background-color: transparent;
    color: #718096;
    border: 1px solid #CBD5E0;
    font-size: 12px;
    font-weight: 600;
    min-height: 34px;
    padding: 6px 14px;
}
#btnConfig:hover { 
    background-color: #EDF2F7;
    border-color: #A0AEC0;
}
#statusConnected {
    color: #38A169;
    font-size: 12px;
    font-weight: 600;
}
#statusDisconnected {
    color: #E53E3E;
    font-size: 12px;
    font-weight: 600;
}
#statusChecking {
    color: #718096;
    font-size: 12px;
    font-weight: 600;
}
"""


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.dashboard = None
        self._db_ok = False
        self.setWindowTitle("Ava Serene Hospital")
        
        # Made window slightly taller to guarantee breathing room
        self.setFixedSize(440, 700)
        self.setStyleSheet(STYLE)
        self._build_ui()
        self._try_connect()

    # ── BUILD ──────────────────────────────────────────────────
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(0)

        # ============ CARD ============
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 32, 28, 32)
        card_layout.setSpacing(0)

        # ── Header Section ──
        header_layout = QVBoxLayout()
        header_layout.setSpacing(6)
        
        icon_label = QLabel()
        icon_label.setFixedSize(56, 56)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(
            "background-color: #0D7377; border-radius: 28px; "
            "background-image: url(none);"
        )
        header_layout.addWidget(icon_label, 0, Qt.AlignCenter)

        title = QLabel("Ava Serene Hospital")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #0D7377; background-color: transparent; border: none; padding: 4px 0;")

        sub = QLabel("Staff Portal")
        sub.setFont(QFont("Segoe UI", 12))
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #718096; background-color: transparent; border: none;")

        header_layout.addWidget(title)
        header_layout.addWidget(sub)
        card_layout.addLayout(header_layout)

        # Separator
        card_layout.addSpacing(16)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #E2E8F0; border: none; max-height: 1px;")
        card_layout.addWidget(separator)

        # ── Status Indicator ──
        card_layout.addSpacing(16)
        
        status_container = QHBoxLayout()
        status_container.addStretch()
        
        self.db_status_lbl = QLabel("● Checking database…")
        self.db_status_lbl.setObjectName("statusChecking")
        self.db_status_lbl.setAlignment(Qt.AlignCenter)
        status_container.addWidget(self.db_status_lbl)
        status_container.addStretch()
        
        card_layout.addLayout(status_container)

        # ── Form Section (Completely Refactored) ──
        card_layout.addSpacing(20)
        
        form_layout = QVBoxLayout()
        form_layout.setSpacing(4) # Very tight spacing between label and input
        
        # Helper method for adding fields directly to avoid wrapper issues
        def add_field(label_text, widget):
            lbl = QLabel(label_text)
            # Prevent label from squishing
            lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            lbl.setStyleSheet("color: #4A5568; font-weight: 600; font-size: 12px; background-color: transparent; border: none;")
            
            # Prevent input from squishing
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            form_layout.addWidget(lbl)
            form_layout.addWidget(widget)
            form_layout.addSpacing(12) # Space after the input before the next label

        # Role
        self.role_input = QComboBox()
        self.role_input.addItems(["admin", "worker"])
        add_field("Role", self.role_input)

        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        add_field("Username", self.username_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.handle_login)
        add_field("Password", self.password_input)

        card_layout.addLayout(form_layout)

        # ── Message Label ──
        card_layout.addSpacing(8)
        self.msg_lbl = QLabel("")
        self.msg_lbl.setAlignment(Qt.AlignCenter)
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setStyleSheet(
            "color: #E53E3E; font-size: 12px; background-color: transparent; border: none; "
            "min-height: 20px;"
        )
        card_layout.addWidget(self.msg_lbl)

        # ── Login Button ──
        card_layout.addSpacing(4)
        self.login_btn = QPushButton("Sign In")
        self.login_btn.clicked.connect(self.handle_login)
        card_layout.addWidget(self.login_btn)

        # ── Config Button ──
        card_layout.addSpacing(16)
        config_layout = QHBoxLayout()
        config_layout.addStretch()
        
        cfg_btn = QPushButton("⚙  Database Settings")
        cfg_btn.setObjectName("btnConfig")
        cfg_btn.clicked.connect(self.open_config)
        cfg_btn.setFixedWidth(180)
        
        config_layout.addWidget(cfg_btn)
        config_layout.addStretch()
        
        card_layout.addLayout(config_layout)

        # ADD STRETCH HERE: This pushes everything up so the layout engine 
        # doesn't try to compress your form elements.
        card_layout.addStretch()

        # ── Footer ──
        footer = QLabel("Secure Staff Access")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(
            "color: #A0AEC0; font-size: 11px; background-color: transparent; border: none;"
        )
        card_layout.addWidget(footer)

        # ============ OUTER LAYOUT ============
        outer.addWidget(card, 1)
        outer.addSpacing(8)
        
        # Version label at bottom
        version_lbl = QLabel("v1.0.0")
        version_lbl.setAlignment(Qt.AlignCenter)
        version_lbl.setStyleSheet(
            "color: #CBD5E0; font-size: 10px; background-color: transparent; border: none;"
        )
        outer.addWidget(version_lbl)

    # ── DB STATUS HELPERS ──────────────────────────────────────
    def _set_db_connected(self):
        self._db_ok = True
        self.db_status_lbl.setText("● Connected")
        self.db_status_lbl.setObjectName("statusConnected")
        self.login_btn.setEnabled(True)

    def _set_db_disconnected(self, reason: str = ""):
        self._db_ok = False
        self.db_status_lbl.setText("● Not Connected")
        self.db_status_lbl.setObjectName("statusDisconnected")
        self.login_btn.setEnabled(False)
        if reason:
            self.msg_lbl.setText(reason)

    def _try_connect(self):
        try:
            init_db()
            self._set_db_connected()
            self.msg_lbl.setText("")
        except Exception as e:
            err = str(e)
            self._set_db_disconnected()
            if any(keyword in err.lower() for keyword in ["password", "does not exist", "connection refused", "no password"]):
                self.open_config()
            else:
                self.msg_lbl.setText(f"DB error: {err}")

    # ── CONFIG DIALOG ──────────────────────────────────────────
    def open_config(self):
        ok = show_config_dialog()
        if ok:
            try:
                init_db()
                self._set_db_connected()
                self.msg_lbl.setStyleSheet(
                    "color: #38A169; font-size: 12px; background-color: transparent; border: none;"
                )
                self.msg_lbl.setText("Connected! You can now log in.")
            except Exception as e:
                self._set_db_disconnected(f"Connected but setup failed: {e}")
        else:
            try:
                conn = get_connection()
                conn.close()
                self._set_db_connected()
            except Exception:
                self._set_db_disconnected("Not connected. Click 'Database Settings' to configure.")

    # ── LOGIN ──────────────────────────────────────────────────
    def handle_login(self):
        self.msg_lbl.setStyleSheet(
            "color: #E53E3E; font-size: 12px; background-color: transparent; border: none;"
        )
        self.msg_lbl.setText("")

        if not self._db_ok:
            self.msg_lbl.setText(
                "Not connected to database.\nClick 'Database Settings' to fix this."
            )
            return

        role = self.role_input.currentText()
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self.msg_lbl.setText("Please fill in username and password.")
            return

        # Disable button during login
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Signing in…")

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, password FROM users WHERE username = %s AND role = %s",
                (username, role),
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
        except Exception as e:
            self._set_db_disconnected(f"Database error: {e}")
            self._reset_login_button()
            return

        if not row:
            self.msg_lbl.setText("Invalid username, role, or password.")
            self._reset_login_button()
            return

        user_id, pw_hash = row
        if isinstance(pw_hash, memoryview):
            pw_hash = bytes(pw_hash)

        if not bcrypt.checkpw(password.encode(), pw_hash):
            self.msg_lbl.setText("Invalid username, role, or password.")
            self._reset_login_button()
            return

        update_last_login(username)

        try:
            if role == "admin":
                from admin import AdminDashboard
                self.dashboard = AdminDashboard()
            else:
                from worker import WorkerDashboard
                self.dashboard = WorkerDashboard()
        except Exception as e:
            QMessageBox.critical(
                self, "Startup Error",
                f"Failed to open {role} dashboard:\n\n{e}"
            )
            self._reset_login_button()
            return

        self.dashboard.show()
        self.hide()

    def _reset_login_button(self):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Sign In")


# ── ENTRY POINT ────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LoginWindow()
    win.show()
    sys.exit(app.exec_())