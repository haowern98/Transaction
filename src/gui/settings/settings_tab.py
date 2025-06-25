"""
Complete settings tab with VS Code-style General subtab
Updated with proper tab sizing to match parent tabs
File: src/gui/settings/settings_tab.py
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
        # NO CUSTOM STYLING - use default Qt styling to match main tabs
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
                background-color: #ffffff;
                border: none;
                padding: 0px;
            }
        """)
        action_frame.setFixedHeight(80)  # Taller for proper vertical centering
        
        layout = QHBoxLayout(action_frame)
        layout.setContentsMargins(20, 20, 20, 20)  # More reasonable margins
        
        # Center horizontally
        layout.addStretch()
        
        # Reset to Defaults button - DEFAULT STYLING
        self.reset_btn = QPushButton("Reset to Defaults")
        # NO setStyleSheet calls - use default appearance
        self.reset_btn.setToolTip("Reset all settings to default values")
        layout.addWidget(self.reset_btn)
        
        # Spacing between buttons
        layout.addSpacing(10)
        
        # Save Settings button - DEFAULT STYLING  
        self.save_btn = QPushButton("Save Settings")
        # NO setStyleSheet calls - use default appearance
        self.save_btn.setToolTip("Save current settings")
        layout.addWidget(self.save_btn)
        
        # Center horizontally
        layout.addStretch()
        
        return action_frame
    
    def _get_file_processing_button_style(self):
        """Get default QPushButton style - NO custom styling to match File Processing exactly"""
        return """
            QPushButton {
                /* Use default system button styling - minimal changes */
                font-family: "Arial";
                border: none;
                background: none;
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
            lambda: print("✓ Settings saved successfully")
        )
        self.settings_manager.settings_loaded.connect(
            lambda: print("✓ Settings loaded successfully")
        )
    
    def save_settings(self):
        """Save all current settings"""
        try:
            # Settings are saved automatically by individual controls
            # This just ensures everything is persisted
            success = self.settings_manager.save_settings()
            
            if success:
                print("✓ Settings saved successfully")
                self.settings_applied.emit()
            else:
                print("✗ Failed to save settings")
                
        except Exception as e:
            print(f"✗ Error saving settings: {e}")
    
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
            try:
                self.settings_manager.reset_to_defaults()
                
                # Reload settings in the general panel
                if hasattr(self, 'general_panel'):
                    self.general_panel.load_settings()
                
                print("✓ All settings reset to defaults")
                self.settings_reset.emit()
                
            except Exception as e:
                print(f"✗ Failed to reset settings: {e}")
    
    def on_zoom_changed(self, zoom_level):
        """Handle zoom level changes"""
        print(f"✓ Zoom level changed to {zoom_level}%")
    
    def on_setting_changed(self, setting_key, value):
        """Handle individual setting changes"""
        # Settings are automatically saved by the settings manager
        # This is just for status updates
        pass
    
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