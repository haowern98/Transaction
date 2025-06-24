"""
Automatic widget discovery and monitoring system
Scans the application for widgets that need zoom scaling without modifying existing code
"""

import weakref
from typing import Set, Dict, List, Optional, Any
from PyQt5.QtWidgets import (QWidget, QApplication, QMainWindow, QDialog, QMessageBox,
                            QLabel, QPushButton, QTableWidget, QLineEdit, QTextEdit,
                            QComboBox, QSpinBox, QCheckBox, QRadioButton, QGroupBox,
                            QTabWidget, QStatusBar, QMenuBar, QToolBar, QFrame,
                            QScrollArea, QSplitter, QStackedWidget)
from PyQt5.QtCore import QObject, QEvent, QTimer, pyqtSignal
from PyQt5.QtGui import QShowEvent, QHideEvent


class WidgetMonitor(QObject):
    """
    Event filter that monitors widget creation, showing, and destruction
    """
    
    # Signals
    widget_discovered = pyqtSignal(object)  # New widget found
    widget_shown = pyqtSignal(object)       # Widget became visible
    widget_hidden = pyqtSignal(object)      # Widget became hidden
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Track discovered widgets to avoid duplicates
        self._discovered_widgets = weakref.WeakSet()
        self._monitored_types = self._get_monitored_widget_types()
        
        # Performance optimization - batch processing
        self._discovery_timer = QTimer()
        self._discovery_timer.setSingleShot(True)
        self._discovery_timer.timeout.connect(self._process_discovery_queue)
        self._discovery_queue = set()
        
        # Configuration
        self.scan_delay_ms = 100  # Delay for batch processing
        self.max_scan_depth = 10  # Maximum widget hierarchy depth to scan
        
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Qt event filter to catch widget events
        
        Args:
            obj: Object receiving the event
            event: The event
            
        Returns:
            bool: False to allow event processing to continue
        """
        try:
            # Only process widget objects
            if not isinstance(obj, QWidget):
                return False
                
            event_type = event.type()
            
            # Handle show events - widget becomes visible
            if event_type == QEvent.Show:
                self._on_widget_shown(obj)
                
            # Handle hide events - widget becomes hidden
            elif event_type == QEvent.Hide:
                self._on_widget_hidden(obj)
                
            # Handle polish events - widget is fully initialized
            elif event_type == QEvent.Polish:
                self._queue_widget_for_discovery(obj)
                
            # Handle child events - new child widgets added
            elif event_type == QEvent.ChildAdded:
                child_obj = event.child()
                if isinstance(child_obj, QWidget):
                    self._queue_widget_for_discovery(child_obj)
                    
        except Exception as e:
            # Silently handle errors to avoid disrupting application
            pass
            
        # Always return False to allow normal event processing
        return False
    
    def _on_widget_shown(self, widget: QWidget):
        """
        Handle widget show event
        
        Args:
            widget: Widget that was shown
        """
        if self._should_monitor_widget(widget):
            self.widget_shown.emit(widget)
            
            # Also trigger discovery for newly shown widgets
            self._queue_widget_for_discovery(widget)
    
    def _on_widget_hidden(self, widget: QWidget):
        """
        Handle widget hide event
        
        Args:
            widget: Widget that was hidden
        """
        if widget in self._discovered_widgets:
            self.widget_hidden.emit(widget)
    
    def _queue_widget_for_discovery(self, widget: QWidget):
        """
        Queue a widget for discovery processing
        
        Args:
            widget: Widget to queue for discovery
        """
        if self._should_monitor_widget(widget):
            self._discovery_queue.add(widget)
            
            # Start timer for batch processing
            if not self._discovery_timer.isActive():
                self._discovery_timer.start(self.scan_delay_ms)
    
    def _process_discovery_queue(self):
        """Process queued widgets for discovery"""
        widgets_to_process = list(self._discovery_queue)
        self._discovery_queue.clear()
        
        for widget in widgets_to_process:
            try:
                self._discover_widget(widget)
            except RuntimeError:
                # Widget was destroyed, ignore
                continue
    
    def _discover_widget(self, widget: QWidget):
        """
        Process a widget for discovery
        
        Args:
            widget: Widget to discover
        """
        if widget in self._discovered_widgets:
            return
            
        if not self._should_monitor_widget(widget):
            return
            
        # Add to discovered set
        self._discovered_widgets.add(widget)
        
        # Emit discovery signal
        self.widget_discovered.emit(widget)
        
        # Recursively discover child widgets
        self._discover_child_widgets(widget)
    
    def _discover_child_widgets(self, parent_widget: QWidget, depth: int = 0):
        """
        Recursively discover child widgets
        
        Args:
            parent_widget: Parent widget to scan
            depth: Current recursion depth
        """
        if depth > self.max_scan_depth:
            return
            
        try:
            for child in parent_widget.findChildren(QWidget):
                if child not in self._discovered_widgets and self._should_monitor_widget(child):
                    self._discover_widget(child)
                    
        except Exception as e:
            # Handle errors gracefully
            pass
    
    def _should_monitor_widget(self, widget: QWidget) -> bool:
        """
        Determine if a widget should be monitored for zoom scaling
        
        Args:
            widget: Widget to check
            
        Returns:
            bool: True if widget should be monitored
        """
        # Check if widget type is in our monitored types
        if not any(isinstance(widget, widget_type) for widget_type in self._monitored_types):
            return False
            
        # Skip widgets without text content
        if not self._widget_has_text_content(widget):
            return False
            
        # Skip system/internal widgets
        if self._is_system_widget(widget):
            return False
            
        # Skip destroyed widgets
        try:
            widget.objectName()  # Test if widget is valid
        except RuntimeError:
            return False
            
        return True
    
    def _widget_has_text_content(self, widget: QWidget) -> bool:
        """
        Check if widget has text content that can benefit from zoom scaling
        
        Args:
            widget: Widget to check
            
        Returns:
            bool: True if widget has scalable text content
        """
        # Widgets that always have text
        if isinstance(widget, (QLabel, QPushButton, QCheckBox, QRadioButton,
                              QGroupBox, QLineEdit, QTextEdit, QComboBox)):
            return True
            
        # Table widgets have text content
        if isinstance(widget, QTableWidget):
            return True
            
        # Tab widgets have tab labels
        if isinstance(widget, QTabWidget):
            return True
            
        # Status bars and menu bars have text
        if isinstance(widget, (QStatusBar, QMenuBar, QToolBar)):
            return True
            
        # For other widgets, check if they have text properties
        try:
            if hasattr(widget, 'text') and widget.text():
                return True
            if hasattr(widget, 'title') and widget.title():
                return True
        except:
            pass
            
        return False
    
    def _is_system_widget(self, widget: QWidget) -> bool:
        """
        Check if widget is a system widget that shouldn't be scaled
        
        Args:
            widget: Widget to check
            
        Returns:
            bool: True if widget is a system widget
        """
        # Check widget class name for system widgets
        class_name = widget.__class__.__name__
        
        # Qt internal widgets
        if class_name.startswith('Q') and class_name.endswith(('Private', 'Internal')):
            return True
            
        # Skip scroll bar widgets and other internal components
        if 'ScrollBar' in class_name or 'Viewport' in class_name:
            return True
            
        # Check object name for system widgets
        object_name = widget.objectName()
        if object_name and ('qt_' in object_name.lower() or 'internal' in object_name.lower()):
            return True
            
        return False
    
    def _get_monitored_widget_types(self) -> tuple:
        """
        Get tuple of widget types that should be monitored for zoom scaling
        
        Returns:
            tuple: Widget types to monitor
        """
        return (
            # Text-containing widgets
            QLabel, QPushButton, QCheckBox, QRadioButton, QGroupBox,
            QLineEdit, QTextEdit, QComboBox, QSpinBox,
            
            # Complex widgets with text content
            QTableWidget, QTabWidget,
            
            # Window and dialog types
            QMainWindow, QDialog, QMessageBox,
            
            # UI container/layout widgets that may contain text
            QStatusBar, QMenuBar, QToolBar,
            
            # Frame widgets that might contain text
            QFrame,
        )
    
    def get_discovered_count(self) -> int:
        """Get number of discovered widgets"""
        return len(self._discovered_widgets)
    
    def force_scan_application(self):
        """Force a complete scan of the entire application"""
        app = QApplication.instance()
        if not app:
            return
            
        print("Force scanning all application widgets...")
        widget_count = 0
        
        # Scan all widgets in the application
        for widget in app.allWidgets():
            if isinstance(widget, QWidget):
                if self._should_monitor_widget(widget):
                    self._discover_widget(widget)
                    widget_count += 1
                    
        print(f"Force scan completed - discovered {widget_count} widgets")
        
        # Also trigger immediate discovery on all top-level widgets
        for widget in app.topLevelWidgets():
            if isinstance(widget, QWidget):
                self._discover_widget_tree(widget)
    
    def _discover_widget_tree(self, parent_widget: QWidget, depth: int = 0):
        """
        Recursively discover all widgets in a widget tree
        
        Args:
            parent_widget: Root widget to start scanning from
            depth: Current recursion depth
        """
        if depth > self.max_scan_depth:
            return
            
        try:
            # Discover the parent widget
            if self._should_monitor_widget(parent_widget):
                self._discover_widget(parent_widget)
            
            # Recursively discover all children
            for child in parent_widget.findChildren(QWidget):
                if self._should_monitor_widget(child):
                    self._discover_widget(child)
                    
        except Exception as e:
            pass


class WidgetScanner:
    """
    High-level widget scanner that coordinates widget discovery and zoom integration
    """
    
    def __init__(self):
        # Widget monitor for automatic discovery
        self.monitor = WidgetMonitor()
        
        # Connect monitor signals
        self.monitor.widget_discovered.connect(self._on_widget_discovered)
        self.monitor.widget_shown.connect(self._on_widget_shown)
        self.monitor.widget_hidden.connect(self._on_widget_hidden)
        
        # Track application state
        self._application_scanned = False
        self._scan_timer = QTimer()
        self._scan_timer.setSingleShot(True)
        self._scan_timer.timeout.connect(self._perform_initial_scan)
        
        # Configuration
        self.auto_scan_enabled = True
        self.initial_scan_delay = 1000  # 1 second delay for initial scan
        
    def start_monitoring(self):
        """Start automatic widget monitoring"""
        app = QApplication.instance()
        if app:
            # Install event filter on application
            app.installEventFilter(self.monitor)
            
            # Schedule initial scan
            if not self._application_scanned:
                self._scan_timer.start(self.initial_scan_delay)
    
    def stop_monitoring(self):
        """Stop automatic widget monitoring"""
        app = QApplication.instance()
        if app:
            app.removeEventFilter(self.monitor)
    
    def _perform_initial_scan(self):
        """Perform initial scan of all existing widgets"""
        if self._application_scanned:
            return
            
        try:
            print("Performing comprehensive initial widget scan...")
            self.monitor.force_scan_application()
            
            # Also force immediate application of zoom to discovered widgets
            from . import get_zoom_manager
            zoom_manager = get_zoom_manager()
            if zoom_manager:
                print("Applying current zoom to all discovered widgets...")
                zoom_manager.force_refresh_all_widgets()
            
            self._application_scanned = True
            print("Initial widget scan completed!")
            
        except Exception as e:
            print(f"Warning: Error during initial widget scan: {e}")
    
    def _on_widget_discovered(self, widget: QWidget):
        """
        Handle widget discovery
        
        Args:
            widget: Newly discovered widget
        """
        try:
            # Get zoom manager and register widget
            from . import get_zoom_manager
            zoom_manager = get_zoom_manager()
            
            if zoom_manager:
                zoom_manager.auto_register_widget(widget)
                
        except Exception as e:
            # Silently handle errors to avoid disrupting application
            pass
    
    def _on_widget_shown(self, widget: QWidget):
        """
        Handle widget shown event
        
        Args:
            widget: Widget that was shown
        """
        # Re-apply zoom when widget becomes visible
        try:
            from . import get_zoom_manager
            zoom_manager = get_zoom_manager()
            
            if zoom_manager:
                zoom_manager.apply_zoom_to_widget(widget)
                
        except Exception as e:
            pass
    
    def _on_widget_hidden(self, widget: QWidget):
        """
        Handle widget hidden event
        
        Args:
            widget: Widget that was hidden
        """
        # Nothing special needed when widget is hidden
        # WeakSet will automatically clean up when widget is destroyed
        pass
    
    def scan_widget_hierarchy(self, root_widget: QWidget):
        """
        Manually scan a specific widget hierarchy
        
        Args:
            root_widget: Root widget to start scanning from
        """
        if isinstance(root_widget, QWidget):
            self.monitor._discover_widget(root_widget)
    
    def get_scanner_stats(self) -> Dict[str, Any]:
        """
        Get scanner statistics
        
        Returns:
            Dict with scanner statistics
        """
        return {
            'discovered_widgets': self.monitor.get_discovered_count(),
            'auto_scan_enabled': self.auto_scan_enabled,
            'application_scanned': self._application_scanned,
            'monitoring_active': self.monitor.parent() is not None
        }


# Global widget scanner instance
_global_scanner = None


def create_widget_monitor() -> WidgetMonitor:
    """
    Create and return a widget monitor for event filtering
    
    Returns:
        WidgetMonitor: Monitor instance for use with QApplication.installEventFilter()
    """
    global _global_scanner
    if _global_scanner is None:
        _global_scanner = WidgetScanner()
    
    return _global_scanner.monitor


def get_widget_scanner() -> WidgetScanner:
    """
    Get the global widget scanner instance
    
    Returns:
        WidgetScanner: Global scanner instance
    """
    global _global_scanner
    if _global_scanner is None:
        _global_scanner = WidgetScanner()
        
    return _global_scanner


def start_widget_monitoring():
    """Start automatic widget monitoring"""
    scanner = get_widget_scanner()
    scanner.start_monitoring()


def stop_widget_monitoring():
    """Stop automatic widget monitoring"""
    if _global_scanner:
        _global_scanner.stop_monitoring()