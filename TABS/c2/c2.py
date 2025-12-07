import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
    QTextEdit, QLabel
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal


class C2Widget(QWidget):
    """C2 (Command and Control) tab widget."""
    
    connect_requested = pyqtSignal()
    send_message_requested = pyqtSignal(str)
    
    def __init__(self, script_dir, parent=None):
        super().__init__(parent)
        self.script_dir = script_dir
        self.init_ui()
        
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(9)
        subtitle_font = QFont()
        subtitle_font.setPointSize(9)

        # Left column - Controls
        left_column_widget = QWidget()
        left_layout = QVBoxLayout(left_column_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        header_layout = QHBoxLayout()
        title = QLabel("COMMAND AND CONTROL")
        title.setFont(title_font)
        header_layout.addWidget(title)
        left_layout.addLayout(header_layout)

        desc = QLabel("Connect to RAT to send commands to and receive output from the 'ghostintheshell' payload.\nCommunication via HTTP Server\nControl victim's device remotely")
        desc.setFont(subtitle_font)
        desc.setStyleSheet("color: #707070;")
        desc.setWordWrap(True)
        left_layout.addWidget(desc)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        left_layout.addWidget(self.connect_btn)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(subtitle_font)
        self.log.setStyleSheet("background-color: #0e0e0e;")
        left_layout.addWidget(self.log)

        input_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Enter command to send...")
        self.cmd_input.returnPressed.connect(self.on_send_clicked)
        self.cmd_input.setEnabled(False)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.on_send_clicked)
        self.send_btn.setEnabled(False)

        input_layout.addWidget(self.cmd_input, 1)
        input_layout.addWidget(self.send_btn)
        left_layout.addLayout(input_layout)

        # Right column - Image
        image_label = QLabel()
        image_path = os.path.join(self.script_dir, "ASSETS", "c2.png")
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            image_label.setPixmap(pixmap.scaled(300, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        image_label.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(left_column_widget, 6)
        main_layout.addWidget(image_label, 4)

    def on_connect_clicked(self):
        self.connect_requested.emit()

    def on_send_clicked(self):
        content = self.cmd_input.text().strip()
        if content:
            self.send_message_requested.emit(content)
            self.cmd_input.clear()

    def log_message(self, message, msg_type="system"):
        color_map = {
            "error": "#808080", 
            "success": "#ffffff", 
            "system": "#a0a0a0", 
            "c2_sent": "#d0d0d0", 
            "c2_recv": "#ffffff", 
            "c2_debug": "#606060"
        }
        color = color_map.get(msg_type, "#c0c0c0")
        self.log.append(f'<font color="{color}">{message}</font>')

    def set_connected(self, is_connected):
        self.cmd_input.setEnabled(is_connected)
        self.send_btn.setEnabled(is_connected)
        self.connect_btn.setText("Disconnect" if is_connected else "Connect")

    def clear_log(self):
        self.log.clear()
