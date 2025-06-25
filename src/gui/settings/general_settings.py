"""
General settings panel with VS Code-like layout
Contains zoom controls and other general application settings
REMOVED: Application Preferences section per user request
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QCheckBox, QFrame, 
                            QSizePolicy, QSpacerItem, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class GeneralSettingsPanel(QWidget):
    """
    General settings panel with VS Code-style layout
    Only includes zoom controls - Application Preferences section removed
    """
    
    # Signals
    zoom_changed = pyqtSignal(int)
    setting_changed = pyqtSignal(str, object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Get zoom system and settings
        from .zoom.zoom_system import get_zoom_system
        from .settings_manager import get_settings_manager
        
        self.zoom_system = get_zoom_system()
        self.settings_manager = get_settings_manager()
        
        self.setup_ui()
        self.connect_signals()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the zoom-only general settings UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Zoom section only - no title or subtitle
        zoom_section = self._create_zoom_section()
        main_layout.addWidget(zoom_section)
        
        # Add flexible space at bottom
        main_layout.addStretch()
    
    def _create_zoom_section(self):
        """Create the zoom controls section"""
        # Section container
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e1e4e8;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(15)
        
        # Section title
        zoom_title = QLabel("Zoom")
        zoom_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        zoom_title.setStyleSheet("color: #24292e; margin-bottom: 5px;")
        layout.addWidget(zoom_title)
        
        # Zoom controls row
        zoom_controls_layout = QHBoxLayout()
        zoom_controls_layout.setSpacing(10)
        
        # Zoom out button
        self.zoom_out_btn = QPushButton("−")
        self.zoom_out_btn.setFixedSize(32, 28)
        self.zoom_out_btn.setStyleSheet(self._get_zoom_button_style())
        self.zoom_out_btn.setToolTip("Decrease zoom level")
        zoom_controls_layout.addWidget(self.zoom_out_btn)
        
        # Zoom level dropdown
        self.zoom_combo = QComboBox()
        self.zoom_combo.setFixedWidth(80)
        self.zoom_combo.addItems([f"{level}%" for level in [50, 75, 90, 100, 110, 125, 150, 175, 200]])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.setStyleSheet(self._get_combo_style())
        zoom_controls_layout.addWidget(self.zoom_combo)
        
        # Zoom in button
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(32, 28)
        self.zoom_in_btn.setStyleSheet(self._get_zoom_button_style())
        self.zoom_in_btn.setToolTip("Increase zoom level")
        zoom_controls_layout.addWidget(self.zoom_in_btn)
        
        # Reset zoom button
        self.reset_zoom_btn = QPushButton("Reset")
        self.reset_zoom_btn.setFixedSize(50, 28)
        self.reset_zoom_btn.setStyleSheet(self._get_reset_button_style())
        self.reset_zoom_btn.setToolTip("Reset zoom to 100%")
        zoom_controls_layout.addWidget(self.reset_zoom_btn)
        
        zoom_controls_layout.addStretch()
        layout.addLayout(zoom_controls_layout)
        
        # Zoom description
        zoom_desc = QLabel("Adjust the interface size for better readability. " +
                          "Use keyboard shortcuts Ctrl+Plus/Minus or the controls above.")
        zoom_desc.setFont(QFont("Segoe UI", 8))
        zoom_desc.setStyleSheet("color: #6a737d; margin-top: 5px;")
        zoom_desc.setWordWrap(True)
        layout.addWidget(zoom_desc)
        
        # Remember zoom setting
        self.remember_zoom_cb = QCheckBox("Remember zoom level between sessions")
        self.remember_zoom_cb.setFont(QFont("Segoe UI", 9))
        self.remember_zoom_cb.setStyleSheet("color: #24292e; margin-top: 8px;")
        self.remember_zoom_cb.setChecked(True)
        layout.addWidget(self.remember_zoom_cb)
        
        return section
    
    def _get_zoom_button_style(self):
        """Get zoom button stylesheet"""
        return """
            QPushButton {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                background-color: #f6f8fa;
                color: #24292e;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
                border-color: #afb8c1;
            }
            QPushButton:pressed {
                background-color: #edeff2;
                border-color: #8c959f;
            }
            QPushButton:disabled {
                color: #8c959f;
                background-color: #f6f8fa;
                border-color: #d0d7de;
            }
        """
    
    def _get_reset_button_style(self):
        """Get reset button stylesheet"""
        return """
            QPushButton {
                font-size: 9px;
                font-weight: 500;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                background-color: #f6f8fa;
                color: #656d76;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
                border-color: #afb8c1;
                color: #24292e;
            }
        """
    
    def _get_combo_style(self):
        """Get combobox stylesheet"""
        return """
            QComboBox {
                font-size: 9px;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                background-color: #ffffff;
                color: #24292e;
                padding: 4px 8px;
            }
            QComboBox:hover {
                border-color: #afb8c1;
            }
            QComboBox::drop-down {
                border: none;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border-style: solid;
                border-width: 4px 3px 0 3px;
                border-color: #656d76 transparent transparent transparent;
                width: 0px;
                height: 0px;
            }
        """
    
    def connect_signals(self):
        """Connect all widget signals"""
        try:
            # Zoom controls
            self.zoom_out_btn.clicked.connect(self.zoom_out)
            self.zoom_in_btn.clicked.connect(self.zoom_in)
            self.reset_zoom_btn.clicked.connect(self.reset_zoom)
            self.zoom_combo.currentTextChanged.connect(self.on_zoom_combo_changed)
            
            # Settings
            self.remember_zoom_cb.toggled.connect(
                lambda checked: self.setting_changed.emit('remember_zoom', checked)
            )
            
            # Zoom system signals
            if self.zoom_system:
                self.zoom_system.zoom_changed.connect(self.on_zoom_level_changed)
            
        except Exception as e:
            print(f"Warning: Failed to connect some signals: {e}")
    
    def load_settings(self):
        """Load settings from settings manager"""
        try:
            if self.zoom_system:
                # Load zoom level
                zoom_level = self.zoom_system.get_zoom_level()
                self.zoom_combo.setCurrentText(f"{zoom_level}%")
                self.update_zoom_button_states()
            
            # Load remember zoom setting
            remember_zoom = self.settings_manager.get('ui', 'remember_zoom', True)
            self.remember_zoom_cb.setChecked(remember_zoom)
            
        except Exception as e:
            print(f"Warning: Failed to load some settings: {e}")
    
    def zoom_in(self):
        """Increase zoom level"""
        if self.zoom_system:
            new_level = self.zoom_system.calculate_next_zoom('in')
            self.zoom_system.set_zoom_level(new_level)
    
    def zoom_out(self):
        """Decrease zoom level"""
        if self.zoom_system:
            new_level = self.zoom_system.calculate_next_zoom('out')
            self.zoom_system.set_zoom_level(new_level)
    
    def reset_zoom(self):
        """Reset zoom to 100%"""
        if self.zoom_system:
            self.zoom_system.reset_zoom()
    
    def on_zoom_combo_changed(self, text):
        """Handle zoom combo box changes"""
        try:
            zoom_level = int(text.replace('%', ''))
            if self.zoom_system:
                self.zoom_system.set_zoom_level(zoom_level)
        except (ValueError, TypeError):
            pass
    
    def on_zoom_level_changed(self, new_level):
        """Handle zoom level changes from zoom system"""
        self.zoom_combo.blockSignals(True)
        self.zoom_combo.setCurrentText(f"{new_level}%")
        self.zoom_combo.blockSignals(False)
        
        self.update_zoom_button_states()
        self.zoom_changed.emit(new_level)
    
    def update_zoom_button_states(self):
        """Update zoom button enabled states"""
        if not self.zoom_system:
            return
            
        current_level = self.zoom_system.get_zoom_level()
        zoom_levels = self.zoom_system.ZOOM_LEVELS
        
        self.zoom_out_btn.setEnabled(current_level > min(zoom_levels))
        self.zoom_in_btn.setEnabled(current_level < max(zoom_levels))