"""
Core table integration wrapper
Provides the main interface for the editable table with basic operations
"""
import os
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from gui.editable_table import EditableTableWidget
from gui.data_manager import TableDataManager


class IntegratedEditableTable:
    """Core wrapper to integrate EditableTableWidget with data management"""
    
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
        
        # Connect table's item change to data manager
        self.table.itemChanged.connect(self.on_table_item_changed)
        
        # Track if we have unsaved changes
        self.has_changes = False
        
    def setup_results_table(self):
        """Setup the results table structure with 6 columns including month paying for"""
        self.table.setColumnCount(6)
        headers = ["Transaction Reference", "Transaction Date", "Matched Parent", 
                  "Matched Child", "Month Paying For", "Amount"]
        self.table.setHorizontalHeaderLabels(headers)
        
        # Store headers in data manager
        self.data_manager.column_headers = headers
        
        # Configure column resizing
        header = self.table.horizontalHeader()
        for i in range(6):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
        
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
                self._set_item_alignment(item, col)
                self.table.setItem(row, col, item)
        
        self.table.resizeRowsToContents()
        self.has_changes = False
        self.update_button_states()
    
    def _set_item_alignment(self, item, col):
        """Set appropriate alignment for table items based on column"""
        if col == 5:  # Amount column
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        elif col in [1, 4]:  # Transaction Date and Month columns
            item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        elif col == 0:  # Transaction Reference
            item.setFlags(item.flags() | Qt.TextWordWrap)
        
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
        """Add editing toolbar buttons including operations and filters"""
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
        
        # Separator
        edit_toolbar.addWidget(QLabel("|"))
        
        # Date Filter button
        self.filter_date_btn = QPushButton("Filter by Date")
        self.filter_date_btn.clicked.connect(self.filter_by_date)
        edit_toolbar.addWidget(self.filter_date_btn)
        
        # Separator
        edit_toolbar.addWidget(QLabel("|"))
        
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

    def filter_by_date(self):
        """Open date filter dialog and apply filter"""
        try:
            from gui.date_filter import DateFilterDialog
            
            # Get current table data
            current_data = self.get_all_data()
            
            if not current_data:
                QMessageBox.warning(None, "Warning", "No data to filter.")
                return
            
            # Create and show date filter dialog
            dialog = DateFilterDialog(current_data, None)
            dialog.filter_requested.connect(self.apply_date_filter)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to open date filter:\n{str(e)}")
    
    def apply_date_filter(self, cutoff_date):
        """Apply the date filter to the table"""
        try:
            from gui.date_filter import DateFilterProcessor
            
            # Get current table data
            current_data = self.get_all_data()
            
            # Create processor to get indices to delete
            processor = DateFilterProcessor()
            indices_to_delete = processor.get_row_indices_to_delete(current_data, cutoff_date)
            
            if not indices_to_delete:
                QMessageBox.information(None, "No Changes", "No transactions match the filter criteria.")
                return
            
            # Create single undo point for the entire operation
            self.data_manager.create_undo_point()
            
            # Delete rows in reverse order to maintain correct indices
            for row_index in sorted(indices_to_delete, reverse=True):
                self.data_manager.delete_row(row_index, create_undo_point=False)
            
            # Refresh table display
            self.refresh_table_from_data_manager()
            
            # Update change tracking
            self.has_changes = True
            self.update_button_states()
            
            # Show success message
            deleted_count = len(indices_to_delete)
            remaining_count = len(current_data) - deleted_count
            
            QMessageBox.information(None, "Filter Applied", 
                                  f"Successfully deleted {deleted_count} transactions.\n"
                                  f"{remaining_count} transactions remain.")
            
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to apply date filter:\n{str(e)}")

    def save_session(self):
        """Save current table data to CSV file"""
        try:
            from gui.session_manager import save_table_session
            save_table_session(self)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to save session:\n{str(e)}")
    
    def load_session(self):
        """Load a previous session from saved CSV files"""
        try:
            from gui.session_manager import load_table_session
            load_table_session(self)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load session:\n{str(e)}")
    
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
                self._set_item_alignment(item, col)
                self.table.setItem(row, col, item)
        
        # Reconnect the signal
        self.table.itemChanged.connect(self.on_table_item_changed)
                
        # Update visual indicators
        self.table.refresh_all_cell_appearances()
        self.table.resizeRowsToContents()
        
    def on_table_item_changed(self, item):
        """Handle table item changes and sync with data manager"""
        if item is None:
            return
            
        row = item.row()
        col = item.column()
        new_value = item.text()
        
        # Update the data manager
        self.data_manager.update_cell(row, col, new_value)
        
        # Update button states
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
            # Enable reset if data manager has changes OR table has unsaved changes
            has_data_changes = self.data_manager.has_unsaved_changes()
            has_table_changes = self.table.has_unsaved_changes()
            self.reset_btn.setEnabled(has_data_changes or has_table_changes or self.has_changes)
            
        # Filter button is enabled when there's data
        if hasattr(self, 'filter_date_btn'):
            self.filter_date_btn.setEnabled(self.table.rowCount() > 0)
            
        # Save/Load session buttons
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