"""
Core editable table widget with basic functionality
Provides the fundamental editable table without complex operations
"""
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence
import copy


class EditableTableWidget(QTableWidget):
    """Core editable table widget with basic Excel-like functionality"""
    
    # Signals
    data_changed = pyqtSignal()  # Emitted when table data is modified
    row_added = pyqtSignal(int)  # Emitted when new row is added
    row_deleted = pyqtSignal(int)  # Emitted when row is deleted
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Track modifications
        self.original_data = []
        self.modified_cells = set()  # Set of (row, col) tuples that have been modified
        self.new_rows = set()  # Set of row indices that are newly added
        
        # Setup table properties
        self.setup_table_properties()
        self.setup_context_menu()
        
        # Connect signals
        self.itemChanged.connect(self.on_item_changed)
        
    def setup_table_properties(self):
        """Configure table properties for Excel-like behavior"""
        # Set selection behavior
        self.setSelectionBehavior(QTableWidget.SelectItems)
        self.setSelectionMode(QTableWidget.ExtendedSelection)
        
        # Enable alternating row colors
        self.setAlternatingRowColors(True)
        
        # Set word wrap
        self.setWordWrap(True)
        
        # Configure headers
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setDefaultSectionSize(50)
        
        # Set font
        font = QFont("Arial", 9)
        self.setFont(font)
        
    def setup_context_menu(self):
        """Setup right-click context menu"""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def show_context_menu(self, position):
        """Show context menu at the given position"""
        from gui.table_operations import TableOperations
        
        item = self.itemAt(position)
        if item is None:
            return
        
        # Delegate to table operations
        operations = TableOperations(self)
        operations.show_context_menu(position, item)
        
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        from gui.table_operations import TableOperations
        
        if event.key() == Qt.Key_Delete:
            operations = TableOperations(self)
            operations.clear_selection()
        elif event.matches(QKeySequence.Copy):
            operations = TableOperations(self)
            operations.copy_selection()
        elif event.matches(QKeySequence.Cut):
            operations = TableOperations(self)
            operations.cut_selection()
        elif event.matches(QKeySequence.Paste):
            operations = TableOperations(self)
            operations.paste_selection()
        elif event.key() == Qt.Key_F2:
            current_item = self.currentItem()
            if current_item:
                self.editItem(current_item)
        else:
            super().keyPressEvent(event)
            
    def insert_row(self, row_index):
        """Insert a new row at the specified index"""
        self.insertRow(row_index)
        self.new_rows.add(row_index)
        
        # Update row indices in tracking sets
        self.update_row_indices_after_insert(row_index)
        
        # Initialize new row with empty items
        for col in range(self.columnCount()):
            item = QTableWidgetItem("")
            self.setItem(row_index, col, item)
            
        self.row_added.emit(row_index)
        self.data_changed.emit()
        
    def delete_row(self, row_index):
        """Delete the specified row"""
        if self.rowCount() <= 1:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Warning", "Cannot delete the last row.")
            return False
            
        # Get the row data before deletion
        row_data = []
        for col in range(self.columnCount()):
            item = self.item(row_index, col)
            row_data.append(item.text() if item else "")
        
        # If it's a new row, just remove it from new_rows tracking
        if row_index in self.new_rows:
            self.new_rows.discard(row_index)
            
        # Remove from table
        self.removeRow(row_index)
        
        # Update indices in tracking sets
        self.update_row_indices_after_delete(row_index)
        
        self.row_deleted.emit(row_index)
        self.data_changed.emit()
        
        return True
        
    def add_new_row(self):
        """Add a new row at the end of the table"""
        row_index = self.rowCount()
        self.insertRow(row_index)
        self.new_rows.add(row_index)
        
        # Initialize new row with empty items
        for col in range(self.columnCount()):
            item = QTableWidgetItem("")
            self.setItem(row_index, col, item)
            
        self.row_added.emit(row_index)
        self.data_changed.emit()
        
    def mark_cell_modified(self, row, col):
        """Mark a cell as modified"""
        if row not in self.new_rows:  # Don't mark new rows as modified
            self.modified_cells.add((row, col))
        self.update_cell_appearance(row, col)
        
    def update_cell_appearance(self, row, col):
        """Update cell appearance based on modification status"""
        item = self.item(row, col)
        if not item:
            return
        
        # Visual indicators for modified cells can be added here
        # Currently keeping default appearance for simplicity
            
    def on_item_changed(self, item):
        """Handle item changes"""
        if item:
            self.mark_cell_modified(item.row(), item.column())
            self.data_changed.emit()
            
    def update_row_indices_after_insert(self, inserted_row):
        """Update row indices in tracking sets after row insertion"""
        # Update modified_cells
        new_modified_cells = set()
        for row, col in self.modified_cells:
            if row >= inserted_row:
                new_modified_cells.add((row + 1, col))
            else:
                new_modified_cells.add((row, col))
        self.modified_cells = new_modified_cells
        
        # Update new_rows
        new_rows = set()
        for row in self.new_rows:
            if row >= inserted_row:
                new_rows.add(row + 1)
            else:
                new_rows.add(row)
        self.new_rows = new_rows
        
    def update_row_indices_after_delete(self, deleted_row):
        """Update row indices in tracking sets after row deletion"""
        # Update modified_cells
        new_modified_cells = set()
        for row, col in self.modified_cells:
            if row > deleted_row:
                new_modified_cells.add((row - 1, col))
            elif row < deleted_row:
                new_modified_cells.add((row, col))
        self.modified_cells = new_modified_cells
        
        # Update new_rows
        new_rows = set()
        for row in self.new_rows:
            if row > deleted_row:
                new_rows.add(row - 1)
            elif row < deleted_row:
                new_rows.add(row)
        self.new_rows = new_rows
        
    def set_original_data(self, data):
        """Set the original data for tracking modifications"""
        self.original_data = copy.deepcopy(data)
        
        # Reset modification tracking
        self.modified_cells.clear()
        self.new_rows.clear()
        
    def get_all_data(self):
        """Get all table data including modifications"""
        data = []
        for row in range(self.rowCount()):
            row_data = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        return data
        
    def has_unsaved_changes(self):
        """Check if there are unsaved changes"""
        return len(self.modified_cells) > 0 or len(self.new_rows) > 0
        
    def refresh_all_cell_appearances(self):
        """Refresh appearance of all cells"""
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                self.update_cell_appearance(row, col)
                
    def clear_selection_contents(self):
        """Clear contents of selected cells"""
        for item in self.selectedItems():
            item.setText("")
            self.mark_cell_modified(item.row(), item.column())
        self.data_changed.emit()
        
    def get_selected_range(self):
        """Get the currently selected range"""
        selection = self.selectedRanges()
        if not selection:
            return None
        return selection[0]
        
    def select_range(self, top_row, left_col, bottom_row, right_col):
        """Select a range of cells"""
        from PyQt5.QtWidgets import QTableWidgetSelectionRange
        
        selection_range = QTableWidgetSelectionRange(top_row, left_col, bottom_row, right_col)
        self.setRangeSelected(selection_range, True)
        
    def ensure_minimum_size(self, min_rows, min_cols):
        """Ensure table has at least the specified number of rows and columns"""
        # Add rows if needed
        while self.rowCount() < min_rows:
            self.add_new_row()
            
        # Add columns if needed
        current_cols = self.columnCount()
        if current_cols < min_cols:
            self.setColumnCount(min_cols)
            # Initialize new columns with empty headers
            for col in range(current_cols, min_cols):
                self.setHorizontalHeaderItem(col, QTableWidgetItem(f"Column {col + 1}"))
                
    def get_cell_text(self, row, col):
        """Get text from a specific cell"""
        item = self.item(row, col)
        return item.text() if item else ""
        
    def set_cell_text(self, row, col, text):
        """Set text in a specific cell"""
        # Ensure the cell exists
        if row >= self.rowCount():
            while self.rowCount() <= row:
                self.add_new_row()
                
        item = self.item(row, col)
        if not item:
            item = QTableWidgetItem()
            self.setItem(row, col, item)
            
        item.setText(str(text))
        self.mark_cell_modified(row, col)
        
    def is_cell_modified(self, row, col):
        """Check if a specific cell has been modified"""
        return (row, col) in self.modified_cells
        
    def is_row_new(self, row):
        """Check if a row is newly added"""
        return row in self.new_rows