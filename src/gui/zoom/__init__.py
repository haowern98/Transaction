"""
Zoom module initialization and global setup
Provides centralized zoom functionality for the entire application without modifying existing files
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QFont

# Global zoom manager instance
_global_zoom_manager = None
_zoom_initialized = False


def initialize_zoom_system():
    """
    Initialize the global zoom system after QApplication is created.
    This is called from within the GUI application.
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    global _global_zoom_manager, _zoom_initialized
    
    if _zoom_initialized:
        return True
    
    # Check if QApplication exists
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()
    if not app:
        print("Warning: Cannot initialize zoom system - no QApplication found")
        return False
        
    try:
        print("Initializing zoom system...")
        
        # Import zoom components (lazy import to avoid circular dependencies)
        from .zoom_manager import ZoomManager
        from .widget_scanner import WidgetScanner
        
        # Create global zoom manager
        _global_zoom_manager = ZoomManager()
        
        # Load zoom settings from config
        _global_zoom_manager.load_zoom_settings()
        
        # Install Qt application hooks for automatic widget detection
        install_application_hooks()
        
        # Set up global keyboard shortcuts (but not UI controls)
        install_global_shortcuts()
        
        # NOTE: We'll use zoom_buttons.py for UI controls instead of zoom_controls.py
        # This avoids duplicate controls
        
        _zoom_initialized = True
        print("Zoom system initialized successfully!")
        return True
        
    except Exception as e:
        print(f"Warning: Failed to initialize zoom system: {e}")
        return False


def get_zoom_manager():
    """
    Get the global zoom manager instance
    
    Returns:
        ZoomManager: The global zoom manager, or None if not initialized
    """
    global _global_zoom_manager
    return _global_zoom_manager


def install_application_hooks():
    """Install Qt application-level hooks for automatic widget discovery"""
    app = QApplication.instance()
    if not app:
        return
        
    try:
        # Install event filter for widget creation monitoring
        from .widget_scanner import create_widget_monitor
        widget_monitor = create_widget_monitor()
        app.installEventFilter(widget_monitor)
        
        # Connect to application focus changes to detect new windows
        app.focusChanged.connect(on_focus_changed)
        
    except Exception as e:
        print(f"Warning: Failed to install application hooks: {e}")


def install_global_shortcuts():
    """Install global keyboard shortcuts for zoom functionality"""
    try:
        # Use simplified keyboard shortcuts without UI injection
        from PyQt5.QtWidgets import QShortcut, QApplication
        from PyQt5.QtGui import QKeySequence
        
        app = QApplication.instance()
        if not app or not _global_zoom_manager:
            return
            
        # Create shortcuts directly
        zoom_in_shortcut1 = QShortcut(QKeySequence("Ctrl++"), app)
        zoom_in_shortcut1.activated.connect(_global_zoom_manager.zoom_in)
        
        zoom_in_shortcut2 = QShortcut(QKeySequence("Ctrl+="), app)
        zoom_in_shortcut2.activated.connect(_global_zoom_manager.zoom_in)
        
        zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+-"), app)
        zoom_out_shortcut.activated.connect(_global_zoom_manager.zoom_out)
        
        reset_shortcut = QShortcut(QKeySequence("Ctrl+0"), app)
        reset_shortcut.activated.connect(_global_zoom_manager.reset_zoom)
        
        print("✓ Keyboard shortcuts installed!")
        
    except Exception as e:
        print(f"Warning: Failed to install global shortcuts: {e}")


def on_focus_changed(old_widget, new_widget):
    """
    Handle application focus changes to detect new windows/dialogs
    
    Args:
        old_widget: Previously focused widget
        new_widget: Newly focused widget
    """
    if new_widget and _global_zoom_manager:
        try:
            # Check if this is a new window that needs zoom injection
            from .zoom_controls import check_and_inject_zoom_controls
            check_and_inject_zoom_controls(new_widget)
            
            # Apply current zoom to the new widget
            _global_zoom_manager.apply_zoom_to_widget(new_widget)
            
        except Exception as e:
            # Silently handle errors to avoid disrupting normal operation
            pass


def inject_zoom_controls_to_main_window():
    """
    Inject zoom controls into the main application window
    This is called after the main window is created
    """
    if not _global_zoom_manager:
        return False
        
    try:
        from .zoom_controls import ZoomControlsInjector
        injector = ZoomControlsInjector()
        return injector.inject_into_main_window()
    except Exception as e:
        print(f"Warning: Failed to inject zoom controls: {e}")
        return False


def cleanup_zoom_system():
    """Clean up zoom system resources when application exits"""
    global _global_zoom_manager, _zoom_initialized
    
    if _global_zoom_manager:
        try:
            _global_zoom_manager.save_zoom_settings()
            _global_zoom_manager.cleanup()
        except Exception as e:
            print(f"Warning: Error during zoom system cleanup: {e}")
        finally:
            _global_zoom_manager = None
            _zoom_initialized = False


# Module exports for external use
__all__ = [
    'initialize_zoom_system',
    'get_zoom_manager', 
    'inject_zoom_controls_to_main_window',
    'add_zoom_buttons_to_main_window',
    'cleanup_zoom_system'
]


def add_zoom_buttons_to_main_window():
    """
    Add zoom buttons to the main window
    This is a simplified interface for external use
    """
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if not app:
            return False
        
        # Find main window
        for widget in app.allWidgets():
            if hasattr(widget, 'tab_widget') and 'transaction' in widget.windowTitle().lower():
                from .zoom_buttons import add_zoom_buttons_to_window
                return add_zoom_buttons_to_window(widget)
        
        return False
    except Exception as e:
        print(f"Error adding zoom buttons: {e}")
        return False


# Auto-cleanup on module unload
import atexit
atexit.register(cleanup_zoom_system)