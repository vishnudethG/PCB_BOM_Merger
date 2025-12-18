# src/ui/screens/screen_dashboard.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QLabel, QPushButton, QTabWidget, 
                             QHeaderView, QMessageBox, QLineEdit, QGroupBox) # Added QLineEdit, QGroupBox
from PyQt5.QtCore import Qt, pyqtSignal

class DashboardScreen(QWidget):
    back_clicked = pyqtSignal()
    export_clicked = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.master_df = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # --- 1. TOP SUMMARY BAR ---
        summary_layout = QHBoxLayout()
        self.lbl_matched = self._create_stat_box("Matched", "0", "#D4EDDA", "#155724")
        self.lbl_xy_err = self._create_stat_box("XY Errors", "0", "#F8D7DA", "#721C24")
        self.lbl_bom_warn = self._create_stat_box("BOM Warnings", "0", "#FFF3CD", "#856404")
        
        summary_layout.addWidget(self.lbl_matched)
        summary_layout.addWidget(self.lbl_xy_err)
        summary_layout.addWidget(self.lbl_bom_warn)
        layout.addLayout(summary_layout)

        # --- 2. BULK ACTIONS BAR (NEW) ---
        action_group = QGroupBox("Bulk Actions")
        action_layout = QHBoxLayout()
        
        action_layout.addWidget(QLabel("Filter Ref Des (e.g. 'TP*', 'FID*'):"))
        
        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("TP*, MH*")
        action_layout.addWidget(self.txt_filter)
        
        self.btn_bulk_ignore = QPushButton("Ignore All Matches")
        self.btn_bulk_ignore.setStyleSheet("background-color: #6c757d; color: white; font-weight: bold;")
        self.btn_bulk_ignore.clicked.connect(self.perform_bulk_ignore)
        action_layout.addWidget(self.btn_bulk_ignore)
        
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)

        # --- 3. TABS ---
        self.tabs = QTabWidget()
        
        # Tab 1: XY Errors
        self.tab_xy = QWidget()
        self.table_xy = self._create_table(["Ref Des", "Layer", "X", "Y", "Action"])
        xy_layout = QVBoxLayout(self.tab_xy)
        xy_layout.addWidget(self.table_xy)
        self.tabs.addTab(self.tab_xy, "XY Errors (Missing Parts)")
        
        # Tab 2: BOM Warnings
        self.tab_bom = QWidget()
        self.table_bom = self._create_table(["Ref Des", "Part Number", "Description", "Action"])
        bom_layout = QVBoxLayout(self.tab_bom)
        bom_layout.addWidget(self.table_bom)
        self.tabs.addTab(self.tab_bom, "BOM Only (No Location)")

        # Tab 3: Matched
        self.tab_match = QWidget()
        self.table_match = self._create_table(["Ref Des", "Layer", "X", "Y", "Part Number", "Rotation"])
        match_layout = QVBoxLayout(self.tab_match)
        match_layout.addWidget(self.table_match)
        self.tabs.addTab(self.tab_match, "Matched Data")

        layout.addWidget(self.tabs)

        # --- 4. BOTTOM BAR ---
        nav_layout = QHBoxLayout()
        btn_back = QPushButton("<< Back")
        btn_back.clicked.connect(self.back_clicked.emit)
        
        self.btn_export = QPushButton("GENERATE EXCEL >>")
        self.btn_export.setStyleSheet("font-weight: bold; padding: 10px; font-size: 14px;")
        self.btn_export.clicked.connect(self.on_export)
        
        nav_layout.addWidget(btn_back)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_export)
        
        layout.addLayout(nav_layout)
        self.setLayout(layout)

    # ... _create_stat_box and _create_table methods stay the same ...
    def _create_stat_box(self, title, count, bg_color, text_color):
        lbl = QLabel(f"{title}: {count}")
        lbl.setStyleSheet(f"background-color: {bg_color}; color: {text_color}; border: 1px solid {text_color}; padding: 10px; font-weight: bold; border-radius: 4px;")
        lbl.setAlignment(Qt.AlignCenter)
        return lbl

    def _create_table(self, columns):
        table = QTableWidget()
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        return table
    
    def set_data(self, df):
        self.master_df = df
        self.refresh_views()

    def refresh_views(self):
        if self.master_df is None: return

        matched = self.master_df[self.master_df["Status"] == "MATCHED"]
        xy_err = self.master_df[(self.master_df["Status"] == "XY_ONLY") & (self.master_df["Is Ignored"] == False)]
        bom_warn = self.master_df[self.master_df["Status"] == "BOM_ONLY"]
        
        self.lbl_matched.setText(f"Matched: {len(matched)}")
        self.lbl_xy_err.setText(f"XY Errors: {len(xy_err)}")
        self.lbl_bom_warn.setText(f"BOM Warnings: {len(bom_warn)}")

        if len(xy_err) > 0:
            self.btn_export.setEnabled(False)
            self.btn_export.setText(f"Fix {len(xy_err)} Critical Errors to Export")
        else:
            self.btn_export.setEnabled(True)
            self.btn_export.setText("GENERATE EXCEL >>")

        self._populate_xy_table(xy_err)
        self._populate_bom_table(bom_warn)
        self._populate_match_table(matched)

    def perform_bulk_ignore(self):
        """Ignores all items matching the filter text."""
        pattern = self.txt_filter.text().strip().upper()
        if not pattern:
            return

        # Convert simple wildcard "TP*" to regex if needed, or just use 'startswith' logic
        # For user simplicity, let's assume standard 'starts with' if * is at end
        clean_prefix = pattern.replace("*", "")
        
        # Count how many we are about to ignore
        mask = (self.master_df["Status"] == "XY_ONLY") & \
               (self.master_df["Is Ignored"] == False) & \
               (self.master_df["Ref Des"].astype(str).str.startswith(clean_prefix))
        
        count = mask.sum()
        
        if count == 0:
            QMessageBox.information(self, "No Matches", f"No active errors start with '{clean_prefix}'")
            return

        # Confirm Action
        reply = QMessageBox.question(self, "Confirm Bulk Ignore", 
                                     f"Are you sure you want to ignore {count} items starting with '{clean_prefix}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Apply Ignore
            self.master_df.loc[mask, "Is Ignored"] = True
            self.refresh_views()
            QMessageBox.information(self, "Done", f"Ignored {count} items.")
            self.txt_filter.clear()

    # ... Helper population methods (_populate_xy_table, etc) stay the same ...
    def _populate_xy_table(self, df):
        self.table_xy.setRowCount(len(df))
        # Performance: Limit display to 100 rows if massive
        display_df = df.head(100)
        self.table_xy.setRowCount(len(display_df))
        
        for r, (idx, row) in enumerate(display_df.iterrows()):
            self.table_xy.setItem(r, 0, QTableWidgetItem(str(row["Ref Des"])))
            self.table_xy.setItem(r, 1, QTableWidgetItem(str(row["Layer"])))
            self.table_xy.setItem(r, 2, QTableWidgetItem(str(row["Mid X"])))
            self.table_xy.setItem(r, 3, QTableWidgetItem(str(row["Mid Y"])))
            
            btn_ignore = QPushButton("Ignore")
            btn_ignore.clicked.connect(lambda _, x=idx: self.mark_ignore(x))
            self.table_xy.setCellWidget(r, 4, btn_ignore)

    def _populate_bom_table(self, df):
        self.table_bom.setRowCount(len(df))
        for r, (idx, row) in enumerate(df.iterrows()):
            self.table_bom.setItem(r, 0, QTableWidgetItem(str(row["Ref Des"])))
            self.table_bom.setItem(r, 1, QTableWidgetItem(str(row["Part Number"])))
            self.table_bom.setItem(r, 2, QTableWidgetItem(str(row["Description"])))

    def _populate_match_table(self, df):
        self.table_match.setRowCount(len(df))
        limit_df = df.head(100) 
        self.table_match.setRowCount(len(limit_df))
        for r, (idx, row) in enumerate(limit_df.iterrows()):
            self.table_match.setItem(r, 0, QTableWidgetItem(str(row["Ref Des"])))
            self.table_match.setItem(r, 1, QTableWidgetItem(str(row["Layer"])))
            self.table_match.setItem(r, 2, QTableWidgetItem(str(row["Mid X"])))
            self.table_match.setItem(r, 3, QTableWidgetItem(str(row["Mid Y"])))
            self.table_match.setItem(r, 4, QTableWidgetItem(str(row["Part Number"])))
            self.table_match.setItem(r, 5, QTableWidgetItem(str(row["Rotation"])))

    def mark_ignore(self, index):
        self.master_df.at[index, "Is Ignored"] = True
        self.refresh_views()

    def on_export(self):
        self.export_clicked.emit(self.master_df)