from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QProgressBar, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ProcessWidget(QFrame):
    """Widget representing a single process in the list"""

    pause_clicked = pyqtSignal(str)
    resume_clicked = pyqtSignal(str)
    cancel_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)
    open_folder_clicked = pyqtSignal(str)
    view_logs_clicked = pyqtSignal(str)

    def __init__(self, process_data, parent=None, theme='light'):
        super().__init__(parent)
        self.process_data = process_data
        self.process_id = process_data['id']
        self.theme = theme
        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header with name and status
        header_layout = QHBoxLayout()

        name_label = QLabel(self.process_data['name'])
        name_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name_label.setObjectName("processName")

        self.status_label = QLabel(self.process_data['status'].upper())
        self.update_status_style(self.process_data['status'])

        header_layout.addWidget(name_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)

        # Progress bar and text
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(5)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(self.process_data.get('progress', 0))

        self.progress_text = QLabel(f"{self.process_data.get('current', 0)}/{self.process_data.get('total', 0)} files")
        self.progress_text.setObjectName("progressText")

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_text)

        # Model info
        model_name = self.process_data.get('model_name', 'N/A')
        model_label = QLabel(f"Model: {model_name}")
        model_label.setObjectName("modelLabel")

        # Instruction preview
        instruction_preview = self.process_data['instruction'][:80]
        if len(self.process_data['instruction']) > 80:
            instruction_preview += "..."
        instruction_label = QLabel(f"Instruction: {instruction_preview}")
        instruction_label.setWordWrap(True)
        instruction_label.setObjectName("instructionLabel")

        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(6)

        self.pause_btn = QPushButton("⏸ Pause")
        self.resume_btn = QPushButton("▶ Resume")
        self.cancel_btn = QPushButton("⏹ Cancel")
        self.delete_btn = QPushButton("🗑 Delete")
        self.open_folder_btn = QPushButton("📂 Open Folder")
        self.view_logs_btn = QPushButton("📋 View Logs")

        self.pause_btn.setObjectName("pauseButton")
        self.resume_btn.setObjectName("resumeButton")
        self.cancel_btn.setObjectName("cancelButton")
        self.delete_btn.setObjectName("deleteButton")
        self.open_folder_btn.setObjectName("openFolderButton")
        self.view_logs_btn.setObjectName("viewLogsButton")

        self.pause_btn.clicked.connect(lambda: self.pause_clicked.emit(self.process_id))
        self.resume_btn.clicked.connect(lambda: self.resume_clicked.emit(self.process_id))
        self.cancel_btn.clicked.connect(lambda: self.cancel_clicked.emit(self.process_id))
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.process_id))
        self.open_folder_btn.clicked.connect(lambda: self.open_folder_clicked.emit(self.process_id))
        self.view_logs_btn.clicked.connect(lambda: self.view_logs_clicked.emit(self.process_id))

        self.resume_btn.hide()

        button_layout.addWidget(self.pause_btn)
        button_layout.addWidget(self.resume_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.open_folder_btn)
        button_layout.addWidget(self.view_logs_btn)
        button_layout.addStretch()

        # Add all to main layout
        layout.addLayout(header_layout)
        layout.addLayout(progress_layout)
        layout.addWidget(model_label)
        layout.addWidget(instruction_label)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def apply_theme(self):
        if self.theme == 'dark':
            self.setStyleSheet("""
                ProcessWidget {
                    border: 2px solid #5D6D7E;
                    border-radius: 8px;
                    background: linear-gradient(to bottom, #34495E, #2C3E50);
                    margin: 8px;
                    padding: 2px;
                }
                ProcessWidget:hover {
                    border: 2px solid #3498DB;
                    background: linear-gradient(to bottom, #4A6278, #34495E);
                }
                QLabel#processName {
                    color: #ECF0F1;
                }
                QLabel#progressText {
                    color: #BDC3C7;
                    font-size: 10px;
                    font-weight: bold;
                }
                QLabel#modelLabel {
                    color: #BDC3C7;
                    font-size: 9px;
                    font-weight: bold;
                    padding: 2px;
                }
                QLabel#instructionLabel {
                    color: #AEB6BF;
                    font-size: 10px;
                    background-color: #2C3E50;
                    padding: 6px;
                    border-radius: 4px;
                    border-left: 3px solid #3498DB;
                }
                QProgressBar {
                    border: 1px solid #5D6D7E;
                    border-radius: 6px;
                    text-align: center;
                    background-color: #2C3E50;
                    height: 20px;
                }
                QProgressBar::chunk {
                    border-radius: 5px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #3498DB, stop:1 #2ECC71);
                }
                QPushButton {
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 10px;
                    min-width: 80px;
                }
                QPushButton#pauseButton {
                    background-color: #F39C12;
                    color: white;
                }
                QPushButton#pauseButton:hover {
                    background-color: #E67E22;
                }
                QPushButton#pauseButton:pressed {
                    background-color: #D35400;
                }
                QPushButton#resumeButton {
                    background-color: #2ECC71;
                    color: white;
                }
                QPushButton#resumeButton:hover {
                    background-color: #27AE60;
                }
                QPushButton#resumeButton:pressed {
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
                QPushButton#deleteButton {
                    background-color: #C0392B;
                    color: white;
                }
                QPushButton#deleteButton:hover {
                    background-color: #A93226;
                }
                QPushButton#deleteButton:pressed {
                    background-color: #922B21;
                }
                QPushButton#openFolderButton {
                    background-color: #3498DB;
                    color: white;
                }
                QPushButton#openFolderButton:hover {
                    background-color: #2980B9;
                }
                QPushButton#openFolderButton:pressed {
                    background-color: #21618C;
                }
                QPushButton#viewLogsButton {
                    background-color: #9B59B6;
                    color: white;
                }
                QPushButton#viewLogsButton:hover {
                    background-color: #8E44AD;
                }
                QPushButton#viewLogsButton:pressed {
                    background-color: #7D3C98;
                }
            """)
        else:
            self.setStyleSheet("""
                ProcessWidget {
                    border: 2px solid #BDC3C7;
                    border-radius: 8px;
                    background: linear-gradient(to bottom, #FFFFFF, #F8F9FA);
                    margin: 8px;
                    padding: 2px;
                }
                ProcessWidget:hover {
                    border: 2px solid #3498DB;
                    background: linear-gradient(to bottom, #FFFFFF, #E8F4FC);
                }
                QLabel#processName {
                    color: #2C3E50;
                }
                QLabel#progressText {
                    color: #7F8C8D;
                    font-size: 10px;
                    font-weight: bold;
                }
                QLabel#modelLabel {
                    color: #34495E;
                    font-size: 9px;
                    font-weight: bold;
                    padding: 2px;
                }
                QLabel#instructionLabel {
                    color: #5D6D7E;
                    font-size: 10px;
                    background-color: #F2F4F4;
                    padding: 6px;
                    border-radius: 4px;
                    border-left: 3px solid #3498DB;
                }
                QProgressBar {
                    border: 1px solid #BDC3C7;
                    border-radius: 6px;
                    text-align: center;
                    background-color: #ECF0F1;
                    height: 20px;
                }
                QProgressBar::chunk {
                    border-radius: 5px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #3498DB, stop:1 #2ECC71);
                }
                QPushButton {
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 10px;
                    min-width: 80px;
                }
                QPushButton#pauseButton {
                    background-color: #F39C12;
                    color: white;
                }
                QPushButton#pauseButton:hover {
                    background-color: #E67E22;
                }
                QPushButton#pauseButton:pressed {
                    background-color: #D35400;
                }
                QPushButton#resumeButton {
                    background-color: #2ECC71;
                    color: white;
                }
                QPushButton#resumeButton:hover {
                    background-color: #27AE60;
                }
                QPushButton#resumeButton:pressed {
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
                QPushButton#deleteButton {
                    background-color: #C0392B;
                    color: white;
                }
                QPushButton#deleteButton:hover {
                    background-color: #A93226;
                }
                QPushButton#deleteButton:pressed {
                    background-color: #922B21;
                }
                QPushButton#openFolderButton {
                    background-color: #3498DB;
                    color: white;
                }
                QPushButton#openFolderButton:hover {
                    background-color: #2980B9;
                }
                QPushButton#openFolderButton:pressed {
                    background-color: #21618C;
                }
                QPushButton#viewLogsButton {
                    background-color: #9B59B6;
                    color: white;
                }
                QPushButton#viewLogsButton:hover {
                    background-color: #8E44AD;
                }
                QPushButton#viewLogsButton:pressed {
                    background-color: #7D3C98;
                }
            """)

    def update_status_style(self, status):
        if self.theme == 'dark':
            styles = {
                'pending': """
                    QLabel {
                        color: #F39C12;
                        font-weight: bold;
                        padding: 4px 8px;
                        background-color: #2C3E50;
                        border-radius: 4px;
                        border: 1px solid #F1C40F;
                    }
                """,
                'running': """
                    QLabel {
                        color: #3498DB;
                        font-weight: bold;
                        padding: 4px 8px;
                        background-color: #2C3E50;
                        border-radius: 4px;
                        border: 1px solid #5DADE2;
                    }
                """,
                'completed': """
                    QLabel {
                        color: #27AE60;
                        font-weight: bold;
                        padding: 4px 8px;
                        background-color: #2C3E50;
                        border-radius: 4px;
                        border: 1px solid #58D68D;
                    }
                """,
                'failed': """
                    QLabel {
                        color: #E74C3C;
                        font-weight: bold;
                        padding: 4px 8px;
                        background-color: #2C3E50;
                        border-radius: 4px;
                        border: 1px solid #F1948A;
                    }
                """,
                'cancelled': """
                    QLabel {
                        color: #95A5A6;
                        font-weight: bold;
                        padding: 4px 8px;
                        background-color: #2C3E50;
                        border-radius: 4px;
                        border: 1px solid #BDC3C7;
                    }
                """,
                'paused': """
                    QLabel {
                        color: #8E44AD;
                        font-weight: bold;
                        padding: 4px 8px;
                        background-color: #2C3E50;
                        border-radius: 4px;
                        border: 1px solid #BB8FCE;
                    }
                """
            }
        else:
            styles = {
                'pending': """
                    QLabel {
                        color: #F39C12;
                        font-weight: bold;
                        padding: 4px 8px;
                        background-color: #FEF9E7;
                        border-radius: 4px;
                        border: 1px solid #F1C40F;
                    }
                """,
                'running': """
                    QLabel {
                        color: #3498DB;
                        font-weight: bold;
                        padding: 4px 8px;
                        background-color: #EBF5FB;
                        border-radius: 4px;
                        border: 1px solid #5DADE2;
                    }
                """,
                'completed': """
                    QLabel {
                        color: #27AE60;
                        font-weight: bold;
                        padding: 4px 8px;
                        background-color: #EAFAF1;
                        border-radius: 4px;
                        border: 1px solid #58D68D;
                    }
                """,
                'failed': """
                    QLabel {
                        color: #E74C3C;
                        font-weight: bold;
                        padding: 4px 8px;
                        background-color: #FDEDEC;
                        border-radius: 4px;
                        border: 1px solid #F1948A;
                    }
                """,
                'cancelled': """
                    QLabel {
                        color: #95A5A6;
                        font-weight: bold;
                        padding: 4px 8px;
                        background-color: #F4F6F6;
                        border-radius: 4px;
                        border: 1px solid #BDC3C7;
                    }
                """,
                'paused': """
                    QLabel {
                        color: #8E44AD;
                        font-weight: bold;
                        padding: 4px 8px;
                        background-color: #F4ECF7;
                        border-radius: 4px;
                        border: 1px solid #BB8FCE;
                    }
                """
            }
        self.status_label.setStyleSheet(styles.get(status, ''))

    def update_status(self, status):
        self.process_data['status'] = status
        self.status_label.setText(status.upper())
        self.update_status_style(status)

    def update_progress(self, current, total):
        self.process_data['current'] = current
        self.process_data['total'] = total
        progress_percent = int((current / total) * 100) if total > 0 else 0
        self.process_data['progress'] = progress_percent
        self.progress_bar.setValue(progress_percent)
        self.progress_text.setText(f"{current}/{total} files")

    def set_theme(self, theme):
        self.theme = theme
        self.apply_theme()
        self.update_status_style(self.process_data['status'])