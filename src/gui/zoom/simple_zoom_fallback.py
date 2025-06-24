"""
Simple immediate zoom system that works without complex widget discovery
Falls back to direct application-wide font scaling
"""
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QObject, pyqtSignal


class SimpleImmediateZoom(QObject):
    """Simple zoom system that applies immediately to all widgets"""
    
    zoom_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.current_zoom = 100
        self.original_fonts = {}  # Store original fonts
        self.zoom_levels = [50, 75, 90, 100, 110, 125, 150, 175, 200, 250, 300]
        
    def set_zoom_level(self, zoom_level: int):
        """Set zoom level and apply immediately"""
        if zoom_level < 50 or zoom_level > 300:
            return False
            
        print(f"Setting zoom to {zoom_level}%...")
        self.current_zoom = zoom_level
        self._apply_zoom_to_all_widgets()
        self.zoom_changed.emit(zoom_level)
        return True
        
    def zoom_in(self):
        """Zoom in to next level"""
        current_index = self._get_current_zoom_index()
        if current_index < len(self.zoom_levels) - 1:
            next_zoom = self.zoom_levels[current_index + 1]
            self.set_zoom_level(next_zoom)
            return next_zoom
        return self.current_zoom
        
    def zoom_out(self):
        """Zoom out to previous level"""
        current_index = self._get_current_zoom_index()
        if current_index > 0:
            prev_zoom = self.zoom_levels[current_index - 1]
            self.set_zoom_level(prev_zoom)
            return prev_zoom
        return self.current_zoom
        
    def reset_zoom(self):
        """Reset to 100%"""
        self.set_zoom_level(100)
        return 100
        
    def get_current_zoom(self):
        """Get current zoom level"""
        return self.current_zoom
        
    def _get_current_zoom_index(self):
        """Get index of current zoom in zoom_levels list"""
        try:
            return self.zoom_levels.index(self.current_zoom)
        except ValueError:
            # Find closest zoom level
            closest_index = 0
            min_diff = abs(self.zoom_levels[0] - self.current_zoom)
            for i, level in enumerate(self.zoom_levels):
                diff = abs(level - self.current_zoom)
                if diff < min_diff:
                    min_diff = diff
                    closest_index = i
            return closest_index
    
    def _apply_zoom_to_all_widgets(self):
        """Apply zoom to all widgets in the application immediately"""
        app = QApplication.instance()
        if not app:
            return
            
        zoom_factor = self.current_zoom / 100.0
        widgets_processed = 0
        
        print(f"Applying {self.current_zoom}% zoom to all application widgets...")
        
        # Process all widgets in the application
        for widget in app.allWidgets():
            try:
                if not isinstance(widget, QWidget):
                    continue
                
                # Skip zoom controls to prevent double-scaling
                if self._is_zoom_control_widget(widget):
                    continue
                    
                # Store original font if not stored yet
                if widget not in self.original_fonts:
                    self.original_fonts[widget] = QFont(widget.font())
                
                # Get original font
                original_font = self.original_fonts[widget]
                original_size = original_font.pointSize()
                
                # Handle invalid font sizes
                if original_size <= 0:
                    original_size = 9  # Default font size
                
                # At 100% zoom, restore exact original
                if self.current_zoom == 100:
                    widget.setFont(QFont(original_font))
                else:
                    # Calculate scaled size
                    new_size = max(6, int(original_size * zoom_factor))
                    
                    # Create scaled font preserving all properties
                    scaled_font = QFont(original_font)
                    scaled_font.setPointSize(new_size)
                    
                    # Apply scaled font
                    widget.setFont(scaled_font)
                
                widgets_processed += 1
                
            except RuntimeError:
                # Widget destroyed, skip
                continue
            except Exception:
                # Other errors, skip
                continue
        
        print(f"✓ Applied zoom to {widgets_processed} widgets")
        
        # Force application to repaint
        app.processEvents()
    
    def _is_zoom_control_widget(self, widget):
        """Check if widget is a zoom control that should be excluded from general scaling"""
        try:
            # Check object name
            if hasattr(widget, 'objectName') and 'ZoomControls' in widget.objectName():
                return True
            
            # Check class name
            class_name = widget.__class__.__name__
            if 'ZoomButtons' in class_name or 'ZoomControl' in class_name:
                return True
            
            # Check parent hierarchy for zoom controls
            parent = widget.parent()
            while parent:
                if hasattr(parent, 'objectName') and 'ZoomControls' in parent.objectName():
                    return True
                if 'ZoomButtons' in parent.__class__.__name__:
                    return True
                parent = parent.parent()
            
            return False
        except:
            return False


# Global instance
_simple_zoom_instance = None


def get_simple_zoom():
    """Get or create the simple zoom instance"""
    global _simple_zoom_instance
    if _simple_zoom_instance is None:
        _simple_zoom_instance = SimpleImmediateZoom()
    return _simple_zoom_instance


def apply_immediate_zoom(zoom_level: int):
    """Apply zoom immediately to all widgets"""
    simple_zoom = get_simple_zoom()
    return simple_zoom.set_zoom_level(zoom_level)


def zoom_in_immediate():
    """Zoom in immediately"""
    simple_zoom = get_simple_zoom()
    return simple_zoom.zoom_in()


def zoom_out_immediate():
    """Zoom out immediately"""
    simple_zoom = get_simple_zoom()
    return simple_zoom.zoom_out()


def reset_zoom_immediate():
    """Reset zoom immediately"""
    simple_zoom = get_simple_zoom()
    return simple_zoom.reset_zoom()