import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt5.QtCore import QProcess, Qt, QEvent

class Console(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(False)  # Allow typing
        self.terminal.setFontFamily("Consolas")
        self.terminal.setFontPointSize(12)
        self.set_theme("dark")

        layout.addWidget(self.terminal)
        self.setLayout(layout)

        # ADD: Keep track of the earliest position the user is allowed to edit.
        self.prompt_position = 0

        # ADD: Install an event filter on the terminal to block edits above prompt_position.
        self.terminal.installEventFilter(self)

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.display_output)
        self.process.readyReadStandardError.connect(self.display_output)

        if os.name == "nt":
            self.process.start("powershell", ["-NoExit"])
        else:
            self.process.start("bash", ["--login"])

        self.terminal.append("[INFO] Terminal started.\n")
        # EDIT: Update prompt_position to prevent deleting the initial text.
        self.prompt_position = len(self.terminal.toPlainText())

    def display_output(self):
        """Read and display process output."""
        output = self.process.readAll().data().decode().strip()
        if output:
            self.terminal.append(output)
            # EDIT: Update prompt_position so newly printed text cannot be edited.
            self.prompt_position = len(self.terminal.toPlainText())

    def keyPressEvent(self, event):
        """Capture keypress events to send commands."""
        # If user presses Enter (without Shift), parse the last line and execute.
        if event.key() == Qt.Key_Return and not (event.modifiers() & Qt.ShiftModifier):
            command = self.terminal.toPlainText().split("\n")[-1].strip()
            if command:
                self.execute_command(command)
        else:
            # ADD: Prevent destructive keys from going before prompt_position.
            if event.key() in (Qt.Key_Backspace, Qt.Key_Delete, 
                               Qt.Key_Left, Qt.Key_Up, Qt.Key_PageUp, Qt.Key_Home):
                cursor = self.terminal.textCursor()
                # If the cursor is at or before prompt_position, block the key.
                if cursor.position() <= self.prompt_position:
                    return
            super().keyPressEvent(event)

    # ADD: Block mouse clicks that place the cursor above prompt_position.
    def eventFilter(self, obj, event):
        if obj == self.terminal:
            if event.type() == QEvent.MouseButtonPress:
                # Let the default happen first.
                result = super().eventFilter(obj, event)
                # Then correct the cursor if it's before prompt_position.
                cursor = self.terminal.textCursor()
                if cursor.position() < self.prompt_position:
                    cursor.setPosition(self.prompt_position)
                    self.terminal.setTextCursor(cursor)
                return True
        return super().eventFilter(obj, event)

    def execute_command(self, command):
        """Send command to PowerShell or Bash."""
        if self.process and self.process.state() == QProcess.Running:
            self.process.write((command + "\n").encode())
            self.terminal.append(f"> {command}")  # Display typed command
            # EDIT: Update prompt_position to protect the just-entered command.
            self.prompt_position = len(self.terminal.toPlainText())

    def update_path(self, new_path):
        """Change working directory inside the embedded terminal."""
        if self.process and self.process.state() == QProcess.Running:
            command = f'cd "{new_path}"' if os.name == "nt" else f'cd "{new_path}"'
            self.execute_command(command)
            self.terminal.append(f"[Changed directory to: {new_path}]\n")
            # EDIT: Update prompt_position again.
            self.prompt_position = len(self.terminal.toPlainText())

    def set_theme(self, theme):
        """Switch between light and dark mode."""
        if theme == "dark":
            self.terminal.setStyleSheet("background-color: black; color: white;")
        else:
            self.terminal.setStyleSheet("background-color: white; color: black;")
