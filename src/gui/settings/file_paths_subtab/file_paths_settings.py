"""
File paths settings panel with VS Code-style layout and individual scroll area
Now includes Fee Record File selection with system default fonts
File: src/gui/settings/file_paths_subtab/file_paths_settings.py
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QCheckBox, QFrame, 
                            QSizePolicy, QSpacerItem, QGroupBox, QGridLayout,
                            QLineEdit, QListWidget, QFileDialog, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class FilePathsPanel(QWidget):
    """
    File paths settings panel with VS Code-style layout and individual scroll area
    Now includes Fee Record File selection functionality
    """
    
    # Signals for future implementation
    file_path_changed = pyqtSignal(str, str)  # path_type, new_path
    setting_changed = pyqtSignal(str, object)  # setting_key, value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Get settings manager for future use
        try:
            from ..settings_manager import get_settings_manager
            self.settings_manager = get_settings_manager()
        except ImportError:
            print("Warning: Could not import settings_manager")
            self.settings_manager = None
        
        # Store file paths
        self.fee_record_file_path = ""
        
        self.setup_ui()
        self.connect_signals()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the VS Code-style file paths settings UI with individual scroll area"""
        # Main layout for the panel
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create scroll area for this panel's content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameStyle(QFrame.NoFrame)  # Remove scroll area border
        
        # FORCE WHITE BACKGROUND for scroll area
        scroll_area.setStyleSheet("QScrollArea { background-color: white; }")
        
        # Content widget inside scroll area
        content_widget = QWidget()
        content_widget.setStyleSheet("QWidget { background-color: white; }")  # Force white background
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(0)
        
        # Header section
        header_section = self._create_header_section()
        content_layout.addWidget(header_section)
        
        # Add spacing after header
        content_layout.addSpacing(40)
        
        # File Selection section
        file_selection_section = self._create_file_selection_section()
        content_layout.addWidget(file_selection_section)
        
        # Add spacing between sections
        content_layout.addSpacing(24)
        
        # Future sections placeholder
        future_section = self._create_future_sections_placeholder()
        content_layout.addWidget(future_section)
        
        # Add flexible space at bottom
        content_layout.addStretch()
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        # Ensure proper size policies
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def _create_header_section(self):
        """Create the main header section like in VS Code"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(11)
        
        # Main title - BOLD and consistent with app
        title_label = QLabel("File Paths & Processing")
        title_label.setFont(QFont("Tahoma", 12, QFont.Bold))  
        title_label.setStyleSheet("color: #1f1f1f;")
        header_layout.addWidget(title_label)
        
        # Subtitle - consistent font
        subtitle_label = QLabel("Configure file locations and processing preferences")
        subtitle_label.setFont(QFont("Tahoma", 8, QFont.Normal))  
        subtitle_label.setStyleSheet("color: #1f1f1f;")
        header_layout.addWidget(subtitle_label)
        
        return header_widget
    
    def _create_file_selection_section(self):
        """Create the file selection section with Fee Record File"""
        file_group = QGroupBox("Parent-student Pair File Selection")
        file_layout = QVBoxLayout(file_group)
        
        # Fee Record File row
        fee_layout = QHBoxLayout()
        
        # Label with system default font
        fee_label = QLabel("Fee Record File:")
        fee_layout.addWidget(fee_label)
        
        # File path input - exactly like File Processing tab
        self.fee_file_input = QLineEdit()
        self.fee_file_input.setPlaceholderText("Select the Excel file containing fee records...")
        self.fee_file_input.textChanged.connect(self.on_fee_file_changed)
        fee_layout.addWidget(self.fee_file_input)
        
        # Browse button - styled to exactly match File Processing tab appearance
        self.fee_browse_btn = QPushButton("Browse...")
        self.fee_browse_btn.clicked.connect(self.browse_fee_file)
        # Apply the same flat styling as File Processing tab with white background and slight rounding
        self.fee_browse_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #adadad;
                padding: 3px 6px;
                text-align: center;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #e5f1fb;
                border: 1px solid #0078d4;
            }
            QPushButton:pressed {
                background-color: #cce4f7;
            }
        """)
        fee_layout.addWidget(self.fee_browse_btn)
        
        file_layout.addLayout(fee_layout)
        
        # Add some spacing below
        file_layout.addSpacing(8)
        
        # Help text for the fee record file
        help_label = QLabel("Select the Excel file that contains the parent-student matching pairs used for transaction processing.")
        help_label.setStyleSheet("color: #666666;")
        help_label.setWordWrap(True)
        file_layout.addWidget(help_label)
        
        return file_group
    
    def _create_future_sections_placeholder(self):
        """Create placeholder for future file path sections"""
        future_group = QGroupBox("Additional Settings")
        future_layout = QVBoxLayout(future_group)
        
        # Placeholder message with system default font
        placeholder_label = QLabel(
            "Additional file path and processing settings will be available here.\n\n"
            "Future features may include:\n"
            "• Transaction file default directory\n"
            "• Export location preferences\n"
            "• Session management settings\n"
            "• Auto-processing options"
        )
        placeholder_label.setStyleSheet("color: #666666; padding: 20px;")
        placeholder_label.setWordWrap(True)
        future_layout.addWidget(placeholder_label)
        
        return future_group
    
    def browse_fee_file(self):
        """Open file browser for Fee Record File selection"""
        try:
            # Get starting directory (use current path if exists, otherwise default)
            start_dir = ""
            if self.fee_record_file_path and os.path.exists(os.path.dirname(self.fee_record_file_path)):
                start_dir = os.path.dirname(self.fee_record_file_path)
            
            # Open file dialog
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Fee Record File",
                start_dir,
                "Excel Files (*.xlsx *.xls);;All Files (*)"
            )
            
            # Update input if file was selected
            if file_path:
                self.fee_file_input.setText(file_path)
                
        except Exception as e:
            print(f"Error opening file dialog: {e}")
    
    def on_fee_file_changed(self, text):
        """Handle fee record file path changes"""
        self.fee_record_file_path = text.strip()
        
        # Emit signal for file path change (for future integration)
        self.file_path_changed.emit("fee_record", self.fee_record_file_path)
        
        # Auto-save the file path to settings
        self._auto_save_file_path()
        
        # TODO: Future file validation could go here
        # self._validate_fee_file(self.fee_record_file_path)
    
    def _auto_save_file_path(self):
        """Automatically save file path changes to settings"""
        try:
            if self.settings_manager:
                # Check if remember paths is enabled
                remember_paths = self.settings_manager.get_setting('files.remember_file_paths', True)
                if remember_paths:
                    # Save the fee record file path
                    self.settings_manager.set_setting('files.last_fee_file', self.fee_record_file_path)
                    # Trigger settings save to JSON file
                    self.settings_manager.save_settings()
                    print(f"Auto-saved fee record file path: {self.fee_record_file_path}")
                    
        except Exception as e:
            print(f"Warning: Failed to auto-save file path: {e}")
    
    def get_fee_record_file_path(self):
        """Get the current fee record file path"""
        return self.fee_record_file_path
    
    def set_fee_record_file_path(self, file_path):
        """Set the fee record file path programmatically"""
        self.fee_file_input.setText(file_path)
    
    def clear_fee_record_file(self):
        """Clear the fee record file path"""
        self.fee_file_input.clear()
    
    def _validate_fee_file(self, file_path):
        """Validate fee record file (placeholder for future implementation)"""
        # Future implementation could include:
        # - File existence check
        # - File format validation
        # - Visual feedback (green/red styling)
        # - Error message display
        pass
    
    def connect_signals(self):
        """Connect widget signals"""
        # Fee file signals are already connected in setup_ui()
        # Additional signal connections for future widgets can go here
        pass
    
    def load_settings(self):
        """Load settings from settings manager"""
        try:
            if self.settings_manager:
                # Load fee record file path if remember paths is enabled
                remember_paths = self.settings_manager.get_setting('files.remember_file_paths', True)
                if remember_paths:
                    saved_fee_file = self.settings_manager.get_setting('files.last_fee_file', '')
                    if saved_fee_file:
                        # Use blockSignals to prevent triggering auto-save during load
                        self.fee_file_input.blockSignals(True)
                        self.set_fee_record_file_path(saved_fee_file)
                        self.fee_file_input.blockSignals(False)
                        print(f"Loaded fee record file path: {saved_fee_file}")
            
        except Exception as e:
            print(f"Warning: Failed to load file path settings: {e}")
    
    def save_settings(self):
        """Save current settings to settings manager"""
        try:
            if self.settings_manager:
                # Save fee record file path if remember paths is enabled
                remember_paths = self.settings_manager.get_setting('files.remember_file_paths', True)
                if remember_paths and self.fee_record_file_path:
                    self.settings_manager.set_setting('files.last_fee_file', self.fee_record_file_path)
                
                return self.settings_manager.save_settings()
            return True
            
        except Exception as e:
            print(f"Warning: Failed to save file path settings: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset file path settings to defaults"""
        try:
            # Clear all file inputs
            self.clear_fee_record_file()
            
            # Reset any other future file path controls
            # self.clear_transaction_file()
            # self.clear_export_directory()
            
            print("File path settings reset to defaults")
            
        except Exception as e:
            print(f"Warning: Failed to reset file path settings: {e}")
    
    def validate_settings(self):
        """Validate current settings"""
        # For now, all settings are valid since file path is optional
        # Future validation could check:
        # - File existence
        # - File permissions
        # - Required vs optional paths
        return True
    
    def get_current_settings(self):
        """Get current file path settings as dictionary"""
        return {
            'fee_record_file': self.fee_record_file_path,
            # Future settings:
            # 'transaction_file': self.transaction_file_path,
            # 'export_directory': self.export_directory_path,
            # 'auto_process': self.auto_process_enabled,
        }
    
    def set_file_path(self, path_type, file_path):
        """Set a specific file path by type"""
        if path_type == "fee_record":
            self.set_fee_record_file_path(file_path)
        # Future path types:
        # elif path_type == "transaction":
        #     self.set_transaction_file_path(file_path)
        # elif path_type == "export_directory":
        #     self.set_export_directory_path(file_path)
    
    def get_file_path(self, path_type):
        """Get a specific file path by type"""
        if path_type == "fee_record":
            return self.get_fee_record_file_path()
        # Future path types:
        # elif path_type == "transaction":
        #     return self.get_transaction_file_path()
        # elif path_type == "export_directory":
        #     return self.get_export_directory_path()
        return ""


# Import os for file path operations
import os