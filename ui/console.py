import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit
from PyQt5.QtCore import QProcess

class Console(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # Output display
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        layout.addWidget(self.terminal)

        # Input field
        self.input_field = QLineEdit()
        self.input_field.returnPressed.connect(self.execute_command)
        layout.addWidget(self.input_field)

        self.setLayout(layout)

        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyRead.connect(self.display_output)

        # Start PowerShell (Windows) or Bash (Linux/macOS)
        if os.name == "nt":
            self.process.start("powershell")
        else:
            self.process.start("bash")

    def display_output(self):
        output = self.process.readAll().data().decode()
        self.terminal.append(output)

    def execute_command(self):
        command = self.input_field.text()
        if command:
            self.terminal.append(f"> {command}")  # Show the command in the terminal
            self.process.write(command.encode() + b"\n")  # Send the command to the process
            self.input_field.clear()  # Clear the input field


