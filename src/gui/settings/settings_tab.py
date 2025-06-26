"""
Complete settings tab with VS Code-style General subtab and new File Paths subtab
Fixed zoom layout issues to prevent bottom action bar from being cut off
File: src/gui/settings/settings_tab.py
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QLabel, QPushButton, QMessageBox, QFileDialog, 
                            QFrame, QSizePolicy, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont


class SettingsTab(QWidget):
    """
    Complete settings tab with VS Code-style General subtab and File Paths subtab
    Fixed to handle zoom changes properly without cutting off bottom action bar
    """
    
    # Signals
    settings_applied = pyqtSignal()
    settings_reset = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Import settings components
        from .settings_manager import get_settings_manager
        
        self.settings_manager = get_settings_manager()
        
        # Layout refresh timer for zoom changes
        self.layout_refresh_timer = QTimer()
        self.layout_refresh_timer.setSingleShot(True)
        self.layout_refresh_timer.timeout.connect(self._refresh_layout)
        
        self.setup_ui()
        self.connect_signals()
        self.register_with_zoom_system()
    
    def setup_ui(self):
        """Setup the complete settings tab UI with scroll areas in individual subtabs"""
        # Main layout - NO scroll area at this level
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create settings content area with tabs - ALWAYS VISIBLE
        self.settings_tabs = QTabWidget()
        # NO CUSTOM STYLING - use default Qt styling to match main tabs
        main_layout.addWidget(self.settings_tabs)
        
        # Add General tab
        self._add_general_tab()
        
        # Add File Paths tab
        self._add_file_paths_tab()
        
        # Settings action bar at bottom - ALWAYS VISIBLE AND FIXED
        action_bar = self._create_action_bar()
        main_layout.addWidget(action_bar)
        
        # Ensure proper size policies
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.settings_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def _add_general_tab(self):
        """Add the General settings tab"""
        from .general_subtab.general_settings import GeneralSettingsPanel
        
        self.general_panel = GeneralSettingsPanel()
        self.settings_tabs.addTab(self.general_panel, "General")
    
    def _add_file_paths_tab(self):
        """Add the File Paths settings tab"""
        try:
            from .file_paths_subtab.file_paths_settings import FilePathsPanel
            
            self.file_paths_panel = FilePathsPanel()
            self.settings_tabs.addTab(self.file_paths_panel, "File Paths")
        except ImportError as e:
            print(f"Warning: Could not load File Paths tab: {e}")
            # Add a placeholder tab if import fails
            placeholder = QWidget()
            placeholder_layout = QVBoxLayout(placeholder)
            placeholder_layout.addWidget(QLabel("File Paths tab temporarily unavailable"))
            self.settings_tabs.addTab(placeholder, "File Paths")
    
    def _create_action_bar(self):
        """Create zoom-responsive bottom action bar with proper scaling"""
        # Action bar container - let it scale naturally with zoom
        action_widget = QWidget()
        action_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Main action layout with flexible margins
        layout = QHBoxLayout(action_widget)
        layout.setContentsMargins(20, 15, 20, 15)  # Reduced margins
        
        # Center horizontally with stretch
        layout.addStretch()
        
        # Reset to Defaults button - NO SIZE RESTRICTIONS for proper zoom scaling
        self.reset_btn = QPushButton("Reset to Defaults")
        # Remove all size restrictions to allow natural zoom scaling
        self.reset_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.reset_btn.setToolTip("Reset all settings to default values")
        layout.addWidget(self.reset_btn)
        
        # Spacing between buttons
        layout.addSpacing(10)
        
        # Save Settings button - NO SIZE RESTRICTIONS for proper zoom scaling  
        self.save_btn = QPushButton("Save Settings")
        # Remove all size restrictions to allow natural zoom scaling
        self.save_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.save_btn.setToolTip("Save current settings")
        layout.addWidget(self.save_btn)
        
        # Center horizontally with stretch
        layout.addStretch()
        
        return action_widget
    
    def register_with_zoom_system(self):
        """Register action buttons with zoom system for proper scaling"""
        try:
            from .zoom.zoom_system import get_zoom_system
            
            zoom_system = get_zoom_system()
            if zoom_system:
                # Register the action buttons with zoom system
                zoom_system.register_widget(self.reset_btn)
                zoom_system.register_widget(self.save_btn)
                
                # Connect to zoom changes for layout refresh
                zoom_system.zoom_changed.connect(self._on_zoom_changed)
                
                print("✓ Settings tab buttons registered with zoom system")
                
        except Exception as e:
            print(f"Warning: Could not register settings buttons with zoom system: {e}")
    
    def _on_zoom_changed(self, zoom_level):
        """Handle zoom level changes with layout refresh"""
        print(f"Settings tab: Zoom changed to {zoom_level}%")
        
        # Trigger layout refresh after a short delay
        self.layout_refresh_timer.start(100)  # 100ms delay
    
    def _refresh_layout(self):
        """Refresh layout after zoom changes"""
        try:
            # Force layout update
            self.updateGeometry()
            
            # Update all child widgets
            for child in self.findChildren(QWidget):
                child.updateGeometry()
            
            # Force repaint
            self.update()
            
            print("✓ Settings tab layout refreshed")
            
        except Exception as e:
            print(f"Warning: Layout refresh failed: {e}")
    
    def showEvent(self, event):
        """Handle show event - register widgets when shown"""
        super().showEvent(event)
        
        # Ensure buttons are registered with zoom system when tab becomes visible
        if hasattr(self, 'reset_btn') and hasattr(self, 'save_btn'):
            self.register_with_zoom_system()
    
    def resizeEvent(self, event):
        """Handle resize events to maintain proper layout"""
        super().resizeEvent(event)
        
        # Trigger layout refresh on resize
        if hasattr(self, 'layout_refresh_timer'):
            self.layout_refresh_timer.start(50)  # Short delay for resize
    
    def connect_signals(self):
        """Connect all widget signals"""
        # Action buttons
        self.save_btn.clicked.connect(self.save_settings)
        self.reset_btn.clicked.connect(self.reset_all_settings)
        
        # General panel signals
        if hasattr(self, 'general_panel'):
            self.general_panel.zoom_changed.connect(self.on_zoom_changed)
            self.general_panel.setting_changed.connect(self.on_setting_changed)
        
        # File paths panel signals
        if hasattr(self, 'file_paths_panel'):
            self.file_paths_panel.file_path_changed.connect(self.on_file_path_changed)
            self.file_paths_panel.setting_changed.connect(self.on_setting_changed)
        
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
                
                # Reload settings in all panels
                if hasattr(self, 'general_panel'):
                    self.general_panel.load_settings()
                
                if hasattr(self, 'file_paths_panel'):
                    self.file_paths_panel.load_settings()
                
                print("✓ All settings reset to defaults")
                self.settings_reset.emit()
                
                # Refresh layout after reset
                self._refresh_layout()
                
            except Exception as e:
                print(f"✗ Failed to reset settings: {e}")
    
    def on_zoom_changed(self, zoom_level):
        """Handle zoom level changes from child panels"""
        print(f"✓ Settings tab: Zoom level changed to {zoom_level}%")
        
        # Re-register buttons with zoom system when zoom changes
        self.register_with_zoom_system()
        
        # Trigger layout refresh
        self._refresh_layout()
    
    def on_setting_changed(self, setting_key, value):
        """Handle individual setting changes"""
        # Settings are automatically saved by the settings manager
        # This is just for status updates
        pass
    
    def on_file_path_changed(self, path_type, new_path):
        """Handle file path changes"""
        # File path changes are handled by the file paths panel
        print(f"File path changed: {path_type} = {new_path}")
    
    def should_auto_process(self):
        """Check if auto-processing is enabled (placeholder)"""
        return False  # Not implemented yet - will be in File Paths tab
    
    def get_processing_thresholds(self):
        """Get processing thresholds (placeholder)"""
        return {'parent_threshold': 70, 'child_threshold': 70}
    
    def force_layout_update(self):
        """Force complete layout update - useful for external calls"""
        self._refresh_layout()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'layout_refresh_timer'):
                self.layout_refresh_timer.stop()
        except:
            pass