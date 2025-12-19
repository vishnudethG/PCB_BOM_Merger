from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QComboBox, QPushButton, QGroupBox, QMessageBox)
from PyQt5.QtCore import pyqtSignal

# Import Config Manager (Ensure you created this file from previous steps)
from src.core.config_manager import load_mapping_config, save_mapping_config

class MappingScreen(QWidget):
    next_clicked = pyqtSignal(dict)
    back_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.mapping_combos = {} # Stores {field: (combobox, source)}
        self.bom_columns = []
        self.xy_columns = []
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
            # --- KEYS (Match these to the columns used for linking) ---
            ("BOM Reference Col", "BOM"), 
            ("XY Reference Col", "XY"),   
            
            # --- XY DATA (From Pick & Place File) ---
            ("Layer / Side", "XY"),
            ("Mid X", "XY"),
            ("Mid Y", "XY"),
            ("Rotation", "XY"),
            
            # --- BOM DATA (From Bill of Materials) ---
            ("Part Number", "BOM"),
            ("Value", "BOM"),
            ("Description", "BOM"),  # <--- CRITICAL: MUST SAY BOM
            ("Manufacturer", "BOM"), # <--- NEW FIELD
            ("Qty", "BOM"),          # <--- NEW FIELD
            ("Footprint", "BOM")     # Optional but recommended
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
        self.bom_columns = bom_cols
        self.xy_columns = xy_cols
        
        # LOAD SAVED CONFIG
        saved_config = load_mapping_config()

        for field, (combo, source) in self.mapping_combos.items():
            combo.clear()
            combo.addItem("-- Select Column --")
            
            # 1. Decide which list to show
            choices = []
            if source == "BOM": choices = self.bom_columns
            elif source == "XY": choices = self.xy_columns
            
            combo.addItems(choices)

            # 2. SMART SELECTION LOGIC
            # Priority A: Check if we have a saved mapping
            saved_col_name = saved_config.get(field)
            if saved_col_name and saved_col_name in choices:
                index = combo.findText(saved_col_name)
                if index >= 0:
                    combo.setCurrentIndex(index)
                    continue 

            # Priority B: Auto-select based on name similarity
            self._auto_select(combo, field, choices)

    def _auto_select(self, combo, target_field, choices):
        """Helper to guess the correct column based on name."""
        target_clean = target_field.lower().replace(" ", "").replace("_", "")
        
        for index, choice in enumerate(choices):
            # Clean the choice (ignore case, spaces, underscores)
            choice_clean = choice.lower().replace(" ", "").replace("_", "")
            
            # 1. Exact match (cleaned)
            if target_clean == choice_clean:
                combo.setCurrentIndex(index + 1) # +1 because of "-- Select --"
                return
            
            # 2. Contains match (e.g. "PartNumber" in "Mfr_PartNumber")
            # Be careful with short words like "X" or "Y"
            if len(target_clean) > 2 and target_clean in choice_clean:
                combo.setCurrentIndex(index + 1)
                return

    def finalize_mapping(self):
        final_map = {}
        missing_fields = []

        for field, (combo, source) in self.mapping_combos.items():
            selected = combo.currentText()
            if selected != "-- Select Column --":
                final_map[field] = selected
            else:
                final_map[field] = None
                # Optional: Force user to select? For now, we allow empty.
        
        # Validate critical Keys
        if not final_map.get("BOM Reference Col") or not final_map.get("XY Reference Col"):
            QMessageBox.warning(self, "Missing Keys", "You MUST map the Reference Designator columns for both files.")
            return

        # SAVE CONFIG
        save_mapping_config(final_map)
        
        self.next_clicked.emit(final_map)