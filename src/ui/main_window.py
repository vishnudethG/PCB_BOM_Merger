from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QMessageBox, QFileDialog)
from src.ui.screens.screen_home import HomeScreen
from src.ui.screens.screen_import import ImportScreen
from src.ui.screens.screen_mapping import MappingScreen
from src.ui.screens.screen_dashboard import DashboardScreen
from src.core.excel_writer import generate_production_files
from src.core.logic_engine import perform_merge_v2
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PCB BOM Merger v2.2")
        
        # --- FULL SCREEN ON STARTUP ---
        #self.showMaximized()
        
        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Stacked Widget (Holds all screens)
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        # Initialize Screens
        self.screen_home = HomeScreen()         # Index 0
        self.screen_import = ImportScreen()     # Index 1
        self.screen_mapping = MappingScreen()   # Index 2
        self.screen_dashboard = DashboardScreen() # Index 3
        
        # Add to Stack
        self.stack.addWidget(self.screen_home)
        self.stack.addWidget(self.screen_import)
        self.stack.addWidget(self.screen_mapping)
        self.stack.addWidget(self.screen_dashboard)
        
        # --- NAVIGATION LOGIC ---
        
        # Home -> Import
        self.screen_home.segregation_clicked.connect(lambda: self.stack.setCurrentIndex(1))
        
        # Import -> Mapping
        self.screen_import.next_clicked.connect(self.go_to_mapping)
        
        # Mapping -> Back to Import
        self.screen_mapping.back_clicked.connect(lambda: self.stack.setCurrentIndex(1))
        # Mapping -> Logic Engine -> Dashboard
        self.screen_mapping.next_clicked.connect(self.run_process)
        
        # Dashboard -> Back to Mapping
        self.screen_dashboard.back_clicked.connect(lambda: self.stack.setCurrentIndex(2))
        # Dashboard -> Export Excel
        self.screen_dashboard.export_clicked.connect(self.perform_final_export)

    def go_to_mapping(self):
        if self.screen_import.bom_df is None or self.screen_import.xy_df is None:
            QMessageBox.warning(self, "Error", "Please load both BOM and XY files first.")
            return

        bom_cols = list(self.screen_import.bom_df.columns)
        xy_cols = list(self.screen_import.xy_df.columns)
        self.screen_mapping.populate_dropdowns(bom_cols, xy_cols)
        self.stack.setCurrentIndex(2)

    def run_process(self, mapping):
        try:
            bom_df = self.screen_import.bom_df
            xy_df = self.screen_import.xy_df
            
            self.final_df = perform_merge_v2(bom_df, xy_df, mapping)
            
            self.screen_dashboard.set_data(self.final_df)
            self.stack.setCurrentIndex(3)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Processing Error", f"Logic Engine Failed:\n{str(e)}")

    def perform_final_export(self, df):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Output", "Production_Output.xlsx", "Excel Files (*.xlsx)", options=options
        )

        if not file_path: return
        if not file_path.lower().endswith('.xlsx'): file_path += '.xlsx'

        try:
            generate_production_files(df, file_path)
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Success")
            msg.setText("File Generated Successfully!")
            msg.setInformativeText(f"Saved to:\n{file_path}")
            btn_open = msg.addButton("Open Folder", QMessageBox.ActionRole)
            msg.addButton(QMessageBox.Ok)
            msg.exec_()

            if msg.clickedButton() == btn_open:
                folder = os.path.dirname(file_path)
                os.startfile(folder)

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to write file:\n{str(e)}")