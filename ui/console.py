import os
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import (
    QWidget, QPlainTextEdit, QLineEdit
)
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtCore import QProcess

class Console(QWidget):
    """
    A 'read-only' console that displays PowerShell/Bash output in QPlainTextEdit,
    and overlays a QLineEdit exactly at the end of the last line (the shell prompt).
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create the read-only text area
        self.output_area = QPlainTextEdit(self)
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("Consolas", 12))

        # Create the input line that we overlay
        self.input_box = QLineEdit(self)
        self.input_box.setFont(QFont("Consolas", 12))
        self.input_box.returnPressed.connect(self.on_enter_pressed)

        # Make sure the input box is on top of the output_area
        self.input_box.raise_()

        # Start the shell process
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        if os.name == "nt":
            self.process.start("powershell", ["-NoExit"])
        else:
            self.process.start("bash", ["--login"])

        self.process.readyReadStandardOutput.connect(self.on_process_output)
        self.process.readyReadStandardError.connect(self.on_process_output)

        # Keep track of commands for history
        self.command_history = []
        self.history_index = -1  # -1 means not browsing history

        # Force the layout so that output_area takes the entire widget,
        # and we'll position the input_box manually in resizeEvent().
        self.output_area.setGeometry(self.rect())
        # We also keep forcing a scroll to bottom so we always see the prompt.
        self.output_area.verticalScrollBar().rangeChanged.connect(
            lambda: self.output_area.verticalScrollBar().setValue(
                self.output_area.verticalScrollBar().maximum()
            )
        )

        # For theming
        self.current_theme = "dark"
        self.apply_theme("dark")

        # Show an initial info message
        self.append_text("[INFO] Shell started.\n")

    #
    # LAYOUT / RESIZING
    #
    def resizeEvent(self, event):
        """
        Whenever this widget is resized, make the output_area fill it,
        then reposition the input line at the end of the last line.
        """
        super().resizeEvent(event)
        # Make the output_area fill the entire Console widget
        self.output_area.setGeometry(self.rect())
        # Then place the input box at the correct spot
        self.position_input_line()

    def position_input_line(self):
        """
        Re-calculate where the cursor is (i.e. at the shell prompt)
        and move the input box so that it sits exactly at that position.
        """
        # EDIT: Instead of manually calculating via document layout,
        # we use the output_area's current text cursor.
        self.output_area.moveCursor(QTextCursor.End)
        # Get the cursor rect (coordinates relative to the viewport)
        cursor_rect = self.output_area.cursorRect()
        # Map the cursor rect's top-left to the Console widget coordinates
        mapped_pos = self.output_area.viewport().mapTo(self, cursor_rect.topLeft())
        # Place the input box slightly to the right of the cursor
        self.input_box.move(mapped_pos.x() + 5, mapped_pos.y())
        # Resize the input box to fill the remaining width (with some margin)
        self.input_box.resize(self.width() - mapped_pos.x() - 15, self.input_box.sizeHint().height())

    #
    # PROCESS OUTPUT
    #
    def on_process_output(self):
        data = self.process.readAll().data().decode("utf-8", errors="replace")
        if data:
            self.append_text(data)

    def append_text(self, text: str):
        self.output_area.moveCursor(QTextCursor.End)
        self.output_area.insertPlainText(text)
        # Force scroll to bottom so we see the prompt
        self.output_area.verticalScrollBar().setValue(
            self.output_area.verticalScrollBar().maximum()
        )
        # Update input box position
        self.position_input_line()

    #
    # USER TYPED A COMMAND
    #
    def on_enter_pressed(self):
        command = self.input_box.text().rstrip()
        if command:
            # Add to history
            self.command_history.append(command)
            self.history_index = -1
            # Echo it in the console
            self.append_text(command + "\n")
            # Send to shell
            self.process.write((command + "\n").encode())
        # Clear input
        self.input_box.clear()

    #
    # OPTIONAL: HISTORY WITH UP/DOWN
    #
    def keyPressEvent(self, event):
        """
        If user presses Up/Down when the input_box has focus, cycle history.
        We forward these to input_box if it is focused.  Another approach is
        to install an eventFilter on self.input_box.
        """
        if self.input_box.hasFocus():
            if event.key() == Qt.Key_Up:
                if self.command_history:
                    # If not browsing, pick last
                    if self.history_index == -1:
                        self.history_index = len(self.command_history) - 1
                    else:
                        self.history_index = max(0, self.history_index - 1)
                    self.input_box.setText(self.command_history[self.history_index])
                return
            elif event.key() == Qt.Key_Down:
                if self.command_history and self.history_index != -1:
                    self.history_index += 1
                    if self.history_index >= len(self.command_history):
                        self.history_index = -1
                        self.input_box.clear()
                    else:
                        self.input_box.setText(self.command_history[self.history_index])
                return
        super().keyPressEvent(event)

    #
    # THEME TOGGLING
    #
    def toggle_theme(self):
        if self.current_theme == "dark":
            self.apply_theme("light")
            self.current_theme = "light"
        else:
            self.apply_theme("dark")
            self.current_theme = "dark"

    def apply_theme(self, theme):
        if theme == "dark":
            self.output_area.setStyleSheet("QPlainTextEdit { background: black; color: white; }")
            self.input_box.setStyleSheet("QLineEdit { background: black; color: white; border: 1px solid gray; }")
        else:
            self.output_area.setStyleSheet("QPlainTextEdit { background: white; color: black; }")
            self.input_box.setStyleSheet("QLineEdit { background: white; color: black; border: 1px solid gray; }")

    #
    # EXTERNAL API: cd to new path if needed
    #
    def update_path(self, new_path):
        if self.process and self.process.state() == QProcess.Running:
            self.process.write(f'cd "{new_path}"\n'.encode())

    def closeEvent(self, event):
        """Clean up the process on close."""
        if self.process and self.process.state() == QProcess.Running:
            self.process.terminate()
        super().closeEvent(event)
