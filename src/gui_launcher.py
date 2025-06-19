"""
Main window for the Transaction Matcher GUI application
Updated with Excel-like editing capabilities and transaction date column
Save this as: src/gui_launcher.py
"""
import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                            QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
                            QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
                            QFileDialog, QMessageBox, QHeaderView, QStatusBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# Add the parent directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import pandas as pd

# Import the new editable table integration
from gui.table_integration import IntegratedEditableTable
print("✅ Successfully imported IntegratedEditableTable")


class ProcessingThread(QThread):
    """Background thread for processing files"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, fee_file_path, transaction_file_path):
        super().__init__()
        self.fee_file_path = fee_file_path
        self.transaction_file_path = transaction_file_path
    
    def run(self):
        try:
            # Import the processing function
            from main import process_fee_matching_gui
            results = process_fee_matching_gui(self.fee_file_path, self.transaction_file_path)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class TransactionMatcherWindow(QMainWindow):
    """Main window for the Transaction Matcher application"""
    
    def __init__(self):
        super().__init__()
        # Set default file paths
        self.fee_file_path = r"C:\Users\user\Downloads\Parent-Student Matching Pair.xlsx"
        self.transaction_file_path = r"C:\Users\user\Downloads\Fee Statements\3985094904Statement (9).csv"
        self.results_data = []
        
        # Initialize the editable table
        self.editable_table = IntegratedEditableTable(self)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Fee Transaction Matcher")
        self.setGeometry(100, 100, 1200, 800)  # Made wider to accommodate editing toolbar
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.addWidget(self.tab_widget)
        
        # Create status bar FIRST (before creating tabs)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create tabs
        self.create_file_processing_tab()
        self.create_settings_tab()
        
    def create_file_processing_tab(self):
        """Create the file processing tab"""
        tab = QWidget()
        self.tab_widget.addTab(tab, "File Processing")
        
        layout = QVBoxLayout(tab)
        
        # File Selection Group
        file_group = QGroupBox("File Selection")
        file_layout = QVBoxLayout(file_group)
        
        # Fee Record File row
        fee_layout = QHBoxLayout()
        fee_layout.addWidget(QLabel("Fee Record File:"))
        self.fee_file_input = QLineEdit()
        self.fee_file_input.setText(self.fee_file_path)  # Set default path
        self.fee_file_input.setPlaceholderText("Select the Excel file containing parent-student records...")
        # Connect text changes to update internal variable
        self.fee_file_input.textChanged.connect(self.on_fee_file_changed)
        fee_layout.addWidget(self.fee_file_input)
        self.fee_browse_btn = QPushButton("Browse...")
        self.fee_browse_btn.clicked.connect(self.browse_fee_file)
        fee_layout.addWidget(self.fee_browse_btn)
        file_layout.addLayout(fee_layout)
        
        # Transaction File row
        trans_layout = QHBoxLayout()
        trans_layout.addWidget(QLabel("Transaction File:"))
        self.transaction_file_input = QLineEdit()
        self.transaction_file_input.setText(self.transaction_file_path)  # Set default path
        self.transaction_file_input.setPlaceholderText("Select the CSV file containing transaction data...")
        # Connect text changes to update internal variable
        self.transaction_file_input.textChanged.connect(self.on_transaction_file_changed)
        trans_layout.addWidget(self.transaction_file_input)
        self.trans_browse_btn = QPushButton("Browse...")
        self.trans_browse_btn.clicked.connect(self.browse_transaction_file)
        trans_layout.addWidget(self.trans_browse_btn)
        file_layout.addLayout(trans_layout)
        
        # Process buttons row
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.process_btn = QPushButton("Process Files")
        self.process_btn.clicked.connect(self.process_files)
        self.process_btn.setEnabled(False)
        button_layout.addWidget(self.process_btn)
        
        self.clear_btn = QPushButton("Clear Results")
        self.clear_btn.clicked.connect(self.clear_results)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        file_layout.addLayout(button_layout)
        
        layout.addWidget(file_group)
        
        # Check if default files are ready on startup
        self.check_files_ready()
        
        # Results Group (takes up most space)
        results_group = QGroupBox("Matching Results")
        results_layout = QVBoxLayout(results_group)
        
        # Summary row
        self.summary_label = QLabel("No results yet. Select files and click 'Process Files' to begin.")
        self.summary_label.setFont(QFont("Arial", 9))
        results_layout.addWidget(self.summary_label)
        
        # Results table (now using editable table)
        self.results_table = self.editable_table.table
        self.editable_table.setup_results_table()
        results_layout.addWidget(self.results_table)
        
        # Add editing toolbar
        self.editable_table.add_toolbar_buttons(results_layout)
        
        # Export buttons row
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        
        self.export_excel_btn = QPushButton("Export to Excel")
        self.export_excel_btn.clicked.connect(self.export_to_excel)
        self.export_excel_btn.setEnabled(False)
        export_layout.addWidget(self.export_excel_btn)
        
        self.export_csv_btn = QPushButton("Export to CSV")
        self.export_csv_btn.clicked.connect(self.export_to_csv)
        self.export_csv_btn.setEnabled(False)
        export_layout.addWidget(self.export_csv_btn)
        
        self.save_report_btn = QPushButton("Save Report")
        self.save_report_btn.clicked.connect(self.save_report)
        self.save_report_btn.setEnabled(False)
        export_layout.addWidget(self.save_report_btn)
        
        export_layout.addStretch()
        results_layout.addLayout(export_layout)
        
        layout.addWidget(results_group)
        
        # Set stretch factors to make results section much larger
        layout.setStretchFactor(file_group, 0)
        layout.setStretchFactor(results_group, 1)
    
    def create_settings_tab(self):
        """Create the settings tab (empty for now)"""
        tab = QWidget()
        self.tab_widget.addTab(tab, "Settings")
        
        layout = QVBoxLayout(tab)
        
        # Empty placeholder
        placeholder = QLabel("Settings will be added later")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setFont(QFont("Arial", 12))
        layout.addWidget(placeholder)
    
    def on_fee_file_changed(self, text):
        """Handle fee file path changes"""
        self.fee_file_path = text.strip()
        self.check_files_ready()
    
    def on_transaction_file_changed(self, text):
        """Handle transaction file path changes"""
        self.transaction_file_path = text.strip()
        self.check_files_ready()
    
    def browse_fee_file(self):
        """Browse for fee record file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Fee Record File", 
            "", 
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        if file_path:
            self.fee_file_input.setText(file_path)
    
    def browse_transaction_file(self):
        """Browse for transaction file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Transaction File", 
            "", 
            "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.transaction_file_input.setText(file_path)
    
    def check_files_ready(self):
        """Check if both files exist and enable/disable process button"""
        fee_ready = os.path.exists(self.fee_file_path) if self.fee_file_path else False
        trans_ready = os.path.exists(self.transaction_file_path) if self.transaction_file_path else False
        
        self.process_btn.setEnabled(fee_ready and trans_ready)
        
        if fee_ready and trans_ready:
            self.status_bar.showMessage("Files ready - click 'Process Files' to begin")
        elif not fee_ready and not trans_ready:
            self.status_bar.showMessage("Please select both fee record and transaction files")
        elif not fee_ready:
            self.status_bar.showMessage("Please select a valid fee record file")
        else:
            self.status_bar.showMessage("Please select a valid transaction file")
    
    def process_files(self):
        """Process the selected files"""
        if not self.fee_file_path or not self.transaction_file_path:
            QMessageBox.warning(self, "Warning", "Please select both files before processing.")
            return
        
        if not os.path.exists(self.fee_file_path):
            QMessageBox.warning(self, "Warning", f"Fee file not found: {self.fee_file_path}")
            return
            
        if not os.path.exists(self.transaction_file_path):
            QMessageBox.warning(self, "Warning", f"Transaction file not found: {self.transaction_file_path}")
            return
        
        # Disable process button during processing
        self.process_btn.setEnabled(False)
        self.status_bar.showMessage("Processing files...")
        
        # Start processing in background thread
        self.processing_thread = ProcessingThread(self.fee_file_path, self.transaction_file_path)
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.error.connect(self.on_processing_error)
        self.processing_thread.start()
    
    def on_processing_finished(self, results):
        """Handle completion of file processing"""
        self.results_data = results.get('results', [])
        self.populate_results_table()
        self.update_summary(results)
        
        # Re-enable buttons
        self.process_btn.setEnabled(True)
        self.export_excel_btn.setEnabled(True)
        self.export_csv_btn.setEnabled(True)
        self.save_report_btn.setEnabled(True)
        
        self.status_bar.showMessage("Processing completed successfully")
    
    def on_processing_error(self, error_message):
        """Handle processing errors"""
        QMessageBox.critical(self, "Processing Error", f"An error occurred during processing:\n\n{error_message}")
        self.process_btn.setEnabled(True)
        self.status_bar.showMessage("Processing failed")
    
    def populate_results_table(self):
        """Populate the results table with data"""
        self.editable_table.populate_results_table(self.results_data)
    
    def update_summary(self, results):
        """Update the summary label with statistics"""
        total = results.get('total_processed', 0)
        matched = results.get('matched_count', 0)
        unmatched = results.get('unmatched_count', 0)
        parent_matched = results.get('parent_matched_count', 0)
        child_matched = results.get('child_matched_count', 0)
        
        match_rate = (matched / total * 100) if total > 0 else 0
        parent_rate = (parent_matched / total * 100) if total > 0 else 0
        child_rate = (child_matched / total * 100) if total > 0 else 0
        
        summary_text = (f"Total: {total} | Matched: {matched} | Unmatched: {unmatched} | "
                       f"Match Rate: {match_rate:.1f}% | Parent Matches: {parent_rate:.1f}% | "
                       f"Child Matches: {child_rate:.1f}%")
        
        self.summary_label.setText(summary_text)
    
    def clear_results(self):
        """Clear all results and reset the interface"""
        self.editable_table.clear_table()
        self.results_table.setRowCount(0)
        self.results_data = []
        self.summary_label.setText("No results yet. Select files and click 'Process Files' to begin.")
        
        # Disable export buttons
        self.export_excel_btn.setEnabled(False)
        self.export_csv_btn.setEnabled(False)
        self.save_report_btn.setEnabled(False)
        
        self.status_bar.showMessage("Results cleared")
    
    def new_session(self):
        """Start a new session"""
        # Reset to default file paths
        self.fee_file_path = r"C:\Users\user\Downloads\Parent-Student Matching Pair.xlsx"
        self.transaction_file_path = r"C:\Users\user\Downloads\Fee Statements\3985094904Statement (9).csv"
        self.fee_file_input.setText(self.fee_file_path)
        self.transaction_file_input.setText(self.transaction_file_path)
        self.clear_results()
        self.check_files_ready()
    
    def export_to_excel(self):
        """Export results to Excel"""
        export_data = self.editable_table.get_all_data()
        if not export_data:
            QMessageBox.warning(self, "Warning", "No results to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export to Excel", 
            "transaction_results.xlsx", 
            "Excel Files (*.xlsx)"
        )
        
        if file_path:
            try:
                # Convert to DataFrame for export
                headers = ["Transaction Reference", "Transaction Date", "Matched Parent", "Matched Child", "Amount"]
                df = pd.DataFrame(export_data, columns=headers)
                df.to_excel(file_path, index=False)
                QMessageBox.information(self, "Success", f"Results exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export to Excel:\n{str(e)}")
    
    def export_to_csv(self):
        """Export results to CSV"""
        export_data = self.editable_table.get_all_data()
        if not export_data:
            QMessageBox.warning(self, "Warning", "No results to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export to CSV", 
            "transaction_results.csv", 
            "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                # Convert to DataFrame for export
                headers = ["Transaction Reference", "Transaction Date", "Matched Parent", "Matched Child", "Amount"]
                df = pd.DataFrame(export_data, columns=headers)
                df.to_csv(file_path, index=False)
                QMessageBox.information(self, "Success", f"Results exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export to CSV:\n{str(e)}")
    
    def save_report(self):
        """Save detailed report"""
        export_data = self.editable_table.get_all_data()
        if not export_data:
            QMessageBox.warning(self, "Warning", "No results to save.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Report", 
            "matching_report.txt", 
            "Text Files (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("Fee Transaction Matching Report\n")
                    f.write("=" * 50 + "\n\n")
                    
                    # Write summary
                    f.write(f"Summary: {self.summary_label.text()}\n\n")
                    
                    # Write change summary if there are edits
                    if self.editable_table.has_changes:
                        change_summary = self.editable_table.data_manager.get_change_summary()
                        f.write("Edit Summary:\n")
                        f.write(f"- Modified cells: {change_summary['modified_cells_count']}\n")
                        f.write(f"- New rows added: {change_summary['new_rows_count']}\n")
                        f.write(f"- Rows deleted: {change_summary['deleted_rows_count']}\n\n")
                    
                    # Write detailed results
                    f.write("Detailed Results:\n")
                    f.write("-" * 20 + "\n")
                    
                    headers = ["Transaction Reference", "Transaction Date", "Matched Parent", "Matched Child", "Amount"]
                    for i, row_data in enumerate(export_data):
                        f.write(f"\nRow {i + 1}:\n")
                        for j, value in enumerate(row_data):
                            f.write(f"  {headers[j]}: {value}\n")
                
                QMessageBox.information(self, "Success", f"Report saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save report:\n{str(e)}")
    
    def validate_files(self):
        """Validate the selected files"""
        if not self.fee_file_path or not self.transaction_file_path:
            QMessageBox.warning(self, "Warning", "Please select both files first.")
            return
        
        errors = []
        
        # Check fee file
        if not os.path.exists(self.fee_file_path):
            errors.append(f"Fee file not found: {self.fee_file_path}")
        else:
            try:
                pd.read_excel(self.fee_file_path)
            except Exception as e:
                errors.append(f"Invalid fee file: {str(e)}")
        
        # Check transaction file
        if not os.path.exists(self.transaction_file_path):
            errors.append(f"Transaction file not found: {self.transaction_file_path}")
        else:
            try:
                pd.read_csv(self.transaction_file_path)
            except Exception as e:
                errors.append(f"Invalid transaction file: {str(e)}")
        
        if errors:
            QMessageBox.critical(self, "Validation Error", "\n".join(errors))
            return
        
        QMessageBox.information(self, "Validation", "Both files are valid and ready for processing.")
    
    def export_results(self):
        """Export results from menu"""
        self.export_to_excel()
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About", 
                         "Fee Transaction Matcher v1.0\n\n"
                         "A tool for matching transaction records with fee statements.\n\n"
                         "Features:\n"
                         "- Fuzzy matching of parent and child names\n"
                         "- Excel-like table editing\n"
                         "- Copy/paste functionality\n"
                         "- Add/delete rows\n"
                         "- Undo/redo operations\n"
                         "- Data validation\n"
                         "- Export to Excel/CSV\n"
                         "- Transaction date extraction and validation")


def main():
    """Main entry point for the GUI application"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Fee Transaction Matcher")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = TransactionMatcherWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()