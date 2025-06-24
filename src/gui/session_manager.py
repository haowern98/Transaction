"""
Session management and export operations for table data
Handles saving/loading sessions and exporting data to various formats
"""
import os
import csv
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from PyQt5.QtWidgets import (QFileDialog, QMessageBox, QDialog, QVBoxLayout, 
                            QListWidget, QPushButton, QHBoxLayout, QLabel)


class SessionManager:
    """Handles session saving/loading and data export operations"""
    
    def __init__(self, saved_sessions_dir="saved_sessions"):
        self.saved_sessions_dir = saved_sessions_dir
        self._ensure_sessions_directory()
        
    def _ensure_sessions_directory(self):
        """Create saved_sessions directory if it doesn't exist"""
        if not os.path.exists(self.saved_sessions_dir):
            os.makedirs(self.saved_sessions_dir)
            
    def _generate_session_filename(self):
        """Generate filename with timestamp: transaction_preview_YYYY-MM-DD_HH-MM-SS.csv"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"transaction_preview_{timestamp}.csv"
        
    def _get_available_sessions(self):
        """Get list of available saved session files"""
        if not os.path.exists(self.saved_sessions_dir):
            return []
            
        session_files = []
        for filename in os.listdir(self.saved_sessions_dir):
            if filename.startswith("transaction_preview_") and filename.endswith(".csv"):
                filepath = os.path.join(self.saved_sessions_dir, filename)
                # Get file modification time for display
                mtime = os.path.getmtime(filepath)
                session_files.append({
                    'filename': filename,
                    'filepath': filepath,
                    'mtime': mtime,
                    'display_name': self._format_session_display_name(filename, mtime)
                })
        
        # Sort by modification time (newest first)
        session_files.sort(key=lambda x: x['mtime'], reverse=True)
        return session_files
        
    def _format_session_display_name(self, filename, mtime):
        """Format session name for display"""
        try:
            # Extract timestamp from filename: transaction_preview_2025-06-19_14-30-15.csv
            timestamp_part = filename.replace("transaction_preview_", "").replace(".csv", "")
            date_part, time_part = timestamp_part.split("_")
            year, month, day = date_part.split("-")
            hour, minute, second = time_part.split("-")
            
            # Format as: "June 19, 2025 at 2:30 PM"
            dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
            formatted_date = dt.strftime("%B %d, %Y at %I:%M %p")
            return f"{formatted_date}"
        except:
            # Fallback to filename if parsing fails
            dt = datetime.fromtimestamp(mtime)
            formatted_date = dt.strftime("%B %d, %Y at %I:%M %p")
            return f"{formatted_date}"

    def save_session(self, table_wrapper):
        """
        Save current table data to CSV file
        
        Args:
            table_wrapper: IntegratedEditableTable instance
        """
        try:
            # Get current table data
            table_data = table_wrapper.get_all_data()
            
            if not table_data:
                QMessageBox.warning(None, "Warning", "No data to save.")
                return False
                
            # Generate filename
            filename = self._generate_session_filename()
            filepath = os.path.join(self.saved_sessions_dir, filename)
            
            # Save to CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write headers
                headers = ["Transaction Reference", "Transaction Date", "Matched Parent", 
                          "Matched Child", "Month Paying For", "Amount"]
                writer.writerow(headers)
                
                # Write data
                for row_data in table_data:
                    writer.writerow(row_data)
            
            QMessageBox.information(None, "Success", 
                                  f"Session saved successfully!\n\nFile: {filename}")
            return True
            
        except Exception as e:
            QMessageBox.critical(None, "Error", 
                               f"Failed to save session:\n{str(e)}")
            return False
    
    def load_session(self, table_wrapper):
        """
        Load a previous session from saved CSV files
        
        Args:
            table_wrapper: IntegratedEditableTable instance
        """
        try:
            # Get available sessions
            available_sessions = self._get_available_sessions()
            
            if not available_sessions:
                QMessageBox.information(None, "No Sessions", 
                                      "No saved sessions found.")
                return False
            
            # Show session selection dialog
            selected_session = self._show_session_selection_dialog(available_sessions)
            
            if selected_session:
                return self._load_session_file(table_wrapper, selected_session['filepath'])
                
            return False
            
        except Exception as e:
            QMessageBox.critical(None, "Error", 
                               f"Failed to load session list:\n{str(e)}")
            return False
    
    def _show_session_selection_dialog(self, available_sessions):
        """Show dialog for selecting a session to load"""
        dialog = QDialog()
        dialog.setWindowTitle("Load Previous Session")
        dialog.setModal(True)
        dialog.resize(500, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Add instruction label
        instruction = QLabel("Select a session to load:")
        layout.addWidget(instruction)
        
        # Create list widget
        session_list = QListWidget()
        for session in available_sessions:
            session_list.addItem(session['display_name'])
        layout.addWidget(session_list)
        
        # Add buttons
        button_layout = QHBoxLayout()
        load_button = QPushButton("Load Selected")
        cancel_button = QPushButton("Cancel")
        
        button_layout.addWidget(load_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # Button logic
        selected_session = None
        
        def load_selected():
            nonlocal selected_session
            current_row = session_list.currentRow()
            if current_row >= 0:
                selected_session = available_sessions[current_row]
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Warning", "Please select a session to load.")
        
        load_button.clicked.connect(load_selected)
        cancel_button.clicked.connect(dialog.reject)
        
        # Show dialog and return result
        if dialog.exec_() == QDialog.Accepted:
            return selected_session
        return None
    
    def _load_session_file(self, table_wrapper, filepath):
        """Load table data from a specific CSV file"""
        try:
            # Check if current table has unsaved changes
            if table_wrapper.has_changes:
                reply = QMessageBox.question(None, "Unsaved Changes",
                                           "You have unsaved changes. Loading a session will discard them.\n\n"
                                           "Do you want to continue?",
                                           QMessageBox.Yes | QMessageBox.No,
                                           QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return False
            
            # Read CSV file
            table_data = []
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                headers = next(reader)  # Skip header row
                
                for row in reader:
                    # Ensure row has exactly 6 columns
                    while len(row) < 6:
                        row.append("")
                    table_data.append(row[:6])  # Take only first 6 columns
            
            # Load data into table
            table_wrapper.populate_table(table_data)
            
            # Extract filename for display
            filename = os.path.basename(filepath)
            
            QMessageBox.information(None, "Success", 
                                  f"Session loaded successfully!\n\nFile: {filename}\n"
                                  f"Loaded {len(table_data)} rows of data.")
            return True
            
        except Exception as e:
            QMessageBox.critical(None, "Error", 
                               f"Failed to load session:\n{str(e)}")
            return False


# Convenience functions for use with table wrapper
def save_table_session(table_wrapper):
    """Save table session using default session manager"""
    manager = SessionManager()
    return manager.save_session(table_wrapper)


def load_table_session(table_wrapper):
    """Load table session using default session manager"""
    manager = SessionManager()
    return manager.load_session(table_wrapper)


def export_table_to_excel(table_wrapper, default_filename="transaction_results.xlsx", parent=None):
    """
    Export table data to Excel format
    
    Args:
        table_wrapper: IntegratedEditableTable instance
        default_filename: Default filename for save dialog
        parent: Parent widget for dialogs
    """
    export_data = table_wrapper.get_all_data()
    if not export_data:
        QMessageBox.warning(parent, "Warning", "No results to export.")
        return False
    
    file_path, _ = QFileDialog.getSaveFileName(
        parent, 
        "Export to Excel", 
        default_filename, 
        "Excel Files (*.xlsx)"
    )
    
    if file_path:
        try:
            # Convert to DataFrame and save
            headers = ["Transaction Reference", "Transaction Date", "Matched Parent", 
                      "Matched Child", "Month Paying For", "Amount"]
            df = pd.DataFrame(export_data, columns=headers)
            df.to_excel(file_path, index=False)
            QMessageBox.information(parent, "Success", f"Results exported to {file_path}")
            return True
        except Exception as e:
            QMessageBox.critical(parent, "Export Error", f"Failed to export to Excel:\n{str(e)}")
            return False
    
    return False


def export_table_to_csv(table_wrapper, default_filename="transaction_results.csv", parent=None):
    """
    Export table data to CSV format
    
    Args:
        table_wrapper: IntegratedEditableTable instance
        default_filename: Default filename for save dialog
        parent: Parent widget for dialogs
    """
    export_data = table_wrapper.get_all_data()
    if not export_data:
        QMessageBox.warning(parent, "Warning", "No results to export.")
        return False
    
    file_path, _ = QFileDialog.getSaveFileName(
        parent, 
        "Export to CSV", 
        default_filename, 
        "CSV Files (*.csv)"
    )
    
    if file_path:
        try:
            # Convert to DataFrame and save
            headers = ["Transaction Reference", "Transaction Date", "Matched Parent", 
                      "Matched Child", "Month Paying For", "Amount"]
            df = pd.DataFrame(export_data, columns=headers)
            df.to_csv(file_path, index=False)
            QMessageBox.information(parent, "Success", f"Results exported to {file_path}")
            return True
        except Exception as e:
            QMessageBox.critical(parent, "Export Error", f"Failed to export to CSV:\n{str(e)}")
            return False
    
    return False


def save_detailed_report(table_wrapper, summary_text, parent=None):
    """
    Save detailed report including summary and data
    
    Args:
        table_wrapper: IntegratedEditableTable instance
        summary_text: Summary text to include in report
        parent: Parent widget for dialogs
    """
    export_data = table_wrapper.get_all_data()
    if not export_data:
        QMessageBox.warning(parent, "Warning", "No results to save.")
        return False
    
    file_path, _ = QFileDialog.getSaveFileName(
        parent, 
        "Save Report", 
        "matching_report.txt", 
        "Text Files (*.txt)"
    )
    
    if file_path:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("Fee Transaction Matching Report\n")
                f.write("=" * 50 + "\n\n")
                
                # Write timestamp
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Write summary
                f.write(f"Summary: {summary_text}\n\n")
                
                # Write change summary if there are edits
                if table_wrapper.has_changes:
                    change_summary = table_wrapper.data_manager.get_change_summary()
                    f.write("Edit Summary:\n")
                    f.write(f"- Modified cells: {change_summary['modified_cells_count']}\n")
                    f.write(f"- New rows added: {change_summary['new_rows_count']}\n")
                    f.write(f"- Rows deleted: {change_summary['deleted_rows_count']}\n\n")
                
                # Write detailed results
                f.write("Detailed Results:\n")
                f.write("-" * 20 + "\n")
                
                headers = ["Transaction Reference", "Transaction Date", "Matched Parent", 
                          "Matched Child", "Month Paying For", "Amount"]
                for i, row_data in enumerate(export_data):
                    f.write(f"\nTransaction {i + 1}:\n")
                    for j, value in enumerate(row_data):
                        header_name = headers[j] if j < len(headers) else f"Column {j}"
                        f.write(f"  {header_name}: {value}\n")
            
            QMessageBox.information(parent, "Success", f"Report saved to {file_path}")
            return True
        except Exception as e:
            QMessageBox.critical(parent, "Save Error", f"Failed to save report:\n{str(e)}")
            return False
    
    return False


def export_change_history(table_wrapper, parent=None):
    """
    Export change history to JSON format
    
    Args:
        table_wrapper: IntegratedEditableTable instance
        parent: Parent widget for dialogs
    """
    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        "Export Change History",
        "change_history.json",
        "JSON Files (*.json)"
    )
    
    if file_path:
        try:
            # Get validation tracker if available
            if hasattr(table_wrapper.data_manager, 'validation_tracker'):
                validation_tracker = table_wrapper.data_manager.validation_tracker
                return validation_tracker.export_change_history(file_path)
            else:
                QMessageBox.warning(parent, "Warning", "Change history not available.")
                return False
        except Exception as e:
            QMessageBox.critical(parent, "Export Error", f"Failed to export change history:\n{str(e)}")
            return False
    
    return False


def get_session_statistics(session_manager=None):
    """
    Get statistics about saved sessions
    
    Args:
        session_manager: SessionManager instance (optional)
        
    Returns:
        Dictionary with session statistics
    """
    if session_manager is None:
        session_manager = SessionManager()
    
    sessions = session_manager._get_available_sessions()
    
    if not sessions:
        return {
            'total_sessions': 0,
            'newest_session': None,
            'oldest_session': None,
            'total_size_mb': 0
        }
    
    # Calculate total size
    total_size = 0
    for session in sessions:
        try:
            total_size += os.path.getsize(session['filepath'])
        except OSError:
            pass
    
    return {
        'total_sessions': len(sessions),
        'newest_session': sessions[0]['display_name'] if sessions else None,
        'oldest_session': sessions[-1]['display_name'] if sessions else None,
        'total_size_mb': total_size / (1024 * 1024)
    }