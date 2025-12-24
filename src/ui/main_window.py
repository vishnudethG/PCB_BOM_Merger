from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QMessageBox, QFileDialog)
from src.ui.screens.screen_import import ImportScreen
from src.ui.screens.screen_mapping import MappingScreen
from src.ui.screens.screen_dashboard import DashboardScreen
from src.core.excel_writer import generate_production_files
import os

# --- UPDATED IMPORT ---
from src.core.logic_engine import perform_merge_v2 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PCB BOM Merger v2.0")
        self.resize(1000, 700)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        self.screen_import = ImportScreen()
        self.screen_mapping = MappingScreen()
        self.screen_dashboard = DashboardScreen()
        
        self.stack.addWidget(self.screen_import)
        self.stack.addWidget(self.screen_mapping)
        self.stack.addWidget(self.screen_dashboard)
        
        self.screen_import.next_clicked.connect(self.go_to_mapping)
        self.screen_mapping.back_clicked.connect(self.go_to_import)
        self.screen_mapping.next_clicked.connect(self.run_process)
        self.screen_dashboard.back_clicked.connect(self.go_to_mapping)
        self.screen_dashboard.export_clicked.connect(self.perform_final_export)

    def go_to_import(self):
        self.stack.setCurrentIndex(0)

    def go_to_mapping(self):
        if self.screen_import.bom_df is None or self.screen_import.xy_df is None:
            QMessageBox.warning(self, "Error", "Please load both BOM and XY files first.")
            return

        bom_cols = list(self.screen_import.bom_df.columns)
        xy_cols = list(self.screen_import.xy_df.columns)
        self.screen_mapping.populate_dropdowns(bom_cols, xy_cols)
        self.stack.setCurrentIndex(1)

    def run_process(self, mapping):
        try:
            bom_df = self.screen_import.bom_df
            xy_df = self.screen_import.xy_df
            
            # --- CALLING THE RENAMED V2 FUNCTION ---
            self.final_df = perform_merge_v2(bom_df, xy_df, mapping)
            
            self.screen_dashboard.set_data(self.final_df)
            self.stack.setCurrentIndex(2)
            
        except Exception as e:
            # Enhanced error message to tell us exactly what failed
            import traceback
            error_details = traceback.format_exc()
            print(error_details) # Print to black console
            QMessageBox.critical(self, "Processing Error", f"Logic Engine V2 Failed:\n{str(e)}")

    def perform_final_export(self, df):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Output", "Production_Output.xlsx", "Excel Files (*.xlsx)", options=options
        )

        if not file_path: return
        if not file_path.lower().endswith('.xlsx'): file_path += '.xlsx'

        try:
            generate_production_files(df, file_path)
            QMessageBox.information(self, "Success", f"Saved to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to write file:\n{str(e)}")