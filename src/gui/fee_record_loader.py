"""
Fee Record Loader Dialog - UI for confirming and tracking fee record loading
Provides confirmation dialog, progress tracking, and error handling
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTextEdit, QProgressBar, QMessageBox,
                            QGroupBox, QCheckBox, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from typing import List, Dict, Any


class FeeRecordLoadingThread(QThread):
    """Background thread for loading data to fee record"""
    
    progress_updated = pyqtSignal(int, str)  # progress, status_message
    finished = pyqtSignal(dict)  # result dictionary
    error = pyqtSignal(str)  # error message
    
    def __init__(self, table_data, fee_record_path):
        super().__init__()
        self.table_data = table_data
        self.fee_record_path = fee_record_path
        
    def run(self):
        """Run the loading process in background"""
        try:
            from core.fee_record_manager import FeeRecordManager
            
            manager = FeeRecordManager()
            
            # Emit progress updates
            self.progress_updated.emit(10, "Validating data...")
            
            # Validate data first
            errors = manager.validate_table_data(self.table_data)
            if errors:
                self.error.emit(f"Validation failed:\n" + "\n".join(errors[:5]))
                return
            
            self.progress_updated.emit(30, "Analyzing fee record structure...")
            
            # Load data
            self.progress_updated.emit(50, "Loading data to fee record...")
            result = manager.load_table_data_to_fee_record(self.table_data, self.fee_record_path)
            
            self.progress_updated.emit(100, "Complete!")
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))


class FeeRecordLoaderDialog(QDialog):
    """Dialog for confirming and tracking fee record loading"""
    
    def __init__(self, table_data, fee_record_path, parent=None):
        super().__init__(parent)
        self.table_data = table_data
        self.fee_record_path = fee_record_path
        self.loading_thread = None
        
        self.setWindowTitle("Load to Fee Record")
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        self.preview_changes()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title and instructions
        title_label = QLabel("Load Preview Table Data to Fee Record")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        instruction_label = QLabel(
            "This will load the current preview table data into your Fee Record file.\n"
            "Please review the changes below before proceeding."
        )
        instruction_label.setWordWrap(True)
        layout.addWidget(instruction_label)
        
        # Preview section
        preview_group = QGroupBox("Preview of Changes")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setFont(QFont("Courier", 9))
        preview_layout.addWidget(self.preview_text)
        
        layout.addWidget(preview_group)
        
        # Options section
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        self.backup_checkbox = QCheckBox("Create backup of original file (recommended)")
        self.backup_checkbox.setChecked(True)
        options_layout.addWidget(self.backup_checkbox)
        
        layout.addWidget(options_group)
        
        # Progress section (initially hidden)
        self.progress_group = QGroupBox("Loading Progress")
        progress_layout = QVBoxLayout(self.progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to load...")
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(self.progress_group)
        self.progress_group.setVisible(False)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.load_btn = QPushButton("Load to Fee Record")
        self.load_btn.setDefault(True)
        self.load_btn.clicked.connect(self.start_loading)
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        button_layout.addWidget(self.load_btn)
        
        layout.addLayout(button_layout)
        
    def preview_changes(self):
        """Preview what changes will be made"""
        try:
            from core.fee_record_manager import FeeRecordManager
            
            manager = FeeRecordManager()
            preview_info = manager.preview_changes(self.table_data, self.fee_record_path)
            
            if "error" in preview_info:
                self.preview_text.setText(f"Error analyzing file: {preview_info['error']}")
                self.load_btn.setEnabled(False)
                return
            
            # Format preview text
            preview_text = f"Fee Record File: {self.fee_record_path}\n\n"
            preview_text += f"Data Summary:\n"
            preview_text += f"• Total rows to process: {preview_info.get('total_rows', 0)}\n"
            preview_text += f"• Parents affected: {len(preview_info.get('affected_parents', []))}\n"
            preview_text += f"• New months to create: {len(preview_info.get('new_months', []))}\n\n"
            
            if preview_info.get('new_months'):
                preview_text += f"New month columns will be created:\n"
                for month in preview_info['new_months']:
                    preview_text += f"• {month}\n"
                preview_text += "\n"
            
            if preview_info.get('affected_parents'):
                preview_text += f"Parents that will be updated:\n"
                for parent in preview_info['affected_parents'][:10]:  # Show first 10
                    preview_text += f"• {parent}\n"
                if len(preview_info['affected_parents']) > 10:
                    preview_text += f"• ... and {len(preview_info['affected_parents']) - 10} more\n"
            
            self.preview_text.setText(preview_text)
            
        except Exception as e:
            self.preview_text.setText(f"Error previewing changes: {str(e)}")
            self.load_btn.setEnabled(False)
            
    def start_loading(self):
        """Start the loading process"""
        # Show progress section
        self.progress_group.setVisible(True)
        self.resize(600, 600)  # Expand dialog
        
        # Disable buttons
        self.load_btn.setEnabled(False)
        self.cancel_btn.setText("Cancel Loading")
        
        # Start loading thread
        self.loading_thread = FeeRecordLoadingThread(self.table_data, self.fee_record_path)
        self.loading_thread.progress_updated.connect(self.update_progress)
        self.loading_thread.finished.connect(self.loading_finished)
        self.loading_thread.error.connect(self.loading_error)
        self.loading_thread.start()
        
    def update_progress(self, progress, status):
        """Update progress bar and status"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
        
    def loading_finished(self, result):
        """Handle successful loading completion"""
        if result.get("success"):
            stats = result.get("stats", {})
            
            success_msg = f"Successfully loaded data to fee record!\n\n"
            success_msg += f"Statistics:\n"
            success_msg += f"• Processed rows: {stats.get('processed_rows', 0)}\n"
            success_msg += f"• Updated entries: {stats.get('updated_entries', 0)}\n"
            success_msg += f"• New parents added: {stats.get('new_parents', 0)}\n"
            success_msg += f"• New months created: {stats.get('new_months_created', 0)}\n"
            
            if stats.get('errors', 0) > 0:
                success_msg += f"• Errors encountered: {stats['errors']}\n"
            
            if result.get("backup_path"):
                success_msg += f"\nBackup saved: {result['backup_path']}"
            
            QMessageBox.information(self, "Success", success_msg)
            self.accept()
        else:
            error_msg = result.get("error", "Unknown error occurred")
            QMessageBox.critical(self, "Error", f"Failed to load data:\n{error_msg}")
            self.reset_ui()
            
    def loading_error(self, error_message):
        """Handle loading errors"""
        QMessageBox.critical(self, "Error", f"Loading failed:\n{error_message}")
        self.reset_ui()
        
    def reset_ui(self):
        """Reset UI to initial state"""
        self.progress_group.setVisible(False)
        self.resize(600, 500)  # Contract dialog
        self.load_btn.setEnabled(True)
        self.cancel_btn.setText("Cancel")
        
    def closeEvent(self, event):
        """Handle dialog close event"""
        if self.loading_thread and self.loading_thread.isRunning():
            reply = QMessageBox.question(
                self, "Loading in Progress",
                "Loading is still in progress. Are you sure you want to cancel?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.loading_thread.terminate()
                self.loading_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def show_fee_record_loader(table_data: List[List[str]], fee_record_path: str, parent=None):
    """Convenience function to show fee record loader dialog"""
    dialog = FeeRecordLoaderDialog(table_data, fee_record_path, parent)
    return dialog.exec_()