# src/ui/screens/screen_import.py
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QTableWidget, QTableWidgetItem, 
                             QGroupBox, QRadioButton, QHeaderView, QMessageBox)
from PyQt5.QtCore import pyqtSignal, Qt

# IMPORT YOUR BACKEND LOGIC
from src.core.file_loader import load_and_clean_file

class ImportScreen(QWidget):
    # Custom Signal to tell MainWindow "We are done here"
    next_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.bom_df = None   # To store loaded BOM data
        self.xy_df = None    # To store loaded XY data
        self.selected_delimiter = ',' # Default delimiter
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- SECTION 1: TOP CONTROLS (File Selection) ---
        top_controls = QHBoxLayout()
        
        # BOM Group
        bom_group = QGroupBox("1. Bill of Materials (BOM)")
        bom_layout = QVBoxLayout()
        self.lbl_bom_path = QLabel("No file selected")
        btn_load_bom = QPushButton("Select BOM File...")
        btn_load_bom.clicked.connect(self.load_bom)
        bom_layout.addWidget(btn_load_bom)
        bom_layout.addWidget(self.lbl_bom_path)
        bom_group.setLayout(bom_layout)

        # XY Group
        xy_group = QGroupBox("2. Centroid / Pick & Place (XY)")
        xy_layout = QVBoxLayout()
        self.lbl_xy_path = QLabel("No file selected")
        btn_load_xy = QPushButton("Select XY File...")
        btn_load_xy.clicked.connect(self.load_xy)
        xy_layout.addWidget(btn_load_xy)
        xy_layout.addWidget(self.lbl_xy_path)
        xy_group.setLayout(xy_layout)

        top_controls.addWidget(bom_group)
        top_controls.addWidget(xy_group)
        layout.addLayout(top_controls)

        # --- SECTION 2: DATA PREVIEW ---
        self.table_preview = QTableWidget()
        self.table_preview.setColumnCount(0)
        self.table_preview.setRowCount(0)
        layout.addWidget(QLabel("Data Preview (First 50 rows):"))
        layout.addWidget(self.table_preview)

        # --- SECTION 3: OPTIONS & NAVIGATION ---
        bottom_bar = QHBoxLayout()
        
        # Delimiter Options
        self.del_group = QGroupBox("Ref Des Delimiter")
        del_layout = QHBoxLayout()
        self.rb_comma = QRadioButton("Comma (,)")
        self.rb_semi = QRadioButton("Semi-colon (;)")
        self.rb_space = QRadioButton("Space ( )")
        self.rb_comma.setChecked(True) # Default
        del_layout.addWidget(self.rb_comma)
        del_layout.addWidget(self.rb_semi)
        del_layout.addWidget(self.rb_space)
        self.del_group.setLayout(del_layout)
        
        bottom_bar.addWidget(self.del_group)
        bottom_bar.addStretch()
        
        self.btn_next = QPushButton("Process & Next >>")
        self.btn_next.setEnabled(False) # Disabled until files are loaded
        # THIS WAS THE MISSING METHOD IN YOUR ERROR
        self.btn_next.clicked.connect(self.process_and_continue)
        bottom_bar.addWidget(self.btn_next)

        layout.addLayout(bottom_bar)
        self.setLayout(layout)

    def load_bom(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open BOM", "", "Excel Files (*.xlsx *.xls *.csv)")
        if path:
            self.lbl_bom_path.setText(os.path.basename(path))
            try:
                # CALLING YOUR BACKEND LOGIC
                self.bom_df = load_and_clean_file(path)
                self.populate_table(self.bom_df)
                self.check_ready()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load BOM:\n{str(e)}")

    def load_xy(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open XY", "", "Text/Excel (*.txt *.csv *.xlsx)")
        if path:
            self.lbl_xy_path.setText(os.path.basename(path))
            try:
                # CALLING YOUR BACKEND LOGIC
                self.xy_df = load_and_clean_file(path)
                # Note: We usually preview BOM, but you could preview XY if you want
                self.check_ready()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load XY:\n{str(e)}")

    def populate_table(self, df):
        """Displays the Pandas DataFrame in the QTableWidget."""
        self.table_preview.clear()
        self.table_preview.setRowCount(min(50, len(df))) # Show max 50 rows
        self.table_preview.setColumnCount(len(df.columns))
        self.table_preview.setHorizontalHeaderLabels(df.columns.astype(str))

        for r in range(self.table_preview.rowCount()):
            for c in range(self.table_preview.columnCount()):
                item_text = str(df.iloc[r, c])
                self.table_preview.setItem(r, c, QTableWidgetItem(item_text))
        
        self.table_preview.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def check_ready(self):
        """Enable 'Next' button only if both files are loaded."""
        if self.bom_df is not None and self.xy_df is not None:
            self.btn_next.setEnabled(True)

    def process_and_continue(self):
        """
        Gathers settings and moves to the Mapping Screen.
        We do NOT normalize here anymore; we pass the raw data and let Logic Engine do it properly.
        """
        # 1. Determine Delimiter
        delimiter = ','
        if self.rb_semi.isChecked(): delimiter = ';'
        if self.rb_space.isChecked(): delimiter = ' '
        
        # Save it to instance so MainWindow can grab it
        self.selected_delimiter = delimiter

        # 2. Prepare Data for Handoff (Pass RAW data)
        self.clean_bom_df = self.bom_df 

        # 3. Emit Signal
        self.next_clicked.emit()