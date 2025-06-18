"""
Integration wrapper to replace QTableWidget with EditableTableWidget
in the existing transaction_main_window.py with minimal changes
"""
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QMessageBox
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
        
    def setup_results_table(self):
        """Setup the results table structure (replaces existing method)"""
        self.table.setColumnCount(4)
        headers = ["Transaction Reference", "Matched Parent", "Matched Child", "Amount"]
        self.table.setHorizontalHeaderLabels(headers)
        
        # Store headers in data manager
        self.data_manager.column_headers = headers
        
        # Make all columns manually resizable and fill the full width
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)  
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        
        # Set minimum column widths for better UX
        self.table.setColumnWidth(0, 1600)  # Transaction Reference
        self.table.setColumnWidth(1, 250)  # Matched Parent
        self.table.setColumnWidth(2, 250)  # Matched Child
        
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
                if col == 3:  # Amount column
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
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
            
            # Matched Parent
            matched_parent = result.get('matched_parent', 'NO MATCH FOUND')
            row_data.append(str(matched_parent))
            
            # Matched Child
            matched_child = result.get('matched_child', 'NO CHILD MATCH FOUND')
            row_data.append(str(matched_child))
            
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
        """Add simplified editing toolbar buttons to the provided layout"""
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
        
        # Spacer to push everything to the left
        edit_toolbar.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Add to main layout
        layout.addLayout(edit_toolbar)
        
        # Update button states
        self.update_button_states()
        
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
        from PyQt5.QtWidgets import QFileDialog
        
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
                if col == 3:  # Amount column
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
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