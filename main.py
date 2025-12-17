# main.py
import sys
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def main():
    # 1. Create the Application
    app = QApplication(sys.argv)
    
    # 2. Apply a Style (Optional, makes it look standard)
    app.setStyle("Fusion")

    # 3. Create and Show the Main Window
    window = MainWindow()
    window.show()

    # 4. Run the Event Loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()