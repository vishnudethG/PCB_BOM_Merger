from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QComboBox, QPushButton, QGroupBox, QMessageBox)
from PyQt5.QtCore import pyqtSignal

class MappingScreen(QWidget):
    next_clicked = pyqtSignal(dict)
    back_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.mapping_combos = {} 
        self.bom_columns = []
        self.xy_columns = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # --- INSTRUCTION BOX ---
        instruction_box = QGroupBox("Step 2: Map Columns")
        inst_layout = QVBoxLayout()
        inst_label = QLabel("Map the file columns to your new requirements.")
        inst_layout.addWidget(inst_label)
        instruction_box.setLayout(inst_layout)
        layout.addWidget(instruction_box)

        # --- MAPPING GRID ---
        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        # --- NEW FIELD REQUIREMENTS (Exact Match to User Request) ---
        self.required_fields = [
            # --- LINKING KEYS (Crucial) ---
            ("BOM Location Col", "BOM"), # Was "Designator"
            ("XY Location Col",  "XY"),  # Was "Designator"
            
            # --- XY DATA ---
            ("Center-X", "XY"),       # Was Ref X
            ("Center-Y", "XY"),       # Was Ref Y
            ("Layer",    "XY"),
            ("Rotation", "XY"),
            
            # --- BOM DATA ---
            ("Part No.",    "BOM"),   # Was Part Number
            ("Description", "BOM"),   # Replaces Value/Remark
            ("Quantity",    "BOM")
        ]

        # Headers
        grid_layout.addWidget(QLabel("<b>Target Field</b>"), 0, 0)
        grid_layout.addWidget(QLabel("<b>Source File</b>"), 0, 1)
        grid_layout.addWidget(QLabel("<b>Select Column</b>"), 0, 2)

        # Generate Rows
        for idx, (field, source) in enumerate(self.required_fields):
            row = idx + 1
            
            # Label
            lbl_field = QLabel(field)
            if "Location" in field: lbl_field.setStyleSheet("font-weight: bold;")
            
            # Badge
            lbl_source = QLabel(source)
            color = "#2c3e50" if source == "BOM" else "#c0392b"
            lbl_source.setStyleSheet(f"color: white; background-color: {color}; padding: 2px 6px; border-radius: 4px;")
            lbl_source.setFixedWidth(50)

            # Dropdown
            combo = QComboBox()
            
            grid_layout.addWidget(lbl_field, row, 0)
            grid_layout.addWidget(lbl_source, row, 1)
            grid_layout.addWidget(combo, row, 2)
            
            self.mapping_combos[field] = (combo, source)

        grid_widget.setLayout(grid_layout)
        layout.addWidget(grid_widget)

        # --- NAVIGATION ---
        nav_layout = QHBoxLayout()
        btn_back = QPushButton("<< Back")
        btn_back.clicked.connect(self.back_clicked.emit)
        
        btn_next = QPushButton("Validate & Process >>")
        btn_next.setStyleSheet("font-weight: bold; padding: 6px;")
        btn_next.clicked.connect(self.finalize_mapping)
        
        nav_layout.addWidget(btn_back)
        nav_layout.addStretch()
        nav_layout.addWidget(btn_next)
        
        layout.addLayout(nav_layout)
        self.setLayout(layout)

    def populate_dropdowns(self, bom_cols, xy_cols):
        self.bom_columns = bom_cols
        self.xy_columns = xy_cols

        for field, (combo, source) in self.mapping_combos.items():
            combo.clear()
            combo.addItem("-- Select Column --")
            choices = self.bom_columns if source == "BOM" else self.xy_columns
            combo.addItems(choices)
            
            self._auto_select(combo, field, choices)

    def _auto_select(self, combo, target_field, choices):
        # Clean target for easier matching
        t_clean = target_field.lower().replace("-", "").replace(".", "").replace(" ", "")
        if "location" in t_clean: t_clean = "designator" # Alias

        for index, choice in enumerate(choices):
            c_clean = choice.lower().replace("-", "").replace(".", "").replace(" ", "")
            
            # Exact or close match
            if t_clean == c_clean:
                combo.setCurrentIndex(index + 1)
                return
            if t_clean in c_clean:
                combo.setCurrentIndex(index + 1)
                return

    def finalize_mapping(self):
        final_map = {}
        for field, (combo, _) in self.mapping_combos.items():
            selected = combo.currentText()
            final_map[field] = selected if selected != "-- Select Column --" else None
        
        # Validation
        if not final_map.get("BOM Location Col") or not final_map.get("XY Location Col"):
            QMessageBox.warning(self, "Error", "Location Columns must be mapped.")
            return

        self.next_clicked.emit(final_map)