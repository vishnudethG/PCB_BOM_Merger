from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox)
from PyQt5.QtCore import pyqtSignal, Qt

class DashboardScreen(QWidget):
    back_clicked = pyqtSignal()
    export_clicked = pyqtSignal(object) # Carries the dataframe

    def __init__(self):
        super().__init__()
        self.df = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # --- TITLE ---
        lbl_title = QLabel("Step 3: Processing Complete")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60;")
        layout.addWidget(lbl_title)

        # --- STATS ROW ---
        stats_layout = QHBoxLayout()
        
        self.card_total = self._create_stat_card("Total Rows", "0")
        self.card_matched = self._create_stat_card("Matched", "0", "#27ae60")
        self.card_xy_only = self._create_stat_card("XY Only (DNP)", "0", "#f39c12")
        self.card_bom_only = self._create_stat_card("BOM Only (Missing)", "0", "#c0392b")
        
        stats_layout.addWidget(self.card_total)
        stats_layout.addWidget(self.card_matched)
        stats_layout.addWidget(self.card_xy_only)
        stats_layout.addWidget(self.card_bom_only)
        layout.addLayout(stats_layout)

        # --- PREVIEW TABLE ---
        self.table = QTableWidget()
        layout.addWidget(QLabel("Preview Data (First 100 Rows):"))
        layout.addWidget(self.table)

        # --- BOTTOM BAR ---
        btn_layout = QHBoxLayout()
        btn_back = QPushButton("<< Adjust Mapping")
        btn_back.clicked.connect(self.back_clicked.emit)
        
        self.btn_export = QPushButton("Generate Excel Files >>")
        self.btn_export.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; padding: 10px;")
        self.btn_export.clicked.connect(lambda: self.export_clicked.emit(self.df))
        
        btn_layout.addWidget(btn_back)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_export)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _create_stat_card(self, title, value, color="#333"):
        group = QGroupBox()
        layout = QVBoxLayout()
        lbl_val = QLabel(value)
        lbl_val.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        lbl_val.setAlignment(Qt.AlignCenter)
        
        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(lbl_val)
        layout.addWidget(lbl_title)
        group.setLayout(layout)
        return group

    def set_data(self, df):
        self.df = df
        
        # 1. Update Stats
        total = len(df)
        matched = len(df[df['Status'] == 'MATCHED'])
        xy_only = len(df[df['Status'] == 'XY_ONLY'])
        bom_only = len(df[df['Status'] == 'BOM_ONLY'])
        
        self.card_total.findChild(QLabel).setText(str(total)) # First label is value due to layout order? No, tricky.
        # Safer way to update text:
        self._update_card_value(self.card_total, total)
        self._update_card_value(self.card_matched, matched)
        self._update_card_value(self.card_xy_only, xy_only)
        self._update_card_value(self.card_bom_only, bom_only)

        # 2. Populate Table
        # Columns to show: Ref Des, Status, Layer, Ref X, Ref Y, Part Number
        cols_to_show = ["Ref Des", "Status", "Layer", "Ref X", "Ref Y", "Part number"]
        # Handle case where column might be missing (e.g. if logic engine failed partially)
        safe_cols = [c for c in cols_to_show if c in df.columns]
        
        self.table.clear()
        self.table.setColumnCount(len(safe_cols))
        self.table.setRowCount(min(100, len(df)))
        self.table.setHorizontalHeaderLabels(safe_cols)
        
        for r in range(self.table.rowCount()):
            for c, col_name in enumerate(safe_cols):
                val = str(df.iloc[r][col_name])
                self.table.setItem(r, c, QTableWidgetItem(val))
                
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def _update_card_value(self, group_box, value):
        # The first label added to the layout is the Value label
        layout = group_box.layout()
        if layout.count() > 0:
            layout.itemAt(0).widget().setText(str(value))