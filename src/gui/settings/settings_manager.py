"""
Settings manager for handling application configuration persistence
Manages saving and loading of all application settings
"""

import json
import os
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal


class SettingsManager(QObject):
    """
    Manages application settings persistence and defaults
    """
    
    # Signals
    settings_changed = pyqtSignal(str, object)  # setting_key, new_value
    settings_loaded = pyqtSignal()
    settings_saved = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Settings file path
        self.settings_file = "transaction_matcher_settings.json"
        
        # Default settings
        self._default_settings = {
            'zoom': {
                'current_level': 100,
                'available_levels': [50, 75, 90, 100, 125, 150, 175, 200, 250, 300],
                'controls_scale_with_zoom': False,
                'remember_zoom_level': True
            },
            'files': {
                'last_fee_file': "",
                'last_transaction_file': "",
                'remember_file_paths': True
            },
            'ui': {
                'theme': 'default',
                'show_tooltips': True,
                'auto_save_sessions': False
            },
            'processing': {
                'parent_match_threshold': 70,
                'child_match_threshold': 70,
                'auto_process_on_file_select': False
            }
        }
        
        # Current settings (loaded from file or defaults)
        self._settings = {}
        
        # Load settings on initialization
        self.load_settings()
    
    def get_setting(self, key_path: str, default=None) -> Any:
        """
        Get a setting value using dot notation
        
        Args:
            key_path: Setting key path like 'zoom.current_level'
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        try:
            keys = key_path.split('.')
            value = self._settings
            
            for key in keys:
                value = value[key]
                
            return value
        except (KeyError, TypeError):
            return default
    
    def set_setting(self, key_path: str, value: Any) -> bool:
        """
        Set a setting value using dot notation
        
        Args:
            key_path: Setting key path like 'zoom.current_level'
            value: New value to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            keys = key_path.split('.')
            settings_ref = self._settings
            
            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in settings_ref:
                    settings_ref[key] = {}
                settings_ref = settings_ref[key]
            
            # Set the final value
            settings_ref[keys[-1]] = value
            
            # Emit change signal
            self.settings_changed.emit(key_path, value)
            
            return True
        except Exception as e:
            print(f"Failed to set setting {key_path}: {e}")
            return False
    
    def get_zoom_settings(self) -> Dict[str, Any]:
        """Get all zoom-related settings"""
        return self.get_setting('zoom', self._default_settings['zoom'].copy())
    
    def set_zoom_level(self, level: int):
        """Set current zoom level"""
        self.set_setting('zoom.current_level', level)
    
    def get_zoom_level(self) -> int:
        """Get current zoom level"""
        return self.get_setting('zoom.current_level', 100)
    
    def get_file_settings(self) -> Dict[str, Any]:
        """Get all file-related settings"""
        return self.get_setting('files', self._default_settings['files'].copy())
    
    def set_last_fee_file(self, file_path: str):
        """Set last used fee file path"""
        if self.get_setting('files.remember_file_paths', True):
            self.set_setting('files.last_fee_file', file_path)
    
    def set_last_transaction_file(self, file_path: str):
        """Set last used transaction file path"""
        if self.get_setting('files.remember_file_paths', True):
            self.set_setting('files.last_transaction_file', file_path)
    
    def load_settings(self) -> bool:
        """
        Load settings from file
        
        Returns:
            True if loaded successfully, False if using defaults
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # Merge with defaults to ensure all required keys exist
                self._settings = self._merge_with_defaults(loaded_settings)
                
                self.settings_loaded.emit()
                print(f"✓ Settings loaded from {self.settings_file}")
                return True
            else:
                # Use defaults
                self._settings = self._default_settings.copy()
                print("✓ Using default settings")
                return False
                
        except Exception as e:
            print(f"✗ Failed to load settings: {e}")
            self._settings = self._default_settings.copy()
            return False
    
    def save_settings(self) -> bool:
        """
        Save current settings to file
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            
            self.settings_saved.emit()
            print(f"✓ Settings saved to {self.settings_file}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to save settings: {e}")
            return False
    
    def reset_to_defaults(self, category: str = None):
        """
        Reset settings to defaults
        
        Args:
            category: Specific category to reset, or None for all
        """
        if category and category in self._default_settings:
            self._settings[category] = self._default_settings[category].copy()
            print(f"✓ Reset {category} settings to defaults")
        else:
            self._settings = self._default_settings.copy()
            print("✓ Reset all settings to defaults")
        
        # Auto-save after reset
        self.save_settings()
    
    def _merge_with_defaults(self, loaded_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded settings with defaults to ensure all keys exist"""
        def merge_dicts(default: dict, loaded: dict) -> dict:
            result = default.copy()
            for key, value in loaded.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dicts(result[key], value)
                else:
                    result[key] = value
            return result
        
        return merge_dicts(self._default_settings, loaded_settings)
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all current settings"""
        return self._settings.copy()
    
    def export_settings(self, file_path: str) -> bool:
        """Export settings to a specific file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Failed to export settings: {e}")
            return False
    
    def import_settings(self, file_path: str) -> bool:
        """Import settings from a specific file"""
        try:
            if not os.path.exists(file_path):
                return False
                
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            self._settings = self._merge_with_defaults(imported_settings)
            self.save_settings()  # Save the imported settings
            
            return True
        except Exception as e:
            print(f"Failed to import settings: {e}")
            return False


# Global settings manager instance
_global_settings_manager = None


def get_settings_manager() -> SettingsManager:
    """Get the global settings manager instance"""
    global _global_settings_manager
    if _global_settings_manager is None:
        _global_settings_manager = SettingsManager()
    return _global_settings_manager


def save_settings():
    """Convenience function to save settings"""
    manager = get_settings_manager()
    return manager.save_settings()


# Auto-save on module cleanup
import atexit
atexit.register(save_settings)