import pickle
import os
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QFileDialog, QVBoxLayout,
    QWidget, QAction, QSplitter, QTreeView, QFileSystemModel, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from ide.editor import CodeEditor
from ui.console import Console
from ide.project import create_new_project

SESSION_FILE = "session.pkl"

class ProjectLoaderThread(QThread):
    project_loaded = pyqtSignal(str)

    def __init__(self, project_path):
        super().__init__()
        self.project_path = project_path

    def run(self):
        """Load project in a separate thread to prevent UI freezing."""
        self.project_loaded.emit(self.project_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My Custom IDE")
        self.setGeometry(50, 50, 1600, 900)
        self.showMaximized()

        layout = QVBoxLayout()

        self.splitter = QSplitter(Qt.Horizontal)
        self.project_tree = QTreeView()
        self.project_tree.setMinimumWidth(200)
        self.project_tree.doubleClicked.connect(self.open_selected_file)

        self.file_model = QFileSystemModel()
        self.file_model.setReadOnly(False)
        self.project_tree.setModel(self.file_model)

        self.project_tabs = QTabWidget()
        self.project_tabs.setTabsClosable(True)
        self.project_tabs.tabCloseRequested.connect(self.close_project_tab)
        self.project_tabs.currentChanged.connect(self.update_project_view)

        self.splitter.addWidget(self.project_tree)
        self.splitter.addWidget(self.project_tabs)
        self.splitter.setStretchFactor(1, 4)

        layout.addWidget(self.splitter)

        self.console = Console()
        self.console.setMinimumHeight(100)
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

        open_project_action = QAction("Open Project", self)
        open_project_action.triggered.connect(self.open_project)
        file_menu.addAction(open_project_action)

        open_file_action = QAction("Open File", self)
        open_file_action.triggered.connect(self.open_file)
        file_menu.addAction(open_file_action)

        close_file_action = QAction("Close File", self)
        close_file_action.triggered.connect(lambda: self.close_file())
        file_menu.addAction(close_file_action)
        
        view_menu = self.menu_bar.addMenu("View")

        toggle_theme_action = QAction("Toggle Theme", self)
        toggle_theme_action.triggered.connect(self.console.toggle_theme)
        view_menu.addAction(toggle_theme_action)

    def new_file(self):
        """Create a new file inside the currently active project."""
        current_index = self.project_tabs.currentIndex()
        if current_index < 0:
            return  # No project tab open

        # EDIT: Always get the project container from the project_tabs,
        # not the currently active child widget.
        current_project = self.project_tabs.widget(current_index)
        if not isinstance(current_project, QTabWidget):
            return  # Prevent file creation if no valid project container

        project_path = self.project_tabs.tabBar().tabData(current_index)
        if not project_path or not os.path.exists(project_path):
            return  # Ensure the project path is valid

        # Ask for a file name
        file_name, _ = QFileDialog.getSaveFileName(
            self, "New File", os.path.join(project_path, "untitled.py"),
            "Python Files (*.py);;All Files (*)"
        )

        if file_name:
            # Create the new file with default content
            with open(file_name, "w") as file:
                file.write("# New Python file\n")

            # Open the new file in the editor
            editor = CodeEditor()
            with open(file_name, "r") as file:
                editor.setPlainText(file.read())

            current_project.addTab(editor, os.path.basename(file_name))
            current_project.setCurrentWidget(editor)

            # Refresh the project file tree
            self.file_model.setRootPath(project_path)
            self.project_tree.setRootIndex(self.file_model.index(project_path))

    def new_project(self):
        """Create a new project and open it automatically."""
        project_path = create_new_project()
        if project_path:
            self.load_project(project_path)

    def open_project(self):
        project_path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if project_path:
            self.load_project(project_path)

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "Python Files (*.py);;All Files (*)"
        )
        if file_name:
            self.open_file_in_editor(file_name)

    def open_selected_file(self, index):
        file_path = self.file_model.filePath(index)
        if os.path.isfile(file_path):
            self.open_file_in_editor(file_path)

    def open_file_in_editor(self, file_path):
        current_index = self.project_tabs.currentIndex()
        if current_index < 0:
            return  # Ensure a project exists before opening a file

        current_project = self.project_tabs.widget(current_index)
        if not isinstance(current_project, QTabWidget):
            return

        with open(file_path, "r") as file:
            editor = CodeEditor()
            editor.setPlainText(file.read())
            current_project.addTab(editor, os.path.basename(file_path))
            current_project.setCurrentWidget(editor)

    def close_file(self, index=None):
        current_index = self.project_tabs.currentIndex()
        if current_index < 0:
            return
        current_project = self.project_tabs.widget(current_index)
        if current_project and isinstance(current_project, QTabWidget):
            if index is None:
                index = current_project.currentIndex()
            if index >= 0:
                current_project.removeTab(index)

    def close_project_tab(self, index):
        self.project_tabs.removeTab(index)
        self.update_project_view()  # Refresh project tree

    def update_project_view(self):
        """Ensure the file tree updates based on the active project."""
        current_index = self.project_tabs.currentIndex()
        if current_index < 0:
            return
        project_path = self.project_tabs.tabBar().tabData(current_index)
        if project_path and os.path.exists(project_path):
            self.file_model.setRootPath(project_path)
            self.project_tree.setRootIndex(self.file_model.index(project_path))
            self.project_tree.setHidden(False)
            self.console.update_path(project_path)

    def save_session(self):
        open_projects = []
        for i in range(self.project_tabs.count()):
            project_path = self.project_tabs.tabBar().tabData(i)
            open_projects.append(project_path)
        with open(SESSION_FILE, "wb") as f:
            pickle.dump(open_projects, f)

    def load_session(self):
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "rb") as f:
                open_projects = pickle.load(f)
                for project_path in open_projects:
                    if project_path:
                        self.load_project(project_path)

    def load_project(self, path):
        """Load a project and update UI elements."""
        new_project_tab = QTabWidget()
        new_project_tab.setTabsClosable(True)
        new_project_tab.tabCloseRequested.connect(self.close_project_tab)
        index = self.project_tabs.addTab(new_project_tab, os.path.basename(path))
        self.project_tabs.setCurrentWidget(new_project_tab)

        self.file_model.setRootPath(path)
        self.project_tree.setRootIndex(self.file_model.index(path))
        self.project_tree.setHidden(False)

        self.project_tabs.tabBar().setTabData(index, path)
        self.update_project_view()
