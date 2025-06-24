"""
Integration wrapper to replace QTableWidget with EditableTableWidget
in the existing transaction_main_window.py with minimal changes
"""
import os
import csv
from datetime import datetime
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from gui.table_editor import EditableTableWidget
from gui.table_data_manager import TableDataManager


class IntegratedEditableTable:
    """Wrapper to integrate EditableTableWidget with existing code"""
    
    def __init__(self, parent=None):
        # Create the editable table widget
        self.table = EditableTableWidget(parent)
        
        # Create the data manager
        self.data_manager = TableDataManager(parent)
        
        # Connect signals
        self.table.data_changed.connect(self.on_data_changed)
        self.table.row_added.connect(self.on_row_added)
        self.table.row_deleted.connect(self.on_row_deleted)
        self.data_manager.validation_error.connect(self.on_validation_error)
        
        # CRITICAL FIX: Connect table's item change to data manager
        self.table.itemChanged.connect(self.on_table_item_changed)
        
        # Track if we have unsaved changes
        self.has_changes = False
        
        # Session management
        self.saved_sessions_dir = "saved_sessions"
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
        # Extract timestamp from filename: transaction_preview_2025-06-19_14-30-15.csv
        try:
            timestamp_part = filename.replace("transaction_preview_", "").replace(".csv", "")
            date_part, time_part = timestamp_part.split("_")
            year, month, day = date_part.split("-")
            hour, minute, second = time_part.split("-")
            
            # Format as: "June 19, 2025 at 2:30 PM"
            dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
            formatted_date = dt.strftime("%B %d, %Y at %I:%M %p")
            return f"{formatted_date} ({filename})"
        except:
            # Fallback to filename if parsing fails
            dt = datetime.fromtimestamp(mtime)
            formatted_date = dt.strftime("%B %d, %Y at %I:%M %p")
            return f"{formatted_date} ({filename})"

    def setup_results_table(self):
        """Setup the results table structure with 6 columns including month paying for"""
        self.table.setColumnCount(6)
        headers = ["Transaction Reference", "Transaction Date", "Matched Parent", "Matched Child", "Month Paying For", "Amount"]
        self.table.setHorizontalHeaderLabels(headers)
        
        # Store headers in data manager
        self.data_manager.column_headers = headers
        
        # Make all columns manually resizable and fill the full width
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # Transaction Reference
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # Transaction Date
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # Matched Parent
        header.setSectionResizeMode(3, QHeaderView.Interactive)  # Matched Child
        header.setSectionResizeMode(4, QHeaderView.Interactive)  # Month Paying For
        header.setSectionResizeMode(5, QHeaderView.Interactive)  # Amount
        
        # Set column widths
        self.table.setColumnWidth(0, 1400)   # Transaction Reference
        self.table.setColumnWidth(1, 180)   # Transaction Date
        self.table.setColumnWidth(2, 180)   # Matched Parent
        self.table.setColumnWidth(3, 180)   # Matched Child
        self.table.setColumnWidth(4, 180)   # Month Paying For
        # Amount column will stretch to fill remaining space
        
        # Enable word wrap for first column
        self.table.setWordWrap(True)
        
        # Set table font size
        font = QFont()
        font.setPointSize(9)
        self.table.setFont(font)
        
    def populate_table(self, table_data):
        """Populate table with data"""
        self.table.setRowCount(len(table_data))
        
        # Store data in data manager
        self.data_manager.set_original_data(table_data, self.data_manager.column_headers)
        
        # Also set original data in table editor for visual tracking
        self.table.set_original_data(table_data)
        
        for row, row_data in enumerate(table_data):
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                if col == 5:  # Amount column (now column 5)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif col == 1:  # Transaction Date column
                    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                elif col == 4:  # Month Paying For column
                    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                elif col == 0:  # Transaction Reference
                    item.setFlags(item.flags() | Qt.TextWordWrap)
                self.table.setItem(row, col, item)
        
        self.table.resizeRowsToContents()
        self.has_changes = False
        self.update_button_states()
        
    def populate_results_table(self, results_data):
        """Populate the results table with processed data"""
        # Convert results data to table format
        table_data = []
        
        for result in results_data:
            row_data = []
            
            # Transaction Reference
            trans_ref = result.get('parent_from_transaction', '')
            row_data.append(str(trans_ref))
            
            # Transaction Date
            transaction_date = result.get('transaction_date', '')
            row_data.append(str(transaction_date))
            
            # Matched Parent
            matched_parent = result.get('matched_parent', 'NO MATCH FOUND')
            row_data.append(str(matched_parent))
            
            # Matched Child
            matched_child = result.get('matched_child', 'NO CHILD MATCH FOUND')
            row_data.append(str(matched_child))
            
            # Month Paying For
            month_paying_for = result.get('month_paying_for', 'NO MONTH FOUND')
            row_data.append(str(month_paying_for))
            
            # Amount
            amount = result.get('amount', 0)
            if isinstance(amount, (int, float)) and amount > 0:
                amount_text = f"{amount:.2f}"
            else:
                amount_text = ""
            row_data.append(amount_text)
            
            table_data.append(row_data)
        
        # Use the standard populate_table method
        self.populate_table(table_data)
        
    def add_toolbar_buttons(self, layout):
        """Add editing toolbar buttons including save/load session functionality"""
        from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy
        
        # Create editing toolbar
        edit_toolbar = QHBoxLayout()
        
        # Undo/Redo buttons
        self.undo_btn = QPushButton("Undo")
        self.undo_btn.clicked.connect(self.undo_changes)
        edit_toolbar.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("Redo")
        self.redo_btn.clicked.connect(self.redo_changes)
        edit_toolbar.addWidget(self.redo_btn)
        
        # Separator
        edit_toolbar.addWidget(QLabel("|"))
        
        # Reset button
        self.reset_btn = QPushButton("Reset All")
        self.reset_btn.clicked.connect(self.reset_to_original)
        edit_toolbar.addWidget(self.reset_btn)
        
        # Save/Load Session buttons
        self.save_session_btn = QPushButton("Save Session")
        self.save_session_btn.clicked.connect(self.save_session)
        edit_toolbar.addWidget(self.save_session_btn)
        
        self.load_session_btn = QPushButton("Load Previous Session")
        self.load_session_btn.clicked.connect(self.load_session)
        edit_toolbar.addWidget(self.load_session_btn)
        
        # Spacer to push everything to the left
        edit_toolbar.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Add to main layout
        layout.addLayout(edit_toolbar)
        
        # Update button states
        self.update_button_states()
        
    def save_session(self):
        """Save current table data to CSV file"""
        try:
            # Get current table data
            table_data = self.get_all_data()
            
            if not table_data:
                QMessageBox.warning(None, "Warning", "No data to save.")
                return
                
            # Ensure directory exists
            self._ensure_sessions_directory()
            
            # Generate filename
            filename = self._generate_session_filename()
            filepath = os.path.join(self.saved_sessions_dir, filename)
            
            # Save to CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write headers
                headers = ["Transaction Reference", "Transaction Date", "Matched Parent", "Matched Child", "Month Paying For", "Amount"]
                writer.writerow(headers)
                
                # Write data
                for row_data in table_data:
                    writer.writerow(row_data)
            
            QMessageBox.information(None, "Success", 
                                  f"Session saved successfully!\n\nFile: {filename}")
            
        except Exception as e:
            QMessageBox.critical(None, "Error", 
                               f"Failed to save session:\n{str(e)}")
    
    def load_session(self):
        """Load a previous session from saved CSV files"""
        try:
            # Get available sessions
            available_sessions = self._get_available_sessions()
            
            if not available_sessions:
                QMessageBox.information(None, "No Sessions", 
                                      "No saved sessions found.")
                return
            
            # Create selection dialog
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout
            
            dialog = QDialog()
            dialog.setWindowTitle("Load Previous Session")
            dialog.setModal(True)
            dialog.resize(500, 300)
            
            layout = QVBoxLayout(dialog)
            
            # Add instruction label
            from PyQt5.QtWidgets import QLabel
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
            
            # Connect button signals
            def load_selected():
                current_row = session_list.currentRow()
                if current_row >= 0:
                    selected_session = available_sessions[current_row]
                    dialog.accept()
                    self._load_session_file(selected_session['filepath'])
                else:
                    QMessageBox.warning(dialog, "Warning", "Please select a session to load.")
            
            load_button.clicked.connect(load_selected)
            cancel_button.clicked.connect(dialog.reject)
            
            # Show dialog
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(None, "Error", 
                               f"Failed to load session list:\n{str(e)}")
    
    def _load_session_file(self, filepath):
        """Load table data from a specific CSV file"""
        try:
            # Check if current table has unsaved changes
            if self.has_changes:
                reply = QMessageBox.question(None, "Unsaved Changes",
                                           "You have unsaved changes. Loading a session will discard them.\n\n"
                                           "Do you want to continue?",
                                           QMessageBox.Yes | QMessageBox.No,
                                           QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
            
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
            self.populate_table(table_data)
            
            # Extract filename for display
            filename = os.path.basename(filepath)
            
            QMessageBox.information(None, "Success", 
                                  f"Session loaded successfully!\n\nFile: {filename}\n"
                                  f"Loaded {len(table_data)} rows of data.")
            
        except Exception as e:
            QMessageBox.critical(None, "Error", 
                               f"Failed to load session:\n{str(e)}")
    
    def add_new_row(self):
        """Add a new row at the end"""
        self.table.add_new_row()
        
    def delete_selected_rows(self):
        """Delete selected rows"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
            
        if not selected_rows:
            QMessageBox.information(None, "Info", "Please select rows to delete.")
            return
            
        # Confirm deletion
        if len(selected_rows) == 1:
            msg = "Delete the selected row?"
        else:
            msg = f"Delete {len(selected_rows)} selected rows?"
            
        reply = QMessageBox.question(None, "Confirm Delete", msg,
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Delete rows in reverse order to maintain indices
            for row in sorted(selected_rows, reverse=True):
                self.table.delete_row(row)
                
    def undo_changes(self):
        """Undo last change"""
        if self.data_manager.undo():
            self.refresh_table_from_data_manager()
            self.update_button_states()
            
    def redo_changes(self):
        """Redo last undone change"""
        if self.data_manager.redo():
            self.refresh_table_from_data_manager()
            self.update_button_states()
            
    def save_changes(self):
        """Save current changes"""
        filename, _ = QFileDialog.getSaveFileName(
            None,
            "Save Changes",
            "table_changes.json",
            "JSON Files (*.json)"
        )
        
        if filename:
            if self.data_manager.save_changes_to_file(filename):
                QMessageBox.information(None, "Success", "Changes saved successfully!")
                self.has_changes = False
                self.update_button_states()
            else:
                QMessageBox.warning(None, "Error", "Failed to save changes.")
                
    def reset_to_original(self):
        """Reset table to original data"""
        reply = QMessageBox.question(None, "Confirm Reset", 
                                   "This will discard all changes. Are you sure?",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.data_manager.reset_to_original()
            self.refresh_table_from_data_manager()
            self.has_changes = False
            self.update_button_states()
            
    def refresh_table_from_data_manager(self):
        """Refresh table display from data manager"""
        data = self.data_manager.current_data
        self.table.setRowCount(len(data))
        
        # Temporarily disconnect to avoid recursive updates
        self.table.itemChanged.disconnect()
        
        for row in range(len(data)):
            for col in range(len(data[row]) if row < len(data) else 0):
                item = QTableWidgetItem(str(data[row][col]))
                if col == 5:  # Amount column (now column 5)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif col == 1:  # Transaction Date column
                    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                elif col == 4:  # Month Paying For column
                    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                elif col == 0:  # Transaction Reference
                    item.setFlags(item.flags() | Qt.TextWordWrap)
                self.table.setItem(row, col, item)
        
        # Reconnect the signal
        self.table.itemChanged.connect(self.on_table_item_changed)
                
        # Update visual indicators
        self.table.refresh_all_cell_appearances()
        self.table.resizeRowsToContents()
        
    def on_table_item_changed(self, item):
        """CRITICAL FIX: Handle table item changes and sync with data manager"""
        if item is None:
            return
            
        row = item.row()
        col = item.column()
        new_value = item.text()
        
        # Update the data manager (this creates undo points automatically)
        self.data_manager.update_cell(row, col, new_value)
        
        # Update button states since we may have new undo points
        self.update_button_states()
        
    def on_data_changed(self):
        """Handle data changes"""
        self.has_changes = self.table.has_unsaved_changes()
        self.update_button_states()
        
    def on_row_added(self, row_index):
        """Handle row addition"""
        # Also add to data manager
        self.data_manager.add_new_row(row_index)
        self.has_changes = True
        self.update_button_states()
        
    def on_row_deleted(self, row_index):
        """Handle row deletion"""
        # Also delete from data manager
        self.data_manager.delete_row(row_index)
        self.has_changes = True
        self.update_button_states()
        
    def on_validation_error(self, message, row, col):
        """Handle validation errors"""
        QMessageBox.warning(None, "Validation Error", 
                          f"Row {row + 1}, Column {col + 1}: {message}")
        
    def update_button_states(self):
        """Update button enabled states"""
        if hasattr(self, 'undo_btn'):
            self.undo_btn.setEnabled(len(self.data_manager.undo_stack) > 0)
            self.redo_btn.setEnabled(len(self.data_manager.redo_stack) > 0)
            self.reset_btn.setEnabled(self.has_changes)
            
        # Save/Load session buttons are always enabled
        if hasattr(self, 'save_session_btn'):
            # Save is enabled when there's data
            self.save_session_btn.setEnabled(self.table.rowCount() > 0)
            # Load is always enabled
            self.load_session_btn.setEnabled(True)
                
    def get_all_data(self):
        """Get all current table data for export"""
        return self.table.get_all_data()
        
    def clear_table(self):
        """Clear the table"""
        self.table.setRowCount(0)
        self.data_manager.clear_change_tracking()
        self.has_changes = False
        self.update_button_states()
        
    # Provide access to the underlying table widget for compatibility
    def __getattr__(self, name):
        """Delegate attribute access to the table widget"""
        return getattr(self.table, name)