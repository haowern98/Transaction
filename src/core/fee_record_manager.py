"""
Fee Record Manager - Core Excel operations for loading table data to fee record
Handles month matching, column creation, and data insertion logic with yellow cell highlighting
File: src/core/fee_record_manager.py
"""
import pandas as pd
import openpyxl
from openpyxl.utils import column_index_from_string, get_column_letter
from openpyxl.styles import PatternFill, Font, Border, Side
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
import os
import shutil


class FeeRecordManager:
    """Manages loading preview table data into Fee Record Excel file with yellow highlighting"""
    
    # Month name mapping from preview table to fee record headers
    MONTH_MAPPING = {
        "Jan": "JANUARY", "Feb": "FEBRUARY", "Mar": "MARCH",
        "Apr": "APRIL", "May": "MAY", "Jun": "JUNE", 
        "Jul": "JULY", "Aug": "AUGUST", "Sep": "SEPTEMBER",
        "Oct": "OCTOBER", "Nov": "NOVEMBER", "Dec": "DECEMBER"
    }
    
    # Reverse mapping for chronological ordering
    MONTH_ORDER = {
        "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4,
        "MAY": 5, "JUNE": 6, "JULY": 7, "AUGUST": 8,
        "SEPTEMBER": 9, "OCTOBER": 10, "NOVEMBER": 11, "DECEMBER": 12
    }
    
    def __init__(self):
        self.workbook = None
        self.worksheet = None
        self.fee_record_path = ""
        self.column_mapping = {}  # {month: {"date_col": col_index, "amount_col": col_index}}
        self.parent_column = 1    # Assume first column has parent names
        
        # Cell styling for highlighting updated cells
        self.highlight_fill = PatternFill(
            start_color="FFFF00",  # Yellow background
            end_color="FFFF00",
            fill_type="solid"
        )
        
        # Light blue fill for new parent names
        self.new_parent_fill = PatternFill(
            start_color="E6F3FF",  # Light blue background
            end_color="E6F3FF",
            fill_type="solid"
        )
        
        # Track updated cells for statistics
        self.updated_cells = []
        
    def load_table_data_to_fee_record(self, table_data: List[List[str]], 
                                     fee_record_file_path: str) -> Dict[str, Any]:
        """
        Main method to load preview table data into fee record file
        Enhanced with cell highlighting and detailed statistics
        
        Args:
            table_data: Current table data from get_all_data()
            fee_record_file_path: Path to fee record Excel file
            
        Returns:
            Dict with success status, statistics, and highlighting info
        """
        try:
            # Validate inputs
            if not table_data:
                return {"success": False, "error": "No data to load"}
                
            if not os.path.exists(fee_record_file_path):
                return {"success": False, "error": f"Fee record file not found: {fee_record_file_path}"}
            
            # Check if file is locked/in use
            if self._is_file_locked(fee_record_file_path):
                return {
                    "success": False, 
                    "error": f"File is currently in use or locked.\n\n"
                            f"Please:\n"
                            f"1. Close Excel if the file is open\n"
                            f"2. Make sure no other program is using the file\n"
                            f"3. Check that you have write permissions\n\n"
                            f"File: {fee_record_file_path}"
                }
            
            # Create backup
            backup_path = self._create_backup(fee_record_file_path)
            
            # Load Excel file with error handling
            try:
                self.fee_record_path = fee_record_file_path
                self.workbook = openpyxl.load_workbook(fee_record_file_path)
                self.worksheet = self.workbook.active
            except PermissionError as e:
                return {
                    "success": False,
                    "error": f"Permission denied accessing file.\n\n"
                            f"Please:\n"
                            f"1. Close Excel if the file is open\n"
                            f"2. Run the application as administrator if needed\n"
                            f"3. Check file permissions\n\n"
                            f"File: {fee_record_file_path}\n"
                            f"Error: {str(e)}"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to open Excel file.\n\n"
                            f"Error: {str(e)}\n"
                            f"File: {fee_record_file_path}"
                }
            
            # Analyze existing structure
            self._analyze_fee_record_structure()
            
            # Process table data (with highlighting)
            stats = self._process_table_data(table_data)
            
            # Get highlighting summary
            highlighting_summary = self.get_highlighting_summary()
            
            # Save changes with error handling
            try:
                self.workbook.save(fee_record_file_path)
            except PermissionError as e:
                return {
                    "success": False,
                    "error": f"Permission denied saving file.\n\n"
                            f"The file may be open in Excel or write-protected.\n"
                            f"Please close Excel and try again.\n\n"
                            f"File: {fee_record_file_path}\n"
                            f"Error: {str(e)}"
                }
            
            return {
                "success": True,
                "backup_path": backup_path,
                "stats": stats,
                "highlighting": highlighting_summary
            }
            
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
        finally:
            if self.workbook:
                try:
                    self.workbook.close()
                except:
                    pass

    def _create_backup(self, file_path: str) -> str:
        """Create backup of original fee record file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup_{timestamp}"
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def _is_file_locked(self, file_path: str) -> bool:
        """
        Check if file is locked or in use by another process
        
        Args:
            file_path: Path to file to check
            
        Returns:
            bool: True if file is locked, False otherwise
        """
        try:
            # Try to open file in append mode (less intrusive than write mode)
            with open(file_path, 'a'):
                pass
            return False
        except IOError:
            return True
        except Exception:
            return True
    
    def _analyze_fee_record_structure(self):
        """Analyze fee record file structure and build column mapping"""
        if not self.worksheet:
            raise Exception("Worksheet not loaded")
        
        # Read header row (row 1)
        headers = []
        for col in range(1, self.worksheet.max_column + 1):
            cell_value = self.worksheet.cell(row=1, column=col).value
            headers.append(str(cell_value) if cell_value else "")
        
        # Find month columns and their sub-columns
        self.column_mapping = {}
        current_month = None
        
        for col_idx, header in enumerate(headers, 1):
            header = header.strip().upper()
            
            # Check if this is a month header
            if header in self.MONTH_ORDER:
                current_month = header
                self.column_mapping[current_month] = {"start_col": col_idx}
                
            # Detect date/amount sub-columns by pattern
            elif current_month and "date_col" not in self.column_mapping[current_month]:
                # First sub-column after month header is date
                self.column_mapping[current_month]["date_col"] = col_idx
                
            elif current_month and "amount_col" not in self.column_mapping[current_month]:
                # Second sub-column after month header is amount
                self.column_mapping[current_month]["amount_col"] = col_idx
                current_month = None  # Reset for next month
    
    def _process_table_data(self, table_data: List[List[str]]) -> Dict[str, int]:
        """Process all table data and insert into fee record with highlighting"""
        stats = {
            "processed_rows": 0,
            "updated_entries": 0,
            "new_parents": 0,
            "new_months_created": 0,
            "errors": 0,
            "highlighted_cells": 0
        }
        
        # Clear updated cells tracking
        self.updated_cells = []
        
        # Group data by required months
        required_months = set()
        for row in table_data:
            if len(row) >= 5 and row[4]:  # Month Paying For column
                month_3letter = row[4].strip()
                if month_3letter in self.MONTH_MAPPING:
                    required_months.add(self.MONTH_MAPPING[month_3letter])
        
        # Create missing month columns
        for month in required_months:
            if month not in self.column_mapping:
                self._create_month_column(month)
                stats["new_months_created"] += 1
        
        # Process each data row
        for row_data in table_data:
            try:
                if self._process_single_row(row_data):
                    stats["updated_entries"] += 1
                stats["processed_rows"] += 1
            except Exception as e:
                print(f"Error processing row {row_data}: {e}")
                stats["errors"] += 1
        
        # Update highlighted cells count
        stats["highlighted_cells"] = len(self.updated_cells)
        
        return stats
    
    def _create_month_column(self, month_name: str):
        """Create new month column with date and amount sub-columns"""
        # Find insertion point (left of last month column)
        insertion_col = self._find_month_insertion_point()
        
        # Insert 2 new columns (date and amount)
        self.worksheet.insert_cols(insertion_col, 2)
        
        # Set headers
        month_header_cell = self.worksheet.cell(row=1, column=insertion_col, value=month_name)
        amount_header_cell = self.worksheet.cell(row=1, column=insertion_col + 1, value="")
        
        # Style the month header (make it bold)
        month_header_cell.font = Font(bold=True)
        
        # Update column mapping
        self.column_mapping[month_name] = {
            "date_col": insertion_col,
            "amount_col": insertion_col + 1
        }
        
        # Update existing column mappings (shift right)
        for month, mapping in self.column_mapping.items():
            if month != month_name:
                if mapping.get("date_col", 0) >= insertion_col:
                    mapping["date_col"] += 2
                if mapping.get("amount_col", 0) >= insertion_col:
                    mapping["amount_col"] += 2
    
    def _find_month_insertion_point(self) -> int:
        """Find where to insert new month column (left of last month)"""
        if not self.column_mapping:
            return 2  # After parent name column
        
        # Find the last (rightmost) month column
        last_month_col = 0
        for month_mapping in self.column_mapping.values():
            amount_col = month_mapping.get("amount_col", 0)
            if amount_col > last_month_col:
                last_month_col = amount_col
        
        return last_month_col + 1
    
    def _process_single_row(self, row_data: List[str]) -> bool:
        """Process a single row from table data with yellow cell highlighting"""
        if len(row_data) < 6:
            return False
        
        # Extract data
        parent_name = row_data[2].strip() if row_data[2] else ""  # Matched Parent
        month_3letter = row_data[4].strip() if row_data[4] else ""  # Month Paying For
        transaction_date = row_data[1].strip() if row_data[1] else ""  # Transaction Date
        amount = row_data[5].strip() if row_data[5] else ""  # Amount
        
        if not all([parent_name, month_3letter]):
            return False
        
        # Convert month
        month_full = self.MONTH_MAPPING.get(month_3letter)
        if not month_full or month_full not in self.column_mapping:
            return False
        
        # Find or create parent row
        parent_row = self._find_or_create_parent_row(parent_name)
        
        # Insert data with yellow highlighting
        month_cols = self.column_mapping[month_full]
        cells_updated = 0
        
        # Insert date with yellow highlighting
        if transaction_date and "date_col" in month_cols:
            date_cell = self.worksheet.cell(row=parent_row, column=month_cols["date_col"], 
                                          value=transaction_date)
            # Apply yellow highlighting
            date_cell.fill = self.highlight_fill
            
            # Track updated cell for statistics
            self.updated_cells.append({
                'row': parent_row,
                'col': month_cols["date_col"],
                'type': 'date',
                'value': transaction_date,
                'parent': parent_name,
                'month': month_full
            })
            cells_updated += 1
        
        # Insert amount with yellow highlighting
        if amount and "amount_col" in month_cols:
            try:
                # Try to convert to float for proper formatting
                amount_float = float(amount.replace(',', '').replace('$', '').replace('RM', ''))
                amount_cell = self.worksheet.cell(row=parent_row, column=month_cols["amount_col"], 
                                                value=amount_float)
            except ValueError:
                # If conversion fails, insert as text
                amount_cell = self.worksheet.cell(row=parent_row, column=month_cols["amount_col"], 
                                                value=amount)
            
            # Apply yellow highlighting
            amount_cell.fill = self.highlight_fill
            
            # Track updated cell for statistics
            self.updated_cells.append({
                'row': parent_row,
                'col': month_cols["amount_col"],
                'type': 'amount',
                'value': amount,
                'parent': parent_name,
                'month': month_full
            })
            cells_updated += 1
        
        return cells_updated > 0
    
    def _find_or_create_parent_row(self, parent_name: str) -> int:
        """Find existing parent row or create new one"""
        # Search existing rows
        for row in range(2, self.worksheet.max_row + 1):
            cell_value = self.worksheet.cell(row=row, column=self.parent_column).value
            if cell_value and str(cell_value).strip().upper() == parent_name.upper():
                return row
        
        # Create new row at the end
        new_row = self.worksheet.max_row + 1
        parent_cell = self.worksheet.cell(row=new_row, column=self.parent_column, value=parent_name)
        
        # Highlight new parent names with light blue
        parent_cell.fill = self.new_parent_fill
        
        return new_row
    
    def get_highlighting_summary(self) -> Dict[str, Any]:
        """Get summary of highlighted cells for user feedback"""
        if not self.updated_cells:
            return {"total_highlighted": 0, "by_type": {}, "by_parent": {}, "by_month": {}}
        
        # Group by type (date vs amount)
        by_type = {"date": 0, "amount": 0}
        by_parent = {}
        by_month = {}
        
        for cell_info in self.updated_cells:
            # Count by type
            cell_type = cell_info['type']
            by_type[cell_type] = by_type.get(cell_type, 0) + 1
            
            # Count by parent
            parent = cell_info['parent']
            by_parent[parent] = by_parent.get(parent, 0) + 1
            
            # Count by month
            month = cell_info['month']
            by_month[month] = by_month.get(month, 0) + 1
        
        return {
            "total_highlighted": len(self.updated_cells),
            "by_type": by_type,
            "by_parent": by_parent,
            "by_month": by_month,
            "details": self.updated_cells
        }
    
    def preview_changes(self, table_data: List[List[str]], 
                       fee_record_file_path: str) -> Dict[str, Any]:
        """Preview what changes will be made without actually modifying the file"""
        try:
            # Temporarily load file for analysis
            temp_workbook = openpyxl.load_workbook(fee_record_file_path, read_only=True)
            temp_worksheet = temp_workbook.active
            
            # Analyze what would happen
            preview_info = {
                "total_rows": len(table_data),
                "new_months": [],
                "affected_parents": set(),
                "data_updates": []
            }
            
            # Check for new months needed
            existing_months = set()
            for col in range(1, temp_worksheet.max_column + 1):
                header = temp_worksheet.cell(row=1, column=col).value
                if header and str(header).upper() in self.MONTH_ORDER:
                    existing_months.add(str(header).upper())
            
            # Find new months required
            for row in table_data:
                if len(row) >= 5 and row[4]:
                    month_3letter = row[4].strip()
                    if month_3letter in self.MONTH_MAPPING:
                        month_full = self.MONTH_MAPPING[month_3letter]
                        if month_full not in existing_months:
                            preview_info["new_months"].append(month_full)
                        
                        if len(row) >= 3 and row[2]:
                            preview_info["affected_parents"].add(row[2].strip())
            
            preview_info["new_months"] = list(set(preview_info["new_months"]))
            preview_info["affected_parents"] = list(preview_info["affected_parents"])
            
            temp_workbook.close()
            return preview_info
            
        except Exception as e:
            return {"error": str(e)}
    
    def validate_table_data(self, table_data: List[List[str]]) -> List[str]:
        """Validate table data before loading"""
        errors = []
        
        if not table_data:
            errors.append("No data to validate")
            return errors
        
        for i, row in enumerate(table_data):
            row_num = i + 1
            
            # Check row length
            if len(row) < 6:
                errors.append(f"Row {row_num}: Missing columns (expected 6)")
                continue
            
            # Check required fields
            if not row[2] or not row[2].strip():  # Matched Parent
                errors.append(f"Row {row_num}: Missing parent name")
            
            if not row[4] or not row[4].strip():  # Month Paying For
                errors.append(f"Row {row_num}: Missing month")
            elif row[4].strip() not in self.MONTH_MAPPING:
                errors.append(f"Row {row_num}: Invalid month '{row[4]}'")
            
            # Validate amount if present
            if row[5] and row[5].strip():
                try:
                    float(row[5].replace(',', '').replace('$', '').replace('RM', ''))
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid amount format '{row[5]}'")
        
        return errors