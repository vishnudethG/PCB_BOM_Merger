from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

def apply_modern_theme(app):
    """
    Applies a modern, flat, professional theme to the entire application.
    """
    app.setStyle("Fusion")

    # --- PALETTE CONFIGURATION ---
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#F4F7F6"))          # Main BG
    palette.setColor(QPalette.WindowText, QColor("#2c3e50"))      # Text
    palette.setColor(QPalette.Base, QColor("#FFFFFF"))            # Input BG
    palette.setColor(QPalette.AlternateBase, QColor("#F9FAFB"))   # Table Alt Rows
    palette.setColor(QPalette.ToolTipBase, QColor("#FFFFFF"))
    palette.setColor(QPalette.ToolTipText, QColor("#2c3e50"))
    palette.setColor(QPalette.Text, QColor("#2c3e50"))
    palette.setColor(QPalette.Button, QColor("#FFFFFF"))
    palette.setColor(QPalette.ButtonText, QColor("#2c3e50"))
    palette.setColor(QPalette.BrightText, QColor("#e74c3c"))
    palette.setColor(QPalette.Link, QColor("#3498db"))
    palette.setColor(QPalette.Highlight, QColor("#BDD7EE"))       # Selection
    palette.setColor(QPalette.HighlightedText, QColor("#2c3e50"))
    app.setPalette(palette)

    # --- GLOBAL STYLESHEET ---
    app.setStyleSheet("""
        /* GLOBAL FONTS */
        QWidget {
            font-family: "Segoe UI", "Roboto", "Helvetica Neue", sans-serif;
            font-size: 14px;
            color: #2c3e50;
        }

        /* BUTTONS */
        QPushButton {
            background-color: #FFFFFF;
            border: 1px solid #dcdcdc;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 600;
            color: #555;
        }
        QPushButton:hover {
            background-color: #f0f4f8;
            border-color: #BDD7EE;
            color: #2c3e50;
        }
        QPushButton:pressed {
            background-color: #BDD7EE;
            border-color: #BDD7EE;
        }
        
        /* PRIMARY ACTION BUTTONS */
        QPushButton[class="primary"] {
            background-color: #27ae60;
            color: white;
            border: none;
        }
        QPushButton[class="primary"]:hover {
            background-color: #2ecc71;
        }

        /* DROP ZONES (NEW) */
        QFrame#DropZone {
            background-color: white;
            border: 2px dashed #bdc3c7;
            border-radius: 15px;
        }
        QFrame#DropZone:hover {
            border: 2px dashed #3498db;
            background-color: #ecf0f1;
        }
        QFrame#DropZone[class="active"] {
            border: 2px solid #27ae60;
            background-color: #f0fff4;
        }

        /* INPUTS & TABLES */
        QLineEdit, QComboBox {
            background-color: white;
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 6px;
        }
        QTableWidget {
            background-color: white;
            gridline-color: #e9ecef;
            border: 1px solid #dee2e6;
        }
        QHeaderView::section {
            background-color: #BDD7EE;
            padding: 8px;
            border: 1px solid #dee2e6;
            font-weight: bold;
            color: #2c3e50;
        }
    """)