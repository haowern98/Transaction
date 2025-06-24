"""
Application configuration management
Handles all configuration settings including zoom preferences, UI settings, and persistence
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt5.QtCore import QSettings, QStandardPaths


class AppConfig:
    """
    Central configuration manager for the Transaction Matcher application
    Handles zoom settings, UI preferences, and file paths
    """
    
    # Default zoom configuration
    DEFAULT_ZOOM_LEVEL = 100
    MIN_ZOOM_LEVEL = 50
    MAX_ZOOM_LEVEL = 300
    ZOOM_INCREMENT = 25
    ZOOM_LEVELS = [50, 75, 90, 100, 110, 125, 150, 175, 200, 250, 300]
    
    # Default font sizes for different UI elements (at 100% zoom)
    BASE_FONT_SIZES = {
        'window_title': 12,
        'tab_header': 10,
        'button': 9,
        'label': 9,
        'table_content': 9,
        'table_header': 10,
        'status_bar': 8,
        'dialog': 9,
        'menu': 9,
        'tooltip': 8
    }
    
    def __init__(self):
        """Initialize configuration manager with default settings"""
        # Use QSettings for cross-platform config storage
        self.settings = QSettings('TransactionMatcher', 'FeeMatcher')
        
        # Current configuration values
        self._zoom_level = self.DEFAULT_ZOOM_LEVEL
        self._font_sizes = self.BASE_FONT_SIZES.copy()
        self._ui_preferences = {}
        self._file_paths = {}
        
        # Load existing configuration
        self.load_configuration()
    
    # ========== Zoom Configuration ==========
    
    def get_zoom_level(self) -> int:
        """Get current zoom level percentage"""
        return self._zoom_level
    
    def set_zoom_level(self, zoom_level: int) -> bool:
        """
        Set zoom level with validation
        
        Args:
            zoom_level: Zoom percentage (50-300)
            
        Returns:
            bool: True if valid and set, False otherwise
        """
        if self.MIN_ZOOM_LEVEL <= zoom_level <= self.MAX_ZOOM_LEVEL:
            self._zoom_level = zoom_level
            self._update_scaled_font_sizes()
            return True
        return False
    
    def get_next_zoom_level(self, direction: str = 'in') -> int:
        """
        Get the next zoom level in the specified direction
        
        Args:
            direction: 'in' for zoom in, 'out' for zoom out
            
        Returns:
            int: Next zoom level, or current if at limit
        """
        current_index = self._find_closest_zoom_index()
        
        if direction == 'in' and current_index < len(self.ZOOM_LEVELS) - 1:
            return self.ZOOM_LEVELS[current_index + 1]
        elif direction == 'out' and current_index > 0:
            return self.ZOOM_LEVELS[current_index - 1]
        
        return self._zoom_level
    
    def _find_closest_zoom_index(self) -> int:
        """Find the index of the closest predefined zoom level"""
        closest_index = 0
        min_diff = abs(self.ZOOM_LEVELS[0] - self._zoom_level)
        
        for i, level in enumerate(self.ZOOM_LEVELS):
            diff = abs(level - self._zoom_level)
            if diff < min_diff:
                min_diff = diff
                closest_index = i
                
        return closest_index
    
    def reset_zoom(self):
        """Reset zoom to default level"""
        self.set_zoom_level(self.DEFAULT_ZOOM_LEVEL)
    
    # ========== Font Configuration ==========
    
    def get_font_size(self, element_type: str) -> int:
        """
        Get current font size for a specific UI element type
        
        Args:
            element_type: Type of UI element (button, label, table_content, etc.)
            
        Returns:
            int: Font size in points
        """
        return self._font_sizes.get(element_type, self.BASE_FONT_SIZES.get(element_type, 9))
    
    def get_all_font_sizes(self) -> Dict[str, int]:
        """Get all current font sizes"""
        return self._font_sizes.copy()
    
    def get_base_font_sizes(self) -> Dict[str, int]:
        """Get base font sizes (100% zoom)"""
        return self.BASE_FONT_SIZES.copy()
    
    def _update_scaled_font_sizes(self):
        """Update font sizes based on current zoom level"""
        zoom_factor = self._zoom_level / 100.0
        
        for element_type, base_size in self.BASE_FONT_SIZES.items():
            scaled_size = max(6, int(base_size * zoom_factor))  # Minimum 6pt font
            self._font_sizes[element_type] = scaled_size
    
    # ========== UI Preferences ==========
    
    def get_ui_preference(self, key: str, default: Any = None) -> Any:
        """Get a UI preference value"""
        return self._ui_preferences.get(key, default)
    
    def set_ui_preference(self, key: str, value: Any):
        """Set a UI preference value"""
        self._ui_preferences[key] = value
    
    def get_window_geometry(self) -> Optional[bytes]:
        """Get saved window geometry"""
        return self.settings.value('window_geometry')
    
    def set_window_geometry(self, geometry: bytes):
        """Save window geometry"""
        self.settings.setValue('window_geometry', geometry)
    
    def get_window_state(self) -> Optional[bytes]:
        """Get saved window state"""
        return self.settings.value('window_state')
    
    def set_window_state(self, state: bytes):
        """Save window state"""
        self.settings.setValue('window_state', state)
    
    # ========== File Path Management ==========
    
    def get_last_fee_file_path(self) -> str:
        """Get the last used fee record file path"""
        return self.settings.value('last_fee_file', '')
    
    def set_last_fee_file_path(self, path: str):
        """Save the last used fee record file path"""
        self.settings.setValue('last_fee_file', path)
    
    def get_last_transaction_file_path(self) -> str:
        """Get the last used transaction file path"""
        return self.settings.value('last_transaction_file', '')
    
    def set_last_transaction_file_path(self, path: str):
        """Save the last used transaction file path"""
        self.settings.setValue('last_transaction_file', path)
    
    def get_last_export_directory(self) -> str:
        """Get the last used export directory"""
        default_dir = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        return self.settings.value('last_export_dir', default_dir)
    
    def set_last_export_directory(self, path: str):
        """Save the last used export directory"""
        self.settings.setValue('last_export_dir', path)
    
    # ========== Configuration Persistence ==========
    
    def load_configuration(self):
        """Load configuration from persistent storage"""
        try:
            # Load zoom level
            saved_zoom = self.settings.value('zoom_level', self.DEFAULT_ZOOM_LEVEL, type=int)
            self.set_zoom_level(saved_zoom)
            
            # Load UI preferences
            ui_prefs = self.settings.value('ui_preferences', {})
            if isinstance(ui_prefs, dict):
                self._ui_preferences = ui_prefs
            
        except Exception as e:
            print(f"Warning: Failed to load configuration: {e}")
            # Use defaults if loading fails
            self.reset_to_defaults()
    
    def save_configuration(self):
        """Save current configuration to persistent storage"""
        try:
            # Save zoom level
            self.settings.setValue('zoom_level', self._zoom_level)
            
            # Save UI preferences
            self.settings.setValue('ui_preferences', self._ui_preferences)
            
            # Ensure settings are written to disk
            self.settings.sync()
            
        except Exception as e:
            print(f"Warning: Failed to save configuration: {e}")
    
    def reset_to_defaults(self):
        """Reset all configuration to default values"""
        self._zoom_level = self.DEFAULT_ZOOM_LEVEL
        self._font_sizes = self.BASE_FONT_SIZES.copy()
        self._ui_preferences = {}
        self._file_paths = {}
        self._update_scaled_font_sizes()
    
    def export_configuration(self, file_path: str) -> bool:
        """
        Export configuration to JSON file
        
        Args:
            file_path: Path to save configuration file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            config_data = {
                'zoom_level': self._zoom_level,
                'ui_preferences': self._ui_preferences,
                'base_font_sizes': self.BASE_FONT_SIZES,
                'version': '1.0'
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exporting configuration: {e}")
            return False
    
    def import_configuration(self, file_path: str) -> bool:
        """
        Import configuration from JSON file
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Import zoom level
            if 'zoom_level' in config_data:
                self.set_zoom_level(config_data['zoom_level'])
            
            # Import UI preferences
            if 'ui_preferences' in config_data:
                self._ui_preferences = config_data['ui_preferences']
            
            return True
        except Exception as e:
            print(f"Error importing configuration: {e}")
            return False


# Global configuration instance
_global_config = None


def get_config() -> AppConfig:
    """
    Get the global configuration instance
    
    Returns:
        AppConfig: Global configuration manager
    """
    global _global_config
    if _global_config is None:
        _global_config = AppConfig()
    return _global_config


def save_config():
    """Save the global configuration"""
    if _global_config:
        _global_config.save_configuration()


# Automatically save configuration on module cleanup
import atexit
atexit.register(save_config)