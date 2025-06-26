"""
General settings panel with VS Code-style layout matching the provided image
Contains main title, subtitle, and organized sections like Auto Mode Timeout
File: src/gui/settings/general_subtab/general_settings.py
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QCheckBox, QFrame, 
                            QSizePolicy, QSpacerItem, QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class GeneralSettingsPanel(QWidget):
    """
    General settings panel with VS Code-style layout
    Matches the structure shown in the provided image
    """
    
    # Signals
    zoom_changed = pyqtSignal(int)
    setting_changed = pyqtSignal(str, object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Get zoom system and settings
        from ..zoom.zoom_system import get_zoom_system
        from ..settings_manager import get_settings_manager
        
        self.zoom_system = get_zoom_system()
        self.settings_manager = get_settings_manager()
        
        self.setup_ui()
        self.connect_signals()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the VS Code-style general settings UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(0)
        
        # Header section
        header_section = self._create_header_section()
        main_layout.addWidget(header_section)
        
        # Add spacing after header
        main_layout.addSpacing(40)
        
        # Zoom section only (in a box)
        zoom_section = self._create_zoom_section()
        main_layout.addWidget(zoom_section)
        
        # Add flexible space at bottom
        main_layout.addStretch()
    
    def _create_header_section(self):
        """Create the main header section like in VS Code"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(11)
        
        # Main title - BOLD and consistent with app
        title_label = QLabel("General Settings")
        title_label.setFont(QFont("Tahoma", 12, QFont.Bold))  
        title_label.setStyleSheet("color: #1f1f1f;")
        header_layout.addWidget(title_label)
        
        # Subtitle - consistent font
        subtitle_label = QLabel("Configure general application settings")
        subtitle_label.setFont(QFont("Tahoma", 8, QFont.Normal)) 
        subtitle_label.setStyleSheet("color: #1f1f1f;")  
        header_layout.addWidget(subtitle_label)
        
        return header_widget
    
    def _create_zoom_section(self):
        """Create the zoom section exactly like Auto Mode Timeout in your project"""
        # Use QGroupBox with QGridLayout like your Auto Mode Timeout
        zoom_group = QGroupBox("Interface Zoom")
        zoom_layout = QGridLayout(zoom_group)
        
        # Row 0: Label and dropdown (like "Auto mode timeout:")
        zoom_layout.addWidget(QLabel("Interface zoom:"), 0, 0)
        
        # Create horizontal layout for zoom controls
        zoom_controls = QWidget()
        controls_layout = QHBoxLayout(zoom_controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(4)
        
        # Zoom level dropdown
        self.zoom_combo = QComboBox()
        self.zoom_combo.setFixedWidth(120)
        self.zoom_combo.addItems([f"{level}%" for level in [50, 75, 90, 100, 110, 125, 150, 175, 200]])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.setStyleSheet(self._get_primary_combo_style())
        controls_layout.addWidget(self.zoom_combo)
        
        # Zoom adjustment buttons
        self.zoom_out_btn = QPushButton("−")
        self.zoom_out_btn.setFixedSize(28, 28)
        self.zoom_out_btn.setStyleSheet(self._get_secondary_button_style())
        self.zoom_out_btn.setToolTip("Decrease zoom level")
        controls_layout.addWidget(self.zoom_out_btn)
        
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(28, 28)
        self.zoom_in_btn.setStyleSheet(self._get_secondary_button_style())
        self.zoom_in_btn.setToolTip("Increase zoom level")
        controls_layout.addWidget(self.zoom_in_btn)
        
        # Reset button
        self.reset_zoom_btn = QPushButton("Reset")
        self.reset_zoom_btn.setFixedSize(60, 28)
        self.reset_zoom_btn.setStyleSheet(self._get_tertiary_button_style())
        self.reset_zoom_btn.setToolTip("Reset zoom to 100%")
        controls_layout.addWidget(self.reset_zoom_btn)
        
        # Add stretch to left-align controls
        controls_layout.addStretch()
        
        zoom_layout.addWidget(zoom_controls, 0, 1)
        
        # Row 1: Help text spanning both columns (like your timeout help)
        zoom_help = QLabel("Interface scaling for better readability. Use keyboard shortcuts Ctrl+Plus/Minus or controls above.")
        zoom_help.setStyleSheet("color: gray;")  # Remove fixed font-size to allow zoom scaling
        zoom_help.setWordWrap(True)
        zoom_layout.addWidget(zoom_help, 1, 0, 1, 2)
        
        # Row 2: Remember zoom checkbox
        self.remember_zoom_cb = QCheckBox("Remember zoom level between sessions")
        zoom_layout.addWidget(self.remember_zoom_cb, 2, 0, 1, 2)
        
        return zoom_group
    
    def _get_primary_combo_style(self):
        """Get primary combobox stylesheet (like the dropdown in image)"""
        return """
            QComboBox {
                font-family: "Arial";
                font-size: 13px;
                font-weight: 400;
                border: 1px solid #cccccc;
                border-radius: 2px;
                background-color: #ffffff;
                color: #1f1f1f;
                padding: 4px 8px;
                min-height: 22px;
            }
            QComboBox:hover {
                border-color: #0078d4;
            }
            QComboBox:focus {
                border-color: #0078d4;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                background: transparent;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-style: solid;
                border-width: 4px 3px 0 3px;
                border-color: #666666 transparent transparent transparent;
                width: 0px;
                height: 0px;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #cccccc;
                background-color: #ffffff;
                selection-background-color: #e5f3ff;
                selection-color: #1f1f1f;
            }
        """
    
    def _get_secondary_button_style(self):
        """Get secondary button stylesheet for zoom +/- buttons"""
        return """
            QPushButton {
                font-family: "Arial";
                font-size: 14px;
                font-weight: 500;
                border: 1px solid #cccccc;
                border-radius: 2px;
                background-color: #f3f3f3;
                color: #1f1f1f;
            }
            QPushButton:hover {
                background-color: #e5f3ff;
                border-color: #0078d4;
            }
            QPushButton:pressed {
                background-color: #cce7ff;
                border-color: #005a9e;
            }
            QPushButton:disabled {
                color: #a6a6a6;
                background-color: #f3f3f3;
                border-color: #cccccc;
            }
        """
    
    def _get_tertiary_button_style(self):
        """Get tertiary button stylesheet for reset button"""
        return """
            QPushButton {
                font-family: "Arial";
                font-size: 13px;
                font-weight: 400;
                border: 1px solid #cccccc;
                border-radius: 2px;
                background-color: #ffffff;
                color: #616161;
            }
            QPushButton:hover {
                background-color: #f3f3f3;
                color: #1f1f1f;
                border-color: #0078d4;
            }
            QPushButton:pressed {
                background-color: #e5e5e5;
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
            
            # Settings checkboxes
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
            
            # Load settings
            remember_zoom = self.settings_manager.get_setting('ui.remember_zoom', True)
            self.remember_zoom_cb.setChecked(remember_zoom)
            
        except Exception as e:
            print(f"Warning: Failed to load some settings: {e}")
    
    def zoom_in(self):
        """Increase zoom level"""
        if self.zoom_system:
            current_text = self.zoom_combo.currentText()
            current_level = int(current_text.replace('%', ''))
            levels = [50, 75, 90, 100, 110, 125, 150, 175, 200]
            
            try:
                current_index = levels.index(current_level)
                if current_index < len(levels) - 1:
                    new_level = levels[current_index + 1]
                    self.zoom_system.set_zoom_level(new_level)
            except ValueError:
                pass
    
    def zoom_out(self):
        """Decrease zoom level"""
        if self.zoom_system:
            current_text = self.zoom_combo.currentText()
            current_level = int(current_text.replace('%', ''))
            levels = [50, 75, 90, 100, 110, 125, 150, 175, 200]
            
            try:
                current_index = levels.index(current_level)
                if current_index > 0:
                    new_level = levels[current_index - 1]
                    self.zoom_system.set_zoom_level(new_level)
            except ValueError:
                pass
    
    def reset_zoom(self):
        """Reset zoom to 100%"""
        if self.zoom_system:
            self.zoom_system.set_zoom_level(100)
    
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
            
        current_text = self.zoom_combo.currentText()
        current_level = int(current_text.replace('%', ''))
        levels = [50, 75, 90, 100, 110, 125, 150, 175, 200]
        
        self.zoom_out_btn.setEnabled(current_level > min(levels))
        self.zoom_in_btn.setEnabled(current_level < max(levels))