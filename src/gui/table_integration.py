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
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # Transaction Reference - resizable
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # Matched Parent - resizable
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # Matched Child - resizable
        header.setSectionResizeMode(3, QHeaderView.Interactive)  # Amount - resizable
        
        # Make the last column stretch to fill any remaining space
        header.setStretchLastSection(True)
        
        # Set initial column widths that will fill most of the table width
        self.table.setColumnWidth(0, 1200)  # Transaction Reference - large
        self.table.setColumnWidth(1, 250)  # Matched Parent
        self.table.setColumnWidth(2, 250)  # Matched Child  
        # Amount column will stretch to fill remaining space
        
        # Enable text wrapping for long content
        self.table.setWordWrap(True)
        
        # Set default row height to accommodate wrapped text
        self.table.verticalHeader().setDefaultSectionSize(50)
        
        # Enable sorting
        self.table.setSortingEnabled(True)
        
        # Set alternating row colors
        self.table.setAlternatingRowColors(True)
        
    def populate_results_table(self, results_data):
        """Populate the results table with data (replaces existing method)"""
        self.table.setRowCount(len(results_data))
        
        # Prepare data for data manager
        table_data = []
        
        for row, result in enumerate(results_data):
            row_data = []
            
            # Transaction Reference - no truncation, full text
            trans_ref = result.get('parent_from_transaction', '')
            trans_ref_item = QTableWidgetItem(str(trans_ref))
            trans_ref_item.setFlags(trans_ref_item.flags() | Qt.TextWordWrap)
            self.table.setItem(row, 0, trans_ref_item)
            row_data.append(str(trans_ref))
            
            # Matched Parent
            matched_parent = result.get('matched_parent', 'NO MATCH FOUND')
            self.table.setItem(row, 1, QTableWidgetItem(str(matched_parent)))
            row_data.append(str(matched_parent))
            
            # Matched Child
            matched_child = result.get('matched_child', 'NO CHILD MATCH FOUND')
            self.table.setItem(row, 2, QTableWidgetItem(str(matched_child)))
            row_data.append(str(matched_child))
            
            # Amount
            amount = result.get('amount', 0)
            if isinstance(amount, (int, float)) and amount > 0:
                amount_text = f"{amount:.2f}"
            else:
                amount_text = ""
            amount_item = QTableWidgetItem(amount_text)
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, amount_item)
            row_data.append(amount_text)
            
            table_data.append(row_data)
        
        # Set original data in data manager and table
        headers = ["Transaction Reference", "Matched Parent", "Matched Child", "Amount"]
        self.data_manager.set_original_data(table_data, headers)
        self.table.set_original_data(table_data)
        
        # Resize rows to fit content after populating
        self.table.resizeRowsToContents()
        
        # Reset change tracking
        self.has_changes = False
        
    def add_toolbar_buttons(self, layout):
        """Add editing toolbar buttons to the provided layout"""
        from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy
        
        # Create editing toolbar
        edit_toolbar = QHBoxLayout()
        
        # Add row button
        self.add_row_btn = QPushButton("Add Row")
        self.add_row_btn.clicked.connect(self.add_new_row)
        edit_toolbar.addWidget(self.add_row_btn)
        
        # Delete selected rows button
        self.delete_rows_btn = QPushButton("Delete Selected")
        self.delete_rows_btn.clicked.connect(self.delete_selected_rows)
        edit_toolbar.addWidget(self.delete_rows_btn)
        
        # Separator
        edit_toolbar.addWidget(QLabel("|"))
        
        # Undo/Redo buttons
        self.undo_btn = QPushButton("Undo")
        self.undo_btn.clicked.connect(self.undo_changes)
        edit_toolbar.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("Redo")
        self.redo_btn.clicked.connect(self.redo_changes)
        edit_toolbar.addWidget(self.redo_btn)
        
        # Separator
        edit_toolbar.addWidget(QLabel("|"))
        
        # Save/Reset buttons
        self.save_changes_btn = QPushButton("Save Changes")
        self.save_changes_btn.clicked.connect(self.save_changes)
        edit_toolbar.addWidget(self.save_changes_btn)
        
        self.reset_btn = QPushButton("Reset All")
        self.reset_btn.clicked.connect(self.reset_to_original)
        edit_toolbar.addWidget(self.reset_btn)
        
        # Spacer
        edit_toolbar.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Status label
        self.changes_label = QLabel("No changes")
        self.changes_label.setStyleSheet("color: gray; font-style: italic;")
        edit_toolbar.addWidget(self.changes_label)
        
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
            
    def redo_changes(self):
        """Redo last undone change"""
        if self.data_manager.redo():
            self.refresh_table_from_data_manager()
            
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
        
        for row in range(len(data)):
            for col in range(len(data[row]) if row < len(data) else 0):
                item = QTableWidgetItem(str(data[row][col]))
                if col == 3:  # Amount column
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif col == 0:  # Transaction Reference
                    item.setFlags(item.flags() | Qt.TextWordWrap)
                self.table.setItem(row, col, item)
                
        # Update visual indicators
        self.table.refresh_all_cell_appearances()
        self.table.resizeRowsToContents()
        
    def on_data_changed(self):
        """Handle data changes"""
        self.has_changes = self.table.has_unsaved_changes()
        self.update_button_states()
        
    def on_row_added(self, row_index):
        """Handle row addition"""
        self.has_changes = True
        self.update_button_states()
        
    def on_row_deleted(self, row_index):
        """Handle row deletion"""
        self.has_changes = True
        self.update_button_states()
        
    def on_validation_error(self, message, row, col):
        """Handle validation errors"""
        QMessageBox.warning(None, "Validation Error", 
                          f"Row {row + 1}, Column {col + 1}: {message}")
        
    def update_button_states(self):
        """Update button enabled states and change indicator"""
        if hasattr(self, 'undo_btn'):
            self.undo_btn.setEnabled(len(self.data_manager.undo_stack) > 0)
            self.redo_btn.setEnabled(len(self.data_manager.redo_stack) > 0)
            self.save_changes_btn.setEnabled(self.has_changes)
            self.reset_btn.setEnabled(self.has_changes)
            
            # Update changes label
            if self.has_changes:
                summary = self.data_manager.get_change_summary()
                changes_text = []
                if summary['modified_cells_count'] > 0:
                    changes_text.append(f"{summary['modified_cells_count']} modified")
                if summary['new_rows_count'] > 0:
                    changes_text.append(f"{summary['new_rows_count']} added")
                if summary['deleted_rows_count'] > 0:
                    changes_text.append(f"{summary['deleted_rows_count']} deleted")
                
                self.changes_label.setText(" | ".join(changes_text))
                self.changes_label.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.changes_label.setText("No changes")
                self.changes_label.setStyleSheet("color: gray; font-style: italic;")
                
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