import os
import subprocess
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QInputDialog

def create_new_project():
    project_dir = QFileDialog.getExistingDirectory(None, "Select Project Directory")
    if not project_dir:
        return  # User canceled

    project_name, ok = QInputDialog.getText(None, "Enter Project Name", "Project Name:")  # Fixed dialog
    if not ok or not project_name:
        return

    project_path = os.path.join(project_dir, project_name)
    os.makedirs(project_path, exist_ok=True)

    # Create Virtual Environment
    subprocess.run(["python", "-m", "venv", os.path.join(project_path, "venv")])

    QMessageBox.information(None, "Project Created", f"Project '{project_name}' created successfully!")


