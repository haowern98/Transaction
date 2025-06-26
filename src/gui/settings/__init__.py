"""
Settings package for Transaction Matcher GUI
Provides organized settings management and UI components
"""

from .settings_tab import SettingsTab
from .general_subtab import GeneralSettingsPanel
from .settings_manager import SettingsManager, get_settings_manager

# Import zoom system from within settings
from .zoom import (
    get_zoom_system,
    initialize_zoom_system_complete,
    cleanup_zoom_system_complete,
    get_zoom_manager
)

__all__ = [
    'SettingsTab', 
    'GeneralSettingsPanel',
    'SettingsManager', 
    'get_settings_manager',
    'get_zoom_system',
    'initialize_zoom_system_complete',
    'cleanup_zoom_system_complete',
    'get_zoom_manager'
]