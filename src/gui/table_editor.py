"""
Editable table widget with Excel-like functionality
"""
from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView, 
                            QMenu, QAction, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData
from PyQt5.QtGui import QFont, QColor, QPalette, QKeySequence
import json


class EditableTableWidget(QTableWidget):
    """Excel-like editable table widget with advanced functionality"""
    
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
        
        # Selection state
        self.selection_start = None
        self.is_selecting = False
        
        # Setup table properties
        self.setup_table_properties()
        self.setup_context_menu()
        
        # Connect signals
        self.itemChanged.connect(self.on_item_changed)
        
    def setup_table_properties(self):
        """Configure table properties for Excel-like behavior"""
        # Enable sorting
        # self.setSortingEnabled(True)
        
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
        item = self.itemAt(position)
        if item is None:
            return
            
        menu = QMenu(self)
        
        # Copy/Cut/Paste actions
        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy_selection)
        menu.addAction(copy_action)
        
        cut_action = QAction("Cut", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.cut_selection)
        menu.addAction(cut_action)
        
        paste_action = QAction("Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste_selection)
        menu.addAction(paste_action)
        
        menu.addSeparator()
        
        # Row operations
        insert_above_action = QAction("Insert Row Above", self)
        insert_above_action.triggered.connect(lambda: self.insert_row(item.row()))
        menu.addAction(insert_above_action)
        
        insert_below_action = QAction("Insert Row Below", self)
        insert_below_action.triggered.connect(lambda: self.insert_row(item.row() + 1))
        menu.addAction(insert_below_action)
        
        delete_row_action = QAction("Delete Row", self)
        delete_row_action.triggered.connect(lambda: self.delete_row(item.row()))
        menu.addAction(delete_row_action)
        
        menu.addSeparator()
        
        # Clear/Reset actions
        clear_action = QAction("Clear Contents", self)
        clear_action.triggered.connect(self.clear_selection)
        menu.addAction(clear_action)
        
        if (item.row(), item.column()) in self.modified_cells:
            reset_action = QAction("Reset to Original", self)
            reset_action.triggered.connect(lambda: self.reset_cell(item.row(), item.column()))
            menu.addAction(reset_action)
        
        menu.exec_(self.mapToGlobal(position))
        
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Delete:
            self.clear_selection()
        elif event.matches(QKeySequence.Copy):
            self.copy_selection()
        elif event.matches(QKeySequence.Cut):
            self.cut_selection()
        elif event.matches(QKeySequence.Paste):
            self.paste_selection()
        elif event.key() == Qt.Key_F2:
            current_item = self.currentItem()
            if current_item:
                self.editItem(current_item)
        else:
            super().keyPressEvent(event)
            
    def copy_selection(self):
        """Copy selected cells to clipboard"""
        selection = self.selectedRanges()
        if not selection:
            return
            
        # Get the selected range
        selected_range = selection[0]
        
        # Create clipboard data
        clipboard_data = []
        for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
            row_data = []
            for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                item = self.item(row, col)
                cell_text = item.text() if item else ""
                row_data.append(cell_text)
            clipboard_data.append("\t".join(row_data))
        
        # Set clipboard
        clipboard_text = "\n".join(clipboard_data)
        QApplication.clipboard().setText(clipboard_text)
        
    def cut_selection(self):
        """Cut selected cells to clipboard"""
        self.copy_selection()
        self.clear_selection()
        
    def paste_selection(self):
        """Paste clipboard content to selected cells"""
        clipboard_text = QApplication.clipboard().text()
        if not clipboard_text:
            return
            
        current_item = self.currentItem()
        if not current_item:
            return
            
        start_row = current_item.row()
        start_col = current_item.column()
        
        # Parse clipboard data
        rows = clipboard_text.split('\n')
        
        for row_offset, row_data in enumerate(rows):
            if not row_data.strip():
                continue
                
            target_row = start_row + row_offset
            
            # Add new rows if needed
            while target_row >= self.rowCount():
                self.add_new_row()
                
            cells = row_data.split('\t')
            for col_offset, cell_data in enumerate(cells):
                target_col = start_col + col_offset
                
                if target_col < self.columnCount():
                    item = self.item(target_row, target_col)
                    if not item:
                        item = QTableWidgetItem()
                        self.setItem(target_row, target_col, item)
                    
                    item.setText(cell_data)
                    self.mark_cell_modified(target_row, target_col)
        
        self.data_changed.emit()
        
    def clear_selection(self):
        """Clear contents of selected cells"""
        for item in self.selectedItems():
            item.setText("")
            self.mark_cell_modified(item.row(), item.column())
        self.data_changed.emit()
        
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
            QMessageBox.warning(self, "Warning", "Cannot delete the last row.")
            return
            
        self.removeRow(row_index)
        
        # Update tracking sets
        self.update_row_indices_after_delete(row_index)
        
        self.row_deleted.emit(row_index)
        self.data_changed.emit()
        
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
        
    def reset_cell(self, row, col):
        """Reset a cell to its original value"""
        if (row, col) in self.modified_cells and row < len(self.original_data):
            original_item = self.original_data[row].get(col, "")
            current_item = self.item(row, col)
            if current_item:
                current_item.setText(str(original_item))
            self.modified_cells.discard((row, col))
            self.update_cell_appearance(row, col)
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
            
        # if row in self.new_rows:
        # #     # New row - light green background
        #      item.setBackground(QColor(230, 255, 230))
        # # elif (row, col) in self.modified_cells:
        # #     # Modified cell - light yellow background
        # #     item.setBackground(QColor(255, 255, 230))
        # else:
        # #     # Original cell - default background
        #      item.setBackground(QColor())
            
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
        self.original_data = []
        for row_data in data:
            row_dict = {}
            for col, value in enumerate(row_data):
                row_dict[col] = value
            self.original_data.append(row_dict)
            
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
        
    def get_modified_data(self):
        """Get only the modified and new data"""
        modified_data = {
            'modified_cells': {},
            'new_rows': [],
            'deleted_rows': []  # Would need additional tracking for this
        }
        
        # Get modified cells
        for row, col in self.modified_cells:
            if row not in modified_data['modified_cells']:
                modified_data['modified_cells'][row] = {}
            item = self.item(row, col)
            modified_data['modified_cells'][row][col] = item.text() if item else ""
            
        # Get new rows
        for row in sorted(self.new_rows):
            row_data = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                row_data.append(item.text() if item else "")
            modified_data['new_rows'].append({
                'index': row,
                'data': row_data
            })
            
        return modified_data
        
    def has_unsaved_changes(self):
        """Check if there are unsaved changes"""
        return len(self.modified_cells) > 0 or len(self.new_rows) > 0
        
    def refresh_all_cell_appearances(self):
        """Refresh appearance of all cells"""
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                self.update_cell_appearance(row, col)