# File: src/gui/outstanding_payments_tab/__init__.py
"""
Outstanding Payments Tab Module
Provides functionality to track and manage outstanding fee payments

This module contains:
- OutstandingPaymentsTab: Main UI tab for outstanding payments analysis
- PaymentAnalyzer: Core logic for analyzing fee records and identifying unpaid parents
- PaymentExporter: Export functionality for outstanding payment data

Usage:
    from gui.outstanding_payments_tab import OutstandingPaymentsTab
    
    # Create tab
    outstanding_tab = OutstandingPaymentsTab(parent)
    
    # Add to main window
    tab_widget.addTab(outstanding_tab, "Outstanding Payments")
"""

from .outstanding_payments_tab import OutstandingPaymentsTab
from .payment_analyzer import PaymentAnalyzer
from .payment_export import PaymentExporter

__all__ = [
    'OutstandingPaymentsTab',
    'PaymentAnalyzer', 
    'PaymentExporter'
]

# Version information
__version__ = "1.0.0"
__author__ = "Transaction Matcher Team"

# Module metadata
MODULE_NAME = "Outstanding Payments Tab"
MODULE_DESCRIPTION = "Fee payment tracking and outstanding payment management"