
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, 
                             QComboBox, QPushButton, QGroupBox, QMessageBox, QHBoxLayout)
from PyQt5.QtCore import pyqtSignal

class MappingScreen(QWidget):
    next_clicked = pyqtSignal(dict) # Signals the "Map" dictionary back to Main
    back_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.bom_columns = []
        self.xy_columns = []
        self.mapping_combos = {} # Stores the dropdown widgets
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        instruction = QLabel("Step 2: Map your File Columns to the Required Fields")
        instruction.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(instruction)

        # --- MAPPING GRID ---
        grid_layout = QGridLayout()
        
        # Define the Fields we NEED
        self.required_fields = [
            # (Field Name, Source File)
            ("Reference Designator", "BOTH"),
            ("Layer / Side", "XY"),
            ("Mid X", "XY"),
            ("Mid Y", "XY"),
            ("Rotation", "XY"),
            ("Part Number", "BOM"),
            ("Value", "BOM"),
            ("Footprint", "BOM"),
            ("Description", "BOM")
        ]

        # Create Headers
        grid_layout.addWidget(QLabel("<b>Target Field</b>"), 0, 0)
        grid_layout.addWidget(QLabel("<b>Source Column</b>"), 0, 1)

        # Create Rows dynamically
        for idx, (field, source) in enumerate(self.required_fields):
            row = idx + 1
            lbl = QLabel(f"{field} ({source})")
            combo = QComboBox()
            
            grid_layout.addWidget(lbl, row, 0)
            grid_layout.addWidget(combo, row, 1)
            
            # Save reference to combo so we can read it later
            # Key = "Part Number", Value = QComboBox Widget
            self.mapping_combos[field] = (combo, source)

        group = QGroupBox("Column Mapping")
        group.setLayout(grid_layout)
        layout.addWidget(group)

        # --- NAVIGATION ---
        nav_layout = QHBoxLayout()
        btn_back = QPushButton("<< Back")
        btn_back.clicked.connect(self.back_clicked.emit)
        
        btn_next = QPushButton("Validate & Merge >>")
        btn_next.clicked.connect(self.finalize_mapping)
        
        nav_layout.addWidget(btn_back)
        nav_layout.addStretch()
        nav_layout.addWidget(btn_next)
        
        layout.addLayout(nav_layout)
        self.setLayout(layout)

    def populate_dropdowns(self, bom_cols, xy_cols):
        """Called by MainWindow to fill the dropdowns with real file headers."""
        self.bom_columns = bom_cols
        self.xy_columns = xy_cols

        for field, (combo, source) in self.mapping_combos.items():
            combo.clear()
            combo.addItem("-- Select Column --")
            
            if source == "BOM":
                combo.addItems(self.bom_columns)
                # Auto-select if name matches exactly (Simple AI)
                self._auto_select(combo, field, self.bom_columns)
            elif source == "XY":
                combo.addItems(self.xy_columns)
                self._auto_select(combo, field, self.xy_columns)
            elif source == "BOTH":
                # For Reference Des, we need it to match BOTH, but usually we map it to BOM 
                # and assume XY has same name, or ask for both. 
                # For simplicity, let's map it to BOM here.
                combo.addItems(self.bom_columns)
                self._auto_select(combo, field, self.bom_columns)

    def _auto_select(self, combo, target, choices):
        """Helper to auto-select if 'Part Number' matches 'Part Number'"""
        target_clean = target.lower().replace(" ", "")
        for i, choice in enumerate(choices):
            choice_clean = str(choice).lower().replace(" ", "").replace("_", "")
            # Fuzzy match keywords
            if target_clean in choice_clean or choice_clean in target_clean:
                combo.setCurrentIndex(i + 1) # +1 because of "-- Select --"
                return

    def finalize_mapping(self):
        """Gather all user selections and send to Main."""
        final_map = {}
        for field, (combo, source) in self.mapping_combos.items():
            selected = combo.currentText()
            if selected == "-- Select Column --":
                # Optional fields can be skipped, but required ones should warn.
                # For now, we just pass None
                final_map[field] = None
            else:
                final_map[field] = selected
        
        # Emit the map
        self.next_clicked.emit(final_map)