"""
Data manager for tracking and validating table changes
"""
import json
import copy
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal


class TableDataManager(QObject):
    """Manages table data, change tracking, and validation"""
    
    # Signals
    validation_error = pyqtSignal(str, int, int)  # message, row, col
    data_validated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Data storage
        self.original_data = []  # Original data from processing
        self.current_data = []   # Current table data
        self.column_headers = []
        
        # Change tracking
        self.modified_cells = {}  # {(row, col): {'old': value, 'new': value}}
        self.new_rows = {}        # {row_index: [values]}
        self.deleted_rows = {}    # {original_row_index: [original_values]}
        
        # Validation rules
        self.validation_rules = {}
        self.setup_default_validation_rules()
        
        # Undo/redo stacks
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_levels = 50
        
    def setup_default_validation_rules(self):
        """Setup default validation rules for transaction table"""
        self.validation_rules = {
            # Column 0: Transaction Reference - should not be empty
            0: {
                'required': True,
                'type': 'text',
                'max_length': 500
            },
            # Column 1: Transaction Date - DD/MM/YYYY format
            1: {
                'required': True,
                'type': 'date',
                'format': 'DD/MM/YYYY',
                'max_length': 10
            },
            # Column 2: Matched Parent - text
            2: {
                'required': False,
                'type': 'text',
                'max_length': 200
            },
            # Column 3: Matched Child - text  
            3: {
                'required': False,
                'type': 'text',
                'max_length': 200
            },
            # Column 4: Month Paying For - 3-letter month format
            4: {
                'required': False,
                'type': 'month',
                'valid_months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            },
            # Column 5: Amount - should be numeric
            5: {
                'required': False,
                'type': 'number',
                'min_value': 0,
                'max_value': 999999.99
            }
        }
        
    def validate_date_format(self, date_string):
        """Validate date string in DD/MM/YYYY format"""
        try:
            datetime.strptime(date_string, '%d/%m/%Y')
            return True
        except ValueError:
            return False
        
    def set_original_data(self, data: List[List[Any]], headers: List[str]):
        """Set the original data from processing results"""
        self.original_data = copy.deepcopy(data)
        self.current_data = copy.deepcopy(data)
        self.column_headers = headers.copy()
        
        # Clear change tracking
        self.clear_change_tracking()
        
    def clear_change_tracking(self):
        """Clear all change tracking"""
        self.modified_cells.clear()
        self.new_rows.clear()
        self.deleted_rows.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        
    def update_cell(self, row: int, col: int, new_value: Any, create_undo_point: bool = True):
        """Update a cell value with change tracking"""
        if create_undo_point:
            self.create_undo_point()
            
        # Get old value
        if row < len(self.current_data) and col < len(self.current_data[row]):
            old_value = self.current_data[row][col]
        else:
            old_value = ""
            
        # Validate new value
        if not self.validate_cell_value(row, col, new_value):
            return False
            
        # Ensure current_data has enough rows/cols
        self.ensure_data_size(row + 1, col + 1)
        
        # Update current data
        self.current_data[row][col] = new_value
        
        # Track the change if it's not a new row
        if row not in self.new_rows:
            # Get original value for comparison
            original_value = ""
            if row < len(self.original_data) and col < len(self.original_data[row]):
                original_value = self.original_data[row][col]
                
            if str(new_value) != str(original_value):
                self.modified_cells[(row, col)] = {
                    'old': original_value,
                    'new': new_value
                }
            else:
                # Value reverted to original, remove from modified tracking
                self.modified_cells.pop((row, col), None)
                
        return True
        
    def add_new_row(self, row_index: int, values: List[Any] = None, create_undo_point: bool = True):
        """Add a new row at the specified index"""
        if create_undo_point:
            self.create_undo_point()
            
        if values is None:
            values = [""] * len(self.column_headers)
            
        # Ensure we have enough columns
        while len(values) < len(self.column_headers):
            values.append("")
            
        # Insert into current data
        self.current_data.insert(row_index, values)
        
        # Track as new row
        self.new_rows[row_index] = values.copy()
        
        # Update indices in tracking dictionaries
        self.update_indices_after_insert(row_index)
        
        return True
        
    def delete_row(self, row_index: int, create_undo_point: bool = True):
        """Delete a row at the specified index"""
        if row_index >= len(self.current_data):
            return False
            
        if create_undo_point:
            self.create_undo_point()
            
        # Get the row data before deletion
        row_data = self.current_data[row_index].copy()
        
        # If it's a new row, just remove it from new_rows tracking
        if row_index in self.new_rows:
            del self.new_rows[row_index]
        else:
            # Track as deleted if it's from original data
            original_row_index = self.get_original_row_index(row_index)
            if original_row_index is not None:
                self.deleted_rows[original_row_index] = row_data
                
        # Remove from current data
        del self.current_data[row_index]
        
        # Update indices in tracking dictionaries
        self.update_indices_after_delete(row_index)
        
        return True
        
    def validate_cell_value(self, row: int, col: int, value: Any) -> bool:
        """Validate a cell value against rules"""
        if col not in self.validation_rules:
            return True
            
        rules = self.validation_rules[col]
        value_str = str(value).strip()
        
        # Required field check
        if rules.get('required', False) and not value_str:
            self.validation_error.emit(f"Column {self.column_headers[col]} is required", row, col)
            return False
            
        # Type validation
        if value_str and 'type' in rules:
            if rules['type'] == 'date':
                # Validate date format DD/MM/YYYY
                if not self.validate_date_format(value_str):
                    self.validation_error.emit("Date must be in DD/MM/YYYY format", row, col)
                    return False
                    
            elif rules['type'] == 'month':
                # Validate month format (3-letter month)
                valid_months = rules.get('valid_months', [])
                if value_str not in valid_months:
                    self.validation_error.emit("Month must be in 3-letter format (Jan, Feb, etc.)", row, col)
                    return False
                    
            elif rules['type'] == 'number':
                try:
                    num_value = float(value_str)
                    
                    # Min/max value checks
                    if 'min_value' in rules and num_value < rules['min_value']:
                        self.validation_error.emit(f"Value must be >= {rules['min_value']}", row, col)
                        return False
                        
                    if 'max_value' in rules and num_value > rules['max_value']:
                        self.validation_error.emit(f"Value must be <= {rules['max_value']}", row, col)
                        return False
                        
                except ValueError:
                    self.validation_error.emit("Value must be a number", row, col)
                    return False
                    
            elif rules['type'] == 'text':
                # Max length check
                if 'max_length' in rules and len(value_str) > rules['max_length']:
                    self.validation_error.emit(f"Text too long (max {rules['max_length']} characters)", row, col)
                    return False
                    
        return True
        
    def validate_all_data(self) -> List[Tuple[int, int, str]]:
        """Validate all data and return list of errors"""
        errors = []
        
        for row in range(len(self.current_data)):
            for col in range(len(self.current_data[row])):
                if not self.validate_cell_value(row, col, self.current_data[row][col]):
                    errors.append((row, col, "Validation failed"))
                    
        return errors
        
    def create_undo_point(self):
        """Create an undo point"""
        current_state = {
            'current_data': copy.deepcopy(self.current_data),
            'modified_cells': copy.deepcopy(self.modified_cells),
            'new_rows': copy.deepcopy(self.new_rows),
            'deleted_rows': copy.deepcopy(self.deleted_rows)
        }
        
        self.undo_stack.append(current_state)
        
        # Limit undo stack size
        if len(self.undo_stack) > self.max_undo_levels:
            self.undo_stack.pop(0)
            
        # Clear redo stack when new action is performed
        self.redo_stack.clear()
        
    def undo(self) -> bool:
        """Undo the last operation"""
        if not self.undo_stack:
            return False
            
        # Save current state to redo stack
        current_state = {
            'current_data': copy.deepcopy(self.current_data),
            'modified_cells': copy.deepcopy(self.modified_cells),
            'new_rows': copy.deepcopy(self.new_rows),
            'deleted_rows': copy.deepcopy(self.deleted_rows)
        }
        self.redo_stack.append(current_state)
        
        # Restore previous state
        previous_state = self.undo_stack.pop()
        self.current_data = previous_state['current_data']
        self.modified_cells = previous_state['modified_cells']
        self.new_rows = previous_state['new_rows']
        self.deleted_rows = previous_state['deleted_rows']
        
        return True
        
    def redo(self) -> bool:
        """Redo the last undone operation"""
        if not self.redo_stack:
            return False
            
        # Save current state to undo stack
        current_state = {
            'current_data': copy.deepcopy(self.current_data),
            'modified_cells': copy.deepcopy(self.modified_cells),
            'new_rows': copy.deepcopy(self.new_rows),
            'deleted_rows': copy.deepcopy(self.deleted_rows)
        }
        self.undo_stack.append(current_state)
        
        # Restore next state
        next_state = self.redo_stack.pop()
        self.current_data = next_state['current_data']
        self.modified_cells = next_state['modified_cells']
        self.new_rows = next_state['new_rows']
        self.deleted_rows = next_state['deleted_rows']
        
        return True
        
    def ensure_data_size(self, min_rows: int, min_cols: int):
        """Ensure current_data has at least the specified size"""
        # Add rows if needed
        while len(self.current_data) < min_rows:
            new_row = [""] * min_cols
            self.current_data.append(new_row)
            
        # Add columns if needed
        for row in self.current_data:
            while len(row) < min_cols:
                row.append("")
                
    def update_indices_after_insert(self, inserted_row: int):
        """Update row indices in tracking after row insertion"""
        # Update modified_cells
        new_modified_cells = {}
        for (row, col), change in self.modified_cells.items():
            if row >= inserted_row:
                new_modified_cells[(row + 1, col)] = change
            else:
                new_modified_cells[(row, col)] = change
        self.modified_cells = new_modified_cells
        
        # Update new_rows
        new_rows = {}
        for row, data in self.new_rows.items():
            if row >= inserted_row:
                new_rows[row + 1] = data
            else:
                new_rows[row] = data
        self.new_rows = new_rows
        
    def update_indices_after_delete(self, deleted_row: int):
        """Update row indices in tracking after row deletion"""
        # Update modified_cells
        new_modified_cells = {}
        for (row, col), change in self.modified_cells.items():
            if row > deleted_row:
                new_modified_cells[(row - 1, col)] = change
            elif row < deleted_row:
                new_modified_cells[(row, col)] = change
            # Skip the deleted row
        self.modified_cells = new_modified_cells
        
        # Update new_rows
        new_rows = {}
        for row, data in self.new_rows.items():
            if row > deleted_row:
                new_rows[row - 1] = data
            elif row < deleted_row:
                new_rows[row] = data
            # Skip the deleted row
        self.new_rows = new_rows
        
    def get_original_row_index(self, current_row: int) -> Optional[int]:
        """Get the original row index for a current row (accounting for insertions/deletions)"""
        # This is a simplified version - a more complex implementation would
        # track the exact mapping between original and current indices
        if current_row < len(self.original_data):
            return current_row
        return None
        
    def get_export_data(self) -> List[List[Any]]:
        """Get data formatted for export"""
        return copy.deepcopy(self.current_data)
        
    def get_change_summary(self) -> Dict[str, Any]:
        """Get a summary of all changes made"""
        return {
            'modified_cells_count': len(self.modified_cells),
            'new_rows_count': len(self.new_rows),
            'deleted_rows_count': len(self.deleted_rows),
            'total_rows': len(self.current_data),
            'has_changes': self.has_unsaved_changes()
        }
        
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes"""
        return (len(self.modified_cells) > 0 or 
                len(self.new_rows) > 0 or 
                len(self.deleted_rows) > 0)
        
    def reset_to_original(self):
        """Reset all data back to original state"""
        self.current_data = copy.deepcopy(self.original_data)
        self.clear_change_tracking()
        
    def save_changes_to_file(self, filename: str):
        """Save current changes to a JSON file"""
        from PyQt5.QtCore import QDateTime
        
        changes_data = {
            'timestamp': str(QDateTime.currentDateTime().toString()),
            'original_data': self.original_data,
            'current_data': self.current_data,
            'modified_cells': {f"{k[0]},{k[1]}": v for k, v in self.modified_cells.items()},
            'new_rows': self.new_rows,
            'deleted_rows': self.deleted_rows,
            'column_headers': self.column_headers
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(changes_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving changes: {e}")
            return False
            
    def load_changes_from_file(self, filename: str):
        """Load changes from a JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                changes_data = json.load(f)
                
            self.original_data = changes_data.get('original_data', [])
            self.current_data = changes_data.get('current_data', [])
            self.column_headers = changes_data.get('column_headers', [])
            
            # Restore modified_cells with tuple keys
            modified_cells_str = changes_data.get('modified_cells', {})
            self.modified_cells = {}
            for key_str, value in modified_cells_str.items():
                row, col = map(int, key_str.split(','))
                self.modified_cells[(row, col)] = value
                
            self.new_rows = changes_data.get('new_rows', {})
            self.deleted_rows = changes_data.get('deleted_rows', {})
            
            return True
        except Exception as e:
            print(f"Error loading changes: {e}")
            return False