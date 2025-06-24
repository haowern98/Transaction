"""
Zoom buttons widget for the zoom folder structure
Integrates with the zoom manager and provides visible UI controls
"""
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel, 
                            QComboBox, QApplication, QSizePolicy, QShortcut)
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence


class ZoomButtonsWidget(QWidget):
    """Zoom buttons widget that integrates with the zoom system"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Get zoom manager
        from . import get_zoom_manager
        self.zoom_manager = get_zoom_manager()
        
        # Configuration
        from core.config import get_config
        self.config = get_config()
        
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()
        self.update_display()
        
        # Scale zoom controls to current zoom level
        current_zoom = 100
        if self.zoom_manager:
            current_zoom = self.zoom_manager.get_current_zoom()
        else:
            # Try to get from simple zoom system
            try:
                from .simple_zoom_fallback import get_simple_zoom
                simple_zoom = get_simple_zoom()
                current_zoom = simple_zoom.get_current_zoom()
            except:
                pass
        
        # Apply initial scaling
        self._scale_zoom_controls(current_zoom)
        self.update_display_for_zoom(current_zoom)
    
    def setup_ui(self):
        """Setup the zoom buttons UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)  # Increased margins
        layout.setSpacing(6)  # Increased spacing
        
        # Zoom label - larger and more visible
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #333;")
        layout.addWidget(zoom_label)
        
        # Zoom out button - larger
        self.zoom_out_btn = QPushButton("−")  # Use proper minus symbol
        self.zoom_out_btn.setFixedSize(35, 28)  # Increased size
        self.zoom_out_btn.setToolTip("Zoom Out (Ctrl+-)")
        self.zoom_out_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 16px;
                border: 1px solid #999;
                border-radius: 3px;
                background-color: #f0f0f0;
                color: #333;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #666;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        layout.addWidget(self.zoom_out_btn)
        
        # Zoom level display/selector - larger
        self.zoom_combo = QComboBox()
        self.zoom_combo.setFixedSize(80, 28)  # Increased size
        self.zoom_combo.setToolTip("Select zoom level")
        
        # Populate zoom levels from config
        for level in self.config.ZOOM_LEVELS:
            self.zoom_combo.addItem(f"{level}%", level)
        
        self.zoom_combo.setStyleSheet("""
            QComboBox {
                font-size: 11px;
                font-weight: bold;
                border: 1px solid #999;
                border-radius: 3px;
                background-color: white;
                padding: 2px 6px;
                color: #333;
            }
            QComboBox:hover {
                border-color: #666;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
                margin-right: 3px;
            }
        """)
        layout.addWidget(self.zoom_combo)
        
        # Zoom in button - larger
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(35, 28)  # Increased size
        self.zoom_in_btn.setToolTip("Zoom In (Ctrl++)")
        self.zoom_in_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 16px;
                border: 1px solid #999;
                border-radius: 3px;
                background-color: #f0f0f0;
                color: #333;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #666;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        layout.addWidget(self.zoom_in_btn)
        
        # Reset button - larger
        self.reset_btn = QPushButton("100%")
        self.reset_btn.setFixedSize(45, 28)  # Increased size
        self.reset_btn.setToolTip("Reset Zoom (Ctrl+0)")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                font-size: 9px;
                font-weight: bold;
                border: 1px solid #999;
                border-radius: 3px;
                background-color: #f8f8f8;
                color: #666;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
                color: #333;
                border-color: #666;
            }
        """)
        layout.addWidget(self.reset_btn)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Make the zoom controls participate in zoom scaling
        self.setObjectName("ZoomControls")  # Identifier for zoom system
    
    def setup_connections(self):
        """Setup button connections"""
        # Always use the immediate zoom system for reliable functionality
        self.zoom_out_btn.clicked.connect(self.immediate_zoom_out)
        self.zoom_in_btn.clicked.connect(self.immediate_zoom_in)
        self.reset_btn.clicked.connect(self.immediate_reset)
        self.zoom_combo.currentIndexChanged.connect(self.immediate_combo_changed)
        
        # Also try to connect to zoom manager if available
        if self.zoom_manager:
            self.zoom_manager.zoom_changed.connect(self.on_zoom_changed)
    
    def immediate_zoom_in(self):
        """Immediate zoom in using simple zoom system"""
        from .simple_zoom_fallback import zoom_in_immediate
        new_zoom = zoom_in_immediate()
        self.update_display_for_zoom(new_zoom)
        self._scale_zoom_controls(new_zoom)  # Scale the controls themselves
        print(f"Zoomed in to {new_zoom}%")
    
    def immediate_zoom_out(self):
        """Immediate zoom out using simple zoom system"""
        from .simple_zoom_fallback import zoom_out_immediate
        new_zoom = zoom_out_immediate()
        self.update_display_for_zoom(new_zoom)
        self._scale_zoom_controls(new_zoom)  # Scale the controls themselves
        print(f"Zoomed out to {new_zoom}%")
    
    def immediate_reset(self):
        """Immediate reset using simple zoom system"""
        from .simple_zoom_fallback import reset_zoom_immediate
        new_zoom = reset_zoom_immediate()
        self.update_display_for_zoom(new_zoom)
        self._scale_zoom_controls(new_zoom)  # Scale the controls themselves
        print(f"Zoom reset to {new_zoom}%")
    
    def immediate_combo_changed(self, index):
        """Immediate combo change using simple zoom system"""
        if index >= 0:
            zoom_level = self.zoom_combo.itemData(index)
            if zoom_level:
                from .simple_zoom_fallback import apply_immediate_zoom
                apply_immediate_zoom(zoom_level)
                self._scale_zoom_controls(zoom_level)  # Scale the controls themselves
                print(f"Zoom set to {zoom_level}%")
    
    def _scale_zoom_controls(self, zoom_level):
        """Scale the zoom controls themselves based on zoom level"""
        scale_factor = zoom_level / 100.0
        
        # Base sizes
        base_button_width = 35
        base_button_height = 28
        base_combo_width = 80
        base_combo_height = 28
        base_reset_width = 45
        
        # Calculate scaled sizes
        button_width = max(25, int(base_button_width * scale_factor))
        button_height = max(20, int(base_button_height * scale_factor))
        combo_width = max(60, int(base_combo_width * scale_factor))
        combo_height = max(20, int(base_combo_height * scale_factor))
        reset_width = max(35, int(base_reset_width * scale_factor))
        
        # Apply scaled sizes
        self.zoom_out_btn.setFixedSize(button_width, button_height)
        self.zoom_in_btn.setFixedSize(button_width, button_height)
        self.zoom_combo.setFixedSize(combo_width, combo_height)
        self.reset_btn.setFixedSize(reset_width, combo_height)
        
        # Scale font sizes in styles
        button_font_size = max(12, int(16 * scale_factor))
        combo_font_size = max(9, int(11 * scale_factor))
        label_font_size = max(9, int(11 * scale_factor))
        reset_font_size = max(8, int(9 * scale_factor))
        
        # Update button styles with scaled fonts
        button_style = f"""
            QPushButton {{
                font-weight: bold;
                font-size: {button_font_size}px;
                border: 1px solid #999;
                border-radius: 3px;
                background-color: #f0f0f0;
                color: #333;
            }}
            QPushButton:hover {{
                background-color: #e0e0e0;
                border-color: #666;
            }}
            QPushButton:pressed {{
                background-color: #d0d0d0;
            }}
        """
        
        combo_style = f"""
            QComboBox {{
                font-size: {combo_font_size}px;
                font-weight: bold;
                border: 1px solid #999;
                border-radius: 3px;
                background-color: white;
                padding: 2px 6px;
                color: #333;
            }}
            QComboBox:hover {{
                border-color: #666;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
                margin-right: 3px;
            }}
        """
        
        reset_style = f"""
            QPushButton {{
                font-size: {reset_font_size}px;
                font-weight: bold;
                border: 1px solid #999;
                border-radius: 3px;
                background-color: #f8f8f8;
                color: #666;
            }}
            QPushButton:hover {{
                background-color: #e8e8e8;
                color: #333;
                border-color: #666;
            }}
        """
        
        # Apply the scaled styles
        self.zoom_out_btn.setStyleSheet(button_style)
        self.zoom_in_btn.setStyleSheet(button_style)
        self.zoom_combo.setStyleSheet(combo_style)
        self.reset_btn.setStyleSheet(reset_style)
        
        # Scale the zoom label
        zoom_labels = self.findChildren(QLabel)
        for label in zoom_labels:
            if label.text() == "Zoom:":
                label.setStyleSheet(f"font-size: {label_font_size}px; font-weight: bold; color: #333;")
                break
    
    def update_display_for_zoom(self, zoom_level):
        """Update display for a specific zoom level"""
        # Update combo box selection
        for i in range(self.zoom_combo.count()):
            if self.zoom_combo.itemData(i) == zoom_level:
                self.zoom_combo.blockSignals(True)
                self.zoom_combo.setCurrentIndex(i)
                self.zoom_combo.blockSignals(False)
                break
        
        # Update button states
        self.zoom_out_btn.setEnabled(zoom_level > 50)
        self.zoom_in_btn.setEnabled(zoom_level < 300)
        self.reset_btn.setEnabled(zoom_level != 100)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Use immediate zoom for keyboard shortcuts too
        self.shortcuts = []
        
        zoom_in_shortcut = QShortcut(QKeySequence("Ctrl++"), self)
        zoom_in_shortcut.activated.connect(self.immediate_zoom_in)
        self.shortcuts.append(zoom_in_shortcut)
        
        zoom_in_shortcut2 = QShortcut(QKeySequence("Ctrl+="), self)
        zoom_in_shortcut2.activated.connect(self.immediate_zoom_in)
        self.shortcuts.append(zoom_in_shortcut2)
        
        zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        zoom_out_shortcut.activated.connect(self.immediate_zoom_out)
        self.shortcuts.append(zoom_out_shortcut)
        
        reset_shortcut = QShortcut(QKeySequence("Ctrl+0"), self)
        reset_shortcut.activated.connect(self.immediate_reset)
        self.shortcuts.append(reset_shortcut)
    
    def on_combo_changed(self, index):
        """Handle combo box selection"""
        if index >= 0 and self.zoom_manager:
            zoom_level = self.zoom_combo.itemData(index)
            if zoom_level:
                self.zoom_manager.set_zoom_level(zoom_level)
    
    def on_zoom_changed(self, zoom_level):
        """Handle zoom level changes from zoom manager"""
        self.update_display()
        self.update_button_states()
    
    def update_display(self):
        """Update the combo box display"""
        if self.zoom_manager:
            current_zoom = self.zoom_manager.get_current_zoom()
        else:
            current_zoom = 100
            
        # Update combo box selection
        for i in range(self.zoom_combo.count()):
            if self.zoom_combo.itemData(i) == current_zoom:
                self.zoom_combo.blockSignals(True)
                self.zoom_combo.setCurrentIndex(i)
                self.zoom_combo.blockSignals(False)
                break
    
    def update_button_states(self):
        """Update button enabled states"""
        if self.zoom_manager:
            current_zoom = self.zoom_manager.get_current_zoom()
            self.zoom_out_btn.setEnabled(current_zoom > self.config.MIN_ZOOM_LEVEL)
            self.zoom_in_btn.setEnabled(current_zoom < self.config.MAX_ZOOM_LEVEL)
            self.reset_btn.setEnabled(current_zoom != self.config.DEFAULT_ZOOM_LEVEL)
        else:
            # Simple fallback
            self.zoom_out_btn.setEnabled(True)
            self.zoom_in_btn.setEnabled(True)
            self.reset_btn.setEnabled(True)
    
    # Fallback methods if zoom manager is not available
    def simple_zoom_in(self):
        """Simple zoom in without zoom manager"""
        self.simple_apply_zoom(110)  # Increase by 10%
        
    def simple_zoom_out(self):
        """Simple zoom out without zoom manager"""
        self.simple_apply_zoom(90)   # Decrease by 10%
    
    def simple_reset(self):
        """Simple reset without zoom manager"""
        self.simple_apply_zoom(100)
    
    def simple_combo_changed(self, index):
        """Simple combo change without zoom manager"""
        if index >= 0:
            zoom_level = self.zoom_combo.itemData(index)
            if zoom_level:
                self.simple_apply_zoom(zoom_level)
    
    def simple_apply_zoom(self, zoom_percent):
        """Apply simple zoom to all widgets"""
        app = QApplication.instance()
        if not app:
            return
        
        # Store original fonts if this is the first time
        if not hasattr(self, '_original_fonts'):
            self._original_fonts = {}
        
        # If zoom is 100%, restore all original fonts
        if zoom_percent == 100:
            for widget in app.allWidgets():
                try:
                    if widget in self._original_fonts:
                        widget.setFont(QFont(self._original_fonts[widget]))
                except:
                    continue
            print(f"Fonts restored to original (100%)")
            return
        
        scale_factor = zoom_percent / 100.0
        
        for widget in app.allWidgets():
            try:
                # Store original font if not stored yet
                if widget not in self._original_fonts:
                    self._original_fonts[widget] = QFont(widget.font())
                
                # Get original font
                original_font = self._original_fonts[widget]
                original_size = original_font.pointSize()
                if original_size <= 0:
                    original_size = 9  # Default
                
                # Calculate new size based on original
                new_size = max(6, int(original_size * scale_factor))
                
                # Create scaled font preserving all properties
                scaled_font = QFont(original_font)
                scaled_font.setPointSize(new_size)
                
                widget.setFont(scaled_font)
                
            except:
                continue
        
        print(f"Simple zoom applied: {zoom_percent}%")


class ZoomButtonsInjector:
    """Handles injection of zoom buttons into the main window"""
    
    @staticmethod
    def inject_into_transaction_window(window):
        """
        Inject zoom buttons into the Transaction Matcher window
        
        Args:
            window: TransactionMatcherWindow instance
            
        Returns:
            bool: True if successful
        """
        try:
            # Create zoom buttons widget
            zoom_buttons = ZoomButtonsWidget(window)
            
            # Try to inject into the File Processing tab
            if ZoomButtonsInjector._inject_into_file_processing_tab(window, zoom_buttons):
                print("✓ Zoom buttons added to File Processing tab!")
                return True
            
            # Fallback: try status bar
            if ZoomButtonsInjector._inject_into_status_bar(window, zoom_buttons):
                print("✓ Zoom buttons added to status bar!")
                return True
            
            print("✗ Could not find suitable location for zoom buttons")
            return False
            
        except Exception as e:
            print(f"✗ Failed to inject zoom buttons: {e}")
            return False
    
    @staticmethod
    def _inject_into_file_processing_tab(window, zoom_buttons):
        """Try to inject into File Processing tab"""
        try:
            # Find the tab widget
            tab_widget = getattr(window, 'tab_widget', None)
            if not tab_widget:
                return False
            
            # Get the File Processing tab (first tab)
            file_tab = tab_widget.widget(0)
            if not file_tab:
                return False
            
            # Get the tab's layout
            tab_layout = file_tab.layout()
            if not tab_layout:
                return False
            
            # Find the file group box (should be first item)
            file_group_item = tab_layout.itemAt(0)
            if not file_group_item:
                return False
            
            file_group = file_group_item.widget()
            if not file_group:
                return False
            
            # Get the file group's layout
            file_layout = file_group.layout()
            if not file_layout:
                return False
            
            # Create a layout for zoom buttons
            from PyQt5.QtWidgets import QHBoxLayout, QSpacerItem
            zoom_layout = QHBoxLayout()
            zoom_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
            zoom_layout.addWidget(zoom_buttons)
            
            # Add to the file group layout
            file_layout.addLayout(zoom_layout)
            
            return True
            
        except Exception as e:
            print(f"File tab injection failed: {e}")
            return False
    
    @staticmethod
    def _inject_into_status_bar(window, zoom_buttons):
        """Try to inject into status bar"""
        try:
            status_bar = getattr(window, 'status_bar', None)
            if status_bar:
                status_bar.addPermanentWidget(zoom_buttons)
                return True
            return False
        except Exception as e:
            print(f"Status bar injection failed: {e}")
            return False


def add_zoom_buttons_to_window(window):
    """
    Main function to add zoom buttons to the transaction window
    
    Args:
        window: TransactionMatcherWindow instance
        
    Returns:
        bool: True if successful
    """
    print("Adding zoom buttons to Transaction Matcher...")
    
    # Initialize zoom system first
    from . import get_zoom_manager
    zoom_manager = get_zoom_manager()
    
    if zoom_manager:
        print("✓ Zoom manager available")
    else:
        print("⚠ Zoom manager not available, using simple zoom")
    
    # Inject zoom buttons
    success = ZoomButtonsInjector.inject_into_transaction_window(window)
    
    if success:
        print("✓ Zoom buttons ready! Use [-] [100%] [+] or Ctrl++/Ctrl+-/Ctrl+0")
    
    return success


# Make this available for import
__all__ = ['ZoomButtonsWidget', 'ZoomButtonsInjector', 'add_zoom_buttons_to_window']