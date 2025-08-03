"""
Main window for the Transaction Matcher GUI application
Updated to properly check saved fee record file path from settings
Integrated with Outstanding Payments Tab functionality
File: src/gui/transaction_window.py
"""
import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                            QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
                            QPushButton, QLineEdit, QFileDialog, QMessageBox, 
                            QStatusBar, QDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

# Import dependencies
from core.processor import process_fee_matching_gui
from gui.table_wrapper import IntegratedEditableTable
from gui.fee_record_loader import show_fee_record_loader
from gui.outstanding_payments_tab import OutstandingPaymentsTab


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
        
        # Initialize settings manager
        from gui.settings import get_settings_manager
        self.settings_manager = get_settings_manager()
        
        self.init_ui()
        self.load_saved_file_paths()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Fee Transaction Matcher")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.addWidget(self.tab_widget)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create tabs
        self.create_outstanding_payments_tab()
        self.create_file_processing_tab()
        self.create_settings_tab()
    
    def create_file_processing_tab(self):
        """Create the file processing tab"""
        tab = QWidget()
        self.tab_widget.addTab(tab, "File Processing")
        
        layout = QVBoxLayout(tab)
        
        # File Selection Group (only Transaction File now)
        layout.addWidget(self._create_file_selection_group())
        
        # Check if default files are ready on startup
        self.check_files_ready()
        
        # Results Group
        layout.addWidget(self._create_results_group())
        
        # Set stretch factors to make results section much larger
        layout.setStretchFactor(layout.itemAt(0).widget(), 0)  # File selection
        layout.setStretchFactor(layout.itemAt(1).widget(), 1)  # Results
    
    def _create_file_selection_group(self):
        """Create the file selection group box with only Transaction File"""
        file_group = QGroupBox("File Selection")
        file_layout = QVBoxLayout(file_group)
        
        # Transaction File row
        trans_layout = QHBoxLayout()
        trans_layout.addWidget(QLabel("Transaction File:"))
        self.transaction_file_input = QLineEdit()
        self.transaction_file_input.setText(self.transaction_file_path)
        self.transaction_file_input.setPlaceholderText("Select the CSV file containing transaction data...")
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
        
        return file_group
    
    def _create_results_group(self):
        """Create the results display group box"""
        results_group = QGroupBox("Matching Results")
        results_layout = QVBoxLayout(results_group)
        
        # Summary row
        self.summary_label = QLabel("No results yet. Select transaction file and click 'Process Files' to begin.")
        results_layout.addWidget(self.summary_label)
        
        # Results table (using editable table)
        self.results_table = self.editable_table.table
        self.editable_table.setup_results_table()
        results_layout.addWidget(self.results_table)
        
        # Add editing toolbar
        self.editable_table.add_toolbar_buttons(results_layout)
        
        # Export buttons row
        results_layout.addLayout(self._create_export_buttons())
        
        return results_group
    
    def _create_export_buttons(self):
        """Create the export buttons layout including Load to Fee Record"""
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        
        # Existing export buttons
        self.export_excel_btn = QPushButton("Export to Excel")
        self.export_excel_btn.clicked.connect(self.export_to_excel)
        self.export_excel_btn.setEnabled(False)
        export_layout.addWidget(self.export_excel_btn)
        
        self.export_csv_btn = QPushButton("Export to CSV")
        self.export_csv_btn.clicked.connect(self.export_to_csv)
        self.export_csv_btn.setEnabled(False)
        export_layout.addWidget(self.export_csv_btn)
        
        # Load to Fee Record button with DEFAULT STYLING (same as others)
        self.load_fee_record_btn = QPushButton("Load to Fee Record")
        self.load_fee_record_btn.clicked.connect(self.load_to_fee_record)
        self.load_fee_record_btn.setEnabled(False)
        export_layout.addWidget(self.load_fee_record_btn)
        
        self.save_report_btn = QPushButton("Save Report")
        self.save_report_btn.clicked.connect(self.save_report)
        self.save_report_btn.setEnabled(False)
        export_layout.addWidget(self.save_report_btn)
        
        export_layout.addStretch()
        return export_layout
    
    def create_settings_tab(self):
        """Create the settings tab with zoom controls"""
        from gui.settings import SettingsTab
        
        self.settings_tab = SettingsTab(self)
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        # Connect settings signals
        self.settings_tab.settings_applied.connect(self.on_settings_applied)
        self.settings_tab.settings_reset.connect(self.on_settings_reset)
    
    def create_outstanding_payments_tab(self):
        """Create the Outstanding Payments tab"""
        try:
            self.outstanding_payments_tab = OutstandingPaymentsTab(self)
            self.tab_widget.addTab(self.outstanding_payments_tab, "Outstanding Payments")
            
            # Connect tab signals if needed
            # self.outstanding_payments_tab.some_signal.connect(self.some_handler)
            
            print("✓ Outstanding Payments tab created successfully")
            
        except Exception as e:
            print(f"✗ Failed to create Outstanding Payments tab: {e}")
            # Create placeholder tab if import fails
            placeholder = QWidget()
            placeholder_layout = QVBoxLayout(placeholder)
            placeholder_layout.addWidget(QLabel("Outstanding Payments tab temporarily unavailable"))
            self.tab_widget.addTab(placeholder, "Outstanding Payments")
    
    def get_fee_record_file_path_from_settings(self):
        """
        Get fee record file path from settings - FIXED to check all sources
        This is the MAIN method that should be used everywhere
        """
        try:
            # Method 1: Try to get from Settings tab file_paths_panel (if available)
            if hasattr(self.settings_tab, 'file_paths_panel'):
                fee_record_path = self.settings_tab.file_paths_panel.get_fee_record_file_path()
                if fee_record_path and fee_record_path.strip():
                    print(f"DEBUG: Got fee record path from file_paths_panel: '{fee_record_path}'")
                    return fee_record_path.strip()
            
            # Method 2: Get directly from settings manager (THIS IS THE KEY FIX)
            saved_fee_record_file = self.settings_manager.get_setting('files.fee_record_file', '')
            if saved_fee_record_file and saved_fee_record_file.strip():
                print(f"DEBUG: Got fee record path from settings manager: '{saved_fee_record_file}'")
                return saved_fee_record_file.strip()
            
            # Method 3: Fallback to old settings key for backward compatibility
            saved_fee_file = self.settings_manager.get_setting('files.last_fee_file', '')
            if saved_fee_file and saved_fee_file.strip():
                print(f"DEBUG: Got fee record path from legacy settings: '{saved_fee_file}'")
                return saved_fee_file.strip()
            
            print("DEBUG: No fee record path found in any settings")
            return ""
            
        except Exception as e:
            print(f"Warning: Could not get fee record file from settings: {e}")
            return ""
    
    def get_fee_file_path_from_settings(self):
        """
        Get fee file path from Settings tab - LEGACY method for processing
        This gets the Parent-Student pair file for processing
        """
        try:
            if hasattr(self.settings_tab, 'file_paths_panel'):
                fee_path = self.settings_tab.file_paths_panel.get_fee_file_path()
                if fee_path and os.path.exists(fee_path):
                    return fee_path
            
            # Fallback to settings manager
            saved_fee_file = self.settings_manager.get_setting('files.last_fee_file', '')
            if saved_fee_file and os.path.exists(saved_fee_file):
                return saved_fee_file
                
            # Final fallback to default
            return self.fee_file_path
            
        except Exception as e:
            print(f"Warning: Could not get fee file from settings: {e}")
            return self.fee_file_path
    
    def load_saved_file_paths(self):
        """Load saved file paths from settings"""
        if self.settings_manager.get_setting('files.remember_file_paths', True):
            # Load fee file from settings
            saved_fee_file = self.settings_manager.get_setting('files.last_fee_file', '')
            if saved_fee_file and os.path.exists(saved_fee_file):
                self.fee_file_path = saved_fee_file
            
            # Load transaction file from settings
            saved_trans_file = self.settings_manager.get_setting('files.last_transaction_file', '')
            if saved_trans_file and os.path.exists(saved_trans_file):
                self.transaction_file_path = saved_trans_file
                self.transaction_file_input.setText(saved_trans_file)
    
    def on_transaction_file_changed(self, text):
        """Handle transaction file path changes"""
        self.transaction_file_path = text.strip()
        self.check_files_ready()
        
        # Save to settings if remember is enabled
        if self.settings_manager.get_setting('files.remember_file_paths', True):
            self.settings_manager.set_last_transaction_file(self.transaction_file_path)
    
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
        # Get fee file path from settings
        current_fee_path = self.get_fee_file_path_from_settings()
        fee_ready = os.path.exists(current_fee_path) if current_fee_path else False
        
        trans_ready = os.path.exists(self.transaction_file_path) if self.transaction_file_path else False
        
        self.process_btn.setEnabled(fee_ready and trans_ready)
        
        if fee_ready and trans_ready:
            self.status_bar.showMessage("Files ready for processing")
            
            # Auto-process if enabled in settings
            if hasattr(self, 'settings_tab') and self.settings_tab.should_auto_process():
                QTimer.singleShot(500, self.process_files)  # Small delay for UI responsiveness
                
        elif not fee_ready and not trans_ready:
            self.status_bar.showMessage("Please configure Fee Record File in Settings and select Transaction File")
        elif not fee_ready:
            self.status_bar.showMessage("Please configure Fee Record File in Settings → File Paths")
        else:
            self.status_bar.showMessage("Please select a valid transaction file")
    
    def process_files(self):
        """Process the selected files"""
        # Get current fee file path from settings
        current_fee_path = self.get_fee_file_path_from_settings()
        
        if not current_fee_path or not self.transaction_file_path:
            QMessageBox.warning(self, "Warning", 
                              "Please configure Fee Record File in Settings → File Paths and select a Transaction File.")
            return
        
        if not os.path.exists(current_fee_path):
            QMessageBox.warning(self, "Warning", 
                              f"Fee Record File not found: {current_fee_path}\n\n"
                              f"Please update the path in Settings → File Paths")
            return
            
        if not os.path.exists(self.transaction_file_path):
            QMessageBox.warning(self, "Warning", f"Transaction file not found: {self.transaction_file_path}")
            return
        
        # Disable process button during processing
        self.process_btn.setEnabled(False)
        self.status_bar.showMessage("Processing files...")
        
        # Start processing in background thread with current fee file path
        self.processing_thread = ProcessingThread(current_fee_path, self.transaction_file_path)
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
        
        # Enable Load to Fee Record button only if fee record file is configured
        self.update_fee_record_button_state()
        
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
        self.summary_label.setText("No results yet. Select transaction file and click 'Process Files' to begin.")
        
        # Disable export buttons
        self.export_excel_btn.setEnabled(False)
        self.export_csv_btn.setEnabled(False)
        self.save_report_btn.setEnabled(False)
        self.load_fee_record_btn.setEnabled(False)
        
        self.status_bar.showMessage("Results cleared")
    
    def export_to_excel(self):
        """Export results to Excel"""
        from gui.session_manager import export_table_to_excel
        export_table_to_excel(self.editable_table, "transaction_results.xlsx", self)
    
    def export_to_csv(self):
        """Export results to CSV"""
        from gui.session_manager import export_table_to_csv
        export_table_to_csv(self.editable_table, "transaction_results.csv", self)
    
    def save_report(self):
        """Save detailed report"""
        from gui.session_manager import save_detailed_report
        save_detailed_report(self.editable_table, self.summary_label.text(), self)
    
    def load_to_fee_record(self):
        """Load current table data to fee record file"""
        try:
            # Get fee record file path from settings - FIXED METHOD
            fee_record_path = self.get_fee_record_file_path_from_settings()
            
            if not fee_record_path:
                QMessageBox.warning(self, "Fee Record File Required", 
                                  "Please configure the Fee Record File path in Settings → File Paths")
                return
                
            if not os.path.exists(fee_record_path):
                QMessageBox.warning(self, "File Not Found", 
                                  f"Fee Record File not found:\n{fee_record_path}\n\n"
                                  "Please update the path in Settings → File Paths")
                return
            
            # Get current table data
            table_data = self.editable_table.get_all_data()
            
            if not table_data:
                QMessageBox.warning(self, "No Data", "No data available to load to fee record.")
                return
            
            # Show fee record loader dialog
            result = show_fee_record_loader(table_data, fee_record_path, self)
            
            if result == QDialog.Accepted:
                self.status_bar.showMessage("Data loaded to fee record successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data to fee record:\n{str(e)}")
    
    def update_fee_record_button_state(self):
        """Update Load to Fee Record button state - FIXED to properly check saved settings"""
        try:
            # Check if we have data - EITHER from processing OR from loaded session
            has_processed_data = len(self.results_data) > 0
            has_table_data = self.editable_table.table.rowCount() > 0
            has_data = has_processed_data or has_table_data
            
            # Check if fee record file is configured and exists - FIXED METHOD
            fee_record_path = self.get_fee_record_file_path_from_settings()
            fee_record_configured = bool(fee_record_path and os.path.exists(fee_record_path))
            
            # DEBUG: Print status to help diagnose
            print(f"DEBUG Fee Record Button State:")
            print(f"  - Has processed data: {has_processed_data} (results count: {len(self.results_data)})")
            print(f"  - Has table data: {has_table_data} (table rows: {self.editable_table.table.rowCount()})")
            print(f"  - Has data (either): {has_data}")
            print(f"  - Fee record path: '{fee_record_path}'")
            print(f"  - Fee record file exists: {os.path.exists(fee_record_path) if fee_record_path else False}")
            print(f"  - Fee record configured: {fee_record_configured}")
            
            # Enable button only if both conditions are met
            button_enabled = has_data and fee_record_configured
            self.load_fee_record_btn.setEnabled(button_enabled)
            
            # Update tooltip to explain why button might be disabled
            if not has_data:
                tooltip = "Process files or load a session first to enable loading to fee record"
            elif not fee_record_configured:
                if not fee_record_path:
                    tooltip = "Configure Fee Record File in Settings → File Paths"
                else:
                    tooltip = f"Fee Record File not found: {fee_record_path}"
            else:
                tooltip = "Load current table data to fee record file"
                
            self.load_fee_record_btn.setToolTip(tooltip)
            
            print(f"  - Button enabled: {button_enabled}")
            print(f"  - Tooltip: {tooltip}")
                
        except Exception as e:
            print(f"Error updating fee record button state: {e}")
            self.load_fee_record_btn.setEnabled(False)
            self.load_fee_record_btn.setToolTip("Error checking fee record configuration")
    
    def on_settings_applied(self):
        """Handle settings being applied"""
        # Reload any settings that affect the main window
        self.load_saved_file_paths()
        # Recheck files ready status since fee file might have changed
        self.check_files_ready()
        # Update fee record button state since fee record path might have changed
        self.update_fee_record_button_state()
        
        # NEW: Refresh Outstanding Payments tab if it exists
        if hasattr(self, 'outstanding_payments_tab'):
            try:
                self.outstanding_payments_tab.load_fee_record_path()
                print("✓ Outstanding Payments tab refreshed after settings change")
            except Exception as e:
                print(f"Warning: Failed to refresh Outstanding Payments tab: {e}")
        
        # Show settings saved message AFTER other operations to prevent overwriting
        self.status_bar.showMessage("Settings saved successfully")
    
    def on_settings_reset(self):
        """Handle settings being reset"""
        self.load_saved_file_paths()
        self.check_files_ready()
        # Update fee record button state after reset
        self.update_fee_record_button_state()
        
        # NEW: Refresh Outstanding Payments tab if it exists
        if hasattr(self, 'outstanding_payments_tab'):
            try:
                self.outstanding_payments_tab.load_fee_record_path()
                print("✓ Outstanding Payments tab refreshed after settings reset")
            except Exception as e:
                print(f"Warning: Failed to refresh Outstanding Payments tab: {e}")
        
        # Show reset message AFTER other operations to prevent overwriting
        self.status_bar.showMessage("Settings reset to defaults")
    
    def on_session_loaded(self):
        """Called when a session is successfully loaded"""
        # Update button states since we now have data in the table
        self.update_fee_record_button_state()
        print("DEBUG: Session loaded, button state updated")
    
    def showEvent(self, event):
        """Handle window show event - update button states when window becomes visible"""
        super().showEvent(event)
        # Update button states when window is shown (helps with startup state)
        QTimer.singleShot(100, self.update_fee_record_button_state)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Save settings before closing
        self.settings_manager.save_settings()
        
        # Clean up zoom system
        try:
            from gui.settings import cleanup_zoom_system_complete
            cleanup_zoom_system_complete()
        except:
            pass
        
        event.accept()


def run_gui_application():
    """Run the GUI application with consolidated zoom system"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Fee Transaction Matcher")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = TransactionMatcherWindow()
    window.show()
    
    # Initialize consolidated zoom system
    try:
        from gui.settings import initialize_zoom_system_complete
        
        print("Initializing consolidated zoom system...")
        
        # Initialize zoom system immediately after window is shown
        zoom_init_success = initialize_zoom_system_complete()
        
        if zoom_init_success:
            print("✓ Zoom system ready! Use Ctrl++/Ctrl+-/Ctrl+0 or go to Settings tab")
        else:
            print("⚠ Zoom system initialization failed")
            
    except Exception as e:
        print(f"Warning: Could not initialize zoom system: {e}")
        print("Application will continue without zoom functionality")
    
    # Start the application
    try:
        sys.exit(app.exec_())
    except SystemExit:
        # Clean up zoom system on exit
        try:
            from gui.settings import cleanup_zoom_system_complete
            cleanup_zoom_system_complete()
        except:
            pass
        raise