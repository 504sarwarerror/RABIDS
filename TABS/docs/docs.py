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

        # Embedded documentation (previously in DOC.md)
        DOC_CONTENT = """
# RABIDS

RABIDS is a modular framework for building payloads and tooling. This in-application documentation provides installation instructions, usage notes, and brief descriptions of available modules.

## Getting Started

1. Install UI dependencies:

```
pip install PyQt5 discord
```

2. Run the application:

```
python3 main.py
```

## Features

- Modular payload composition
- Cross-platform compilation (Windows/Linux/macOS)
- Optional Docker-based obfuscation
- Integrated C2 and build UI

Refer to the repository README for more details.
"""

        self.docs_text.setMarkdown(DOC_CONTENT)
        self.docs_text.setStyleSheet("background-color: #0e0e0e;")
        layout.addWidget(self.docs_text)
