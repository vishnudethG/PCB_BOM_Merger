# src/ui/main_window.py
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QStackedWidget, QMessageBox)
from src.ui.screens.screen_import import ImportScreen
from src.ui.screens.screen_mapping import MappingScreen
from src.ui.screens.screen_dashboard import DashboardScreen # <--- NEW
from src.core.logic_engine import perform_merge_and_validation # <--- NEW

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PCB BOM Merger Tool")
        self.resize(1100, 800) # Slightly larger

        self.bom_df = None
        self.xy_df = None

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)

        # Screens
        self.screen_import = ImportScreen()
        self.screen_mapping = MappingScreen()
        self.screen_dashboard = DashboardScreen() # <--- NEW

        self.stack.addWidget(self.screen_import)   # 0
        self.stack.addWidget(self.screen_mapping)  # 1
        self.stack.addWidget(self.screen_dashboard)# 2
        
        # Signals
        self.screen_import.next_clicked.connect(self.go_to_mapping)
        self.screen_mapping.back_clicked.connect(self.go_to_import)
        self.screen_mapping.next_clicked.connect(self.go_to_validation)
        
        # Dashboard Signals
        self.screen_dashboard.back_clicked.connect(self.go_to_mapping_from_dash)
        self.screen_dashboard.export_clicked.connect(self.perform_final_export)

    def go_to_mapping(self):
        if not hasattr(self.screen_import, 'clean_bom_df') or self.screen_import.xy_df is None:
             QMessageBox.warning(self, "Error", "Data not ready.")
             return
        self.bom_df = self.screen_import.clean_bom_df
        self.xy_df = self.screen_import.xy_df
        
        bom_cols = list(self.bom_df.columns)
        xy_cols = list(self.xy_df.columns)
        self.screen_mapping.populate_dropdowns(bom_cols, xy_cols)
        self.stack.setCurrentIndex(1)

    def go_to_import(self):
        self.stack.setCurrentIndex(0)

    def go_to_validation(self, mapping_dict):
        try:
            # CALL LOGIC ENGINE
            result_df = perform_merge_and_validation(self.bom_df, self.xy_df, mapping_dict)
            
            # LOAD DATA INTO DASHBOARD
            self.screen_dashboard.set_data(result_df)
            
            # SWITCH SCREEN
            self.stack.setCurrentIndex(2)
            
        except Exception as e:
            QMessageBox.critical(self, "Merge Error", f"Logic Failed:\n{str(e)}")

    def go_to_mapping_from_dash(self):
        self.stack.setCurrentIndex(1)

    def perform_final_export(self, final_df):
        print("Ready to export!")
        # We will implement this in Iteration 4
        QMessageBox.information(self, "Done", "Export function coming in next update!")