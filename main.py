import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow  # Import MainWindow from the correct location

if __name__ == "__main__":
    app = QApplication(sys.argv)  # This must be created first
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())  # Start the event loop

