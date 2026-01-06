import sys
import ctypes  # <--- NEW: Required for Windows Taskbar Icon
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow

# Import the theme manager
from src.ui.styles import apply_modern_theme

def main():
    # --- [NEW] WINDOWS TASKBAR ICON FIX ---
    # This tells Windows: "I am a standalone app, not just Python"
    if sys.platform == 'win32':
        myappid = 'pcb.bom.segregator.v2' # Unique string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    # --------------------------------------

    app = QApplication(sys.argv)
    
    apply_modern_theme(app)
    
    window = MainWindow()
    window.showMaximized() 
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()