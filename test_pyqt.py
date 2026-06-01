import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Window")
        self.setGeometry(300, 200, 300, 200)
        label = QLabel("If you see this, PyQt5 works!")
        layout = QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())