import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
    QLabel, QGroupBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal


class SettingsWidget(QWidget):
    """Settings tab widget."""
    
    save_requested = pyqtSignal()
    install_nim_tool_requested = pyqtSignal()
    install_rust_tool_requested = pyqtSignal()
    install_python_requested = pyqtSignal()
    install_nimble_requested = pyqtSignal()
    install_rust_targets_requested = pyqtSignal()
    install_docker_requested = pyqtSignal()
    
    def __init__(self, script_dir, parent=None):
        super().__init__(parent)
        self.script_dir = script_dir
        self.installer_buttons = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 15, 0, 15)
        
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(9)
        subtitle_font = QFont()
        subtitle_font.setPointSize(9)

        def create_setting_layout(label_text, input_widget, description_text):
            setting_layout = QVBoxLayout()
            label_layout = QHBoxLayout()
            label = QLabel(label_text)
            label.setFont(subtitle_font)
            desc_label = QLabel(description_text)
            desc_label.setFont(QFont("Arial", 8))
            desc_label.setStyleSheet("color: #808080;")
            desc_label.setWordWrap(True)
            setting_layout.setContentsMargins(15, 0, 15, 0)
            label_layout.addWidget(label)
            setting_layout.addLayout(label_layout)
            setting_layout.addWidget(input_widget)
            setting_layout.addWidget(desc_label)
            setting_layout.addSpacing(10)
            return setting_layout

        # Server URL
        server_url_label = QLabel("HTTP Server URL")
        self.server_url_edit = QLineEdit()
        server_url_desc = "The URL of your HTTP C2 server. Example: http://your-server.com:8080"
        server_url_layout = create_setting_layout(server_url_label.text(), self.server_url_edit, server_url_desc)
        layout.addLayout(server_url_layout)

        layout.addSpacing(20)

        # Dependency Installation
        installer_group = QGroupBox("Dependency Installation")
        installer_group.setFont(title_font)
        installer_layout = QVBoxLayout(installer_group)
        installer_layout.setContentsMargins(15, 0, 15, 0)
        
        installer_desc = QLabel("Install the core compilers and their required packages. It is recommended to run these in order.")
        installer_desc.setFont(subtitle_font)
        installer_desc.setWordWrap(True)
        installer_layout.addWidget(installer_desc)

        self.install_nim_tool_btn = QPushButton("Install Nim")
        self.install_nim_tool_btn.clicked.connect(self.install_nim_tool_requested.emit)
        installer_layout.addWidget(self.install_nim_tool_btn)

        self.install_rust_tool_btn = QPushButton("Install Rust")
        self.install_rust_tool_btn.clicked.connect(self.install_rust_tool_requested.emit)
        installer_layout.addWidget(self.install_rust_tool_btn)

        self.install_py_btn = QPushButton("Install Python Packages")
        self.install_py_btn.clicked.connect(self.install_python_requested.emit)
        installer_layout.addWidget(self.install_py_btn)

        self.install_nim_btn = QPushButton("Install Nimble Packages")
        self.install_nim_btn.clicked.connect(self.install_nimble_requested.emit)
        installer_layout.addWidget(self.install_nim_btn)

        openssl_note = QLabel('For Windows, if the Nim build fails with SSL errors, you may need to manually download OpenSSL from <a href="https://openssl-library.org/source/">https://openssl-library.org/source/</a>')
        openssl_note.setOpenExternalLinks(True)
        openssl_note.setFont(QFont("Arial", 8))
        openssl_note.setStyleSheet("color: #808080;")
        openssl_note.setWordWrap(True)
        installer_layout.addWidget(openssl_note)

        self.install_rust_btn = QPushButton("Install Rust Targets")
        self.install_rust_btn.clicked.connect(self.install_rust_targets_requested.emit)
        installer_layout.addWidget(self.install_rust_btn)

        # Docker group
        docker_group = QGroupBox("Obfuscation Dependencies (Optional)")
        docker_group.setFont(title_font)
        docker_layout = QVBoxLayout(docker_group)
        docker_layout.setContentsMargins(0, 0, 0, 0)

        docker_desc = QLabel("The obfuscation feature requires Docker. This will pull the large Obfuscator-LLVM image from the container registry.")
        docker_desc.setFont(subtitle_font)
        docker_desc.setWordWrap(True)
        docker_layout.addWidget(docker_desc)

        self.install_docker_btn = QPushButton("Pull Docker Image")
        self.install_docker_btn.clicked.connect(self.install_docker_requested.emit)
        docker_layout.addWidget(self.install_docker_btn)

        installer_layout.addWidget(docker_group)

        self.installer_buttons = [
            self.install_nim_tool_btn, 
            self.install_rust_tool_btn, 
            self.install_py_btn, 
            self.install_nim_btn, 
            self.install_rust_btn, 
            self.install_docker_btn
        ]

        layout.addWidget(installer_group)
        layout.addStretch()

        # Save button
        save_settings_btn = QPushButton("Save Settings")
        save_settings_btn.setFont(subtitle_font)
        save_settings_btn.clicked.connect(self.save_requested.emit)
        save_btn_container = QWidget()
        save_btn_layout = QHBoxLayout(save_btn_container)
        save_btn_layout.setContentsMargins(15, 0, 15, 0)
        save_btn_layout.addWidget(save_settings_btn)
        layout.addWidget(save_btn_container)

    def set_installer_buttons_enabled(self, enabled):
        for btn in self.installer_buttons:
            btn.setEnabled(enabled)

    def get_settings(self):
        return {
            'server_url': self.server_url_edit.text()
        }

    def load_settings(self, settings):
        self.server_url_edit.setText(settings.get('server_url', 'http://localhost:8080'))
