"""
General settings panel with VS Code-like layout
Contains zoom controls and other general application settings
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QCheckBox, QFrame, 
                            QSizePolicy, QSpacerItem, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class GeneralSettingsPanel(QWidget):
    """
    General settings panel with VS Code-style layout
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
        """Setup the VS Code-style general settings UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)
        
        # Title
        title_label = QLabel("General Settings")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet("color: #333; margin-bottom: 5px;")
        main_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Configure general application settings")
        subtitle_label.setFont(QFont("Segoe UI", 9))
        subtitle_label.setStyleSheet("color: #666; margin-bottom: 15px;")
        main_layout.addWidget(subtitle_label)
        
        # Zoom Section
        main_layout.addWidget(self._create_zoom_section())
        
        # General Preferences Section
        main_layout.addWidget(self._create_preferences_section())
        
        # Add stretch to push content to top
        main_layout.addStretch()
    
    def _create_zoom_section(self):
        """Create the zoom control section"""
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
        zoom_controls_layout.setSpacing(8)
        
        # Zoom label
        zoom_label = QLabel("Zoom level:")
        zoom_label.setFont(QFont("Segoe UI", 9))
        zoom_label.setStyleSheet("color: #586069; min-width: 100px;")
        zoom_controls_layout.addWidget(zoom_label)
        
        # Zoom out button
        self.zoom_out_btn = QPushButton("−")
        self.zoom_out_btn.setFixedSize(32, 28)
        self.zoom_out_btn.setToolTip("Zoom Out (Ctrl+-)")
        self.zoom_out_btn.setStyleSheet(self._get_zoom_button_style())
        zoom_controls_layout.addWidget(self.zoom_out_btn)
        
        # Zoom dropdown
        self.zoom_combo = QComboBox()
        self.zoom_combo.setFixedSize(80, 28)
        self.zoom_combo.setToolTip("Select zoom level")
        
        # Populate zoom levels
        if self.zoom_system:
            for level in self.zoom_system.get_zoom_levels():
                self.zoom_combo.addItem(f"{level}%", level)
        
        self.zoom_combo.setStyleSheet(self._get_combo_style())
        zoom_controls_layout.addWidget(self.zoom_combo)
        
        # Zoom in button
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(32, 28)
        self.zoom_in_btn.setToolTip("Zoom In (Ctrl++)")
        self.zoom_in_btn.setStyleSheet(self._get_zoom_button_style())
        zoom_controls_layout.addWidget(self.zoom_in_btn)
        
        # Reset button
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFixedSize(60, 28)
        self.reset_btn.setToolTip("Reset to 100% (Ctrl+0)")
        self.reset_btn.setStyleSheet(self._get_reset_button_style())
        zoom_controls_layout.addWidget(self.reset_btn)
        
        # Add stretch to align left
        zoom_controls_layout.addStretch()
        
        layout.addLayout(zoom_controls_layout)
        
        # Zoom description
        zoom_desc = QLabel("Controls the zoom level of the interface. Use keyboard shortcuts Ctrl+Plus/Minus or the controls above.")
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
    
    def _create_preferences_section(self):
        """Create the general preferences section"""
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
        prefs_title = QLabel("Application Preferences")
        prefs_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        prefs_title.setStyleSheet("color: #24292e; margin-bottom: 5px;")
        layout.addWidget(prefs_title)
        
        # Tooltips checkbox
        self.tooltips_cb = QCheckBox("Show tooltips")
        self.tooltips_cb.setFont(QFont("Segoe UI", 9))
        self.tooltips_cb.setStyleSheet("color: #24292e;")
        self.tooltips_cb.setChecked(True)
        layout.addWidget(self.tooltips_cb)
        
        # Tooltips description
        tooltips_desc = QLabel("Display helpful tooltips when hovering over interface elements.")
        tooltips_desc.setFont(QFont("Segoe UI", 8))
        tooltips_desc.setStyleSheet("color: #6a737d; margin-left: 20px; margin-bottom: 10px;")
        tooltips_desc.setWordWrap(True)
        layout.addWidget(tooltips_desc)
        
        # Auto-save checkbox
        self.auto_save_cb = QCheckBox("Auto-save sessions")
        self.auto_save_cb.setFont(QFont("Segoe UI", 9))
        self.auto_save_cb.setStyleSheet("color: #24292e;")
        self.auto_save_cb.setChecked(False)
        layout.addWidget(self.auto_save_cb)
        
        # Auto-save description
        autosave_desc = QLabel("Automatically save work sessions to prevent data loss.")
        autosave_desc.setFont(QFont("Segoe UI", 8))
        autosave_desc.setStyleSheet("color: #6a737d; margin-left: 20px;")
        autosave_desc.setWordWrap(True)
        layout.addWidget(autosave_desc)
        
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
                font-weight: 500;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                background-color: #ffffff;
                padding: 4px 8px;
                color: #24292e;
            }
            QComboBox:hover {
                border-color: #afb8c1;
            }
            QComboBox:focus {
                border-color: #0969da;
                box-shadow: 0 0 0 3px rgba(9, 105, 218, 0.3);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #656d76;
                margin-right: 4px;
            }
        """
    
    def connect_signals(self):
        """Connect all widget signals"""
        if not self.zoom_system:
            return
        
        # Zoom control buttons
        self.zoom_out_btn.clicked.connect(self.zoom_system.zoom_out)
        self.zoom_in_btn.clicked.connect(self.zoom_system.zoom_in)
        self.reset_btn.clicked.connect(self.zoom_system.reset_zoom)
        
        # Zoom combo
        self.zoom_combo.currentIndexChanged.connect(self.on_combo_changed)
        
        # Zoom system signals
        self.zoom_system.zoom_changed.connect(self.on_zoom_changed)
        
        # Settings checkboxes
        self.remember_zoom_cb.toggled.connect(self.on_remember_zoom_toggled)
        self.tooltips_cb.toggled.connect(self.on_tooltips_toggled)
        self.auto_save_cb.toggled.connect(self.on_auto_save_toggled)
    
    def on_combo_changed(self, index):
        """Handle zoom combo selection"""
        if index >= 0 and self.zoom_system:
            zoom_level = self.zoom_combo.itemData(index)
            if zoom_level:
                self.zoom_system.set_zoom_level(zoom_level)
    
    def on_zoom_changed(self, zoom_level):
        """Handle zoom level changes"""
        # Update combo box
        for i in range(self.zoom_combo.count()):
            if self.zoom_combo.itemData(i) == zoom_level:
                self.zoom_combo.blockSignals(True)
                self.zoom_combo.setCurrentIndex(i)
                self.zoom_combo.blockSignals(False)
                break
        
        # Update button states
        self.update_button_states(zoom_level)
        
        # Save to settings if remember is enabled
        if self.remember_zoom_cb.isChecked():
            self.settings_manager.set_zoom_level(zoom_level)
        
        # Emit signal
        self.zoom_changed.emit(zoom_level)
    
    def update_button_states(self, zoom_level):
        """Update button enabled states"""
        if self.zoom_system:
            zoom_levels = self.zoom_system.get_zoom_levels()
            self.zoom_out_btn.setEnabled(zoom_level > min(zoom_levels))
            self.zoom_in_btn.setEnabled(zoom_level < max(zoom_levels))
            self.reset_btn.setEnabled(zoom_level != 100)
    
    def on_remember_zoom_toggled(self, checked):
        """Handle remember zoom preference change"""
        self.settings_manager.set_setting('zoom.remember_zoom_level', checked)
        self.setting_changed.emit('zoom.remember_zoom_level', checked)
    
    def on_tooltips_toggled(self, checked):
        """Handle tooltips preference change"""
        self.settings_manager.set_setting('ui.show_tooltips', checked)
        self.setting_changed.emit('ui.show_tooltips', checked)
    
    def on_auto_save_toggled(self, checked):
        """Handle auto-save preference change"""
        self.settings_manager.set_setting('ui.auto_save_sessions', checked)
        self.setting_changed.emit('ui.auto_save_sessions', checked)
    
    def load_settings(self):
        """Load settings and update UI"""
        # Load zoom settings
        zoom_settings = self.settings_manager.get_zoom_settings()
        self.remember_zoom_cb.setChecked(zoom_settings.get('remember_zoom_level', True))
        
        # Load UI settings
        ui_settings = self.settings_manager.get_setting('ui', {})
        self.tooltips_cb.setChecked(ui_settings.get('show_tooltips', True))
        self.auto_save_cb.setChecked(ui_settings.get('auto_save_sessions', False))
        
        # Load zoom level if remember is enabled
        if zoom_settings.get('remember_zoom_level', True):
            saved_zoom = zoom_settings.get('current_level', 100)
            if self.zoom_system and 50 <= saved_zoom <= 300:
                self.zoom_system.set_zoom_level(saved_zoom)
    
    def get_current_zoom_level(self):
        """Get current zoom level"""
        return self.zoom_system.get_current_zoom() if self.zoom_system else 100