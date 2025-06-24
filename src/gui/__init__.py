"""
GUI components for the Transaction Matcher application
Provides a complete GUI framework for fee transaction matching and editing
"""

# Main window and application entry point
from .transaction_window import TransactionMatcherWindow, ProcessingThread, run_gui_application

# Core table components
from .table_wrapper import IntegratedEditableTable
from .editable_table import EditableTableWidget
from .table_operations import TableOperations

# Data management
from .data_manager import TableDataManager
from .validation_tracker import ValidationTracker

# Session and export management
from .session_manager import (
    SessionManager, 
    save_table_session, 
    load_table_session,
    export_table_to_excel,
    export_table_to_csv,
    save_detailed_report
)

# Date filtering
from .date_filter import DateFilterDialog, DateFilterProcessor

# Main exports for external use
__all__ = [
    # Main application
    'TransactionMatcherWindow',
    'run_gui_application',
    
    # Core table system
    'IntegratedEditableTable',
    'EditableTableWidget', 
    'TableOperations',
    
    # Data management
    'TableDataManager',
    'ValidationTracker',
    
    # Session management
    'SessionManager',
    'save_table_session',
    'load_table_session', 
    'export_table_to_excel',
    'export_table_to_csv',
    'save_detailed_report',
    
    # Date filtering
    'DateFilterDialog',
    'DateFilterProcessor',
    
    # Background processing
    'ProcessingThread'
]