import os
import json
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QGroupBox, QFormLayout, 
                             QFileDialog, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt


class SettingsDialog(QDialog):
    """Settings window for API key and default folder configuration"""

    def __init__(self, parent=None, theme='light'):
        super().__init__(parent)
        self.theme = theme
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(450)
        self.settings_file = "saves/app_settings.json"
        self.settings = self.load_settings()
        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        layout = QVBoxLayout()

        # API Key Section
        api_group = QGroupBox("Hugging Face API Configuration")
        api_group.setObjectName("apiGroup")
        api_layout = QFormLayout()
        api_layout.setSpacing(15)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setText(self.settings.get('hf_api_key', ''))
        self.api_key_input.setPlaceholderText("Enter your Hugging Face API key")

        show_key_btn = QPushButton("Show")
        show_key_btn.setMaximumWidth(80)

        key_layout = QHBoxLayout()
        key_layout.addWidget(self.api_key_input)
        key_layout.addWidget(show_key_btn)

        api_layout.addRow("API Key:", key_layout)

        # Model Name
        self.model_input = QLineEdit()
        self.model_input.setText(self.settings.get('model_name', 'ServiceNow-AI/Apriel-1.6-15b-Thinker:together'))
        self.model_input.setPlaceholderText("e.g., ServiceNow-AI/Apriel-1.6-15b-Thinker:together")
        api_layout.addRow("Default Model:", self.model_input)

        api_group.setLayout(api_layout)

        # Default Folder Section
        folder_group = QGroupBox("Default Output Location")
        folder_group.setObjectName("folderGroup")
        folder_layout = QVBoxLayout()
        folder_layout.setSpacing(10)

        folder_select_layout = QHBoxLayout()
        self.folder_path_input = QLineEdit()
        self.folder_path_input.setText(self.settings.get('default_output_folder', ''))
        self.folder_path_input.setReadOnly(True)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_folder)

        folder_select_layout.addWidget(self.folder_path_input)
        folder_select_layout.addWidget(browse_btn)
        folder_layout.addLayout(folder_select_layout)

        folder_info = QLabel("This is where all process results will be saved by default.")
        folder_info.setWordWrap(True)
        folder_info.setObjectName("folderInfo")
        folder_layout.addWidget(folder_info)

        folder_group.setLayout(folder_layout)

        # Theme Section
        theme_group = QGroupBox("Appearance")
        theme_group.setObjectName("themeGroup")
        theme_layout = QHBoxLayout()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light Theme", "Dark Theme"])
        current_theme = self.settings.get('theme', 'Light Theme')
        self.theme_combo.setCurrentText(current_theme)

        theme_layout.addWidget(QLabel("Theme:"))
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()

        theme_group.setLayout(theme_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setObjectName("saveButton")
        save_btn.clicked.connect(self.save_settings)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        # Add all to main layout
        layout.addWidget(api_group)
        layout.addWidget(folder_group)
        layout.addWidget(theme_group)
        layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Connect signals
        show_key_btn.pressed.connect(lambda: self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal))
        show_key_btn.released.connect(lambda: self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password))

    def apply_theme(self):
        if self.theme == 'dark':
            self.setStyleSheet("""
                SettingsDialog {
                    background-color: #2C3E50;
                }
                QGroupBox#apiGroup, QGroupBox#folderGroup, QGroupBox#themeGroup {
                    font-weight: bold;
                    border: 2px solid #4A90E2;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 15px;
                    background-color: #34495E;
                    color: #ECF0F1;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 10px 0 10px;
                    color: #ECF0F1;
                }
                QLineEdit {
                    padding: 8px;
                    border: 1px solid #5D6D7E;
                    border-radius: 4px;
                    background-color: #2C3E50;
                    color: #ECF0F1;
                }
                QLineEdit:focus {
                    border: 2px solid #3498DB;
                    background-color: #34495E;
                }
                QLineEdit[readOnly="true"] {
                    background-color: #2C3E50;
                    color: #BDC3C7;
                }
                QPushButton {
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton#saveButton {
                    background-color: #27AE60;
                    color: white;
                }
                QPushButton#saveButton:hover {
                    background-color: #229954;
                }
                QPushButton#saveButton:pressed {
                    background-color: #1E8449;
                }
                QPushButton#cancelButton {
                    background-color: #E74C3C;
                    color: white;
                }
                QPushButton#cancelButton:hover {
                    background-color: #CB4335;
                }
                QPushButton#cancelButton:pressed {
                    background-color: #B03A2E;
                }
                QPushButton:not(#saveButton):not(#cancelButton) {
                    background-color: #7F8C8D;
                    color: white;
                }
                QPushButton:not(#saveButton):not(#cancelButton):hover {
                    background-color: #717D7E;
                }
                QPushButton:not(#saveButton):not(#cancelButton):pressed {
                    background-color: #616A6B;
                }
                QLabel#folderInfo {
                    color: #BDC3C7;
                    font-size: 10px;
                    padding: 5px;
                }
                QComboBox {
                    padding: 6px;
                    border: 1px solid #5D6D7E;
                    border-radius: 4px;
                    background-color: #2C3E50;
                    color: #ECF0F1;
                }
                QComboBox:hover {
                    border: 1px solid #3498DB;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: none;
                    border: none;
                }
            """)
        else:
            self.setStyleSheet("""
                SettingsDialog {
                    background-color: #ECF0F1;
                }
                QGroupBox#apiGroup, QGroupBox#folderGroup, QGroupBox#themeGroup {
                    font-weight: bold;
                    border: 2px solid #4A90E2;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 15px;
                    background-color: #FFFFFF;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 10px 0 10px;
                    color: #2C3E50;
                }
                QLineEdit {
                    padding: 8px;
                    border: 1px solid #BDC3C7;
                    border-radius: 4px;
                    background-color: #F8F9FA;
                }
                QLineEdit:focus {
                    border: 2px solid #3498DB;
                    background-color: #FFFFFF;
                }
                QLineEdit[readOnly="true"] {
                    background-color: #ECF0F1;
                    color: #2C3E50;
                }
                QPushButton {
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton#saveButton {
                    background-color: #2ECC71;
                    color: white;
                }
                QPushButton#saveButton:hover {
                    background-color: #27AE60;
                }
                QPushButton#saveButton:pressed {
                    background-color: #219653;
                }
                QPushButton#cancelButton {
                    background-color: #E74C3C;
                    color: white;
                }
                QPushButton#cancelButton:hover {
                    background-color: #C0392B;
                }
                QPushButton#cancelButton:pressed {
                    background-color: #A93226;
                }
                QPushButton:not(#saveButton):not(#cancelButton) {
                    background-color: #7F8C8D;
                    color: white;
                }
                QPushButton:not(#saveButton):not(#cancelButton):hover {
                    background-color: #95A5A6;
                }
                QPushButton:not(#saveButton):not(#cancelButton):pressed {
                    background-color: #6C7B7D;
                }
                QLabel#folderInfo {
                    color: #7F8C8D;
                    font-size: 10px;
                    padding: 5px;
                }
                QComboBox {
                    padding: 6px;
                    border: 1px solid #BDC3C7;
                    border-radius: 4px;
                    background-color: #F8F9FA;
                }
                QComboBox:hover {
                    border: 1px solid #3498DB;
                }
            """)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.folder_path_input.setText(folder)

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
        return {}

    def save_settings(self):
        try:
            self.settings['hf_api_key'] = self.api_key_input.text()
            self.settings['model_name'] = self.model_input.text()
            self.settings['default_output_folder'] = self.folder_path_input.text()
            self.settings['theme'] = self.theme_combo.currentText()

            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)

            QMessageBox.information(self, "Success",
                                    "Settings saved successfully!\nRestart the application for theme changes to take full effect.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def get_settings(self):
        return self.settings