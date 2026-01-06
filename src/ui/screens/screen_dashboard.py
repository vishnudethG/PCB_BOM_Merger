from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QLabel, QPushButton, QHeaderView, 
                             QTabWidget, QAbstractItemView, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import pandas as pd

class DashboardScreen(QWidget):
    back_clicked = pyqtSignal()
    export_clicked = pyqtSignal(object) 

    def __init__(self):
        super().__init__()
        self.full_df = pd.DataFrame()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        title_lbl = QLabel("Production Dashboard")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        
        self.lbl_subtitle = QLabel("Preview of final output. 'Exceptions' can be edited.")
        self.lbl_subtitle.setStyleSheet("color: #7f8c8d; font-style: italic;")
        
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_subtitle)
        layout.addLayout(header_layout)

        # --- TABS ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #bdc3c7; top: -1px; }
            QTabBar::tab {
                background: #ecf0f1;
                border: 1px solid #bdc3c7;
                padding: 8px 15px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
                color: #7f8c8d;
            }
            QTabBar::tab:selected {
                background: #BDD7EE; 
                border-bottom-color: #BDD7EE;
                color: #2c3e50;
            }
        """)

        # Define Tabs
        self.tables = {}
        tab_defs = [
            ("Internal BOM", "Internal BOM (Grouped)"),
            ("XY Data", "Master XY Data"),
            ("BOM Top", "Top Assembly (Grouped)"),
            ("BOM Bottom", "Bottom Assembly (Grouped)"),
            ("XY Top", "Top XY (Placement)"),
            ("XY Bottom", "Bottom XY (Placement)"),
            ("Exceptions", "Exceptions Report")
        ]

        for key, title in tab_defs:
            tab = QWidget()
            t_layout = QVBoxLayout(tab)
            t_layout.setContentsMargins(5,5,5,5)
            
            # Create Table (Exceptions is Editable)
            is_editable = (key == "Exceptions")
            table = self._create_table(editable=is_editable)
            
            if is_editable:
                table.itemChanged.connect(self.handle_exception_edit)
            
            self.tables[key] = table
            t_layout.addWidget(table)
            self.tabs.addTab(tab, title)

        layout.addWidget(self.tabs)

        # --- FOOTER ---
        footer = QHBoxLayout()
        
        btn_back = QPushButton("<< Adjust Mapping")
        btn_back.setFixedWidth(150)
        btn_back.clicked.connect(self.back_clicked.emit)
        
        self.btn_refresh = QPushButton("Reprocess Changes")
        self.btn_refresh.setFixedWidth(160)
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.setStyleSheet("color: #d35400; border: 1px solid #d35400;")
        self.btn_refresh.clicked.connect(self.reprocess_data)
        
        btn_export = QPushButton("Export to Excel >>")
        btn_export.setFixedWidth(200)
        btn_export.setProperty("class", "primary")
        btn_export.clicked.connect(self.finalize_export)
        
        footer.addWidget(btn_back)
        footer.addStretch()
        footer.addWidget(self.btn_refresh)
        footer.addStretch()
        footer.addWidget(btn_export)
        
        layout.addLayout(footer)
        self.setLayout(layout)

    def _create_table(self, editable=False):
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        
        font = QFont()
        font.setPointSize(10)
        table.setFont(font)
        
        header = table.horizontalHeader()
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #BDD7EE;
                color: black;
                font-weight: bold;
                border: 1px solid #bdc3c7;
                padding: 4px;
                height: 35px;
            }
        """)
        header.setStretchLastSection(True)

        if not editable:
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        else:
            table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
            
        return table

    def set_data(self, df):
        self.full_df = df.copy()
        
        if "_id" not in self.full_df.columns:
            self.full_df["_id"] = range(len(self.full_df))

        # Ensure Remarks column exists for editing
        if "Remarks" not in self.full_df.columns:
            self.full_df["Remarks"] = ""
            
        # Classify Layers
        if 'Layer' in self.full_df.columns:
            self.full_df['Layer_Classified'] = self.full_df['Layer'].apply(self._classify_layer)
        else:
            self.full_df['Layer_Classified'] = "Unknown"

        self.refresh_views()

    def _classify_layer(self, val):
        s = str(val).strip().lower()
        if s in ['b', 'bottom', 'bot', 'bottomlayer', 'bottom layer', 'back', 'solder']: return 'Bottom'
        if s in ['t', 'top', 'toplayer', 'top layer', 'front', 'component']: return 'Top'
        return 'Unknown'

    def _group_bom_data(self, df):
        if df.empty: return df
        
        fill_cols = ['Part Number', 'Description']
        for c in fill_cols:
            if c in df.columns: df[c] = df[c].fillna('')

        valid_group_cols = [c for c in fill_cols if c in df.columns]
        if not valid_group_cols: return df

        agg_rules = {}
        if 'Location' in df.columns: agg_rules['Location'] = lambda x: ', '.join(sorted(x.astype(str)))
        elif 'Ref Des' in df.columns: agg_rules['Ref Des'] = lambda x: ', '.join(sorted(x.astype(str)))
        else: agg_rules['Designator'] = lambda x: ', '.join(sorted(x.astype(str)))

        if 'BOM_Order' in df.columns: agg_rules['BOM_Order'] = 'min'

        grouped = df.groupby(valid_group_cols).agg(agg_rules).reset_index()
        
        for potential in ['Ref Des', 'Designator']:
            if potential in grouped.columns:
                grouped.rename(columns={potential: 'Location'}, inplace=True)

        if 'Location' in grouped.columns:
            grouped['Quantity'] = grouped['Location'].apply(lambda x: len(str(x).split(',')))
        
        return grouped

    def refresh_views(self):
        df = self.full_df
        df_top_all = df[df['Layer_Classified'] == 'Top'].copy()
        df_bot_all = df[df['Layer_Classified'] == 'Bottom'].copy()

        # 1. Internal BOM
        df_internal = df[df['Status'] != 'XY_ONLY'].copy()
        df_int_grp = self._group_bom_data(df_internal)
        self._fill_table("Internal BOM", df_int_grp, ['Part Number', 'Description', 'Location', 'Quantity'])

        # 2. XY Data
        df_xy = df[df['Status'] != 'BOM_ONLY'].copy()
        disp_xy = df_xy.rename(columns={'Ref Des': 'Location', 'Ref X': 'X', 'Ref Y': 'Y'})
        self._fill_table("XY Data", disp_xy, ['X', 'Y', 'Location', 'Rotation', 'Layer'])

        # 3. BOM Top
        df_btop = df_top_all[df_top_all['Status'] != 'XY_ONLY'].copy()
        df_btop_grp = self._group_bom_data(df_btop)
        df_btop_grp['Layer'] = "TopLayer"
        self._fill_table("BOM Top", df_btop_grp, ['Sl No.', 'Part Number', 'Description', 'Location', 'Quantity', 'Layer'], add_sl=True)

        # 4. BOM Bottom
        df_bbot = df_bot_all[df_bot_all['Status'] != 'XY_ONLY'].copy()
        df_bbot_grp = self._group_bom_data(df_bbot)
        df_bbot_grp['Layer'] = "BottomLayer"
        self._fill_table("BOM Bottom", df_bbot_grp, ['Sl No.', 'Part Number', 'Description', 'Location', 'Quantity', 'Layer'], add_sl=True)

        # 5. XY Top
        df_xyt = df_top_all[df_top_all['Status'] != 'BOM_ONLY'].copy()
        df_xyt['Layer'] = "TopLayer"
        disp_xyt = df_xyt.rename(columns={'Ref Des': 'Location', 'Ref X': 'X', 'Ref Y': 'Y'})
        self._fill_table("XY Top", disp_xyt, ['Sl No.', 'Part Number', 'Location', 'X', 'Y', 'Rotation', 'Description', 'Layer'], add_sl=True)

        # 6. XY Bottom
        df_xyb = df_bot_all[df_bot_all['Status'] != 'BOM_ONLY'].copy()
        df_xyb['Layer'] = "BottomLayer"
        disp_xyb = df_xyb.rename(columns={'Ref Des': 'Location', 'Ref X': 'X', 'Ref Y': 'Y'})
        self._fill_table("XY Bottom", disp_xyb, ['Sl No.', 'Part Number', 'Location', 'X', 'Y', 'Rotation', 'Description', 'Layer'], add_sl=True)

        # 7. Exceptions (Added Remarks)
        mask_error = (df['Status'] != 'MATCHED') & (df['Is Ignored'] == False)
        df_errors = df[mask_error].copy()
        df_errors['Issue Type'] = "Unknown Error"
        df_errors.loc[df_errors['Status'] == 'XY_ONLY', 'Issue Type'] = 'On Board, Not in BOM'
        df_errors.loc[df_errors['Status'] == 'BOM_ONLY', 'Issue Type'] = 'In BOM, Not on Board'
        
        if 'Ref Des' in df_errors.columns:
            df_errors.rename(columns={'Ref Des': 'Location'}, inplace=True)

        # Added 'Remarks' to the end of the list
        self._fill_table("Exceptions", df_errors, ['Location', 'Issue Type', 'Part Number', 'Layer', 'Description', 'Remarks'])

    def _fill_table(self, key, df, columns, add_sl=False):
        table = self.tables[key]
        table.blockSignals(True)
        table.clear()
        
        if add_sl and not df.empty:
            df = df.copy()
            df.reset_index(drop=True, inplace=True)
            df['Sl No.'] = df.index + 1
        
        for c in columns:
            if c not in df.columns: df[c] = ""
            
        table.setColumnCount(len(columns))
        table.setRowCount(len(df))
        table.setHorizontalHeaderLabels(columns)

        if key == "Exceptions":
            self.exc_row_map = {}

        for r_idx, (df_idx, row) in enumerate(df.iterrows()):
            if key == "Exceptions":
                self.exc_row_map[r_idx] = row["_id"]

            for c_idx, col in enumerate(columns):
                val = str(row[col]) if pd.notna(row[col]) else ""
                item = QTableWidgetItem(val)
                table.setItem(r_idx, c_idx, item)
        
        table.resizeColumnsToContents()
        table.blockSignals(False)

    def handle_exception_edit(self, item):
        row = item.row()
        col = item.column()
        
        if row not in self.exc_row_map: return
        record_id = self.exc_row_map[row]
        
        table = self.tables["Exceptions"]
        col_name = table.horizontalHeaderItem(col).text()
        
        # Mapping Display Header -> Logic Engine Column
        if col_name == "Location": df_col = "Ref Des"
        else: df_col = col_name

        new_val = item.text()
        
        if df_col not in self.full_df.columns and col_name == "Location":
             if "Ref Des" in self.full_df.columns: df_col = "Ref Des"
             elif "Designator" in self.full_df.columns: df_col = "Designator"

        idx = self.full_df.index[self.full_df["_id"] == record_id].tolist()
        if idx:
            # Check if column exists, if not create it (e.g. Remarks)
            if df_col not in self.full_df.columns:
                self.full_df[df_col] = ""
            self.full_df.at[idx[0], df_col] = new_val

    def reprocess_data(self):
        if 'Layer' in self.full_df.columns:
            self.full_df['Layer_Classified'] = self.full_df['Layer'].apply(self._classify_layer)
        self.refresh_views()
        QMessageBox.information(self, "Refreshed", "Dashboard updated based on edits.")

    def finalize_export(self):
        export_df = self.full_df.drop(columns=["_id", "Layer_Classified"], errors="ignore")
        self.export_clicked.emit(export_df)