# File: src/gui/outstanding_payments_tab/outstanding_payments_tab.py
"""
Outstanding Payments Tab - Simplified version with title, refresh button, and single export button
Shows parents and their outstanding months in a clean two-column format
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                            QTableWidget, QTableWidgetItem, QPushButton, QLabel, 
                            QHeaderView, QMessageBox, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from typing import Dict, Any, List
import os

from .payment_analyzer import PaymentAnalyzer
from .payment_export import PaymentExporter


class AnalysisThread(QThread):
    """Background thread for analyzing outstanding payments across all months"""
    
    finished = pyqtSignal(dict)  # analysis_results
    error = pyqtSignal(str)      # error_message
    
    def __init__(self, fee_record_path: str):
        super().__init__()
        self.fee_record_path = fee_record_path
        
    def run(self):
        """Run payment analysis for all months"""
        try:
            analyzer = PaymentAnalyzer()
            
            if not analyzer.load_fee_record(self.fee_record_path):
                self.error.emit("Failed to load fee record file")
                return
            
            # Get all available months
            available_months = analyzer.get_available_months()
            
            if not available_months:
                self.error.emit("No months found in fee record")
                return
            
            # Analyze each month to find outstanding payments
            all_outstanding = {}  # {parent_name: [list_of_outstanding_months]}
            
            for month in available_months:
                results = analyzer.analyze_month_payments(
                    month, 
                    include_zero_amounts=False,
                    empty_cells_unpaid=True
                )
                
                if 'error' not in results:
                    unpaid_parents = results.get('unpaid_parents', [])
                    month_display = results.get('month_display', month)
                    
                    for parent_data in unpaid_parents:
                        parent_name = parent_data.get('parent_name', '')
                        date_value = parent_data.get('date_value', '')
                        amount_value = parent_data.get('amount_value')
                        
                        # FIXED LOGIC: Only include if BOTH date AND amount are empty
                        date_is_empty = not date_value or date_value.strip() == ''
                        amount_is_empty = amount_value is None
                        
                        # Only add to outstanding if BOTH cells are completely empty
                        if parent_name and date_is_empty and amount_is_empty:
                            if parent_name not in all_outstanding:
                                all_outstanding[parent_name] = []
                            all_outstanding[parent_name].append(month_display)
            
            # Format results
            outstanding_list = []
            for parent_name, months in all_outstanding.items():
                outstanding_list.append({
                    'parent_name': parent_name,
                    'outstanding_months': months,
                    'outstanding_months_str': ', '.join(sorted(months))
                })
            
            # Sort by parent name
            outstanding_list.sort(key=lambda x: x['parent_name'])
            
            results = {
                'outstanding_parents': outstanding_list,
                'total_parents_with_outstanding': len(outstanding_list),
                'total_months_checked': len(available_months)
            }
            
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))
        finally:
            if 'analyzer' in locals():
                analyzer.close()


class OutstandingPaymentsTab(QWidget):
    """
    Simplified Outstanding Payments Tab
    Shows title, description, results table with refresh button, and single export button
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize components
        self.payment_exporter = PaymentExporter(self)
        self.analysis_thread = None
        self.current_results = {}
        
        # Get settings manager for fee record path
        try:
            from gui.settings import get_settings_manager
            self.settings_manager = get_settings_manager()
        except ImportError:
            self.settings_manager = None
        
        self.setup_ui()
        self.auto_generate_if_ready()
        
    def setup_ui(self):
        """Setup simplified UI with title, table with refresh button, and export button"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)  # Same as general settings
        main_layout.setSpacing(0)
        
        # Header section - same style as General Settings
        header_section = self._create_header_section()
        main_layout.addWidget(header_section)
        
        # Add spacing after header
        main_layout.addSpacing(40)
        
        # Results section (takes most space)
        results_section = self._create_results_section()
        main_layout.addWidget(results_section)
        main_layout.setStretchFactor(results_section, 1)
        
        # Export button at bottom center
        export_section = self._create_export_section()
        main_layout.addWidget(export_section)
        
    def _create_header_section(self):
        """Create header with title and description - same style as General Settings"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(11)
        
        # Main title - SAME FONT as General Settings
        title_label = QLabel("Outstanding Payments")
        title_label.setFont(QFont("Tahoma", 12, QFont.Bold))  # Same as General Settings
        title_label.setStyleSheet("color: #1f1f1f;")
        header_layout.addWidget(title_label)
        
        # Subtitle - SAME FONT as General Settings
        subtitle_label = QLabel("View parents who have not made payments for specific months")
        subtitle_label.setFont(QFont("Tahoma", 8, QFont.Normal))  # Same as General Settings
        subtitle_label.setStyleSheet("color: #1f1f1f;")
        header_layout.addWidget(subtitle_label)
        
        return header_widget
        
    def _create_results_section(self):
        """Create main results table with refresh button"""
        results_group = QGroupBox("Outstanding Payments Results")
        results_layout = QVBoxLayout(results_group)
        
        # Status row with refresh button
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Checking for outstanding payments...")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        # Refresh button - DEFAULT STYLING (matches existing project buttons)
        self.refresh_btn = QPushButton("Refresh List")
        self.refresh_btn.clicked.connect(self.generate_outstanding_list)
        self.refresh_btn.setToolTip("Refresh the outstanding payments list")
        status_layout.addWidget(self.refresh_btn)
        
        results_layout.addLayout(status_layout)
        
        # Results table
        self.results_table = QTableWidget()
        self.setup_results_table()
        results_layout.addWidget(self.results_table)
        
        return results_group
        
    def _create_export_section(self):
        """Create single export button centered at bottom"""
        export_widget = QWidget()
        export_layout = QHBoxLayout(export_widget)
        export_layout.setContentsMargins(0, 20, 0, 0)  # Top margin for spacing
        
        # Center the button
        export_layout.addStretch()
        
        # Single export button - DEFAULT STYLING (matches existing project buttons)
        self.export_csv_btn = QPushButton("Export to CSV")
        self.export_csv_btn.clicked.connect(self.export_to_csv)
        self.export_csv_btn.setEnabled(False)
        export_layout.addWidget(self.export_csv_btn)
        
        export_layout.addStretch()
        
        return export_widget
        
    def setup_results_table(self):
        """Setup the two-column results table"""
        # Set columns: Parent Name | Outstanding Months
        headers = ["Parent Name", "Outstanding Months"]
        self.results_table.setColumnCount(len(headers))
        self.results_table.setHorizontalHeaderLabels(headers)
        
        # Configure table properties
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setSortingEnabled(True)
        
        # Set column widths
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # Parent Name
        header.setSectionResizeMode(1, QHeaderView.Stretch)     # Outstanding Months
        
        self.results_table.setColumnWidth(0, 300)  # Parent Name width
        
    def auto_generate_if_ready(self):
        """Automatically generate outstanding list if fee record is available"""
        fee_record_path = self.get_fee_record_file_path()
        
        if fee_record_path and os.path.exists(fee_record_path):
            self.generate_outstanding_list()
        else:
            if not fee_record_path:
                self.status_label.setText("No fee record file configured. Please set up in Settings → File Paths")
            else:
                self.status_label.setText(f"Fee record file not found: {fee_record_path}")
    
    def load_fee_record_path(self):
        """Load fee record path from settings and refresh"""
        self.auto_generate_if_ready()
    
    def get_fee_record_file_path(self) -> str:
        """Get fee record file path from settings"""
        try:
            if self.settings_manager:
                return self.settings_manager.get_setting('files.fee_record_file', '')
            return ""
        except Exception:
            return ""
    
    def generate_outstanding_list(self):
        """Generate outstanding payments list for all months"""
        fee_record_path = self.get_fee_record_file_path()
        
        if not fee_record_path or not os.path.exists(fee_record_path):
            self.status_label.setText("Fee record file not found. Please check Settings → File Paths.")
            return
        
        # Disable refresh button during analysis
        self.refresh_btn.setEnabled(False)
        
        # Update status
        self.status_label.setText("Analyzing outstanding payments across all months...")
        self.export_csv_btn.setEnabled(False)
        
        # Start analysis thread
        self.analysis_thread = AnalysisThread(fee_record_path)
        self.analysis_thread.finished.connect(self.analysis_finished)
        self.analysis_thread.error.connect(self.analysis_error)
        self.analysis_thread.start()
    
    def analysis_finished(self, results: Dict[str, Any]):
        """Handle completed analysis"""
        self.current_results = results
        
        # Re-enable refresh button
        self.refresh_btn.setEnabled(True)
        
        # Populate results table
        self.populate_results_table(results)
        
        # Update status
        total_parents = results.get('total_parents_with_outstanding', 0)
        total_months = results.get('total_months_checked', 0)
        
        if total_parents > 0:
            self.status_label.setText(
                f"Found {total_parents} parents with outstanding payments across {total_months} months"
            )
            self.export_csv_btn.setEnabled(True)
        else:
            self.status_label.setText(f"All parents have paid for all {total_months} months - no outstanding payments!")
            self.export_csv_btn.setEnabled(False)
    
    def analysis_error(self, error_message: str):
        """Handle analysis errors"""
        # Re-enable refresh button
        self.refresh_btn.setEnabled(True)
        
        self.status_label.setText(f"Analysis failed: {error_message}")
        self.export_csv_btn.setEnabled(False)
    
    def populate_results_table(self, results: Dict[str, Any]):
        """Populate the two-column results table"""
        outstanding_parents = results.get('outstanding_parents', [])
        
        # Set row count
        self.results_table.setRowCount(len(outstanding_parents))
        
        # Populate table
        for row, parent_data in enumerate(outstanding_parents):
            # Parent Name
            parent_name = parent_data.get('parent_name', '')
            self.results_table.setItem(row, 0, QTableWidgetItem(parent_name))
            
            # Outstanding Months (comma-separated)
            outstanding_months = parent_data.get('outstanding_months_str', '')
            self.results_table.setItem(row, 1, QTableWidgetItem(outstanding_months))
    
    def export_to_csv(self):
        """Export outstanding payments to CSV"""
        if not self.current_results:
            QMessageBox.warning(self, "Warning", "No results to export.")
            return
        
        # Prepare data for CSV export
        export_data = {
            'outstanding_parents': self.current_results.get('outstanding_parents', []),
            'total_parents': self.current_results.get('total_parents_with_outstanding', 0),
            'summary': f"Outstanding payments report - {self.current_results.get('total_parents_with_outstanding', 0)} parents with outstanding payments"
        }
        
        self.payment_exporter.export_outstanding_payments_csv(export_data, self)