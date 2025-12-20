import sys
import os
import json
import shutil
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QLineEdit,
                             QTextEdit, QFileDialog, QProgressBar, QGroupBox,
                             QMessageBox, QDialog, QFormLayout, QScrollArea,
                             QFrame, QListWidget, QSplitter, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor

from core.worker import ProcessWorker
from core.process_widget import ProcessWidget
from core.dialogs import SettingsDialog


class MainWindow(QMainWindow):
    """Main control window for the application"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Processing Manager")
        self.setGeometry(100, 100, 1200, 700)

        self.settings_file = "saves/app_settings.json"
        self.processes_file = "saves/processes_state.json"
        self.folders_file = "saves/folders_state.json"

        self.settings = self.load_settings()
        self.processes = {}
        self.folders = {}
        self.current_folder = "root"
        self.workers = {}
        self.process_widgets = {}
        self.process_logs = {}

        # Determine theme from settings
        self.theme = 'dark' if self.settings.get('theme', 'Light Theme') == 'Dark Theme' else 'light'

        self.init_ui()
        self.apply_theme()
        self.load_folders_state()
        self.load_processes_state()
        self.refresh_folder_list()
        self.refresh_process_list()

        # Use timer to resume processes after UI is fully initialized
        QTimer.singleShot(500, self.resume_processes)

    def init_ui(self):
        # Central widget
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Top toolbar
        toolbar_layout = QHBoxLayout()

        new_process_btn = QPushButton("📄 New Process")
        new_process_btn.setObjectName("newProcessButton")
        new_process_btn.clicked.connect(self.create_new_process)

        new_folder_btn = QPushButton("📁 New Folder")
        new_folder_btn.setObjectName("newFolderButton")
        new_folder_btn.clicked.connect(self.create_new_folder)

        settings_btn = QPushButton("⚙ Settings")
        settings_btn.setObjectName("settingsButton")
        settings_btn.clicked.connect(self.open_settings)

        toolbar_layout.addWidget(new_process_btn)
        toolbar_layout.addWidget(new_folder_btn)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(settings_btn)

        # Statistics dashboard
        stats_group = QGroupBox("📊 Process Statistics")
        stats_group.setObjectName("statsGroup")
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)

        self.total_label = QLabel("📋 Total: 0")
        self.completed_label = QLabel("✅ Completed: 0")
        self.failed_label = QLabel("❌ Failed: 0")
        self.running_label = QLabel("⚡ Running: 0")

        for label in [self.total_label, self.completed_label, self.failed_label, self.running_label]:
            label.setFont(QFont("Segoe UI", 11))
            label.setObjectName("statsLabel")

        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.completed_label)
        stats_layout.addWidget(self.failed_label)
        stats_layout.addWidget(self.running_label)
        stats_layout.addStretch()

        stats_group.setLayout(stats_layout)

        # Main content: folder list + process list
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setObjectName("contentSplitter")

        # Left panel: Folder navigation
        folder_widget = QWidget()
        folder_widget.setObjectName("folderWidget")
        folder_layout = QVBoxLayout(folder_widget)
        folder_layout.setContentsMargins(10, 10, 10, 10)
        folder_layout.setSpacing(10)

        folder_header = QLabel("📂 Folders")
        folder_header.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        folder_header.setObjectName("folderHeader")
        folder_layout.addWidget(folder_header)

        self.folder_list = QListWidget()
        self.folder_list.itemClicked.connect(self.on_folder_selected)
        folder_layout.addWidget(self.folder_list)

        delete_folder_btn = QPushButton("🗑 Delete Folder")
        delete_folder_btn.setObjectName("deleteFolderButton")
        delete_folder_btn.clicked.connect(self.delete_current_folder)
        folder_layout.addWidget(delete_folder_btn)

        # Right panel: Process list
        process_widget = QWidget()
        process_widget.setObjectName("processWidget")
        process_layout = QVBoxLayout(process_widget)
        process_layout.setContentsMargins(10, 10, 10, 10)
        process_layout.setSpacing(10)

        self.current_folder_label = QLabel("📁 Current Folder: Root")
        self.current_folder_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.current_folder_label.setObjectName("currentFolderLabel")
        process_layout.addWidget(self.current_folder_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("processScroll")

        self.process_container = QWidget()
        self.process_container.setObjectName("processContainer")
        self.process_layout = QVBoxLayout(self.process_container)
        self.process_layout.addStretch()

        scroll.setWidget(self.process_container)
        process_layout.addWidget(scroll)

        # Add to splitter
        content_splitter.addWidget(folder_widget)
        content_splitter.addWidget(process_widget)
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 3)

        # Add all to main layout
        main_layout.addLayout(toolbar_layout)
        main_layout.addWidget(stats_group)
        main_layout.addWidget(content_splitter)

        # Update stats timer
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_statistics)
        self.stats_timer.start(1000)

    def apply_theme(self):
        if self.theme == 'dark':
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2C3E50;
                }
                QWidget#centralWidget {
                    background-color: #2C3E50;
                }
                QLabel {
                    color: #ECF0F1;
                }
                QLineEdit, QTextEdit {
                    background-color: #34495E;
                    color: #ECF0F1;
                    border: 1px solid #5D6D7E;
                    border-radius: 4px;
                    padding: 6px;
                    selection-background-color: #3498DB;
                }
                QLineEdit:focus, QTextEdit:focus {
                    border: 2px solid #3498DB;
                }
                QTextEdit {
                    font-family: 'Segoe UI', Arial;
                }
                QListWidget {
                    background-color: #34495E;
                    color: #ECF0F1;
                    border: 1px solid #5D6D7E;
                    border-radius: 6px;
                    padding: 5px;
                }
                QListWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #2C3E50;
                }
                QListWidget::item:selected {
                    background-color: #3498DB;
                    color: white;
                    border-radius: 4px;
                }
                QListWidget::item:hover {
                    background-color: #4A6278;
                    border-radius: 4px;
                }
                QScrollArea {
                    border: none;
                    background-color: transparent;
                }
                QScrollBar:vertical {
                    background-color: #2C3E50;
                    width: 12px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background-color: #95A5A6;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #7F8C8D;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QGroupBox#statsGroup {
                    font-weight: bold;
                    border: 2px solid #7F8C8D;
                    border-radius: 8px;
                    padding-top: 10px;
                    background-color: #34495E;
                    color: #ECF0F1;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 10px 0 10px;
                    color: #ECF0F1;
                }
                QLabel#statsLabel {
                    padding: 10px;
                    background-color: #2C3E50;
                    border-radius: 6px;
                    border: 1px solid #5D6D7E;
                    min-width: 150px;
                    text-align: center;
                }
                QPushButton#newProcessButton {
                    background-color: #2ECC71;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton#newProcessButton:hover {
                    background-color: #27AE60;
                }
                QPushButton#newProcessButton:pressed {
                    background-color: #219653;
                }
                QPushButton#newFolderButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton#newFolderButton:hover {
                    background-color: #2980B9;
                }
                QPushButton#newFolderButton:pressed {
                    background-color: #21618C;
                }
                QPushButton#settingsButton {
                    background-color: #9B59B6;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton#settingsButton:hover {
                    background-color: #8E44AD;
                }
                QPushButton#settingsButton:pressed {
                    background-color: #7D3C98;
                }
                QPushButton#deleteFolderButton {
                    background-color: #E74C3C;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton#deleteFolderButton:hover {
                    background-color: #C0392B;
                }
                QPushButton#deleteFolderButton:pressed {
                    background-color: #A93226;
                }
                QWidget#folderWidget {
                    background-color: #34495E;
                    border-radius: 8px;
                }
                QWidget#processWidget {
                    background-color: #34495E;
                    border-radius: 8px;
                }
                QWidget#processContainer {
                    background-color: #2C3E50;
                }
                QLabel#folderHeader, QLabel#currentFolderLabel {
                    color: #ECF0F1;
                    padding: 10px;
                    background-color: #2C3E50;
                    border-radius: 6px;
                    border: 2px solid #5D6D7E;
                }
                QSplitter#contentSplitter::handle {
                    background-color: #5D6D7E;
                    width: 3px;
                }
                QSplitter#contentSplitter::handle:hover {
                    background-color: #3498DB;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #ECF0F1;
                }
                QWidget#centralWidget {
                    background-color: #ECF0F1;
                }
                QLabel {
                    color: #2C3E50;
                }
                QLineEdit, QTextEdit {
                    background-color: #FFFFFF;
                    border: 1px solid #BDC3C7;
                    border-radius: 4px;
                    padding: 6px;
                    selection-background-color: #3498DB;
                }
                QLineEdit:focus, QTextEdit:focus {
                    border: 2px solid #3498DB;
                }
                QTextEdit {
                    font-family: 'Segoe UI', Arial;
                }
                QListWidget {
                    background-color: #FFFFFF;
                    border: 1px solid #BDC3C7;
                    border-radius: 6px;
                    padding: 5px;
                }
                QListWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #ECF0F1;
                }
                QListWidget::item:selected {
                    background-color: #3498DB;
                    color: white;
                    border-radius: 4px;
                }
                QListWidget::item:hover {
                    background-color: #D6EAF8;
                    border-radius: 4px;
                }
                QScrollArea {
                    border: none;
                    background-color: transparent;
                }
                QScrollBar:vertical {
                    background-color: #ECF0F1;
                    width: 12px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background-color: #95A5A6;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #7F8C8D;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QGroupBox#statsGroup {
                    font-weight: bold;
                    border: 2px solid #7F8C8D;
                    border-radius: 8px;
                    padding-top: 10px;
                    background-color: #FFFFFF;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 10px 0 10px;
                    color: #2C3E50;
                }
                QLabel#statsLabel {
                    padding: 10px;
                    background-color: #F8F9FA;
                    border-radius: 6px;
                    border: 1px solid #BDC3C7;
                    min-width: 150px;
                    text-align: center;
                }
                QPushButton#newProcessButton {
                    background-color: #2ECC71;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton#newProcessButton:hover {
                    background-color: #27AE60;
                }
                QPushButton#newProcessButton:pressed {
                    background-color: #219653;
                }
                QPushButton#newFolderButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton#newFolderButton:hover {
                    background-color: #2980B9;
                }
                QPushButton#newFolderButton:pressed {
                    background-color: #21618C;
                }
                QPushButton#settingsButton {
                    background-color: #9B59B6;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton#settingsButton:hover {
                    background-color: #8E44AD;
                }
                QPushButton#settingsButton:pressed {
                    background-color: #7D3C98;
                }
                QPushButton#deleteFolderButton {
                    background-color: #E74C3C;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton#deleteFolderButton:hover {
                    background-color: #C0392B;
                }
                QPushButton#deleteFolderButton:pressed {
                    background-color: #A93226;
                }
                QWidget#folderWidget {
                    background-color: #F8F9FA;
                    border-radius: 8px;
                }
                QWidget#processWidget {
                    background-color: #FFFFFF;
                    border-radius: 8px;
                }
                QWidget#processContainer {
                    background-color: #ECF0F1;
                }
                QLabel#folderHeader, QLabel#currentFolderLabel {
                    color: #2C3E50;
                    padding: 10px;
                    background-color: #F8F9FA;
                    border-radius: 6px;
                    border: 2px solid #BDC3C7;
                }
                QSplitter#contentSplitter::handle {
                    background-color: #BDC3C7;
                    width: 3px;
                }
                QSplitter#contentSplitter::handle:hover {
                    background-color: #3498DB;
                }
            """)

    def create_new_folder(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Folder")
        dialog.setMinimumWidth(400)
        dialog.setObjectName("newFolderDialog")

        layout = QVBoxLayout()

        name_layout = QFormLayout()
        name_layout.setSpacing(15)

        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter folder name")
        name_input.setObjectName("folderNameInput")
        name_layout.addRow("📁 Folder Name:", name_input)

        button_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        create_btn.setObjectName("createFolderButton")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelFolderButton")

        create_btn.clicked.connect(lambda: self.save_new_folder(name_input.text(), dialog))
        cancel_btn.clicked.connect(dialog.reject)

        button_layout.addStretch()
        button_layout.addWidget(create_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(name_layout)
        layout.addStretch()
        layout.addLayout(button_layout)

        dialog.setLayout(layout)

        # Apply theme to dialog
        if self.theme == 'dark':
            dialog.setStyleSheet("""
                QDialog#newFolderDialog {
                    background-color: #2C3E50;
                }
                QLabel {
                    color: #ECF0F1;
                }
                QLineEdit#folderNameInput {
                    padding: 10px;
                    border: 2px solid #5D6D7E;
                    border-radius: 6px;
                    background-color: #34495E;
                    color: #ECF0F1;
                    font-size: 12px;
                }
                QLineEdit#folderNameInput:focus {
                    border: 2px solid #3498DB;
                }
                QPushButton#createFolderButton {
                    background-color: #2ECC71;
                    color: white;
                    border: none;
                    padding: 10px 25px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton#createFolderButton:hover {
                    background-color: #27AE60;
                }
                QPushButton#createFolderButton:pressed {
                    background-color: #219653;
                }
                QPushButton#cancelFolderButton {
                    background-color: #95A5A6;
                    color: white;
                    border: none;
                    padding: 10px 25px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton#cancelFolderButton:hover {
                    background-color: #7F8C8D;
                }
                QPushButton#cancelFolderButton:pressed {
                    background-color: #6C7B7D;
                }
            """)
        else:
            dialog.setStyleSheet("""
                QDialog#newFolderDialog {
                    background-color: #ECF0F1;
                }
                QLabel {
                    color: #2C3E50;
                }
                QLineEdit#folderNameInput {
                    padding: 10px;
                    border: 2px solid #BDC3C7;
                    border-radius: 6px;
                    background-color: #FFFFFF;
                    font-size: 12px;
                }
                QLineEdit#folderNameInput:focus {
                    border: 2px solid #3498DB;
                }
                QPushButton#createFolderButton {
                    background-color: #2ECC71;
                    color: white;
                    border: none;
                    padding: 10px 25px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton#createFolderButton:hover {
                    background-color: #27AE60;
                }
                QPushButton#createFolderButton:pressed {
                    background-color: #219653;
                }
                QPushButton#cancelFolderButton {
                    background-color: #95A5A6;
                    color: white;
                    border: none;
                    padding: 10px 25px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton#cancelFolderButton:hover {
                    background-color: #7F8C8D;
                }
                QPushButton#cancelFolderButton:pressed {
                    background-color: #6C7B7D;
                }
            """)

        dialog.exec()

    def save_new_folder(self, name, dialog):
        if not name:
            QMessageBox.warning(self, "Error", "Folder name is required!")
            return

        folder_id = f"folder_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.folders[folder_id] = {
            'id': folder_id,
            'name': name,
            'created_at': datetime.now().isoformat()
        }

        self.save_folders_state()
        self.refresh_folder_list()
        dialog.accept()

    def delete_current_folder(self):
        if self.current_folder == "root":
            QMessageBox.warning(self, "Error", "Cannot delete root folder!")
            return

        folder_name = None
        for fid, folder in self.folders.items():
            if fid == self.current_folder:
                folder_name = folder['name']
                break

        if not folder_name:
            return

        # Check if folder has processes
        processes_in_folder = [p for p in self.processes.values() if p.get('folder_id') == self.current_folder]

        if processes_in_folder:
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Folder '{folder_name}' contains {len(processes_in_folder)} process(es).\n"
                "Deleting this folder will also delete all processes and their outputs.\n\n"
                "Are you sure you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        else:
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete folder '{folder_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

        if reply == QMessageBox.StandardButton.Yes:
            # Delete all processes in the folder
            for process in processes_in_folder:
                self.delete_process_internal(process['id'], skip_confirmation=True)

            # Delete folder
            del self.folders[self.current_folder]
            self.save_folders_state()

            # Switch to root
            self.current_folder = "root"
            self.refresh_folder_list()
            self.refresh_process_list()

    def on_folder_selected(self, item):
        folder_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_folder = folder_id

        if folder_id == "root":
            self.current_folder_label.setText("📁 Current Folder: Root")
        else:
            folder_name = self.folders[folder_id]['name']
            self.current_folder_label.setText(f"📁 Current Folder: {folder_name}")

        self.refresh_process_list()

    def refresh_folder_list(self):
        self.folder_list.clear()

        # Add root folder
        root_item = self.folder_list.addItem("🏠 Root")
        item = self.folder_list.item(0)
        item.setData(Qt.ItemDataRole.UserRole, "root")

        if self.current_folder == "root":
            item.setSelected(True)

        # Add other folders
        for folder_id, folder in self.folders.items():
            item_text = f"📁 {folder['name']}"
            self.folder_list.addItem(item_text)
            item = self.folder_list.item(self.folder_list.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, folder_id)

            if self.current_folder == folder_id:
                item.setSelected(True)

    def refresh_process_list(self):
        # Clear existing widgets
        while self.process_layout.count() > 1:  # Keep the stretch
            item = self.process_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.process_widgets.clear()

        # Add processes from current folder
        for process_id, process_data in self.processes.items():
            if process_data.get('folder_id', 'root') == self.current_folder:
                self.add_process_widget(process_data)

    def create_new_process(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Process")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(500)
        dialog.setObjectName("newProcessDialog")

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Process name
        name_layout = QFormLayout()
        name_layout.setSpacing(10)

        name_input = QLineEdit()
        name_input.setPlaceholderText("My PDF Processing Task")
        name_input.setObjectName("processNameInput")
        name_layout.addRow("📝 Process Name:", name_input)

        # Instruction
        instruction_label = QLabel("💡 Instruction/Prompt:")
        instruction_input = QTextEdit()
        instruction_input.setPlaceholderText("Enter processing instructions...")
        instruction_input.setMaximumHeight(150)
        instruction_input.setObjectName("instructionInput")

        # Model selection
        model_layout = QHBoxLayout()
        model_input = QLineEdit()
        model_input.setText(self.settings.get('model_name', 'ServiceNow-AI/Apriel-1.6-15b-Thinker:together'))
        model_input.setPlaceholderText("e.g., ServiceNow-AI/Apriel-1.6-15b-Thinker:together")
        model_input.setObjectName("modelInput")
        model_layout.addWidget(QLabel("🤖 Model:"))
        model_layout.addWidget(model_input)

        # PDF Folder
        pdf_folder_layout = QHBoxLayout()
        pdf_folder_input = QLineEdit()
        pdf_folder_input.setReadOnly(True)
        pdf_folder_input.setPlaceholderText("Select folder containing PDF files...")
        pdf_folder_input.setObjectName("pdfFolderInput")

        pdf_folder_btn = QPushButton("📁 Browse...")
        pdf_folder_btn.setObjectName("browseButton")
        pdf_folder_btn.clicked.connect(lambda: self.select_folder(pdf_folder_input))

        pdf_folder_layout.addWidget(QLabel("📄 PDF Folder:"))
        pdf_folder_layout.addWidget(pdf_folder_input)
        pdf_folder_layout.addWidget(pdf_folder_btn)

        # Buttons
        button_layout = QHBoxLayout()
        create_btn = QPushButton("🚀 Create & Start")
        create_btn.setObjectName("createProcessButton")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelProcessButton")

        create_btn.clicked.connect(lambda: self.start_new_process(
            name_input.text(),
            instruction_input.toPlainText(),
            pdf_folder_input.text(),
            model_input.text(),
            dialog
        ))
        cancel_btn.clicked.connect(dialog.reject)

        button_layout.addStretch()
        button_layout.addWidget(create_btn)
        button_layout.addWidget(cancel_btn)

        # Add to layout
        layout.addLayout(name_layout)
        layout.addWidget(instruction_label)
        layout.addWidget(instruction_input)
        layout.addLayout(model_layout)
        layout.addLayout(pdf_folder_layout)
        layout.addStretch()
        layout.addLayout(button_layout)

        dialog.setLayout(layout)

        # Apply theme to dialog
        if self.theme == 'dark':
            dialog.setStyleSheet("""
                QDialog#newProcessDialog {
                    background-color: #2C3E50;
                }
                QLabel {
                    color: #ECF0F1;
                    font-weight: bold;
                }
                QLineEdit#processNameInput, QLineEdit#modelInput {
                    padding: 10px;
                    border: 2px solid #5D6D7E;
                    border-radius: 6px;
                    background-color: #34495E;
                    color: #ECF0F1;
                    font-size: 12px;
                }
                QLineEdit#processNameInput:focus, QLineEdit#modelInput:focus {
                    border: 2px solid #3498DB;
                }
                QLineEdit#pdfFolderInput {
                    padding: 10px;
                    border: 2px solid #5D6D7E;
                    border-radius: 6px;
                    background-color: #2C3E50;
                    font-size: 12px;
                    color: #BDC3C7;
                }
                QTextEdit#instructionInput {
                    padding: 10px;
                    border: 2px solid #5D6D7E;
                    border-radius: 6px;
                    background-color: #34495E;
                    font-size: 12px;
                    color: #ECF0F1;
                }
                QTextEdit#instructionInput:focus {
                    border: 2px solid #3498DB;
                }
                QPushButton#browseButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton#browseButton:hover {
                    background-color: #2980B9;
                }
                QPushButton#browseButton:pressed {
                    background-color: #21618C;
                }
                QPushButton#createProcessButton {
                    background-color: #2ECC71;
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton#createProcessButton:hover {
                    background-color: #27AE60;
                }
                QPushButton#createProcessButton:pressed {
                    background-color: #219653;
                }
                QPushButton#cancelProcessButton {
                    background-color: #95A5A6;
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton#cancelProcessButton:hover {
                    background-color: #7F8C8D;
                }
                QPushButton#cancelProcessButton:pressed {
                    background-color: #6C7B7D;
                }
            """)
        else:
            dialog.setStyleSheet("""
                QDialog#newProcessDialog {
                    background-color: #ECF0F1;
                }
                QLabel {
                    color: #2C3E50;
                    font-weight: bold;
                }
                QLineEdit#processNameInput, QLineEdit#modelInput {
                    padding: 10px;
                    border: 2px solid #BDC3C7;
                    border-radius: 6px;
                    background-color: #FFFFFF;
                    font-size: 12px;
                }
                QLineEdit#processNameInput:focus, QLineEdit#modelInput:focus {
                    border: 2px solid #3498DB;
                }
                QLineEdit#pdfFolderInput {
                    padding: 10px;
                    border: 2px solid #BDC3C7;
                    border-radius: 6px;
                    background-color: #F8F9FA;
                    font-size: 12px;
                    color: #7F8C8D;
                }
                QTextEdit#instructionInput {
                    padding: 10px;
                    border: 2px solid #BDC3C7;
                    border-radius: 6px;
                    background-color: #FFFFFF;
                    font-size: 12px;
                }
                QTextEdit#instructionInput:focus {
                    border: 2px solid #3498DB;
                }
                QPushButton#browseButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton#browseButton:hover {
                    background-color: #2980B9;
                }
                QPushButton#browseButton:pressed {
                    background-color: #21618C;
                }
                QPushButton#createProcessButton {
                    background-color: #2ECC71;
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton#createProcessButton:hover {
                    background-color: #27AE60;
                }
                QPushButton#createProcessButton:pressed {
                    background-color: #219653;
                }
                QPushButton#cancelProcessButton {
                    background-color: #95A5A6;
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton#cancelProcessButton:hover {
                    background-color: #7F8C8D;
                }
                QPushButton#cancelProcessButton:pressed {
                    background-color: #6C7B7D;
                }
            """)

        dialog.exec()

    def select_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            line_edit.setText(folder)

    def start_new_process(self, name, instruction, pdf_folder, model_name, dialog):
        if not name or not instruction or not pdf_folder:
            QMessageBox.warning(self, "Error", "All fields are required!")
            return

        if not model_name:
            QMessageBox.warning(self, "Error", "Model name is required!")
            return

        if not os.path.exists(pdf_folder):
            QMessageBox.warning(self, "Error", "PDF folder does not exist!")
            return

        process_id = f"process_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create output folder
        default_output = self.settings.get('default_output_folder', os.getcwd())
        output_folder = os.path.join(default_output, name)

        try:
            os.makedirs(output_folder, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create output folder: {str(e)}")
            return

        process_data = {
            'id': process_id,
            'name': name,
            'instruction': instruction,
            'pdf_folder': pdf_folder,
            'output_folder': output_folder,
            'model_name': model_name,
            'folder_id': self.current_folder,
            'status': 'pending',
            'current': 0,
            'total': 0,
            'progress': 0,
            'created_at': datetime.now().isoformat()
        }

        self.processes[process_id] = process_data
        self.process_logs[process_id] = []

        if process_data.get('folder_id', 'root') == self.current_folder:
            self.add_process_widget(process_data)

        self.save_processes_state()

        # Start worker
        QTimer.singleShot(100, lambda: self.start_worker(process_id))

        dialog.accept()

    def add_process_widget(self, process_data):
        widget = ProcessWidget(process_data, self, self.theme)

        # Connect signals
        widget.pause_clicked.connect(self.pause_process)
        widget.resume_clicked.connect(self.resume_process)
        widget.cancel_clicked.connect(self.cancel_process)
        widget.delete_clicked.connect(self.delete_process)
        widget.open_folder_clicked.connect(self.open_output_folder)
        widget.view_logs_clicked.connect(self.view_logs)

        self.process_layout.insertWidget(self.process_layout.count() - 1, widget)
        self.process_widgets[process_data['id']] = widget

    def start_worker(self, process_id):
        if process_id in self.workers and self.workers[process_id].isRunning():
            return

        if process_id not in self.processes:
            return

        worker = ProcessWorker(self.processes[process_id], self.settings)
        worker.progress_updated.connect(self.on_progress_updated)
        worker.status_changed.connect(self.on_status_changed)
        worker.finished.connect(self.on_process_finished)
        worker.log_message.connect(self.on_log_message)

        self.workers[process_id] = worker
        worker.start()

    def pause_process(self, process_id):
        if process_id in self.workers:
            self.workers[process_id].pause()
            self.on_status_changed(process_id, 'paused')
            widget = self.process_widgets.get(process_id)
            if widget:
                widget.pause_btn.hide()
                widget.resume_btn.show()

    def resume_process(self, process_id):
        if process_id in self.workers:
            self.workers[process_id].resume()
            self.on_status_changed(process_id, 'running')
            widget = self.process_widgets.get(process_id)
            if widget:
                widget.resume_btn.hide()
                widget.pause_btn.show()

    def cancel_process(self, process_id):
        reply = QMessageBox.question(self, "Confirm Cancel",
                                     "Are you sure you want to cancel this process?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if process_id in self.workers:
                self.workers[process_id].cancel()

    def delete_process(self, process_id):
        self.delete_process_internal(process_id, skip_confirmation=False)

    def delete_process_internal(self, process_id, skip_confirmation=False):
        if process_id not in self.processes:
            return

        process_name = self.processes[process_id]['name']
        output_folder = self.processes[process_id]['output_folder']

        # Check if process is running
        is_running = process_id in self.workers and self.workers[process_id].isRunning()

        if is_running and not skip_confirmation:
            QMessageBox.warning(self, "Error", "Cannot delete a running process. Please cancel it first.")
            return

        if not skip_confirmation:
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete process '{process_name}'?\n\n"
                "This will permanently delete:\n"
                f"- The process from the dashboard\n"
                f"- All output files in: {output_folder}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

        # Cancel worker if running
        if process_id in self.workers:
            self.workers[process_id].cancel()
            self.workers[process_id].wait(2000)  # Wait up to 2 seconds
            if self.workers[process_id].isRunning():
                self.workers[process_id].terminate()
            del self.workers[process_id]

        # Delete output folder
        if os.path.exists(output_folder):
            try:
                shutil.rmtree(output_folder)
            except Exception as e:
                if not skip_confirmation:
                    QMessageBox.warning(self, "Warning", f"Failed to delete output folder: {str(e)}")

        # Remove from UI
        if process_id in self.process_widgets:
            widget = self.process_widgets[process_id]
            self.process_layout.removeWidget(widget)
            widget.deleteLater()
            del self.process_widgets[process_id]

        # Remove from data
        if process_id in self.process_logs:
            del self.process_logs[process_id]

        del self.processes[process_id]
        self.save_processes_state()

        if not skip_confirmation:
            QMessageBox.information(self, "Success", f"Process '{process_name}' deleted successfully!")

    def open_output_folder(self, process_id):
        folder = self.processes[process_id]['output_folder']
        if os.path.exists(folder):
            if sys.platform == 'win32':
                os.startfile(folder)
            elif sys.platform == 'darwin':
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')
        else:
            QMessageBox.warning(self, "Error", "Output folder does not exist yet.")

    def view_logs(self, process_id):
        logs = self.process_logs.get(process_id, [])
        log_text = "\n".join(logs) if logs else "No logs available yet."

        dialog = QDialog(self)
        dialog.setWindowTitle(f"📋 Logs - {self.processes[process_id]['name']}")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)
        dialog.setObjectName("logDialog")

        layout = QVBoxLayout()

        log_display = QTextEdit()
        log_display.setReadOnly(True)
        log_display.setPlainText(log_text)
        log_display.setObjectName("logDisplay")

        close_btn = QPushButton("Close")
        close_btn.setObjectName("closeLogButton")
        close_btn.clicked.connect(dialog.accept)

        layout.addWidget(log_display)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)

        # Apply theme to log dialog
        if self.theme == 'dark':
            dialog.setStyleSheet("""
                QDialog#logDialog {
                    background-color: #2C3E50;
                }
                QTextEdit#logDisplay {
                    background-color: #1C2833;
                    color: #ECF0F1;
                    font-family: 'Courier New', monospace;
                    font-size: 11px;
                    padding: 10px;
                    border: 2px solid #34495E;
                    border-radius: 6px;
                }
                QPushButton#closeLogButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton#closeLogButton:hover {
                    background-color: #2980B9;
                }
                QPushButton#closeLogButton:pressed {
                    background-color: #21618C;
                }
            """)
        else:
            dialog.setStyleSheet("""
                QDialog#logDialog {
                    background-color: #ECF0F1;
                }
                QTextEdit#logDisplay {
                    background-color: #2C3E50;
                    color: #ECF0F1;
                    font-family: 'Courier New', monospace;
                    font-size: 11px;
                    padding: 10px;
                    border: 2px solid #34495E;
                    border-radius: 6px;
                }
                QPushButton#closeLogButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton#closeLogButton:hover {
                    background-color: #2980B9;
                }
                QPushButton#closeLogButton:pressed {
                    background-color: #21618C;
                }
            """)

        dialog.exec()

    def on_progress_updated(self, process_id, current, total):
        if process_id in self.process_widgets:
            # Force immediate UI update
            widget = self.process_widgets[process_id]
            widget.update_progress(current, total)
            widget.repaint()  # Force widget repaint
            QApplication.processEvents()  # Process pending events

        if process_id in self.processes:
            self.processes[process_id]['current'] = current
            self.processes[process_id]['total'] = total
            self.save_processes_state()

    def on_status_changed(self, process_id, status):
        if process_id in self.process_widgets:
            self.process_widgets[process_id].update_status(status)

        if process_id in self.processes:
            self.processes[process_id]['status'] = status
            self.save_processes_state()

    def on_log_message(self, process_id, message):
        if process_id not in self.process_logs:
            self.process_logs[process_id] = []
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.process_logs[process_id].append(f"[{timestamp}] {message}")

    def on_process_finished(self, process_id, success, message):
        if process_id in self.workers:
            self.workers[process_id].wait()  # Wait for thread to finish
            del self.workers[process_id]

        status = 'completed' if success else 'failed'
        self.on_status_changed(process_id, status)
        self.on_log_message(process_id, message)

        if process_id in self.processes:
            msg_type = QMessageBox.Icon.Information if success else QMessageBox.Icon.Warning
            msg = QMessageBox(self)
            msg.setIcon(msg_type)
            msg.setWindowTitle("Process Finished")
            msg.setText(f"{self.processes[process_id]['name']}\n\n{message}")
            msg.exec()

    def update_statistics(self):
        # Only count processes in current folder
        current_processes = [p for p in self.processes.values()
                             if p.get('folder_id', 'root') == self.current_folder]

        total = len(current_processes)
        completed = sum(1 for p in current_processes if p['status'] == 'completed')
        failed = sum(1 for p in current_processes if p['status'] == 'failed')
        running = sum(1 for p in current_processes if p['status'] == 'running')

        self.total_label.setText(f"📋 Total: {total}")
        self.completed_label.setText(f"✅ Completed: {completed}")
        self.failed_label.setText(f"❌ Failed: {failed}")
        self.running_label.setText(f"⚡ Running: {running}")

    def open_settings(self):
        dialog = SettingsDialog(self, self.theme)
        if dialog.exec():
            self.settings = dialog.get_settings()
            # Update theme if changed
            new_theme = 'dark' if self.settings.get('theme', 'Light Theme') == 'Dark Theme' else 'light'
            if new_theme != self.theme:
                self.theme = new_theme
                self.apply_theme()
                # Update all existing process widgets
                for widget in self.process_widgets.values():
                    widget.set_theme(self.theme)

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
        return {}

    def save_processes_state(self):
        try:
            with open(self.processes_file, 'w') as f:
                json.dump(self.processes, f, indent=2)
        except Exception as e:
            print(f"Error saving processes: {e}")

    def load_processes_state(self):
        try:
            if os.path.exists(self.processes_file):
                with open(self.processes_file, 'r') as f:
                    self.processes = json.load(f)

                    for process_data in self.processes.values():
                        if process_data['id'] not in self.process_logs:
                            self.process_logs[process_data['id']] = []
        except Exception as e:
            print(f"Error loading processes: {e}")

    def save_folders_state(self):
        try:
            with open(self.folders_file, 'w') as f:
                json.dump(self.folders, f, indent=2)
        except Exception as e:
            print(f"Error saving folders: {e}")

    def load_folders_state(self):
        try:
            if os.path.exists(self.folders_file):
                with open(self.folders_file, 'r') as f:
                    self.folders = json.load(f)
        except Exception as e:
            print(f"Error loading folders: {e}")

    def resume_processes(self):
        """Resume incomplete processes on startup"""
        for process_id, process_data in self.processes.items():
            if process_data['status'] in ['pending', 'running', 'paused']:
                self.start_worker(process_id)

    def closeEvent(self, event):
        """Save state and cleanup before closing"""
        # Cancel all running workers
        for process_id, worker in list(self.workers.items()):
            if worker.isRunning():
                worker.cancel()
                worker.wait(2000)  # Wait up to 2 seconds
                if worker.isRunning():
                    worker.terminate()

        self.save_processes_state()
        self.save_folders_state()
        event.accept()


def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Apply default palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(44, 62, 80))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(236, 240, 241))
    palette.setColor(QPalette.ColorRole.Base, QColor(52, 73, 94))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(44, 62, 80))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(44, 62, 80))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(236, 240, 241))
    palette.setColor(QPalette.ColorRole.Text, QColor(236, 240, 241))
    palette.setColor(QPalette.ColorRole.Button, QColor(52, 152, 219))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Link, QColor(41, 128, 185))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(52, 152, 219))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()