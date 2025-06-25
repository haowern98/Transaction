"""
Complete settings tab with VS Code-style General subtab
Updated with proper tab sizing to match parent tabs
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QLabel, QPushButton, QMessageBox, QFileDialog, 
                            QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class SettingsTab(QWidget):
    """
    Complete settings tab with VS Code-style General subtab
    """
    
    # Signals
    settings_applied = pyqtSignal()
    settings_reset = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Import settings components
        from .settings_manager import get_settings_manager
        
        self.settings_manager = get_settings_manager()
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the complete settings tab UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create settings content area with tabs
        self.settings_tabs = QTabWidget()
        self.settings_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #f6f8fa;
                border: 1px solid #d0d7de;
                border-bottom: none;
                padding: 8px 16px;
                margin-right: 2px;
                font-size: 11px;
                font-weight: 500;
                color: #656d76;
                min-width: 60px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #24292e;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background-color: #f3f4f6;
                color: #24292e;
            }
        """)
        main_layout.addWidget(self.settings_tabs)
        
        # Add only the General tab for now
        self._add_general_tab()
        
        # Settings action bar at bottom
        action_bar = self._create_action_bar()
        main_layout.addWidget(action_bar)
    
    def _add_general_tab(self):
        """Add the General settings tab"""
        from .general_settings import GeneralSettingsPanel
        
        self.general_panel = GeneralSettingsPanel()
        self.settings_tabs.addTab(self.general_panel, "General")
    
    def _create_action_bar(self):
        """Create the bottom action bar"""
        action_frame = QFrame()
        action_frame.setStyleSheet("""
            QFrame {
                background-color: #f6f8fa;
                border-top: 1px solid #d0d7de;
                padding: 10px;
            }
        """)
        action_frame.setFixedHeight(50)
        
        layout = QHBoxLayout(action_frame)
        layout.setContentsMargins(15, 8, 15, 8)
        
        # Status label
        self.status_label = QLabel("Settings loaded successfully")
        self.status_label.setFont(QFont("Segoe UI", 8))
        self.status_label.setStyleSheet("color: #656d76;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Action buttons
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.setFixedSize(120, 28)
        self.reset_btn.setStyleSheet(self._get_secondary_button_style())
        self.reset_btn.setToolTip("Reset all settings to default values")
        layout.addWidget(self.reset_btn)
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setFixedSize(100, 28)
        self.save_btn.setStyleSheet(self._get_primary_button_style())
        self.save_btn.setToolTip("Save current settings")
        layout.addWidget(self.save_btn)
        
        return action_frame
    
    def _get_primary_button_style(self):
        """Get primary button stylesheet"""
        return """
            QPushButton {
                font-size: 9px;
                font-weight: 500;
                border: 1px solid #1f883d;
                border-radius: 6px;
                background-color: #1f883d;
                color: #ffffff;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #1a7f37;
                border-color: #1a7f37;
            }
            QPushButton:pressed {
                background-color: #166f2c;
                border-color: #166f2c;
            }
        """
    
    def _get_secondary_button_style(self):
        """Get secondary button stylesheet"""
        return """
            QPushButton {
                font-size: 9px;
                font-weight: 500;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                background-color: #f6f8fa;
                color: #24292e;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
                border-color: #afb8c1;
            }
            QPushButton:pressed {
                background-color: #edeff2;
                border-color: #8c959f;
            }
        """
    
    def connect_signals(self):
        """Connect all widget signals"""
        # Action buttons
        self.save_btn.clicked.connect(self.save_settings)
        self.reset_btn.clicked.connect(self.reset_all_settings)
        
        # General panel signals
        if hasattr(self, 'general_panel'):
            self.general_panel.zoom_changed.connect(self.on_zoom_changed)
            self.general_panel.setting_changed.connect(self.on_setting_changed)
        
        # Settings manager signals
        self.settings_manager.settings_saved.connect(
            lambda: self.update_status("Settings saved successfully")
        )
        self.settings_manager.settings_loaded.connect(
            lambda: self.update_status("Settings loaded successfully")
        )
    
    def save_settings(self):
        """Save all current settings"""
        try:
            # Settings are saved automatically by individual controls
            # This just ensures everything is persisted
            success = self.settings_manager.save_settings()
            
            if success:
                self.update_status("Settings saved successfully")
                self.settings_applied.emit()
            else:
                self.update_status("Failed to save settings", error=True)
                
        except Exception as e:
            self.update_status(f"Error saving settings: {e}", error=True)
    
    def reset_all_settings(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "This will reset ALL settings to their default values.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.settings_manager.reset_to_defaults()
            
            # Reload settings in the general panel
            if hasattr(self, 'general_panel'):
                self.general_panel.load_settings()
            
            self.update_status("All settings reset to defaults")
            self.settings_reset.emit()
    
    def on_zoom_changed(self, zoom_level):
        """Handle zoom level changes"""
        self.update_status(f"Zoom level changed to {zoom_level}%")
    
    def on_setting_changed(self, setting_key, value):
        """Handle individual setting changes"""
        # Settings are automatically saved by the settings manager
        # This is just for status updates
        pass
    
    def update_status(self, message, error=False):
        """Update status message"""
        if error:
            self.status_label.setStyleSheet("color: #cf222e; font-size: 8px;")
        else:
            self.status_label.setStyleSheet("color: #656d76; font-size: 8px;")
        
        self.status_label.setText(message)
        
        # Auto-clear status after 3 seconds
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self.status_label.setText(""))
    
    def should_auto_process(self):
        """Check if auto-processing is enabled (placeholder)"""
        return False  # Not implemented in General tab yet
    
    def get_processing_thresholds(self):
        """Get processing thresholds (placeholder)"""
        return {'parent_threshold': 70, 'child_threshold': 70}
    
    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        # Settings are loaded automatically by the general panel