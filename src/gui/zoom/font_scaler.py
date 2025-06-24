"""
Font scaling logic and specialized font operations
Handles font detection, scaling calculations, caching, and widget-specific font management
"""

import weakref
from typing import Dict, Tuple, Optional, Any, List
from PyQt5.QtWidgets import (QWidget, QTableWidget, QHeaderView, QTabWidget, 
                            QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
                            QCheckBox, QRadioButton, QGroupBox, QStatusBar, QMenuBar)
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QFont, QFontMetrics, QFontDatabase


class FontScaler(QObject):
    """
    Advanced font scaling engine with caching and widget-specific optimizations
    """
    
    # Signals
    font_scaled = pyqtSignal(object, QFont)  # Widget, new font
    cache_cleared = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Font caching system
        self._font_cache = {}  # {(family, size, weight, italic): QFont}
        self._widget_font_cache = weakref.WeakKeyDictionary()  # {widget: cached_font}
        self._original_fonts = weakref.WeakKeyDictionary()  # {widget: original_font}
        
        # Font analysis
        self._system_fonts = self._analyze_system_fonts()
        self._font_fallbacks = self._create_font_fallbacks()
        
        # Scaling configuration
        self.min_font_size = 6
        self.max_font_size = 72
        self.scale_precision = 1  # Round to nearest integer
        
        # Performance settings
        self.cache_enabled = True
        self.max_cache_size = 200
        
    # ========== Font Detection and Analysis ==========
    
    def extract_widget_font_info(self, widget: QWidget) -> Dict[str, Any]:
        """
        Extract comprehensive font information from a widget
        
        Args:
            widget: Widget to analyze
            
        Returns:
            Dict containing font properties and metadata
        """
        if not isinstance(widget, QWidget):
            return {}
            
        font = widget.font()
        
        font_info = {
            'family': font.family(),
            'point_size': font.pointSize(),
            'pixel_size': font.pixelSize(),
            'weight': font.weight(),
            'bold': font.bold(),
            'italic': font.italic(),
            'underline': font.underline(),
            'strikeout': font.strikeOut(),
            'letter_spacing': font.letterSpacing(),
            'word_spacing': font.wordSpacing(),
            'stretch': font.stretch(),
            'style_hint': font.styleHint(),
            'style_strategy': font.styleStrategy(),
            'widget_type': widget.__class__.__name__,
            'object_name': widget.objectName()
        }
        
        # Add font metrics
        metrics = QFontMetrics(font)
        font_info['metrics'] = {
            'height': metrics.height(),
            'ascent': metrics.ascent(),
            'descent': metrics.descent(),
            'leading': metrics.leading(),
            'line_spacing': metrics.lineSpacing(),
            'max_width': metrics.maxWidth(),
            'average_char_width': metrics.averageCharWidth()
        }
        
        return font_info
    
    def capture_original_font(self, widget: QWidget) -> QFont:
        """
        Capture and store the original font of a widget
        
        Args:
            widget: Widget to capture font from
            
        Returns:
            QFont: Copy of the original font
        """
        if widget in self._original_fonts:
            return self._original_fonts[widget]
            
        original_font = QFont(widget.font())
        self._original_fonts[widget] = original_font
        return original_font
    
    def _analyze_system_fonts(self) -> Dict[str, List[str]]:
        """
        Analyze available system fonts and categorize them
        
        Returns:
            Dict mapping font categories to font families
        """
        database = QFontDatabase()
        families = database.families()
        
        categories = {
            'serif': [],
            'sans_serif': [],
            'monospace': [],
            'decorative': [],
            'symbol': []
        }
        
        # Categorize fonts based on known families and characteristics
        for family in families:
            family_lower = family.lower()
            
            # Serif fonts
            if any(serif in family_lower for serif in ['times', 'serif', 'georgia', 'palatino']):
                categories['serif'].append(family)
            # Sans-serif fonts
            elif any(sans in family_lower for sans in ['arial', 'helvetica', 'verdana', 'tahoma', 'calibri']):
                categories['sans_serif'].append(family)
            # Monospace fonts
            elif any(mono in family_lower for mono in ['courier', 'consolas', 'monaco', 'menlo', 'lucida console']):
                categories['monospace'].append(family)
            # Symbol fonts
            elif any(symbol in family_lower for symbol in ['symbol', 'wingdings', 'webdings']):
                categories['symbol'].append(family)
            else:
                categories['decorative'].append(family)
                
        return categories
    
    def _create_font_fallbacks(self) -> Dict[str, List[str]]:
        """
        Create font fallback chains for different widget types
        
        Returns:
            Dict mapping widget types to preferred font families
        """
        return {
            'button': ['Segoe UI', 'Arial', 'Helvetica', 'sans-serif'],
            'label': ['Segoe UI', 'Arial', 'Helvetica', 'sans-serif'],
            'table_content': ['Segoe UI', 'Arial', 'Tahoma', 'sans-serif'],
            'table_header': ['Segoe UI', 'Arial', 'Helvetica', 'sans-serif'],
            'dialog': ['Segoe UI', 'Arial', 'Helvetica', 'sans-serif'],
            'menu': ['Segoe UI', 'Arial', 'Helvetica', 'sans-serif'],
            'status_bar': ['Segoe UI', 'Arial', 'Helvetica', 'sans-serif'],
            'tab_header': ['Segoe UI', 'Arial', 'Helvetica', 'sans-serif'],
            'monospace': ['Consolas', 'Courier New', 'Monaco', 'monospace']
        }
    
    # ========== Font Scaling Operations ==========
    
    def scale_font(self, original_font: QFont, target_size: int, preserve_properties: bool = True) -> QFont:
        """
        Scale a font to a target size while preserving properties
        
        Args:
            original_font: Original font to scale
            target_size: Target size in points
            preserve_properties: Whether to preserve bold, italic, etc.
            
        Returns:
            QFont: Scaled font object
        """
        # Validate target size
        target_size = max(self.min_font_size, min(self.max_font_size, target_size))
        
        # Create cache key
        cache_key = self._create_font_cache_key(original_font, target_size)
        
        # Check cache first
        if self.cache_enabled and cache_key in self._font_cache:
            return self._font_cache[cache_key]
        
        # Create scaled font
        scaled_font = QFont(original_font)
        scaled_font.setPointSize(target_size)
        
        if preserve_properties:
            # Preserve all font properties
            scaled_font.setBold(original_font.bold())
            scaled_font.setItalic(original_font.italic())
            scaled_font.setUnderline(original_font.underline())
            scaled_font.setStrikeOut(original_font.strikeOut())
            scaled_font.setLetterSpacing(QFont.PercentageSpacing, original_font.letterSpacing())
            scaled_font.setWordSpacing(original_font.wordSpacing())
            scaled_font.setStretch(original_font.stretch())
            scaled_font.setStyleHint(original_font.styleHint())
            scaled_font.setStyleStrategy(original_font.styleStrategy())
        
        # Cache the font
        if self.cache_enabled:
            self._cache_font(cache_key, scaled_font)
        
        return scaled_font
    
    def scale_font_proportionally(self, original_font: QFont, zoom_factor: float) -> QFont:
        """
        Scale a font proportionally by a zoom factor
        
        Args:
            original_font: Original font to scale
            zoom_factor: Zoom factor (1.0 = 100%, 1.5 = 150%, etc.)
            
        Returns:
            QFont: Proportionally scaled font
        """
        current_size = original_font.pointSize()
        if current_size <= 0:
            current_size = 9  # Default fallback
            
        target_size = int(current_size * zoom_factor)
        return self.scale_font(original_font, target_size)
    
    def calculate_optimal_font_size(self, widget: QWidget, base_size: int, zoom_factor: float) -> int:
        """
        Calculate optimal font size for a specific widget type
        
        Args:
            widget: Target widget
            base_size: Base font size at 100% zoom
            zoom_factor: Current zoom factor
            
        Returns:
            int: Optimal font size in points
        """
        # Apply zoom factor
        scaled_size = base_size * zoom_factor
        
        # Apply widget-specific adjustments
        widget_type = widget.__class__.__name__
        
        if isinstance(widget, QTableWidget):
            # Tables benefit from slightly smaller fonts for better data density
            scaled_size *= 0.95
        elif isinstance(widget, (QCheckBox, QRadioButton)):
            # Checkboxes and radio buttons look better with slightly smaller text
            scaled_size *= 0.9
        elif isinstance(widget, QStatusBar):
            # Status bars typically use smaller fonts
            scaled_size *= 0.85
        elif isinstance(widget, (QLineEdit, QTextEdit, QComboBox)):
            # Input widgets benefit from consistent sizing
            scaled_size *= 1.0
        
        # Round and constrain
        final_size = max(self.min_font_size, min(self.max_font_size, round(scaled_size)))
        return int(final_size)
    
    # ========== Widget-Specific Font Operations ==========
    
    def apply_font_to_widget(self, widget: QWidget, font: QFont) -> bool:
        """
        Apply a font to a widget with special handling for complex widgets
        
        Args:
            widget: Target widget
            font: Font to apply
            
        Returns:
            bool: True if successful
        """
        try:
            # Standard font application
            widget.setFont(font)
            
            # Special handling for complex widgets
            if isinstance(widget, QTableWidget):
                self._apply_font_to_table(widget, font)
            elif isinstance(widget, QTabWidget):
                self._apply_font_to_tab_widget(widget, font)
            
            # Cache the applied font
            self._widget_font_cache[widget] = font
            
            # Emit signal
            self.font_scaled.emit(widget, font)
            
            return True
            
        except Exception as e:
            print(f"Warning: Failed to apply font to widget: {e}")
            return False
    
    def _apply_font_to_table(self, table: QTableWidget, font: QFont):
        """
        Apply font to table widget with special header handling
        
        Args:
            table: Table widget
            font: Font to apply
        """
        # Apply to table content
        table.setFont(font)
        
        # Apply to horizontal header
        if table.horizontalHeader():
            header_font = QFont(font)
            header_font.setBold(True)  # Headers typically bold
            table.horizontalHeader().setFont(header_font)
            
        # Apply to vertical header
        if table.verticalHeader():
            header_font = QFont(font)
            table.verticalHeader().setFont(header_font)
        
        # Adjust row heights based on font size
        metrics = QFontMetrics(font)
        row_height = max(25, metrics.height() + 8)  # 8px padding
        
        for row in range(table.rowCount()):
            table.setRowHeight(row, row_height)
    
    def _apply_font_to_tab_widget(self, tab_widget: QTabWidget, font: QFont):
        """
        Apply font to tab widget headers
        
        Args:
            tab_widget: Tab widget
            font: Font to apply
        """
        tab_bar = tab_widget.tabBar()
        if tab_bar:
            tab_bar.setFont(font)
    
    # ========== Font Caching System ==========
    
    def _create_font_cache_key(self, font: QFont, target_size: int) -> Tuple:
        """
        Create a cache key for a font configuration
        
        Args:
            font: Source font
            target_size: Target size
            
        Returns:
            Tuple: Cache key
        """
        return (
            font.family(),
            target_size,
            font.weight(),
            font.italic(),
            font.underline(),
            font.strikeOut(),
            font.stretch()
        )
    
    def _cache_font(self, cache_key: Tuple, font: QFont):
        """
        Cache a font object with size management
        
        Args:
            cache_key: Cache key
            font: Font to cache
        """
        # Manage cache size
        if len(self._font_cache) >= self.max_cache_size:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(self._font_cache.keys())[:self.max_cache_size // 4]
            for key in keys_to_remove:
                del self._font_cache[key]
        
        self._font_cache[cache_key] = font
    
    def clear_font_cache(self):
        """Clear all cached fonts"""
        self._font_cache.clear()
        self._widget_font_cache.clear()
        self.cache_cleared.emit()
    
    def get_cached_font_for_widget(self, widget: QWidget) -> Optional[QFont]:
        """
        Get cached font for a specific widget
        
        Args:
            widget: Target widget
            
        Returns:
            QFont or None: Cached font if available
        """
        return self._widget_font_cache.get(widget)
    
    # ========== Font Quality and Validation ==========
    
    def validate_font_readability(self, font: QFont, sample_text: str = "Sample Text 123") -> Dict[str, Any]:
        """
        Validate font readability and provide metrics
        
        Args:
            font: Font to validate
            sample_text: Text to use for testing
            
        Returns:
            Dict with readability metrics
        """
        metrics = QFontMetrics(font)
        
        # Calculate text dimensions
        text_width = metrics.horizontalAdvance(sample_text)
        text_height = metrics.height()
        
        # Readability assessment
        point_size = font.pointSize()
        readability_score = 100  # Start with perfect score
        
        # Penalize very small fonts
        if point_size < 8:
            readability_score -= (8 - point_size) * 15
        
        # Penalize very large fonts
        if point_size > 24:
            readability_score -= (point_size - 24) * 5
        
        # Bonus for good size range
        if 9 <= point_size <= 14:
            readability_score += 10
        
        return {
            'point_size': point_size,
            'text_width': text_width,
            'text_height': text_height,
            'readability_score': max(0, min(100, readability_score)),
            'is_readable': readability_score > 60,
            'ascent': metrics.ascent(),
            'descent': metrics.descent(),
            'leading': metrics.leading()
        }
    
    def suggest_font_improvements(self, widget: QWidget, current_font: QFont) -> List[str]:
        """
        Suggest font improvements for better readability
        
        Args:
            widget: Target widget
            current_font: Current font
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        validation = self.validate_font_readability(current_font)
        
        point_size = current_font.pointSize()
        
        if point_size < 8:
            suggestions.append(f"Font too small ({point_size}pt), consider increasing to 8-12pt")
        elif point_size > 20:
            suggestions.append(f"Font very large ({point_size}pt), consider reducing for better layout")
        
        if validation['readability_score'] < 60:
            suggestions.append("Font may be difficult to read, consider adjusting size")
        
        # Widget-specific suggestions
        if isinstance(widget, QTableWidget) and point_size > 12:
            suggestions.append("Large fonts in tables may reduce data visibility")
        
        if isinstance(widget, QStatusBar) and point_size > 10:
            suggestions.append("Status bar text typically uses smaller fonts")
        
        return suggestions
    
    # ========== Utility and Information Methods ==========
    
    def get_font_cache_stats(self) -> Dict[str, Any]:
        """
        Get font cache statistics
        
        Returns:
            Dict with cache statistics
        """
        return {
            'cached_fonts': len(self._font_cache),
            'widget_fonts': len(self._widget_font_cache),
            'original_fonts': len(self._original_fonts),
            'max_cache_size': self.max_cache_size,
            'cache_enabled': self.cache_enabled,
            'system_font_categories': {cat: len(fonts) for cat, fonts in self._system_fonts.items()}
        }
    
    def export_font_configuration(self, widget: QWidget) -> Dict[str, Any]:
        """
        Export complete font configuration for a widget
        
        Args:
            widget: Widget to export configuration for
            
        Returns:
            Dict with complete font configuration
        """
        current_font = widget.font()
        original_font = self._original_fonts.get(widget, current_font)
        
        return {
            'widget_info': {
                'class_name': widget.__class__.__name__,
                'object_name': widget.objectName()
            },
            'current_font': self.extract_widget_font_info(widget),
            'original_font': self.extract_widget_font_info(type('MockWidget', (), {'font': lambda: original_font})),
            'readability': self.validate_font_readability(current_font),
            'suggestions': self.suggest_font_improvements(widget, current_font)
        }
    
    def cleanup(self):
        """Clean up resources and caches"""
        self.clear_font_cache()
        self._original_fonts.clear()