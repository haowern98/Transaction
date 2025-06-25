"""
Reusable setting section component for VS Code-style settings layout
Creates consistent section formatting like "Auto Mode Timeout" in the image
File: src/gui/settings/components/setting_section.py
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QFrame, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class SettingSection(QWidget):
    """
    Reusable setting section component that matches VS Code settings style
    Creates sections like the "Auto Mode Timeout" shown in the provided image
    """
    
    def __init__(self, title, control_widget=None, description=None, options_widget=None, parent=None):
        """
        Initialize a setting section
        
        Args:
            title (str): Section title (e.g., "Auto Mode Timeout")
            control_widget (QWidget): Main control widget (dropdown, buttons, etc.)
            description (str): Optional description text below controls
            options_widget (QWidget): Optional additional options below description
            parent (QWidget): Parent widget
        """
        super().__init__(parent)
        
        self.title = title
        self.control_widget = control_widget
        self.description = description
        self.options_widget = options_widget
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the section UI with VS Code styling"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # Section title
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Segoe UI", 15, QFont.Normal))
        title_label.setStyleSheet("color: #1f1f1f; font-weight: 400;")
        main_layout.addWidget(title_label)
        
        # Add spacing after title
        main_layout.addSpacing(4)
        
        # Main control widget
        if self.control_widget:
            main_layout.addWidget(self.control_widget)
        
        # Description text (if provided)
        if self.description:
            main_layout.addSpacing(4)
            desc_label = QLabel(self.description)
            desc_label.setFont(QFont("Segoe UI", 12))
            desc_label.setStyleSheet("color: #616161; font-weight: 400;")
            desc_label.setWordWrap(True)
            main_layout.addWidget(desc_label)
        
        # Additional options widget (if provided)
        if self.options_widget:
            main_layout.addSpacing(8)
            main_layout.addWidget(self.options_widget)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    
    def set_control_widget(self, widget):
        """Set or replace the main control widget"""
        if self.control_widget:
            # Remove existing control widget
            self.layout().removeWidget(self.control_widget)
            self.control_widget.setParent(None)
        
        self.control_widget = widget
        
        if widget:
            # Insert after title (position 2, after title and spacing)
            self.layout().insertWidget(2, widget)
    
    def set_description(self, description):
        """Set or update the description text"""
        self.description = description
        
        # Find and update existing description label
        layout = self.layout()
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QLabel) and hasattr(widget, 'wordWrap'):
                    if widget.wordWrap():  # This is likely our description label
                        widget.setText(description)
                        return
        
        # If no description label found, add one
        if description:
            desc_label = QLabel(description)
            desc_label.setFont(QFont("Segoe UI", 12))
            desc_label.setStyleSheet("color: #616161; font-weight: 400;")
            desc_label.setWordWrap(True)
            
            # Insert after control widget
            insert_pos = 3 if self.control_widget else 2
            layout.insertWidget(insert_pos, desc_label)
    
    def add_options_widget(self, widget):
        """Add an options widget below the description"""
        if self.options_widget:
            # Remove existing options widget
            self.layout().removeWidget(self.options_widget)
            self.options_widget.setParent(None)
        
        self.options_widget = widget
        
        if widget:
            # Add at the end
            self.layout().addWidget(widget)
    
    def get_title(self):
        """Get the section title"""
        return self.title
    
    def set_title(self, title):
        """Update the section title"""
        self.title = title
        
        # Find and update the title label (first QLabel)
        layout = self.layout()
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QLabel):
                    # Check if it's the title label (has the title styling)
                    if "font-weight: 400" in widget.styleSheet() and "#1f1f1f" in widget.styleSheet():
                        widget.setText(title)
                        break
    
    def set_enabled(self, enabled):
        """Enable or disable the entire section"""
        super().setEnabled(enabled)
        
        # Also enable/disable child widgets
        if self.control_widget:
            self.control_widget.setEnabled(enabled)
        if self.options_widget:
            self.options_widget.setEnabled(enabled)
    
    def set_visible(self, visible):
        """Show or hide the entire section"""
        super().setVisible(visible)


class SettingSectionGroup(QWidget):
    """
    Container for multiple SettingSection widgets with proper spacing
    Useful for organizing related settings sections
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.sections = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the group container"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(24)  # Standard spacing between sections
    
    def add_section(self, section):
        """Add a SettingSection to the group"""
        if isinstance(section, SettingSection):
            self.sections.append(section)
            self.main_layout.addWidget(section)
        else:
            raise TypeError("Only SettingSection widgets can be added to SettingSectionGroup")
    
    def remove_section(self, section):
        """Remove a SettingSection from the group"""
        if section in self.sections:
            self.sections.remove(section)
            self.main_layout.removeWidget(section)
            section.setParent(None)
    
    def get_section_by_title(self, title):
        """Get a section by its title"""
        for section in self.sections:
            if section.get_title() == title:
                return section
        return None
    
    def get_all_sections(self):
        """Get all sections in the group"""
        return self.sections.copy()
    
    def clear_sections(self):
        """Remove all sections from the group"""
        for section in self.sections.copy():
            self.remove_section(section)


# Utility functions for common setting section patterns

def create_dropdown_section(title, items, current_item=None, description=None):
    """
    Create a section with a dropdown control (like Auto Mode Timeout)
    
    Args:
        title (str): Section title
        items (list): List of items for dropdown
        current_item (str): Currently selected item
        description (str): Optional description text
    
    Returns:
        SettingSection: Configured section with dropdown
    """
    from PyQt5.QtWidgets import QComboBox
    
    # Create dropdown
    dropdown = QComboBox()
    dropdown.addItems(items)
    if current_item and current_item in items:
        dropdown.setCurrentText(current_item)
    
    # Style the dropdown
    dropdown.setStyleSheet("""
        QComboBox {
            font-family: "Segoe UI";
            font-size: 13px;
            font-weight: 400;
            border: 1px solid #cccccc;
            border-radius: 2px;
            background-color: #ffffff;
            color: #1f1f1f;
            padding: 4px 8px;
            min-height: 22px;
            min-width: 120px;
        }
        QComboBox:hover {
            border-color: #0078d4;
        }
    """)
    
    return SettingSection(title, dropdown, description)


def create_checkbox_section(title, checkbox_text, checked=False, description=None):
    """
    Create a section with a checkbox control
    
    Args:
        title (str): Section title
        checkbox_text (str): Text for the checkbox
        checked (bool): Initial checked state
        description (str): Optional description text
    
    Returns:
        SettingSection: Configured section with checkbox
    """
    from PyQt5.QtWidgets import QCheckBox
    
    # Create checkbox
    checkbox = QCheckBox(checkbox_text)
    checkbox.setChecked(checked)
    checkbox.setFont(QFont("Segoe UI", 13))
    checkbox.setStyleSheet("color: #1f1f1f;")
    
    return SettingSection(title, checkbox, description)