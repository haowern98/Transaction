"""
Zoom UI controls and keyboard shortcuts
Provides zoom controls injection, keyboard shortcuts, and user interface for zoom functionality
"""

from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                            QComboBox, QLabel, QApplication, QMainWindow,
                            QToolBar, QStatusBar, QShortcut, QSizePolicy,
                            QFrame, QSpacerItem)
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QSize
from PyQt5.QtGui import QKeySequence, QFont, QIcon, QPalette


class ZoomControlWidget(QWidget):
    """
    Compact zoom control widget with zoom in/out buttons and level display
    """
    
    # Signals
    zoom_in_requested = pyqtSignal()
    zoom_out_requested = pyqtSignal()
    zoom_level_requested = pyqtSignal(int)
    reset_zoom_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Get zoom manager for current state
        from . import get_zoom_manager
        self.zoom_manager = get_zoom_manager()
        
        # UI setup
        self.setup_ui()
        self.setup_connections()
        self.update_display()
        
        # Connect to zoom manager if available
        if self.zoom_manager:
            self.zoom_manager.zoom_changed.connect(self.on_zoom_changed)
    
    def setup_ui(self):
        """Setup the zoom control UI components"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Zoom out button
        self.zoom_out_btn = QPushButton("🔍-")
        self.zoom_out_btn.setToolTip("Zoom Out (Ctrl+-)")
        self.zoom_out_btn.setFixedSize(30, 24)
        self.zoom_out_btn.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.zoom_out_btn)
        
        # Zoom level dropdown
        self.zoom_combo = QComboBox()
        self.zoom_combo.setToolTip("Select zoom level")
        self.zoom_combo.setFixedSize(60, 24)
        self.zoom_combo.setEditable(False)
        self.zoom_combo.setFocusPolicy(Qt.NoFocus)
        
        # Populate zoom levels
        from core.config import get_config
        config = get_config()
        for level in config.ZOOM_LEVELS:
            self.zoom_combo.addItem(f"{level}%", level)
        
        layout.addWidget(self.zoom_combo)
        
        # Zoom in button
        self.zoom_in_btn = QPushButton("🔍+")
        self.zoom_in_btn.setToolTip("Zoom In (Ctrl++)")
        self.zoom_in_btn.setFixedSize(30, 24)
        self.zoom_in_btn.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.zoom_in_btn)
        
        # Optional reset button (hidden by default)
        self.reset_btn = QPushButton("⚬")
        self.reset_btn.setToolTip("Reset Zoom (Ctrl+0)")
        self.reset_btn.setFixedSize(20, 24)
        self.reset_btn.setFocusPolicy(Qt.NoFocus)
        self.reset_btn.setVisible(False)  # Hidden by default
        layout.addWidget(self.reset_btn)
        
        # Style the widgets
        self.apply_widget_styling()
    
    def apply_widget_styling(self):
        """Apply consistent styling to zoom controls"""
        button_style = """
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 2px;
                background-color: #f0f0f0;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #999;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QPushButton:disabled {
                color: #999;
                background-color: #f8f8f8;
            }
        """
        
        combo_style = """
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 2px;
                background-color: white;
                font-size: 9px;
                padding: 2px;
            }
            QComboBox:hover {
                border-color: #999;
            }
            QComboBox::drop-down {
                border: none;
                width: 15px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #666;
                margin-right: 2px;
            }
        """
        
        self.zoom_out_btn.setStyleSheet(button_style)
        self.zoom_in_btn.setStyleSheet(button_style)
        self.reset_btn.setStyleSheet(button_style)
        self.zoom_combo.setStyleSheet(combo_style)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.zoom_out_btn.clicked.connect(self.zoom_out_requested.emit)
        self.zoom_in_btn.clicked.connect(self.zoom_in_requested.emit)
        self.reset_btn.clicked.connect(self.reset_zoom_requested.emit)
        self.zoom_combo.currentIndexChanged.connect(self.on_combo_changed)
    
    def on_combo_changed(self, index):
        """Handle zoom combo selection"""
        if index >= 0:
            zoom_level = self.zoom_combo.itemData(index)
            if zoom_level:
                self.zoom_level_requested.emit(zoom_level)
    
    def on_zoom_changed(self, zoom_level: int):
        """Handle zoom level changes from zoom manager"""
        self.update_display()
        self.update_button_states()
    
    def update_display(self):
        """Update the displayed zoom level"""
        if self.zoom_manager:
            current_zoom = self.zoom_manager.get_current_zoom()
            
            # Update combo box selection
            for i in range(self.zoom_combo.count()):
                if self.zoom_combo.itemData(i) == current_zoom:
                    self.zoom_combo.blockSignals(True)
                    self.zoom_combo.setCurrentIndex(i)
                    self.zoom_combo.blockSignals(False)
                    break
    
    def update_button_states(self):
        """Update button enabled states based on zoom limits"""
        if not self.zoom_manager:
            return
            
        current_zoom = self.zoom_manager.get_current_zoom()
        from core.config import get_config
        config = get_config()
        
        # Update button states
        self.zoom_out_btn.setEnabled(current_zoom > config.MIN_ZOOM_LEVEL)
        self.zoom_in_btn.setEnabled(current_zoom < config.MAX_ZOOM_LEVEL)
        self.reset_btn.setEnabled(current_zoom != config.DEFAULT_ZOOM_LEVEL)
    
    def set_show_reset_button(self, show: bool):
        """Show or hide the reset button"""
        self.reset_btn.setVisible(show)
    
    def set_compact_mode(self, compact: bool):
        """Toggle compact mode (smaller buttons)"""
        if compact:
            button_size = QSize(25, 20)
            combo_size = QSize(50, 20)
        else:
            button_size = QSize(30, 24)
            combo_size = QSize(60, 24)
            
        self.zoom_out_btn.setFixedSize(button_size)
        self.zoom_in_btn.setFixedSize(button_size)
        self.zoom_combo.setFixedSize(combo_size)
        self.reset_btn.setFixedSize(QSize(18, 20) if compact else QSize(20, 24))


class ZoomControlsInjector(QObject):
    """
    Injects zoom controls into existing UI without modifying original files
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Track injected controls
        self.injected_controls = []
        self.main_window_controls = None
        
        # Get zoom manager
        from . import get_zoom_manager
        self.zoom_manager = get_zoom_manager()
    
    def inject_into_main_window(self) -> bool:
        """
        Inject zoom controls into the main application window
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            main_window = self.find_main_window()
            if not main_window:
                return False
            
            # Try different injection strategies
            success = (self.inject_into_toolbar(main_window) or
                      self.inject_into_status_bar(main_window) or
                      self.inject_into_layout(main_window))
            
            if success:
                self.setup_zoom_connections()
            
            return success
            
        except Exception as e:
            print(f"Warning: Failed to inject zoom controls: {e}")
            return False
    
    def find_main_window(self) -> Optional[QMainWindow]:
        """
        Find the main application window
        
        Returns:
            QMainWindow or None: Main window if found
        """
        app = QApplication.instance()
        if not app:
            return None
            
        # Look for QMainWindow instances
        for widget in app.allWidgets():
            if isinstance(widget, QMainWindow) and widget.isVisible():
                # Check if it looks like our main window
                if hasattr(widget, 'tab_widget') or 'transaction' in widget.windowTitle().lower():
                    return widget
                    
        # Fallback: return first visible main window
        for widget in app.allWidgets():
            if isinstance(widget, QMainWindow) and widget.isVisible():
                return widget
                
        return None
    
    def inject_into_toolbar(self, main_window: QMainWindow) -> bool:
        """
        Inject zoom controls into existing toolbar
        
        Args:
            main_window: Main window to inject into
            
        Returns:
            bool: True if successful
        """
        try:
            # Look for existing toolbars
            toolbars = main_window.findChildren(QToolBar)
            
            # Try to find a suitable toolbar or create one
            target_toolbar = None
            if toolbars:
                target_toolbar = toolbars[0]  # Use first toolbar
            else:
                # Create a new toolbar
                target_toolbar = main_window.addToolBar("Zoom")
                target_toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            
            if target_toolbar:
                # Add separator before zoom controls
                target_toolbar.addSeparator()
                
                # Create and add zoom controls
                zoom_controls = ZoomControlWidget()
                zoom_controls.set_compact_mode(True)
                zoom_controls.set_show_reset_button(True)
                
                target_toolbar.addWidget(zoom_controls)
                
                self.main_window_controls = zoom_controls
                self.injected_controls.append(zoom_controls)
                
                return True
                
        except Exception as e:
            print(f"Warning: Toolbar injection failed: {e}")
            
        return False
    
    def inject_into_status_bar(self, main_window: QMainWindow) -> bool:
        """
        Inject zoom controls into status bar
        
        Args:
            main_window: Main window to inject into
            
        Returns:
            bool: True if successful
        """
        try:
            status_bar = main_window.statusBar()
            if not status_bar:
                return False
            
            # Create zoom controls
            zoom_controls = ZoomControlWidget()
            zoom_controls.set_compact_mode(True)
            
            # Add to status bar (permanent widget, right side)
            status_bar.addPermanentWidget(zoom_controls)
            
            self.main_window_controls = zoom_controls
            self.injected_controls.append(zoom_controls)
            
            return True
            
        except Exception as e:
            print(f"Warning: Status bar injection failed: {e}")
            
        return False
    
    def inject_into_layout(self, main_window: QMainWindow) -> bool:
        """
        Inject zoom controls into main window layout
        
        Args:
            main_window: Main window to inject into
            
        Returns:
            bool: True if successful
        """
        try:
            # Look for the central widget
            central_widget = main_window.centralWidget()
            if not central_widget:
                return False
            
            # Try to find a suitable layout
            layout = central_widget.layout()
            if not layout:
                return False
            
            # Create a horizontal layout for zoom controls
            zoom_layout = QHBoxLayout()
            zoom_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
            
            # Add zoom label
            zoom_label = QLabel("Zoom:")
            zoom_label.setStyleSheet("font-size: 9px; color: #666;")
            zoom_layout.addWidget(zoom_label)
            
            # Add zoom controls
            zoom_controls = ZoomControlWidget()
            zoom_controls.set_compact_mode(True)
            zoom_layout.addWidget(zoom_controls)
            
            # Add to main layout
            if hasattr(layout, 'addLayout'):
                layout.addLayout(zoom_layout)
            elif hasattr(layout, 'addWidget'):
                zoom_widget = QWidget()
                zoom_widget.setLayout(zoom_layout)
                layout.addWidget(zoom_widget)
            else:
                return False
            
            self.main_window_controls = zoom_controls
            self.injected_controls.append(zoom_controls)
            
            return True
            
        except Exception as e:
            print(f"Warning: Layout injection failed: {e}")
            
        return False
    
    def setup_zoom_connections(self):
        """Setup connections between zoom controls and zoom manager"""
        if not self.main_window_controls or not self.zoom_manager:
            return
            
        # Connect zoom control signals to zoom manager
        self.main_window_controls.zoom_in_requested.connect(self.zoom_manager.zoom_in)
        self.main_window_controls.zoom_out_requested.connect(self.zoom_manager.zoom_out)
        self.main_window_controls.zoom_level_requested.connect(self.zoom_manager.set_zoom_level)
        self.main_window_controls.reset_zoom_requested.connect(self.zoom_manager.reset_zoom)
    
    def remove_injected_controls(self):
        """Remove all injected zoom controls"""
        for control in self.injected_controls:
            try:
                if control.parent():
                    control.parent().layout().removeWidget(control)
                control.deleteLater()
            except:
                pass
                
        self.injected_controls.clear()
        self.main_window_controls = None


class GlobalZoomShortcuts(QObject):
    """
    Global keyboard shortcuts for zoom functionality
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Get zoom manager
        from . import get_zoom_manager
        self.zoom_manager = get_zoom_manager()
        
        # Shortcut objects
        self.shortcuts = []
        
        # Install shortcuts
        self.install_shortcuts()
    
    def install_shortcuts(self):
        """Install global zoom keyboard shortcuts"""
        if not self.zoom_manager:
            return
            
        app = QApplication.instance()
        if not app:
            return
        
        try:
            # Use string-based shortcuts instead of StandardKey enums
            # Zoom In: Ctrl++, Ctrl+=
            zoom_in_shortcut1 = QShortcut(QKeySequence("Ctrl++"), app)
            zoom_in_shortcut1.activated.connect(self.zoom_manager.zoom_in)
            self.shortcuts.append(zoom_in_shortcut1)
            
            zoom_in_shortcut2 = QShortcut(QKeySequence("Ctrl+="), app)
            zoom_in_shortcut2.activated.connect(self.zoom_manager.zoom_in)
            self.shortcuts.append(zoom_in_shortcut2)
            
            # Zoom Out: Ctrl+-
            zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+-"), app)
            zoom_out_shortcut.activated.connect(self.zoom_manager.zoom_out)
            self.shortcuts.append(zoom_out_shortcut)
            
            # Reset Zoom: Ctrl+0
            reset_zoom_shortcut = QShortcut(QKeySequence("Ctrl+0"), app)
            reset_zoom_shortcut.activated.connect(self.zoom_manager.reset_zoom)
            self.shortcuts.append(reset_zoom_shortcut)
            
            print("✓ Keyboard shortcuts installed successfully!")
            
        except Exception as e:
            print(f"Warning: Failed to install zoom shortcuts: {e}")
    
    def uninstall_shortcuts(self):
        """Remove all zoom shortcuts"""
        for shortcut in self.shortcuts:
            try:
                shortcut.deleteLater()
            except:
                pass
        self.shortcuts.clear()


