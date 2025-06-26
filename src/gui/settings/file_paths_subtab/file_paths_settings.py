"""
File paths settings panel with VS Code-style layout and individual scroll area
Now includes both Parent-student Pair File and Fee Record File selections
File: src/gui/settings/file_paths_subtab/file_paths_settings.py
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QCheckBox, QFrame, 
                            QSizePolicy, QSpacerItem, QGroupBox, QGridLayout,
                            QLineEdit, QListWidget, QFileDialog, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import os


class FilePathsPanel(QWidget):
    """
    File paths settings panel with VS Code-style layout and individual scroll area
    Now includes both Parent-student Pair File and Fee Record File selections
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
        
        # Store file paths for both file types
        self.fee_file_path = ""           # Parent-student pair file (existing)
        self.fee_record_file_path = ""    # Fee record file (NEW)
        
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
        
        # Parent-student Pair File Selection section (existing)
        parent_student_section = self._create_parent_student_section()
        content_layout.addWidget(parent_student_section)
        
        # Add spacing between sections
        content_layout.addSpacing(24)
        
        # Fee Record File section (NEW)
        fee_record_section = self._create_fee_record_section()
        content_layout.addWidget(fee_record_section)
        
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
    
    def _create_parent_student_section(self):
        """Create the parent-student pair file selection section (existing functionality)"""
        parent_group = QGroupBox("Parent-student Pair File Selection")
        parent_layout = QVBoxLayout(parent_group)
        
        # Parent-student file row
        parent_file_layout = QHBoxLayout()
        
        # Label with system default font
        parent_label = QLabel("Parent-student Pair File:")
        parent_file_layout.addWidget(parent_label)
        
        # File path input - exactly like File Processing tab
        self.fee_file_input = QLineEdit()
        self.fee_file_input.setPlaceholderText("Select the Excel file containing parent-student pairs...")
        self.fee_file_input.textChanged.connect(self.on_fee_file_changed)
        parent_file_layout.addWidget(self.fee_file_input)
        
        # Browse button - styled to exactly match File Processing tab appearance
        self.fee_browse_btn = QPushButton("Browse...")
        self.fee_browse_btn.clicked.connect(self.browse_fee_file)
        self.fee_browse_btn.setStyleSheet(self._get_browse_button_style())
        parent_file_layout.addWidget(self.fee_browse_btn)
        
        parent_layout.addLayout(parent_file_layout)
        
        # Add some spacing below
        parent_layout.addSpacing(8)
        
        # Help text for the parent-student pair file
        help_label = QLabel("Select the Excel file that contains the parent-student matching pairs used for transaction processing.")
        help_label.setStyleSheet("color: #666666;")
        help_label.setWordWrap(True)
        parent_layout.addWidget(help_label)
        
        return parent_group
    
    def _create_fee_record_section(self):
        """Create the fee record file selection section (NEW)"""
        fee_record_group = QGroupBox("Fee Record File")
        fee_record_layout = QVBoxLayout(fee_record_group)
        
        # Fee record file row
        fee_record_file_layout = QHBoxLayout()
        
        # Label with system default font
        fee_record_label = QLabel("Fee Record File:")
        fee_record_file_layout.addWidget(fee_record_label)
        
        # File path input - exactly like File Processing tab
        self.fee_record_input = QLineEdit()
        self.fee_record_input.setPlaceholderText("Select the Excel file containing fee records...")
        self.fee_record_input.textChanged.connect(self.on_fee_record_file_changed)
        fee_record_file_layout.addWidget(self.fee_record_input)
        
        # Browse button - styled to exactly match File Processing tab appearance
        self.fee_record_browse_btn = QPushButton("Browse...")
        self.fee_record_browse_btn.clicked.connect(self.browse_fee_record_file)
        self.fee_record_browse_btn.setStyleSheet(self._get_browse_button_style())
        fee_record_file_layout.addWidget(self.fee_record_browse_btn)
        
        fee_record_layout.addLayout(fee_record_file_layout)
        
        # Add some spacing below
        fee_record_layout.addSpacing(8)
        
        # Help text for the fee record file
        help_label = QLabel("Select the Excel file that contains the fee records and transaction data.")
        help_label.setStyleSheet("color: #666666;")
        help_label.setWordWrap(True)
        fee_record_layout.addWidget(help_label)
        
        return fee_record_group
    
    def _get_browse_button_style(self):
        """Get consistent browse button styling for both sections"""
        return """
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
        """
    
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
        """Open file browser for Parent-student Pair File selection (existing)"""
        try:
            # Get starting directory (use current path if exists, otherwise default)
            start_dir = ""
            if self.fee_file_path and os.path.exists(os.path.dirname(self.fee_file_path)):
                start_dir = os.path.dirname(self.fee_file_path)
            
            # Open file dialog
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Parent-student Pair File",
                start_dir,
                "Excel Files (*.xlsx *.xls);;All Files (*)"
            )
            
            # Update input if file was selected
            if file_path:
                self.fee_file_input.setText(file_path)
                
        except Exception as e:
            print(f"Error opening file dialog: {e}")
    
    def browse_fee_record_file(self):
        """Open file browser for Fee Record File selection (NEW)"""
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
                self.fee_record_input.setText(file_path)
                
        except Exception as e:
            print(f"Error opening file dialog: {e}")
    
    def on_fee_file_changed(self, text):
        """Handle parent-student pair file path changes (existing)"""
        self.fee_file_path = text.strip()
        
        # Emit signal for file path change
        self.file_path_changed.emit("parent_student_pair", self.fee_file_path)
        
        # Auto-save the file path to settings
        self._auto_save_fee_file_path()
    
    def on_fee_record_file_changed(self, text):
        """Handle fee record file path changes (NEW)"""
        self.fee_record_file_path = text.strip()
        
        # Emit signal for file path change
        self.file_path_changed.emit("fee_record", self.fee_record_file_path)
        
        # Auto-save the file path to settings
        self._auto_save_fee_record_file_path()
    
    def _auto_save_fee_file_path(self):
        """Automatically save parent-student pair file path changes to settings"""
        try:
            if self.settings_manager:
                # Check if remember paths is enabled
                remember_paths = self.settings_manager.get_setting('files.remember_file_paths', True)
                if remember_paths:
                    # Save the parent-student pair file path
                    self.settings_manager.set_setting('files.last_fee_file', self.fee_file_path)
                    # Trigger settings save to JSON file
                    self.settings_manager.save_settings()
                    print(f"Auto-saved parent-student pair file path: {self.fee_file_path}")
                    
        except Exception as e:
            print(f"Warning: Failed to auto-save parent-student pair file path: {e}")
    
    def _auto_save_fee_record_file_path(self):
        """Automatically save fee record file path changes to settings (NEW)"""
        try:
            if self.settings_manager:
                # Check if remember paths is enabled
                remember_paths = self.settings_manager.get_setting('files.remember_file_paths', True)
                if remember_paths:
                    # Save the fee record file path
                    self.settings_manager.set_setting('files.fee_record_file', self.fee_record_file_path)
                    # Trigger settings save to JSON file
                    self.settings_manager.save_settings()
                    print(f"Auto-saved fee record file path: {self.fee_record_file_path}")
                    
        except Exception as e:
            print(f"Warning: Failed to auto-save fee record file path: {e}")
    
    def get_fee_file_path(self):
        """Get the current parent-student pair file path (existing)"""
        return self.fee_file_path
    
    def get_fee_record_file_path(self):
        """Get the current fee record file path (NEW)"""
        return self.fee_record_file_path
    
    def set_fee_file_path(self, file_path):
        """Set the parent-student pair file path programmatically (existing)"""
        self.fee_file_input.setText(file_path)
    
    def set_fee_record_file_path(self, file_path):
        """Set the fee record file path programmatically (NEW)"""
        self.fee_record_input.setText(file_path)
    
    def clear_fee_file(self):
        """Clear the parent-student pair file path (existing)"""
        self.fee_file_input.clear()
    
    def clear_fee_record_file(self):
        """Clear the fee record file path (NEW)"""
        self.fee_record_input.clear()
    
    def connect_signals(self):
        """Connect widget signals"""
        # File signals are already connected in setup_ui()
        # Additional signal connections for future widgets can go here
        pass
    
    def load_settings(self):
        """Load settings from settings manager"""
        try:
            if self.settings_manager:
                # Load file paths if remember paths is enabled
                remember_paths = self.settings_manager.get_setting('files.remember_file_paths', True)
                if remember_paths:
                    # Load parent-student pair file path (existing)
                    saved_fee_file = self.settings_manager.get_setting('files.last_fee_file', '')
                    if saved_fee_file:
                        # Use blockSignals to prevent triggering auto-save during load
                        self.fee_file_input.blockSignals(True)
                        self.set_fee_file_path(saved_fee_file)
                        self.fee_file_input.blockSignals(False)
                        print(f"Loaded parent-student pair file path: {saved_fee_file}")
                    
                    # Load fee record file path (NEW)
                    saved_fee_record_file = self.settings_manager.get_setting('files.fee_record_file', '')
                    if saved_fee_record_file:
                        # Use blockSignals to prevent triggering auto-save during load
                        self.fee_record_input.blockSignals(True)
                        self.set_fee_record_file_path(saved_fee_record_file)
                        self.fee_record_input.blockSignals(False)
                        print(f"Loaded fee record file path: {saved_fee_record_file}")
            
        except Exception as e:
            print(f"Warning: Failed to load file path settings: {e}")
    
    def save_settings(self):
        """Save current settings to settings manager"""
        try:
            if self.settings_manager:
                # Save file paths if remember paths is enabled
                remember_paths = self.settings_manager.get_setting('files.remember_file_paths', True)
                if remember_paths:
                    # Save parent-student pair file path (existing)
                    if self.fee_file_path:
                        self.settings_manager.set_setting('files.last_fee_file', self.fee_file_path)
                    
                    # Save fee record file path (NEW)
                    if self.fee_record_file_path:
                        self.settings_manager.set_setting('files.fee_record_file', self.fee_record_file_path)
                
                return self.settings_manager.save_settings()
            return True
            
        except Exception as e:
            print(f"Warning: Failed to save file path settings: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset file path settings to defaults"""
        try:
            # Clear all file inputs
            self.clear_fee_file()
            self.clear_fee_record_file()
            
            print("File path settings reset to defaults")
            
        except Exception as e:
            print(f"Warning: Failed to reset file path settings: {e}")
    
    def validate_settings(self):
        """Validate current settings"""
        # For now, all settings are valid since file paths are optional
        # Future validation could check:
        # - File existence
        # - File permissions
        # - Required vs optional paths
        return True
    
    def get_current_settings(self):
        """Get current file path settings as dictionary"""
        return {
            'parent_student_pair_file': self.fee_file_path,
            'fee_record_file': self.fee_record_file_path,
        }
    
    def set_file_path(self, path_type, file_path):
        """Set a specific file path by type"""
        if path_type == "parent_student_pair":
            self.set_fee_file_path(file_path)
        elif path_type == "fee_record":
            self.set_fee_record_file_path(file_path)
    
    def get_file_path(self, path_type):
        """Get a specific file path by type"""
        if path_type == "parent_student_pair":
            return self.get_fee_file_path()
        elif path_type == "fee_record":
            return self.get_fee_record_file_path()
        return ""