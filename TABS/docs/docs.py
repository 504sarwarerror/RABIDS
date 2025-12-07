import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt5.QtGui import QFont


class DocsWidget(QWidget):
    """Documentation tab widget."""
    
    def __init__(self, script_dir, parent=None):
        super().__init__(parent)
        self.script_dir = script_dir
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        subtitle_font = QFont()
        subtitle_font.setPointSize(9)

        self.docs_text = QTextEdit()
        self.docs_text.setFont(subtitle_font)
        self.docs_text.setReadOnly(True)

        doc_path = os.path.join(self.script_dir, "DOC.md")
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                doc_content = f.read()
            self.docs_text.setMarkdown(doc_content)
        except FileNotFoundError:
            self.docs_text.setText("Error: DOC.md not found.")

        self.docs_text.setStyleSheet("background-color: #0e0e0e;")
        layout.addWidget(self.docs_text)
