"""
Consolidated zoom system that prevents cascading scaling issues
Replaces multiple conflicting zoom systems with a single, robust implementation
"""

import weakref
from typing import Dict, Set, Optional, Any
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QTableWidget,
                            QLineEdit, QTextEdit, QComboBox, QCheckBox, QRadioButton,
                            QGroupBox, QTabWidget, QStatusBar, QMenuBar, QShortcut)
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QKeySequence


class ConsolidatedZoomSystem(QObject):
    """
    Single, authoritative zoom system that prevents cascading scaling issues
    """
    
    # Signals
    zoom_changed = pyqtSignal(int)  # New zoom level
    emergency_reset = pyqtSignal()  # Emergency reset triggered
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Core state
        self._current_zoom = 100
        self._zoom_levels = [50, 75, 90, 100, 125, 150, 175, 200, 250]
        
        # Widget tracking with weak references
        self._original_fonts = weakref.WeakKeyDictionary()  # {widget: original_font}
        self._zoom_excluded_widgets = weakref.WeakSet()     # Widgets to never scale
        self._tracked_widgets = weakref.WeakSet()           # All tracked widgets
        
        # System state
        self._fonts_captured = False
        self._zoom_in_progress = False
        self._emergency_mode = False
        
        # Performance optimization
        self._batch_timer = QTimer()
        self._batch_timer.setSingleShot(True)
        self._batch_timer.timeout.connect(self._process_batch_updates)
        self._pending_widgets = set()
        
        # Install emergency shortcuts immediately
        self._install_emergency_shortcuts()
        
    def initialize(self):
        """Initialize the zoom system - call this after QApplication is created"""
        try:
            app = QApplication.instance()
            if not app:
                print("Warning: No QApplication found for zoom system")
                return False
                
            # Capture original fonts BEFORE any scaling occurs
            self._capture_all_original_fonts()
            
            # Install normal shortcuts
            self._install_shortcuts()
            
            # Load saved zoom level
            self._load_zoom_settings()
            
            print(f"✓ Zoom system initialized with {len(self._original_fonts)} original fonts captured")
            return True
            
        except Exception as e:
            print(f"✗ Failed to initialize zoom system: {e}")
            return False
    
    def _capture_all_original_fonts(self):
        """Capture original fonts from ALL widgets before any scaling"""
        if self._fonts_captured:
            return
            
        app = QApplication.instance()
        if not app:
            return
            
        captured_count = 0
        
        # Capture fonts from all existing widgets
        for widget in app.allWidgets():
            if isinstance(widget, QWidget) and self._should_track_widget(widget):
                try:
                    # Store the CURRENT font as original (before any zoom)
                    original_font = QFont(widget.font())
                    self._original_fonts[widget] = original_font
                    self._tracked_widgets.add(widget)
                    captured_count += 1
                    
                    # Mark zoom controls for exclusion
                    if self._is_zoom_control(widget):
                        self._zoom_excluded_widgets.add(widget)
                        
                except Exception:
                    continue
        
        self._fonts_captured = True
        print(f"✓ Captured {captured_count} original fonts")
    
    def _should_track_widget(self, widget: QWidget) -> bool:
        """Determine if widget should be tracked for zoom"""
        try:
            # Skip destroyed widgets
            widget.objectName()
            
            # Only track widgets with text content
            return isinstance(widget, (QLabel, QPushButton, QLineEdit, QTextEdit,
                                     QComboBox, QCheckBox, QRadioButton, QGroupBox,
                                     QTableWidget, QTabWidget, QStatusBar, QMenuBar))
        except RuntimeError:
            return False
    
    def _is_zoom_control(self, widget: QWidget) -> bool:
        """Check if widget is a zoom control that should be excluded"""
        try:
            # Check object name
            if hasattr(widget, 'objectName'):
                obj_name = widget.objectName().lower()
                if 'zoom' in obj_name:
                    return True
            
            # Check class name
            class_name = widget.__class__.__name__.lower()
            if 'zoom' in class_name:
                return True
            
            # Check parent hierarchy
            parent = widget.parent()
            while parent:
                if hasattr(parent, 'objectName'):
                    parent_name = parent.objectName().lower()
                    if 'zoom' in parent_name:
                        return True
                if 'zoom' in parent.__class__.__name__.lower():
                    return True
                parent = parent.parent()
                
            return False
        except:
            return False
    
    def set_zoom_level(self, zoom_level: int) -> bool:
        """Set zoom level with validation and safeguards"""
        # Validation
        if zoom_level < 25 or zoom_level > 500:
            print(f"✗ Invalid zoom level: {zoom_level}% (must be 25-500%)")
            return False
        
        # Prevent recursive calls
        if self._zoom_in_progress:
            return False
            
        self._zoom_in_progress = True
        
        try:
            old_zoom = self._current_zoom
            self._current_zoom = zoom_level
            
            # Apply zoom to all tracked widgets
            self._apply_zoom_to_all_widgets()
            
            # Emit signal
            self.zoom_changed.emit(zoom_level)
            
            # Save settings
            self._save_zoom_settings()
            
            print(f"✓ Zoom changed from {old_zoom}% to {zoom_level}%")
            return True
            
        except Exception as e:
            print(f"✗ Error setting zoom level: {e}")
            # Restore previous zoom on error
            self._current_zoom = old_zoom if 'old_zoom' in locals() else 100
            return False
        finally:
            self._zoom_in_progress = False
    
    def _apply_zoom_to_all_widgets(self):
        """Apply current zoom to all tracked widgets"""
        if not self._fonts_captured:
            return
            
        zoom_factor = self._current_zoom / 100.0
        applied_count = 0
        
        for widget in list(self._tracked_widgets):
            try:
                # Skip if widget was destroyed
                if not widget or widget not in self._original_fonts:
                    continue
                    
                # Skip zoom controls
                if widget in self._zoom_excluded_widgets:
                    continue
                
                # Get original font
                original_font = self._original_fonts[widget]
                original_size = original_font.pointSize()
                
                if original_size <= 0:
                    original_size = 9  # Default fallback
                
                # Calculate new size
                new_size = max(6, min(72, int(original_size * zoom_factor)))
                
                # Create scaled font preserving all properties
                scaled_font = QFont(original_font)
                scaled_font.setPointSize(new_size)
                
                # Apply font
                widget.setFont(scaled_font)
                applied_count += 1
                
            except RuntimeError:
                # Widget destroyed, will be auto-removed from WeakSet
                continue
            except Exception as e:
                # Log but continue with other widgets
                continue
        
        print(f"✓ Applied {self._current_zoom}% zoom to {applied_count} widgets")
    
    def zoom_in(self):
        """Zoom in to next level"""
        current_index = self._get_zoom_index()
        if current_index < len(self._zoom_levels) - 1:
            next_zoom = self._zoom_levels[current_index + 1]
            self.set_zoom_level(next_zoom)
    
    def zoom_out(self):
        """Zoom out to previous level"""
        current_index = self._get_zoom_index()
        if current_index > 0:
            prev_zoom = self._zoom_levels[current_index - 1]
            self.set_zoom_level(prev_zoom)
    
    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.set_zoom_level(100)
    
    def emergency_reset(self):
        """Emergency reset - forcibly restore all original fonts"""
        if not self._fonts_captured:
            return
            
        print("🚨 Emergency zoom reset activated")
        self._emergency_mode = True
        
        try:
            # Force restore all original fonts
            restored_count = 0
            for widget, original_font in list(self._original_fonts.items()):
                try:
                    widget.setFont(QFont(original_font))
                    restored_count += 1
                except RuntimeError:
                    continue
            
            self._current_zoom = 100
            self.zoom_changed.emit(100)
            
            print(f"🚨 Emergency reset complete - restored {restored_count} widgets")
            self.emergency_reset.emit()
            
        except Exception as e:
            print(f"🚨 Emergency reset failed: {e}")
        finally:
            self._emergency_mode = False
    
    def _get_zoom_index(self) -> int:
        """Get index of current zoom in zoom levels list"""
        try:
            return self._zoom_levels.index(self._current_zoom)
        except ValueError:
            # Find closest zoom level
            closest_index = 0
            min_diff = abs(self._zoom_levels[0] - self._current_zoom)
            for i, level in enumerate(self._zoom_levels):
                diff = abs(level - self._current_zoom)
                if diff < min_diff:
                    min_diff = diff
                    closest_index = i
            return closest_index
    
    def register_widget(self, widget: QWidget):
        """Register a new widget for zoom tracking"""
        if not isinstance(widget, QWidget) or not self._should_track_widget(widget):
            return
            
        if widget not in self._original_fonts:
            # Capture original font
            original_font = QFont(widget.font())
            self._original_fonts[widget] = original_font
            self._tracked_widgets.add(widget)
            
            # Mark zoom controls for exclusion
            if self._is_zoom_control(widget):
                self._zoom_excluded_widgets.add(widget)
            
            # Apply current zoom
            self._apply_zoom_to_widget(widget)
    
    def _apply_zoom_to_widget(self, widget: QWidget):
        """Apply current zoom to a specific widget"""
        if widget in self._zoom_excluded_widgets or widget not in self._original_fonts:
            return
            
        try:
            original_font = self._original_fonts[widget]
            zoom_factor = self._current_zoom / 100.0
            original_size = original_font.pointSize()
            
            if original_size <= 0:
                original_size = 9
                
            new_size = max(6, min(72, int(original_size * zoom_factor)))
            
            scaled_font = QFont(original_font)
            scaled_font.setPointSize(new_size)
            
            widget.setFont(scaled_font)
            
        except Exception:
            pass
    
    def _install_shortcuts(self):
        """Install normal zoom shortcuts"""
        app = QApplication.instance()
        if not app:
            return
            
        try:
            # Find main window for shortcuts
            main_window = None
            for widget in app.allWidgets():
                if hasattr(widget, 'setWindowTitle') and hasattr(widget, 'centralWidget'):
                    main_window = widget
                    break
            
            if not main_window:
                print("Warning: No main window found for shortcuts")
                return
            
            # Zoom in shortcuts
            zoom_in_1 = QShortcut("Ctrl++", main_window)
            zoom_in_1.activated.connect(self.zoom_in)
            
            zoom_in_2 = QShortcut("Ctrl+=", main_window)
            zoom_in_2.activated.connect(self.zoom_in)
            
            # Zoom out shortcut
            zoom_out = QShortcut("Ctrl+-", main_window)
            zoom_out.activated.connect(self.zoom_out)
            
            # Reset shortcut
            reset_zoom = QShortcut("Ctrl+0", main_window)
            reset_zoom.activated.connect(self.reset_zoom)
            
            print("✓ Zoom shortcuts installed")
            
        except Exception as e:
            print(f"Warning: Failed to install zoom shortcuts: {e}")
    
    def _install_emergency_shortcuts(self):
        """Install emergency reset shortcuts"""
        app = QApplication.instance()
        if app:
            try:
                # Find main window for emergency shortcut
                main_window = None
                for widget in app.allWidgets():
                    if hasattr(widget, 'setWindowTitle') and hasattr(widget, 'centralWidget'):
                        main_window = widget
                        break
                
                if main_window:
                    # Emergency reset: Ctrl+Alt+0
                    emergency = QShortcut("Ctrl+Alt+0", main_window)
                    emergency.activated.connect(self.emergency_reset)
                    print("✓ Emergency shortcut (Ctrl+Alt+0) installed")
            except Exception as e:
                print(f"Warning: Failed to install emergency shortcut: {e}")
    
    def _load_zoom_settings(self):
        """Load zoom settings from config"""
        try:
            from core.config import get_config
            config = get_config()
            saved_zoom = config.get_zoom_level()
            if 50 <= saved_zoom <= 300:
                self.set_zoom_level(saved_zoom)
        except:
            self.set_zoom_level(100)
    
    def _save_zoom_settings(self):
        """Save current zoom settings"""
        try:
            from core.config import get_config
            config = get_config()
            config.set_zoom_level(self._current_zoom)
            config.save_configuration()
        except:
            pass
    
    def get_current_zoom(self) -> int:
        """Get current zoom level"""
        return self._current_zoom
    
    def get_zoom_levels(self) -> list:
        """Get available zoom levels"""
        return self._zoom_levels.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get zoom system statistics"""
        return {
            'current_zoom': self._current_zoom,
            'tracked_widgets': len(self._tracked_widgets),
            'original_fonts': len(self._original_fonts),
            'excluded_widgets': len(self._zoom_excluded_widgets),
            'fonts_captured': self._fonts_captured,
            'emergency_mode': self._emergency_mode
        }
    
    def _process_batch_updates(self):
        """Process batched widget updates for performance"""
        if not self._pending_widgets:
            return
            
        widgets_to_update = list(self._pending_widgets)
        self._pending_widgets.clear()
        
        for widget in widgets_to_update:
            try:
                if widget and not widget.isHidden():
                    self._apply_zoom_to_widget(widget)
            except RuntimeError:
                # Widget destroyed, ignore
                continue
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self._save_zoom_settings()
            if self._batch_timer.isActive():
                self._batch_timer.stop()
        except:
            pass


# Global zoom system instance
_global_zoom_system = None


def get_zoom_system() -> Optional[ConsolidatedZoomSystem]:
    """Get the global zoom system instance"""
    global _global_zoom_system
    return _global_zoom_system


def initialize_zoom_system() -> bool:
    """Initialize the global zoom system"""
    global _global_zoom_system
    
    if _global_zoom_system is not None:
        return True
        
    try:
        _global_zoom_system = ConsolidatedZoomSystem()
        success = _global_zoom_system.initialize()
        
        if success:
            print("✓ Consolidated zoom system ready")
        else:
            print("✗ Failed to initialize zoom system")
            
        return success
        
    except Exception as e:
        print(f"✗ Error creating zoom system: {e}")
        return False


def cleanup_zoom_system():
    """Clean up the zoom system"""
    global _global_zoom_system
    
    if _global_zoom_system:
        _global_zoom_system.cleanup()
        _global_zoom_system = None


# Auto-cleanup
import atexit
atexit.register(cleanup_zoom_system)