from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGraphicsDropShadowEffect, QGridLayout)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QCursor

class Card(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title, description, icon_text, is_disabled=False):
        super().__init__()
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.is_disabled = is_disabled
        
        # Style
        bg_color = "#f8f9fa" if is_disabled else "white"
        border_color = "#e9ecef"
        text_color = "#6c757d" if is_disabled else "#2c3e50"
        hover_border = "#3498db" if not is_disabled else border_color
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 15px;
            }}
            QFrame:hover {{
                border-color: {hover_border};
                background-color: #fcfcfc;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        # Icon (Using Text as placeholder for FontAwesome)
        lbl_icon = QLabel(icon_text)
        lbl_icon.setStyleSheet(f"font-size: 50px; border: none; color: {text_color}; background: transparent;")
        lbl_icon.setAlignment(Qt.AlignCenter)
        
        # Title
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 22px; font-weight: bold; border: none; color: {text_color}; margin-top: 15px; background: transparent;")
        lbl_title.setAlignment(Qt.AlignCenter)
        
        # Desc
        lbl_desc = QLabel(description)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(f"font-size: 14px; border: none; color: #7f8c8d; margin-top: 5px; background: transparent;")
        lbl_desc.setAlignment(Qt.AlignCenter)

        layout.addWidget(lbl_icon)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        self.setLayout(layout)

        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(Qt.lightGray)
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)

    def mousePressEvent(self, event):
        if not self.is_disabled:
            self.clicked.emit()

class HomeScreen(QWidget):
    segregation_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Header
        header_layout = QVBoxLayout()
        title = QLabel("Welcome to PCB BOM Merger")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #2c3e50; margin-bottom: 5px;")
        title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("Select a workflow to begin")
        subtitle.setStyleSheet("font-size: 18px; color: #7f8c8d; margin-bottom: 40px;")
        subtitle.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)

        # Grid for Cards
        grid = QHBoxLayout()
        grid.setSpacing(40)
        
        # Card 1: BOM Segregation
        self.card_seg = Card(
            "BOM Segregation", 
            "Merge BOM & XY Data. Generate Top/Bottom BOMs and Exceptions Report.",
            "⛭" # Gear Unicode Icon
        )
        self.card_seg.setFixedWidth(350)
        self.card_seg.setFixedHeight(250)
        self.card_seg.clicked.connect(self.segregation_clicked.emit)
        
        # Card 2: Kit List (Disabled)
        self.card_kit = Card(
            "Internal BOM & Kit List", 
            "Generate Store BOMs and Kitting Lists for procurement.\n(Coming Soon)",
            "📋", # Clipboard Unicode Icon
            is_disabled=True
        )
        self.card_kit.setFixedWidth(350)
        self.card_kit.setFixedHeight(250)

        grid.addStretch()
        grid.addWidget(self.card_seg)
        grid.addWidget(self.card_kit)
        grid.addStretch()
        
        main_layout.addLayout(grid)
        self.setLayout(main_layout)