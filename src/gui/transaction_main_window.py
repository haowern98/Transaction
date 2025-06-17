"""
Main window for the Transaction Matcher GUI application
Save this as: src/gui/transaction_main_window.py
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
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Fee Transaction Matcher")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_file_processing_tab()
        self.create_settings_tab()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Note: Menu bar removed for cleaner interface
    
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # Set menu bar styling to align with window title
        menubar.setStyleSheet("""
            QMenuBar {
                padding-left: 8px;
                spacing: 8px;
            }
            QMenuBar::item {
                padding: 4px 8px;
                margin: 0px;
            }
        """)
        
        # File menu
        file_menu = menubar.addMenu('File')
        file_menu.addAction('New Session', self.new_session)
        file_menu.addAction('Export Results', self.export_results)
        file_menu.addSeparator()
        file_menu.addAction('Exit', self.close)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        tools_menu.addAction('Clear Results', self.clear_results)
        tools_menu.addAction('Validate Files', self.validate_files)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        help_menu.addAction('About', self.show_about)
    
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
        
        # Results table
        self.results_table = QTableWidget()
        self.setup_results_table()
        results_layout.addWidget(self.results_table)
        
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
    
    def setup_results_table(self):
        """Setup the results table structure"""
        self.results_table.setColumnCount(4)
        headers = ["Transaction Reference", "Matched Parent", "Matched Child", "Amount"]
        self.results_table.setHorizontalHeaderLabels(headers)
        
        # Make all columns manually resizable and fill the full width
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # Transaction Reference - resizable
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # Matched Parent - resizable
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # Matched Child - resizable
        header.setSectionResizeMode(3, QHeaderView.Interactive)  # Amount - resizable
        
        # Make the last column stretch to fill any remaining space
        header.setStretchLastSection(True)
        
        # Set initial column widths that will fill most of the table width
        self.results_table.setColumnWidth(0, 600)  # Transaction Reference - large
        self.results_table.setColumnWidth(1, 180)  # Matched Parent
        self.results_table.setColumnWidth(2, 180)  # Matched Child  
        # Amount column will stretch to fill remaining space
        
        # Enable text wrapping for long content
        self.results_table.setWordWrap(True)
        
        # Set default row height to accommodate wrapped text
        self.results_table.verticalHeader().setDefaultSectionSize(50)
        
        # Enable sorting
        self.results_table.setSortingEnabled(True)
        
        # Set alternating row colors
        self.results_table.setAlternatingRowColors(True)
    
    def on_fee_file_changed(self, text):
        """Handle changes to fee file text field"""
        self.fee_file_path = text.strip()
        self.check_files_ready()
    
    def on_transaction_file_changed(self, text):
        """Handle changes to transaction file text field"""
        self.transaction_file_path = text.strip()
        self.check_files_ready()
    
    def browse_fee_file(self):
        """Browse for fee record file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Fee Record File", "", 
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        if file_path:
            self.fee_file_path = file_path
            self.fee_file_input.setText(file_path)
            self.check_files_ready()
    
    def browse_transaction_file(self):
        """Browse for transaction file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Transaction File", "", 
            "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.transaction_file_path = file_path
            self.transaction_file_input.setText(file_path)
            self.check_files_ready()
    
    def check_files_ready(self):
        """Check if both files are selected and enable process button"""
        if self.fee_file_path and self.transaction_file_path:
            self.process_btn.setEnabled(True)
        else:
            self.process_btn.setEnabled(False)
    
    def process_files(self):
        """Process the selected files"""
        if not self.fee_file_path or not self.transaction_file_path:
            QMessageBox.warning(self, "Warning", "Please select both fee record and transaction files.")
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
        self.results_table.setRowCount(len(self.results_data))
        
        for row, result in enumerate(self.results_data):
            # Transaction Reference - no truncation, full text
            trans_ref = result.get('parent_from_transaction', '')
            trans_ref_item = QTableWidgetItem(str(trans_ref))
            # Enable text wrapping for this cell
            trans_ref_item.setFlags(trans_ref_item.flags() | Qt.TextWordWrap)
            self.results_table.setItem(row, 0, trans_ref_item)
            
            # Matched Parent
            matched_parent = result.get('matched_parent', 'NO MATCH FOUND')
            self.results_table.setItem(row, 1, QTableWidgetItem(str(matched_parent)))
            
            # Matched Child
            matched_child = result.get('matched_child', 'NO CHILD MATCH FOUND')
            self.results_table.setItem(row, 2, QTableWidgetItem(str(matched_child)))
            
            # Amount
            amount = result.get('amount', 0)
            if isinstance(amount, (int, float)) and amount > 0:
                amount_text = f"{amount:.2f}"
            else:
                amount_text = ""
            amount_item = QTableWidgetItem(amount_text)
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.results_table.setItem(row, 3, amount_item)
        
        # Resize rows to fit content after populating
        self.results_table.resizeRowsToContents()
    
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
        if not self.results_data:
            QMessageBox.warning(self, "Warning", "No results to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to Excel", "transaction_matching_results.xlsx", 
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if file_path:
            try:
                # Convert results to DataFrame and save
                df = pd.DataFrame(self.results_data)
                df.to_excel(file_path, index=False)
                QMessageBox.information(self, "Success", f"Results exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export results:\n{str(e)}")
    
    def export_to_csv(self):
        """Export results to CSV"""
        if not self.results_data:
            QMessageBox.warning(self, "Warning", "No results to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to CSV", "transaction_matching_results.csv", 
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                # Convert results to DataFrame and save
                df = pd.DataFrame(self.results_data)
                df.to_csv(file_path, index=False)
                QMessageBox.information(self, "Success", f"Results exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export results:\n{str(e)}")
    
    def save_report(self):
        """Save a detailed report"""
        # For now, same as export to Excel
        self.export_to_excel()
    
    def validate_files(self):
        """Validate the selected files"""
        if not self.fee_file_path:
            QMessageBox.information(self, "Validation", "Please select a fee record file first.")
            return
        
        if not self.transaction_file_path:
            QMessageBox.information(self, "Validation", "Please select a transaction file first.")
            return
        
        # Check if files exist
        if not os.path.exists(self.fee_file_path):
            QMessageBox.warning(self, "Validation Error", "Fee record file does not exist.")
            return
        
        if not os.path.exists(self.transaction_file_path):
            QMessageBox.warning(self, "Validation Error", "Transaction file does not exist.")
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
                         "Supports fuzzy matching of parent and child names.")


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