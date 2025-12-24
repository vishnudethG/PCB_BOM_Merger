import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QTableWidget, QTableWidgetItem, 
                             QGroupBox, QRadioButton, QHeaderView, QMessageBox)
from PyQt5.QtCore import pyqtSignal, Qt

# --- UPDATE IMPORTS TO USE NEW LOADERS ---
from src.core.file_loader import load_bom_file, load_xy_file 

class ImportScreen(QWidget):
    next_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.bom_df = None
        self.xy_df = None
        self.selected_delimiter = ',' 
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- TOP CONTROLS ---
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
        xy_group = QGroupBox("2. Pick & Place (XY)")
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

        # --- DATA PREVIEW ---
        self.table_preview = QTableWidget()
        self.table_preview.setColumnCount(0)
        self.table_preview.setRowCount(0)
        layout.addWidget(QLabel("Data Preview (First 50 rows of last loaded file):"))
        layout.addWidget(self.table_preview)

        # --- BOTTOM BAR ---
        bottom_bar = QHBoxLayout()
        
        # Delimiter Options
        self.del_group = QGroupBox("Ref Des Delimiter")
        del_layout = QHBoxLayout()
        self.rb_comma = QRadioButton("Comma (,)")
        self.rb_semi = QRadioButton("Semi-colon (;)")
        self.rb_space = QRadioButton("Space ( )")
        self.rb_comma.setChecked(True) 
        del_layout.addWidget(self.rb_comma)
        del_layout.addWidget(self.rb_semi)
        del_layout.addWidget(self.rb_space)
        self.del_group.setLayout(del_layout)
        
        bottom_bar.addWidget(self.del_group)
        bottom_bar.addStretch()
        
        self.btn_next = QPushButton("Next: Map Columns >>")
        self.btn_next.setEnabled(False)
        self.btn_next.clicked.connect(self.process_and_continue)
        bottom_bar.addWidget(self.btn_next)

        layout.addLayout(bottom_bar)
        self.setLayout(layout)

    def load_bom(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open BOM", "", "Excel/CSV (*.xlsx *.xls *.csv *.txt)")
        if path:
            self.lbl_bom_path.setText(os.path.basename(path))
            try:
                # USE NEW BOM LOADER
                self.bom_df = load_bom_file(path)
                self.populate_table(self.bom_df)
                self.check_ready()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load BOM:\n{str(e)}")

    def load_xy(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open XY", "", "Text/CSV/Excel (*.txt *.csv *.xlsx *.xls)")
        if path:
            self.lbl_xy_path.setText(os.path.basename(path))
            try:
                # USE NEW XY LOADER
                self.xy_df = load_xy_file(path)
                self.populate_table(self.xy_df)
                self.check_ready()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load XY:\n{str(e)}")

    def populate_table(self, df):
        self.table_preview.clear()
        if df is None: return
        
        self.table_preview.setRowCount(min(50, len(df)))
        self.table_preview.setColumnCount(len(df.columns))
        self.table_preview.setHorizontalHeaderLabels(df.columns.astype(str))

        for r in range(self.table_preview.rowCount()):
            for c in range(self.table_preview.columnCount()):
                item_text = str(df.iloc[r, c])
                self.table_preview.setItem(r, c, QTableWidgetItem(item_text))
        
        self.table_preview.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def check_ready(self):
        if self.bom_df is not None and self.xy_df is not None:
            self.btn_next.setEnabled(True)

    def process_and_continue(self):
        delimiter = ','
        if self.rb_semi.isChecked(): delimiter = ';'
        if self.rb_space.isChecked(): delimiter = ' '
        self.selected_delimiter = delimiter
        self.next_clicked.emit()