# Global instances
_global_injector = None
_global_shortcuts = None


def check_and_inject_zoom_controls(widget: QWidget):
    """
    Check if zoom controls need to be injected for a new widget
    
    Args:
        widget: Widget to check
    """
    # Only inject into main windows
    if isinstance(widget, QMainWindow):
        global _global_injector
        if _global_injector is None:
            _global_injector = ZoomControlsInjector()
        
        _global_injector.inject_into_main_window()


def install_global_zoom_shortcuts():
    """Install global zoom keyboard shortcuts"""
    global _global_shortcuts
    if _global_shortcuts is None:
        _global_shortcuts = GlobalZoomShortcuts()


def cleanup_zoom_controls():
    """Clean up zoom controls and shortcuts"""
    global _global_injector, _global_shortcuts
    
    if _global_injector:
        _global_injector.remove_injected_controls()
        _global_injector = None
        
    if _global_shortcuts:
        _global_shortcuts.uninstall_shortcuts()
        _global_shortcuts = None


def get_zoom_controls_info() -> Dict[str, Any]:
    """
    Get information about injected zoom controls
    
    Returns:
        Dict with zoom controls information
    """
    global _global_injector, _global_shortcuts
    
    return {
        'injector_created': _global_injector is not None,
        'shortcuts_installed': _global_shortcuts is not None,
        'injected_controls_count': len(_global_injector.injected_controls) if _global_injector else 0,
        'shortcuts_count': len(_global_shortcuts.shortcuts) if _global_shortcuts else 0
    }