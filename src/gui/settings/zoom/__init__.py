"""
Zoom module within settings package
Simplified zoom system for settings integration
"""

from .zoom_system import (
    ConsolidatedZoomSystem,
    get_zoom_system,
    initialize_zoom_system,
    cleanup_zoom_system
)

# Main functions for external use
def initialize_zoom_system_complete():
    """Initialize zoom system without UI injection"""
    return initialize_zoom_system()

def get_zoom_manager():
    """Compatibility function"""
    return get_zoom_system()

def cleanup_zoom_system_complete():
    """Clean up zoom system"""
    cleanup_zoom_system()

__all__ = [
    'initialize_zoom_system_complete',
    'get_zoom_manager', 
    'cleanup_zoom_system_complete',
    'ConsolidatedZoomSystem',
    'get_zoom_system'
]