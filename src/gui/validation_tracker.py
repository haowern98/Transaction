"""
Validation rules and detailed change tracking for table data
Handles validation logic and advanced change tracking operations
"""
import copy
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal


class ValidationTracker(QObject):
    """Handles validation rules and detailed change tracking"""
    
    # Signals
    validation_error = pyqtSignal(str, int, int)  # message, row, col
    data_validated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Validation rules
        self.validation_rules = {}
        self.setup_default_validation_rules()
        
        # Advanced change tracking
        self.change_history = []  # Detailed history of all changes
        self.validation_cache = {}  # Cache validation results
        
    def setup_default_validation_rules(self):
        """Setup default validation rules for transaction table"""
        self.validation_rules = {
            # Column 0: Transaction Reference - should not be empty
            0: {
                'required': True,
                'type': 'text',
                'max_length': 500,
                'name': 'Transaction Reference'
            },
            # Column 1: Transaction Date - DD/MM/YYYY format
            1: {
                'required': True,
                'type': 'date',
                'format': 'DD/MM/YYYY',
                'max_length': 10,
                'name': 'Transaction Date'
            },
            # Column 2: Matched Parent - text
            2: {
                'required': False,
                'type': 'text',
                'max_length': 200,
                'name': 'Matched Parent'
            },
            # Column 3: Matched Child - text  
            3: {
                'required': False,
                'type': 'text',
                'max_length': 200,
                'name': 'Matched Child'
            },
            # Column 4: Month Paying For - 3-letter month format
            4: {
                'required': False,
                'type': 'month',
                'valid_months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                'name': 'Month Paying For'
            },
            # Column 5: Amount - should be numeric
            5: {
                'required': False,
                'type': 'number',
                'min_value': 0,
                'max_value': 999999.99,
                'name': 'Amount'
            }
        }
        
    def validate_date_format(self, date_string):
        """Validate date string in DD/MM/YYYY format"""
        try:
            datetime.strptime(date_string, '%d/%m/%Y')
            return True
        except ValueError:
            return False
            
    def validate_cell_value(self, row: int, col: int, value: Any) -> bool:
        """
        Validate a cell value against rules
        
        Args:
            row: Row index
            col: Column index
            value: Value to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Check cache first
        cache_key = (row, col, str(value))
        if cache_key in self.validation_cache:
            return self.validation_cache[cache_key]
            
        if col not in self.validation_rules:
            self.validation_cache[cache_key] = True
            return True
            
        rules = self.validation_rules[col]
        value_str = str(value).strip()
        
        # Required field check
        if rules.get('required', False) and not value_str:
            error_msg = f"Column {rules.get('name', col)} is required"
            self.validation_error.emit(error_msg, row, col)
            self.validation_cache[cache_key] = False
            return False
            
        # Type validation
        if value_str and 'type' in rules:
            validation_result = self._validate_by_type(value_str, rules, row, col)
            self.validation_cache[cache_key] = validation_result
            return validation_result
            
        self.validation_cache[cache_key] = True
        return True
        
    def _validate_by_type(self, value_str: str, rules: Dict, row: int, col: int) -> bool:
        """Validate value based on its type"""
        rule_type = rules['type']
        rule_name = rules.get('name', col)
        
        if rule_type == 'date':
            # Validate date format DD/MM/YYYY
            if not self.validate_date_format(value_str):
                self.validation_error.emit("Date must be in DD/MM/YYYY format", row, col)
                return False
                
        elif rule_type == 'month':
            # Validate month format (3-letter month)
            valid_months = rules.get('valid_months', [])
            if value_str not in valid_months:
                self.validation_error.emit("Month must be in 3-letter format (Jan, Feb, etc.)", row, col)
                return False
                
        elif rule_type == 'number':
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
                
        elif rule_type == 'text':
            # Max length check
            if 'max_length' in rules and len(value_str) > rules['max_length']:
                self.validation_error.emit(f"Text too long (max {rules['max_length']} characters)", row, col)
                return False
                
        return True
        
    def validate_all_data(self, data: List[List[Any]]) -> List[Tuple[int, int, str]]:
        """
        Validate all data and return list of errors
        
        Args:
            data: Table data to validate
            
        Returns:
            List of (row, col, error_message) tuples
        """
        errors = []
        
        for row in range(len(data)):
            for col in range(len(data[row])):
                if not self.validate_cell_value(row, col, data[row][col]):
                    errors.append((row, col, "Validation failed"))
                    
        return errors
        
    def clear_validation_cache(self):
        """Clear the validation cache"""
        self.validation_cache.clear()
        
    def add_validation_rule(self, column: int, rule: Dict[str, Any]):
        """
        Add or update a validation rule for a column
        
        Args:
            column: Column index
            rule: Validation rule dictionary
        """
        self.validation_rules[column] = rule
        self.clear_validation_cache()  # Clear cache when rules change
        
    def remove_validation_rule(self, column: int):
        """Remove validation rule for a column"""
        if column in self.validation_rules:
            del self.validation_rules[column]
            self.clear_validation_cache()
            
    def get_validation_rule(self, column: int) -> Optional[Dict[str, Any]]:
        """Get validation rule for a column"""
        return self.validation_rules.get(column)
        
    def get_all_validation_rules(self) -> Dict[int, Dict[str, Any]]:
        """Get all validation rules"""
        return self.validation_rules.copy()
        
    def record_change(self, row: int, col: int, old_value: Any, new_value: Any, change_type: str = "modify"):
        """
        Record a detailed change in the history
        
        Args:
            row: Row index
            col: Column index  
            old_value: Previous value
            new_value: New value
            change_type: Type of change (modify, insert, delete)
        """
        change_record = {
            'timestamp': datetime.now().isoformat(),
            'type': change_type,
            'row': row,
            'col': col,
            'old_value': old_value,
            'new_value': new_value,
            'validation_passed': self.validate_cell_value(row, col, new_value)
        }
        
        self.change_history.append(change_record)
        
        # Limit history size
        if len(self.change_history) > 1000:
            self.change_history = self.change_history[-1000:]
            
    def record_row_change(self, row: int, old_row_data: List[Any], new_row_data: List[Any], change_type: str):
        """
        Record a row-level change
        
        Args:
            row: Row index
            old_row_data: Previous row data
            new_row_data: New row data
            change_type: Type of change (insert_row, delete_row, move_row)
        """
        change_record = {
            'timestamp': datetime.now().isoformat(),
            'type': change_type,
            'row': row,
            'old_row_data': old_row_data,
            'new_row_data': new_row_data,
            'validation_passed': self._validate_row_data(new_row_data, row)
        }
        
        self.change_history.append(change_record)
        
    def _validate_row_data(self, row_data: List[Any], row: int) -> bool:
        """Validate an entire row of data"""
        for col, value in enumerate(row_data):
            if not self.validate_cell_value(row, col, value):
                return False
        return True
        
    def get_change_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get change history
        
        Args:
            limit: Maximum number of changes to return
            
        Returns:
            List of change records
        """
        if limit:
            return self.change_history[-limit:]
        return self.change_history.copy()
        
    def get_changes_for_cell(self, row: int, col: int) -> List[Dict[str, Any]]:
        """Get all changes for a specific cell"""
        return [change for change in self.change_history 
                if change.get('row') == row and change.get('col') == col]
        
    def get_changes_for_row(self, row: int) -> List[Dict[str, Any]]:
        """Get all changes for a specific row"""
        return [change for change in self.change_history 
                if change.get('row') == row]
        
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation results"""
        total_changes = len(self.change_history)
        validation_failures = sum(1 for change in self.change_history 
                                if not change.get('validation_passed', True))
        
        return {
            'total_changes': total_changes,
            'validation_failures': validation_failures,
            'validation_success_rate': ((total_changes - validation_failures) / total_changes * 100) 
                                     if total_changes > 0 else 100,
            'cache_size': len(self.validation_cache)
        }
        
    def clear_change_history(self):
        """Clear the change history"""
        self.change_history.clear()
        
    def export_change_history(self, filename: str):
        """Export change history to JSON file"""
        import json
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.change_history, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting change history: {e}")
            return False
            
    def import_change_history(self, filename: str):
        """Import change history from JSON file"""
        import json
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.change_history = json.load(f)
            return True
        except Exception as e:
            print(f"Error importing change history: {e}")
            return False
            
    def get_data_quality_report(self, data: List[List[Any]]) -> Dict[str, Any]:
        """
        Generate a data quality report
        
        Args:
            data: Table data to analyze
            
        Returns:
            Dictionary with data quality metrics
        """
        report = {
            'total_cells': 0,
            'empty_cells': 0,
            'validation_errors': [],
            'column_stats': {},
            'data_types': {},
            'recommendations': []
        }
        
        # Analyze each cell
        for row_idx, row in enumerate(data):
            for col_idx, value in enumerate(row):
                report['total_cells'] += 1
                
                value_str = str(value).strip()
                if not value_str:
                    report['empty_cells'] += 1
                    
                # Validate cell
                if not self.validate_cell_value(row_idx, col_idx, value):
                    report['validation_errors'].append({
                        'row': row_idx,
                        'col': col_idx,
                        'value': value,
                        'rule': self.validation_rules.get(col_idx, {})
                    })
                    
                # Track column statistics
                if col_idx not in report['column_stats']:
                    report['column_stats'][col_idx] = {
                        'total_values': 0,
                        'empty_values': 0,
                        'unique_values': set(),
                        'max_length': 0
                    }
                    
                col_stats = report['column_stats'][col_idx]
                col_stats['total_values'] += 1
                if not value_str:
                    col_stats['empty_values'] += 1
                else:
                    col_stats['unique_values'].add(value_str)
                    col_stats['max_length'] = max(col_stats['max_length'], len(value_str))
        
        # Convert sets to counts for JSON serialization
        for col_idx in report['column_stats']:
            report['column_stats'][col_idx]['unique_count'] = len(report['column_stats'][col_idx]['unique_values'])
            del report['column_stats'][col_idx]['unique_values']
            
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(report)
        
        # Calculate percentages
        if report['total_cells'] > 0:
            report['empty_cell_percentage'] = (report['empty_cells'] / report['total_cells']) * 100
            report['error_percentage'] = (len(report['validation_errors']) / report['total_cells']) * 100
        
        return report
        
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate data quality recommendations based on the report"""
        recommendations = []
        
        # Check for high empty cell percentage
        if report.get('empty_cell_percentage', 0) > 20:
            recommendations.append("Consider filling empty cells or reviewing data completeness")
            
        # Check for validation errors
        if len(report['validation_errors']) > 0:
            recommendations.append(f"Fix {len(report['validation_errors'])} validation errors")
            
        # Check column-specific issues
        for col_idx, stats in report['column_stats'].items():
            empty_percentage = (stats['empty_values'] / stats['total_values']) * 100 if stats['total_values'] > 0 else 0
            
            if empty_percentage > 50:
                col_name = self.validation_rules.get(col_idx, {}).get('name', f'Column {col_idx}')
                recommendations.append(f"{col_name} has {empty_percentage:.1f}% empty values")
                
        return recommendations