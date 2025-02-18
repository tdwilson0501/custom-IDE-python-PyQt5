import pickle
import os
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QFileDialog, QMessageBox, QVBoxLayout, QWidget, 
    QAction, QSplitter, QTreeView, QFileSystemModel, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize
from ide.editor import CodeEditor
from ui.console import Console
from ide.project import create_new_project

SESSION_FILE = "session.pkl"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My Custom IDE")
        self.setGeometry(50, 50, 1600, 900)  # Full-size window
        self.showMaximized()  # Open full screen by default

        layout = QVBoxLayout()

        self.splitter = QSplitter(Qt.Horizontal)  # Resizable UI
        self.project_tree = QTreeView()
        self.project_tree.setMinimumWidth(200)  # Reduce project view width
        self.project_tree.setHidden(True)  # Hide initially
        self.project_tree.doubleClicked.connect(self.open_selected_file)

        self.file_model = QFileSystemModel()
        self.file_model.setReadOnly(False)
        self.project_tree.setModel(self.file_model)

        self.project_tabs = QTabWidget()  # Main project tabs
        self.project_tabs.setTabsClosable(True)  
        self.project_tabs.tabCloseRequested.connect(self.close_project_tab)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        self.project_tabs.addTab(self.tabs, "Untitled Project")  # Default tab

        self.splitter.addWidget(self.project_tree)
        self.splitter.addWidget(self.project_tabs)
        self.splitter.setStretchFactor(1, 4)  # Prioritize the text editor space

        layout.addWidget(self.splitter)

        self.console = Console()
        self.console.setMinimumHeight(100)  # Reduce console height
        self.console.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.console)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.menu_bar = self.menuBar()
        self.setup_menus()

        self.load_session()

    def setup_menus(self):
        file_menu = self.menu_bar.addMenu("File")

        new_file_action = QAction("New File", self)
        new_file_action.triggered.connect(self.new_file)
        file_menu.addAction(new_file_action)

        new_project_action = QAction("New Project", self)
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)

        open_project_action = QAction("Open Project", self)  # Added "Open Project"
        open_project_action.triggered.connect(self.open_project)
        file_menu.addAction(open_project_action)

        open_file_action = QAction("Open File", self)
        open_file_action.triggered.connect(self.open_file)
        file_menu.addAction(open_file_action)

        close_file_action = QAction("Close File", self)
        close_file_action.triggered.connect(self.close_file)
        file_menu.addAction(close_file_action)

        save_session_action = QAction("Save Session", self)
        save_session_action.triggered.connect(self.save_session)
        file_menu.addAction(save_session_action)

    def new_file(self):
        editor = CodeEditor()
        self.tabs.addTab(editor, "Untitled")

    def new_project(self):
        create_new_project()
        self.load_project()

    def open_project(self):  # New: Open existing project
        project_path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if project_path:
            new_tab = QTabWidget()
            self.project_tabs.addTab(new_tab, os.path.basename(project_path))
            self.load_project(project_path)

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Python Files (*.py);;All Files (*)")
        if file_name:
            self.open_file_in_editor(file_name)

    def open_selected_file(self, index):
        file_path = self.file_model.filePath(index)
        if os.path.isfile(file_path):
            self.open_file_in_editor(file_path)

    def open_file_in_editor(self, file_path):
        with open(file_path, "r") as file:
            editor = CodeEditor()
            editor.setPlainText(file.read())
            self.tabs.addTab(editor, os.path.basename(file_path))

    def close_file(self):
        index = self.tabs.currentIndex()
        if index >= 0:
            self.close_tab(index)

    def close_tab(self, index):
        self.tabs.removeTab(index)

    def close_project_tab(self, index):
        self.project_tabs.removeTab(index)

    def save_session(self):
        open_files = []
        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            file_name = self.tabs.tabText(i)
            open_files.append((file_name, editor.toPlainText()))

        with open(SESSION_FILE, "wb") as f:
            pickle.dump(open_files, f)

    def load_session(self):
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "rb") as f:
                open_files = pickle.load(f)
                for file_name, content in open_files:
                    editor = CodeEditor()
                    editor.setPlainText(content)
                    self.tabs.addTab(editor, file_name)

    def load_project(self, path=None):
        if not path:
            path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
            if not path:
                return

        self.file_model.setRootPath(path)
        self.project_tree.setRootIndex(self.file_model.index(path))
        self.project_tree.setHidden(False)
