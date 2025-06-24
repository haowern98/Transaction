"""
Complex table operations for the editable table
Handles copy/paste, context menus, and advanced editing operations
"""
from PyQt5.QtWidgets import (QMenu, QAction, QMessageBox, QApplication, 
                            QTableWidgetItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence


class TableOperations:
    """Handles complex operations for the editable table widget"""
    
    def __init__(self, table_widget):
        """
        Initialize with reference to the table widget
        
        Args:
            table_widget: The EditableTableWidget instance
        """
        self.table = table_widget
        
    def show_context_menu(self, position, item):
        """
        Show context menu at the given position
        
        Args:
            position: Position where menu was requested
            item: Table item at the position
        """
        if item is None:
            return
            
        menu = QMenu(self.table)
        
        # Copy/Cut/Paste actions
        copy_action = QAction("Copy", self.table)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy_selection)
        menu.addAction(copy_action)
        
        cut_action = QAction("Cut", self.table)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.cut_selection)
        menu.addAction(cut_action)
        
        paste_action = QAction("Paste", self.table)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste_selection)
        menu.addAction(paste_action)
        
        menu.addSeparator()
        
        # Row operations
        insert_above_action = QAction("Insert Row Above", self.table)
        insert_above_action.triggered.connect(lambda: self.table.insert_row(item.row()))
        menu.addAction(insert_above_action)
        
        insert_below_action = QAction("Insert Row Below", self.table)
        insert_below_action.triggered.connect(lambda: self.table.insert_row(item.row() + 1))
        menu.addAction(insert_below_action)
        
        delete_row_action = QAction("Delete Row", self.table)
        delete_row_action.triggered.connect(lambda: self.table.delete_row(item.row()))
        menu.addAction(delete_row_action)
        
        menu.addSeparator()
        
        # Clear/Reset actions
        clear_action = QAction("Clear Contents", self.table)
        clear_action.triggered.connect(self.clear_selection)
        menu.addAction(clear_action)
        
        if self.table.is_cell_modified(item.row(), item.column()):
            reset_action = QAction("Reset to Original", self.table)
            reset_action.triggered.connect(lambda: self.reset_cell(item.row(), item.column()))
            menu.addAction(reset_action)
        
        menu.exec_(self.table.mapToGlobal(position))
        
    def copy_selection(self):
        """Copy selected cells to clipboard"""
        selection = self.table.selectedRanges()
        if not selection:
            return
            
        # Get the selected range
        selected_range = selection[0]
        
        # Create clipboard data
        clipboard_data = []
        for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
            row_data = []
            for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                item = self.table.item(row, col)
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
            
        current_item = self.table.currentItem()
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
            while target_row >= self.table.rowCount():
                self.table.add_new_row()
                
            cells = row_data.split('\t')
            for col_offset, cell_data in enumerate(cells):
                target_col = start_col + col_offset
                
                if target_col < self.table.columnCount():
                    self.table.set_cell_text(target_row, target_col, cell_data)
        
        self.table.data_changed.emit()
        
    def clear_selection(self):
        """Clear contents of selected cells"""
        for item in self.table.selectedItems():
            item.setText("")
            self.table.mark_cell_modified(item.row(), item.column())
        self.table.data_changed.emit()
        
    def reset_cell(self, row, col):
        """Reset a cell to its original value"""
        if row < len(self.table.original_data) and col < len(self.table.original_data[row]):
            original_value = self.table.original_data[row][col]
            self.table.set_cell_text(row, col, str(original_value))
            # Remove from modified tracking
            self.table.modified_cells.discard((row, col))
            self.table.update_cell_appearance(row, col)
            self.table.data_changed.emit()
            
    def select_all(self):
        """Select all cells in the table"""
        self.table.selectAll()
        
    def select_row(self, row):
        """Select an entire row"""
        self.table.selectRow(row)
        
    def select_column(self, col):
        """Select an entire column"""
        self.table.selectColumn(col)
        
    def insert_rows(self, start_row, count=1):
        """Insert multiple rows starting at the specified position"""
        for i in range(count):
            self.table.insert_row(start_row + i)
            
    def delete_rows(self, row_indices):
        """Delete multiple rows"""
        # Sort in reverse order to maintain correct indices during deletion
        sorted_indices = sorted(row_indices, reverse=True)
        
        for row_index in sorted_indices:
            self.table.delete_row(row_index)
            
    def duplicate_row(self, row):
        """Duplicate a row"""
        if row >= self.table.rowCount():
            return
            
        # Get data from the row to duplicate
        row_data = []
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            row_data.append(item.text() if item else "")
        
        # Insert new row below the current one
        new_row = row + 1
        self.table.insert_row(new_row)
        
        # Copy data to the new row
        for col, value in enumerate(row_data):
            self.table.set_cell_text(new_row, col, value)
            
    def move_row_up(self, row):
        """Move a row up by one position"""
        if row <= 0:
            return
            
        self._swap_rows(row, row - 1)
        
    def move_row_down(self, row):
        """Move a row down by one position"""
        if row >= self.table.rowCount() - 1:
            return
            
        self._swap_rows(row, row + 1)
        
    def _swap_rows(self, row1, row2):
        """Swap the contents of two rows"""
        # Get data from both rows
        row1_data = []
        row2_data = []
        
        for col in range(self.table.columnCount()):
            item1 = self.table.item(row1, col)
            item2 = self.table.item(row2, col)
            row1_data.append(item1.text() if item1 else "")
            row2_data.append(item2.text() if item2 else "")
        
        # Swap the data
        for col in range(self.table.columnCount()):
            self.table.set_cell_text(row1, col, row2_data[col])
            self.table.set_cell_text(row2, col, row1_data[col])
            
    def find_and_replace(self, find_text, replace_text, match_case=False, whole_word=False):
        """
        Find and replace text in the table
        
        Args:
            find_text: Text to find
            replace_text: Text to replace with
            match_case: Whether to match case
            whole_word: Whether to match whole words only
        """
        replacements_made = 0
        
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if not item:
                    continue
                    
                cell_text = item.text()
                
                # Perform the search and replace based on options
                if self._should_replace(cell_text, find_text, match_case, whole_word):
                    new_text = self._perform_replace(cell_text, find_text, replace_text, match_case, whole_word)
                    if new_text != cell_text:
                        self.table.set_cell_text(row, col, new_text)
                        replacements_made += 1
        
        return replacements_made
        
    def _should_replace(self, cell_text, find_text, match_case, whole_word):
        """Check if text should be replaced based on search criteria"""
        search_text = cell_text if match_case else cell_text.lower()
        target_text = find_text if match_case else find_text.lower()
        
        if whole_word:
            import re
            pattern = r'\b' + re.escape(target_text) + r'\b'
            flags = 0 if match_case else re.IGNORECASE
            return bool(re.search(pattern, search_text, flags))
        else:
            return target_text in search_text
            
    def _perform_replace(self, cell_text, find_text, replace_text, match_case, whole_word):
        """Perform the actual text replacement"""
        if whole_word:
            import re
            pattern = r'\b' + re.escape(find_text) + r'\b'
            flags = 0 if match_case else re.IGNORECASE
            return re.sub(pattern, replace_text, cell_text, flags=flags)
        else:
            if match_case:
                return cell_text.replace(find_text, replace_text)
            else:
                # Case-insensitive replacement
                import re
                pattern = re.escape(find_text)
                return re.sub(pattern, replace_text, cell_text, flags=re.IGNORECASE)
                
    def format_as_currency(self, decimal_places=2, currency_symbol="$"):
        """Format selected cells as currency"""
        for item in self.table.selectedItems():
            try:
                value = float(item.text().replace(',', '').replace(currency_symbol, ''))
                formatted = f"{currency_symbol}{value:,.{decimal_places}f}"
                item.setText(formatted)
                self.table.mark_cell_modified(item.row(), item.column())
            except ValueError:
                # Skip cells that can't be converted to numbers
                continue
        
        self.table.data_changed.emit()
        
    def format_as_percentage(self, decimal_places=1):
        """Format selected cells as percentage"""
        for item in self.table.selectedItems():
            try:
                value = float(item.text().replace('%', ''))
                # If value is > 1, assume it's already a percentage, otherwise multiply by 100
                if value <= 1:
                    value *= 100
                formatted = f"{value:.{decimal_places}f}%"
                item.setText(formatted)
                self.table.mark_cell_modified(item.row(), item.column())
            except ValueError:
                # Skip cells that can't be converted to numbers
                continue
        
        self.table.data_changed.emit()
        
    def auto_resize_columns(self):
        """Auto-resize all columns to fit content"""
        self.table.resizeColumnsToContents()
        
    def auto_resize_rows(self):
        """Auto-resize all rows to fit content"""
        self.table.resizeRowsToContents()
        
    def get_selection_info(self):
        """Get information about the current selection"""
        selection = self.table.selectedRanges()
        if not selection:
            return None
            
        selected_range = selection[0]
        return {
            'top_row': selected_range.topRow(),
            'bottom_row': selected_range.bottomRow(),
            'left_col': selected_range.leftColumn(),
            'right_col': selected_range.rightColumn(),
            'row_count': selected_range.rowCount(),
            'col_count': selected_range.columnCount()
        }