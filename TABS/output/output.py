import os
import sys
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, 
    QLabel, QListWidget, QListWidgetItem
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal


class OutputWidget(QWidget):
    """Output tab widget for displaying build logs and loot files."""
    
    def __init__(self, script_dir, parent=None):
        super().__init__(parent)
        self.script_dir = script_dir
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(9)
        subtitle_font = QFont()
        subtitle_font.setPointSize(9)

        # Output log
        self.output_log = QTextEdit()
        self.output_log.setFont(subtitle_font)
        self.output_log.setReadOnly(True)
        self.output_log.setPlaceholderText("")
        self.output_log.setStyleSheet("background-color: #0e0e0e; color: #909090;")
        layout.addWidget(self.output_log, 3)

        # Loot section
        loot_section_layout = QHBoxLayout()

        folder_icon_label = QLabel()
        folder_icon_path = os.path.join(self.script_dir, "ASSETS", "folder.png")
        pixmap = QPixmap(folder_icon_path)
        if not pixmap.isNull():
            folder_icon_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        folder_icon_label.setAlignment(Qt.AlignCenter)
        loot_section_layout.addWidget(folder_icon_label, 2)

        loot_content_widget = QWidget()
        loot_content_layout = QVBoxLayout(loot_content_widget)
        loot_content_layout.setContentsMargins(0, 0, 0, 0)

        loot_header_layout = QHBoxLayout()
        loot_label = QLabel("LOOT")
        loot_label.setFont(title_font)
        loot_header_layout.addWidget(loot_label)
        loot_header_layout.addStretch()
        
        refresh_loot_btn = QPushButton("⟳ Refresh")
        refresh_loot_btn.clicked.connect(self.update_loot_folder_view)
        loot_header_layout.addWidget(refresh_loot_btn)
        
        open_loot_btn = QPushButton("Open Folder")
        open_loot_btn.clicked.connect(self.open_loot_folder)
        loot_header_layout.addWidget(open_loot_btn)
        loot_content_layout.addLayout(loot_header_layout)

        self.loot_files_list = QListWidget()
        self.loot_files_list.setFont(subtitle_font)
        self.loot_files_list.setStyleSheet("background-color: #0e0e0e;")
        loot_content_layout.addWidget(self.loot_files_list)

        loot_section_layout.addWidget(loot_content_widget, 8)
        layout.addLayout(loot_section_layout, 1)
        
        self.update_loot_folder_view()

    def log_message(self, message, msg_type="system"):
        if msg_type == "error":
            color = "#808080"
        elif msg_type == "success":
            color = "#ffffff"
        elif msg_type == "system":
            color = "#a0a0a0"
        else:
            color = "#c0c0c0"
        
        if msg_type == "c2_sent":
            color = "#d0d0d0"
        elif msg_type == "c2_recv":
            color = "#ffffff"

        if not message.strip():
            return

        self.output_log.append(f'<font color="{color}">{message}</font>')

    def clear_log(self):
        self.output_log.clear()

    def open_loot_folder(self):
        loot_dir = Path(self.script_dir) / 'LOOT'
        if not loot_dir.is_dir():
            self.log_message(f"loot directory not found: {loot_dir}", "error")
            loot_dir.mkdir(exist_ok=True)
            self.log_message(f"created loot directory: {loot_dir}", "system")

        if sys.platform == "win32":
            os.startfile(loot_dir)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(loot_dir)])
        else:
            subprocess.Popen(["xdg-open", str(loot_dir)])
        self.update_loot_folder_view()

    def update_loot_folder_view(self):
        self.loot_files_list.clear()
        loot_dir = Path(self.script_dir) / 'LOOT'
        if not loot_dir.is_dir():
            self.loot_files_list.addItem("loot directory not found")
            return
        try:
            files = [f for f in loot_dir.iterdir() if f.is_file()]
            if not files:
                self.loot_files_list.addItem("loot directory is empty")
                return

            for file_path in sorted(files, key=os.path.getmtime, reverse=True):
                self.loot_files_list.addItem(QListWidgetItem(file_path.name))
        except Exception as e:
            self.loot_files_list.addItem(f"Error reading LOOT directory: {e}")
