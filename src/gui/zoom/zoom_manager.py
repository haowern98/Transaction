"""
Core zoom manager for application-wide font scaling
Handles central zoom logic, widget tracking, and automatic scaling without modifying existing widgets
"""

import weakref
from typing import Dict, Set, Optional, Any
from PyQt5.QtWidgets import (QWidget, QApplication, QLabel, QPushButton, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QDialog, QMessageBox,
                            QLineEdit, QTextEdit, QComboBox, QSpinBox, QCheckBox,
                            QRadioButton, QGroupBox, QTabWidget, QStatusBar, QMenuBar)
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QFontMetrics


class ZoomManager(QObject):
    """
    Central zoom manager that automatically discovers and scales widgets
    without requiring modifications to existing widget code
    """
    
    # Signals
    zoom_changed = pyqtSignal(int)  # Emitted when zoom level changes
    widget_scaled = pyqtSignal(object, int)  # Emitted when a widget is scaled
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuration
        from core.config import get_config
        self.config = get_config()
        
        # Widget tracking using weak references to avoid memory leaks
        self._tracked_widgets = weakref.WeakSet()
        self._widget_original_fonts = weakref.WeakKeyDictionary()
        self._widget_types = weakref.WeakKeyDictionary()
        
        # Font management
        self._font_cache = {}  # Cache for scaled fonts
        self._original_fonts_captured = False
        
        # Performance optimization
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._batch_update_widgets)
        self._pending_widgets = set()
        
        # Auto-discovery settings
        self.auto_discovery_enabled = True
        self.scale_dialogs = True
        self.scale_menus = True
        
        # Initialize with current zoom level
        self._current_zoom = self.config.get_zoom_level()
        
    # ========== Core Zoom Control ==========
    
    def get_current_zoom(self) -> int:
        """Get current zoom level percentage"""
        return self._current_zoom
    
    def set_zoom_level(self, zoom_level: int) -> bool:
        """
        Set application zoom level
        
        Args:
            zoom_level: Zoom percentage (50-300)
            
        Returns:
            bool: True if successful, False if invalid
        """
        if not self.config.set_zoom_level(zoom_level):
            return False
            
        old_zoom = self._current_zoom
        self._current_zoom = zoom_level
        
        # Clear font cache when zoom changes
        self._font_cache.clear()
        
        print(f"Zoom level changed from {old_zoom}% to {zoom_level}%")
        
        # Force immediate application to all widgets
        self._force_apply_zoom_to_all_widgets()
        
        # Emit signal
        self.zoom_changed.emit(zoom_level)
        
        return True
    
    def _force_apply_zoom_to_all_widgets(self):
        """Force immediate application of zoom to all widgets"""
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if not app:
            return
            
        print(f"Force applying {self._current_zoom}% zoom to all widgets...")
        widgets_processed = 0
        
        # Apply to all widgets in the application
        for widget in app.allWidgets():
            try:
                if isinstance(widget, QWidget) and widget.isVisible():
                    # Register widget if not already registered
                    if widget not in self._tracked_widgets:
                        self.register_widget(widget)
                    
                    # Apply zoom immediately
                    self.apply_zoom_to_widget(widget)
                    widgets_processed += 1
                    
            except RuntimeError:
                # Widget was destroyed, skip
                continue
            except Exception as e:
                # Other errors, skip this widget
                continue
        
        print(f"Applied zoom to {widgets_processed} widgets")
        
        # Also apply to tracked widgets
        self._apply_zoom_to_all_widgets()
    
    def zoom_in(self) -> int:
        """
        Zoom in to next level
        
        Returns:
            int: New zoom level
        """
        next_zoom = self.config.get_next_zoom_level('in')
        self.set_zoom_level(next_zoom)
        return next_zoom
    
    def zoom_out(self) -> int:
        """
        Zoom out to previous level
        
        Returns:
            int: New zoom level
        """
        next_zoom = self.config.get_next_zoom_level('out')
        self.set_zoom_level(next_zoom)
        return next_zoom
    
    def reset_zoom(self) -> int:
        """
        Reset zoom to 100%
        
        Returns:
            int: New zoom level (should be 100)
        """
        self.config.reset_zoom()
        self.set_zoom_level(100)
        return 100
    
    # ========== Widget Management ==========
    
    def register_widget(self, widget: QWidget, widget_type: str = None):
        """
        Register a widget for zoom tracking
        
        Args:
            widget: Widget to track
            widget_type: Optional widget type classification
        """
        if not isinstance(widget, QWidget):
            return
            
        # Add to tracked widgets
        self._tracked_widgets.add(widget)
        
        # Capture original font if not already done
        if widget not in self._widget_original_fonts:
            original_font = widget.font()
            self._widget_original_fonts[widget] = original_font
            
        # Determine widget type for appropriate font sizing
        if widget_type is None:
            widget_type = self._classify_widget(widget)
        self._widget_types[widget] = widget_type
        
        # Apply current zoom immediately
        self.apply_zoom_to_widget(widget)
    
    def unregister_widget(self, widget: QWidget):
        """
        Unregister a widget from zoom tracking
        
        Args:
            widget: Widget to unregister
        """
        # WeakSet automatically handles removal when widget is destroyed
        # But we can explicitly remove from dictionaries
        self._widget_original_fonts.pop(widget, None)
        self._widget_types.pop(widget, None)
    
    def apply_zoom_to_widget(self, widget: QWidget):
        """
        Apply current zoom level to a specific widget
        
        Args:
            widget: Widget to apply zoom to
        """
        if not isinstance(widget, QWidget):
            return
        
        # Capture original font if not already done
        if widget not in self._widget_original_fonts:
            original_font = widget.font()
            self._widget_original_fonts[widget] = QFont(original_font)  # Deep copy
            
        # Get widget type for appropriate font selection
        widget_type = self._widget_types.get(widget)
        if widget_type is None:
            widget_type = self._classify_widget(widget)
            self._widget_types[widget] = widget_type
        
        # Get original font
        original_font = self._widget_original_fonts[widget]
        
        # If zoom is 100%, restore exact original font
        if self._current_zoom == 100:
            widget.setFont(QFont(original_font))  # Exact copy of original
            self.widget_scaled.emit(widget, self._current_zoom)
            return
        
        # Calculate target font size based on original font size and zoom
        original_size = original_font.pointSize()
        if original_size <= 0:
            original_size = 9  # Default fallback
        
        # Apply zoom factor to original size
        zoom_factor = self._current_zoom / 100.0
        target_size = max(6, int(original_size * zoom_factor))
        
        # Create or get cached font
        font_key = (widget_type, original_size, target_size, self._current_zoom)
        if font_key not in self._font_cache:
            from .font_scaler import FontScaler
            font_scaler = FontScaler()
            scaled_font = font_scaler.scale_font(original_font, target_size, preserve_properties=True)
            self._font_cache[font_key] = scaled_font
        
        # Apply font to widget
        scaled_font = self._font_cache[font_key]
        widget.setFont(scaled_font)
        
        # Handle special widget types
        self._apply_special_scaling(widget, widget_type)
        
        # Emit signal
        self.widget_scaled.emit(widget, self._current_zoom)
    
    def _classify_widget(self, widget: QWidget) -> str:
        """
        Classify widget type for appropriate font sizing
        
        Args:
            widget: Widget to classify
            
        Returns:
            str: Widget type classification
        """
        # Map widget types to font categories
        if isinstance(widget, (QPushButton,)):
            return 'button'
        elif isinstance(widget, (QLabel,)):
            return 'label'
        elif isinstance(widget, (QTableWidget,)):
            return 'table_content'
        elif isinstance(widget, (QLineEdit, QTextEdit, QComboBox, QSpinBox)):
            return 'dialog'
        elif isinstance(widget, (QCheckBox, QRadioButton)):
            return 'button'
        elif isinstance(widget, (QGroupBox,)):
            return 'label'
        elif isinstance(widget, (QTabWidget,)):
            return 'tab_header'
        elif isinstance(widget, (QStatusBar,)):
            return 'status_bar'
        elif isinstance(widget, (QMenuBar,)):
            return 'menu'
        elif isinstance(widget, (QDialog, QMessageBox)):
            return 'dialog'
        else:
            return 'label'  # Default fallback
    
    def _create_scaled_font(self, original_font: QFont, target_size: int) -> QFont:
        """
        Create a scaled font based on original font properties
        
        Args:
            original_font: Original font to scale
            target_size: Target font size in points
            
        Returns:
            QFont: Scaled font object
        """
        scaled_font = QFont(original_font)
        scaled_font.setPointSize(max(6, target_size))  # Minimum 6pt
        return scaled_font
    
    def _apply_special_scaling(self, widget: QWidget, widget_type: str):
        """
        Apply special scaling for specific widget types
        
        Args:
            widget: Widget to apply special scaling to
            widget_type: Type of widget
        """
        # Handle table widgets specially
        if isinstance(widget, QTableWidget):
            self._scale_table_widget(widget)
        
        # Handle tab widgets
        elif isinstance(widget, QTabWidget):
            self._scale_tab_widget(widget)
    
    def _scale_table_widget(self, table: QTableWidget):
        """
        Apply special scaling to table widgets
        
        Args:
            table: Table widget to scale
        """
        try:
            # Scale row heights based on font size
            font_size = self.config.get_font_size('table_content')
            row_height = max(25, int(font_size * 1.8))  # Minimum 25px height
            
            # Apply to all rows
            for row in range(table.rowCount()):
                table.setRowHeight(row, row_height)
            
            # Scale header if it exists
            if table.horizontalHeader():
                header_font_size = self.config.get_font_size('table_header')
                header_font = self._create_scaled_font(table.horizontalHeader().font(), header_font_size)
                table.horizontalHeader().setFont(header_font)
                
            if table.verticalHeader():
                header_font_size = self.config.get_font_size('table_header')
                header_font = self._create_scaled_font(table.verticalHeader().font(), header_font_size)
                table.verticalHeader().setFont(header_font)
                
        except Exception as e:
            # Silently handle errors to avoid disrupting table functionality
            pass
    
    def _scale_tab_widget(self, tab_widget: QTabWidget):
        """
        Apply scaling to tab widget headers
        
        Args:
            tab_widget: Tab widget to scale
        """
        try:
            # Scale tab bar font
            tab_bar = tab_widget.tabBar()
            if tab_bar:
                font_size = self.config.get_font_size('tab_header')
                tab_font = self._create_scaled_font(tab_bar.font(), font_size)
                tab_bar.setFont(tab_font)
        except Exception as e:
            pass
    
    # ========== Batch Updates and Performance ==========
    
    def _apply_zoom_to_all_widgets(self):
        """Apply current zoom to all tracked widgets efficiently"""
        # Use timer to batch updates for better performance
        self._pending_widgets.update(self._tracked_widgets)
        self._update_timer.start(50)  # 50ms delay for batching
    
    def _batch_update_widgets(self):
        """Batch update widgets for better performance"""
        widgets_to_update = list(self._pending_widgets)
        self._pending_widgets.clear()
        
        for widget in widgets_to_update:
            try:
                if widget and not widget.isHidden():  # Only update visible widgets
                    self.apply_zoom_to_widget(widget)
            except RuntimeError:
                # Widget was destroyed, will be auto-removed from WeakSet
                continue
    
    # ========== Auto-Discovery Integration ==========
    
    def auto_register_widget(self, widget: QWidget):
        """
        Automatically register a widget discovered by the widget scanner
        
        Args:
            widget: Widget discovered by auto-discovery
        """
        if not self.auto_discovery_enabled:
            return
            
        # Filter out widgets we don't want to scale
        if self._should_skip_widget(widget):
            return
            
        self.register_widget(widget)
    
    def _should_skip_widget(self, widget: QWidget) -> bool:
        """
        Determine if a widget should be skipped from auto-scaling
        
        Args:
            widget: Widget to check
            
        Returns:
            bool: True if widget should be skipped
        """
        # Skip system dialogs if configured
        if not self.scale_dialogs and isinstance(widget, (QDialog, QMessageBox)):
            return True
            
        # Skip hidden widgets
        if widget.isHidden():
            return True
            
        # Skip if parent is hidden
        parent = widget.parent()
        while parent:
            if isinstance(parent, QWidget) and parent.isHidden():
                return True
            parent = parent.parent()
            
        return False
    
    # ========== Configuration Integration ==========
    
    def load_zoom_settings(self):
        """Load zoom settings from configuration"""
        try:
            zoom_level = self.config.get_zoom_level()
            self.set_zoom_level(zoom_level)
        except Exception as e:
            print(f"Warning: Failed to load zoom settings: {e}")
            self.reset_zoom()
    
    def save_zoom_settings(self):
        """Save current zoom settings to configuration"""
        try:
            self.config.set_zoom_level(self._current_zoom)
            self.config.save_configuration()
        except Exception as e:
            print(f"Warning: Failed to save zoom settings: {e}")
    
    # ========== Cleanup and Resource Management ==========
    
    def cleanup(self):
        """Clean up resources and save settings"""
        try:
            # Save current settings
            self.save_zoom_settings()
            
            # Stop any pending timers
            if self._update_timer.isActive():
                self._update_timer.stop()
            
            # Clear caches
            self._font_cache.clear()
            self._pending_widgets.clear()
            
        except Exception as e:
            print(f"Warning: Error during zoom manager cleanup: {e}")
    
    # ========== Utility Methods ==========
    
    def get_widget_count(self) -> int:
        """Get number of tracked widgets"""
        return len(self._tracked_widgets)
    
    def get_zoom_info(self) -> Dict[str, Any]:
        """
        Get comprehensive zoom information
        
        Returns:
            Dict containing zoom statistics and settings
        """
        return {
            'current_zoom': self._current_zoom,
            'tracked_widgets': len(self._tracked_widgets),
            'cached_fonts': len(self._font_cache),
            'auto_discovery': self.auto_discovery_enabled,
            'min_zoom': self.config.MIN_ZOOM_LEVEL,
            'max_zoom': self.config.MAX_ZOOM_LEVEL,
            'available_levels': self.config.ZOOM_LEVELS
        }
    
    def force_refresh_all_widgets(self):
        """Force refresh of all tracked widgets (for debugging)"""
        self._font_cache.clear()
        self._apply_zoom_to_all_widgets()