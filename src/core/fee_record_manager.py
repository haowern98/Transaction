"""
Enhanced Fee Record Manager - Core Excel operations with conflict handling
Fixed all syntax errors and indentation issues
File: src/core/fee_record_manager.py
"""
import pandas as pd
import openpyxl
from openpyxl.utils import column_index_from_string, get_column_letter
from openpyxl.styles import PatternFill, Font, Border, Side, Alignment
from typing import List, Dict, Tuple, Optional, Any, Set
from datetime import datetime
import os
import shutil


class FeeRecordManager:
    """Enhanced manager for loading preview table data into Fee Record Excel file with conflict handling"""
    
    # Month name mapping from preview table to fee record headers
    MONTH_MAPPING = {
        "Jan": "JANUARY", "Feb": "FEBRUARY", "Mar": "MARCH",
        "Apr": "APRIL", "May": "MAY", "Jun": "JUNE", 
        "Jul": "JULY", "Aug": "AUGUST", "Sep": "SEPTEMBER",
        "Oct": "OCTOBER", "Nov": "NOVEMBER", "Dec": "DECEMBER"
    }
    
    # Chronological month order for proper insertion
    MONTH_ORDER = {
        "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4,
        "MAY": 5, "JUNE": 6, "JULY": 7, "AUGUST": 8,
        "SEPTEMBER": 9, "OCTOBER": 10, "NOVEMBER": 11, "DECEMBER": 12
    }
    
    def __init__(self):
        self.workbook = None
        self.worksheet = None
        self.fee_record_path = ""
        self.column_mapping = {}
        self.parent_column = 1
        
        # Cell styling for highlighting
        self.highlight_fill = PatternFill(
            start_color="FFFF00", end_color="FFFF00", fill_type="solid"
        )
        self.conflict_fill = PatternFill(
            start_color="FF6B6B", end_color="FF6B6B", fill_type="solid"
        )
        self.new_parent_fill = PatternFill(
            start_color="E6F3FF", end_color="E6F3FF", fill_type="solid"
        )
        
        # Track updated cells
        self.updated_cells = []
        self.conflict_cells = []
        
    def load_table_data_to_fee_record(self, table_data: List[List[str]], 
                                     fee_record_file_path: str) -> Dict[str, Any]:
        """Main method to load preview table data into fee record file with conflict handling"""
        try:
            if not table_data:
                return {"success": False, "error": "No data to load"}
                
            if not os.path.exists(fee_record_file_path):
                return {"success": False, "error": f"Fee record file not found: {fee_record_file_path}"}
            
            if self._is_file_locked(fee_record_file_path):
                return {
                    "success": False, 
                    "error": "File is currently in use or locked. Please close Excel and try again."
                }
            
            backup_path = self._create_backup(fee_record_file_path)
            
            try:
                self.fee_record_path = fee_record_file_path
                self.workbook = openpyxl.load_workbook(fee_record_file_path)
                self.worksheet = self.workbook.active
            except PermissionError as e:
                return {
                    "success": False,
                    "error": f"Permission denied. Please close Excel and try again. Error: {str(e)}"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to open Excel file. Error: {str(e)}"
                }
            
            self._analyze_fee_record_structure()
            stats = self._process_table_data_with_conflicts(table_data)
            
            try:
                self.workbook.save(fee_record_file_path)
            except PermissionError as e:
                return {
                    "success": False,
                    "error": f"Permission denied saving file. Please close Excel. Error: {str(e)}"
                }
            
            return {
                "success": True,
                "backup_path": backup_path,
                "stats": stats,
                "highlighting": self.get_highlighting_summary(),
                "conflicts": self.get_conflict_summary()
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
        """Check if file is locked or in use by another process"""
        try:
            with open(file_path, 'a'):
                pass
            return False
        except IOError:
            return True
        except Exception:
            return True
    
    def _analyze_fee_record_structure(self):
        """Dynamically analyze fee record file structure and build column mapping"""
        if not self.worksheet:
            raise Exception("Worksheet not loaded")
        
        self.column_mapping = {}
        merged_ranges = list(self.worksheet.merged_cells.ranges)
        
        for merged_range in merged_ranges:
            if merged_range.min_row <= 1 <= merged_range.max_row:
                header_cell = self.worksheet.cell(row=1, column=merged_range.min_col)
                header_value = header_cell.value
                
                if header_value:
                    header_text = str(header_value).strip().upper()
                    
                    if header_text in self.MONTH_ORDER:
                        start_col = merged_range.min_col
                        end_col = merged_range.max_col
                        
                        if end_col - start_col + 1 == 2:
                            self.column_mapping[header_text] = {
                                "merged_range": (start_col, end_col),
                                "date_col": start_col,
                                "amount_col": start_col + 1
                            }
        
        self._detect_non_merged_months()
    
    def _detect_non_merged_months(self):
        """Detect non-merged month headers as fallback"""
        for col in range(1, self.worksheet.max_column + 1):
            header_cell = self.worksheet.cell(row=1, column=col)
            if header_cell.value:
                header_text = str(header_cell.value).strip().upper()
                
                if header_text in self.MONTH_ORDER and header_text not in self.column_mapping:
                    if col + 1 <= self.worksheet.max_column:
                        self.column_mapping[header_text] = {
                            "merged_range": (col, col + 1),
                            "date_col": col,
                            "amount_col": col + 1
                        }
    
    def _process_table_data_with_conflicts(self, table_data: List[List[str]]) -> Dict[str, int]:
        """Process all table data with enhanced conflict handling and statistics"""
        stats = {
            "processed_rows": 0,
            "new_entries": 0,
            "appended_entries": 0,
            "conflicts_resolved": 0,
            "new_parents": 0,
            "new_months_created": 0,
            "highlighted_cells": 0,
            "conflict_cells": 0,
            "errors": 0
        }
        
        self.updated_cells = []
        self.conflict_cells = []
        
        # Create missing months
        required_months = set()
        for row in table_data:
            if len(row) >= 5 and row[4]:
                month_3letter = row[4].strip()
                if month_3letter in self.MONTH_MAPPING:
                    required_months.add(self.MONTH_MAPPING[month_3letter])
        
        for month in required_months:
            if month not in self.column_mapping:
                self._create_month_column(month)
                stats["new_months_created"] += 1
                self._analyze_fee_record_structure()
        
        # Process each row
        for row_data in table_data:
            try:
                result = self._process_single_row_with_conflicts(row_data)
                if result["updated"]:
                    stats["new_entries"] += result.get("new_entries", 0)
                    stats["appended_entries"] += result.get("appended_entries", 0)
                    stats["conflicts_resolved"] += result.get("conflicts", 0)
                stats["processed_rows"] += 1
            except Exception as e:
                print(f"Error processing row {row_data}: {e}")
                stats["errors"] += 1
        
        stats["highlighted_cells"] = len(self.updated_cells)
        stats["conflict_cells"] = len(self.conflict_cells)
        
        return stats
    
    def _is_cell_empty(self, cell) -> bool:
        """Check if a cell is empty or contains only whitespace"""
        if cell.value is None:
            return True
        cell_text = str(cell.value).strip()
        return len(cell_text) == 0
    
    def _append_to_cell_simple(self, cell, new_value: str) -> bool:
        """Append new value to existing cell content with simple concatenation"""
        if self._is_cell_empty(cell):
            cell.value = new_value
            return False
        
        existing_value = str(cell.value).strip()
        combined_value = f"{existing_value}; {new_value}"
        cell.value = combined_value
        return True
    
    def _process_single_row_with_conflicts(self, row_data: List[str]) -> Dict[str, Any]:
        """Process a single row with enhanced conflict detection and handling"""
        result = {
            "updated": False,
            "new_entries": 0,
            "appended_entries": 0,
            "conflicts": 0
        }
        
        if len(row_data) < 6:
            return result
        
        parent_name = row_data[2].strip() if row_data[2] else ""
        month_3letter = row_data[4].strip() if row_data[4] else ""
        transaction_date = row_data[1].strip() if row_data[1] else ""
        amount = row_data[5].strip() if row_data[5] else ""
        
        if not all([parent_name, month_3letter]):
            return result
        
        month_full = self.MONTH_MAPPING.get(month_3letter)
        if not month_full or month_full not in self.column_mapping:
            return result
        
        parent_row = self._find_or_create_parent_row(parent_name)
        target_row = self._find_next_available_row_in_month(month_full, parent_row)
        month_cols = self.column_mapping[month_full]
        
        # Process date cell
        if transaction_date and "date_col" in month_cols:
            date_cell = self.worksheet.cell(row=target_row, column=month_cols["date_col"])
            had_conflict = self._append_to_cell_simple(date_cell, transaction_date)
            
            if had_conflict:
                date_cell.fill = self.conflict_fill
                result["appended_entries"] += 1
                result["conflicts"] += 1
                self.conflict_cells.append({
                    'row': target_row, 'col': month_cols["date_col"],
                    'type': 'date_conflict', 'value': transaction_date,
                    'parent': parent_name, 'month': month_full
                })
            else:
                date_cell.fill = self.highlight_fill
                result["new_entries"] += 1
                self.updated_cells.append({
                    'row': target_row, 'col': month_cols["date_col"],
                    'type': 'date', 'value': transaction_date,
                    'parent': parent_name, 'month': month_full
                })
        
        # Process amount cell
        if amount and "amount_col" in month_cols:
            amount_cell = self.worksheet.cell(row=target_row, column=month_cols["amount_col"])
            
            try:
                amount_float = float(amount.replace(',', '').replace('$', '').replace('RM', ''))
                formatted_amount = f"{amount_float:.2f}"
            except ValueError:
                formatted_amount = amount
            
            had_conflict = self._append_to_cell_simple(amount_cell, formatted_amount)
            
            if had_conflict:
                amount_cell.fill = self.conflict_fill
                result["appended_entries"] += 1
                result["conflicts"] += 1
                self.conflict_cells.append({
                    'row': target_row, 'col': month_cols["amount_col"],
                    'type': 'amount_conflict', 'value': formatted_amount,
                    'parent': parent_name, 'month': month_full
                })
            else:
                amount_cell.fill = self.highlight_fill
                result["new_entries"] += 1
                self.updated_cells.append({
                    'row': target_row, 'col': month_cols["amount_col"],
                    'type': 'amount', 'value': formatted_amount,
                    'parent': parent_name, 'month': month_full
                })
        
        result["updated"] = True
        return result
    
    def _create_month_column(self, month_name: str):
        """Create new month column with merged header spanning 2 columns"""
        insertion_col = self._find_month_insertion_point(month_name)
        self.worksheet.insert_cols(insertion_col, 2)
        
        month_header_cell = self.worksheet.cell(row=1, column=insertion_col, value=month_name)
        month_header_cell.font = Font(bold=True)
        
        self.worksheet.merge_cells(
            start_row=1, start_column=insertion_col,
            end_row=1, end_column=insertion_col + 1
        )
        
        month_header_cell.alignment = Alignment(horizontal='center', vertical='center')
        
        self.column_mapping[month_name] = {
            "merged_range": (insertion_col, insertion_col + 1),
            "date_col": insertion_col,
            "amount_col": insertion_col + 1
        }
        
        self._shift_column_mappings_after_insertion(insertion_col, 2)
    
    def _find_month_insertion_point(self, month_name: str) -> int:
        """Find where to insert new month column based on reverse chronological order"""
        target_order = self.MONTH_ORDER.get(month_name, 0)
        
        if not self.column_mapping:
            return self.parent_column + 1
        
        insertion_point = None
        leftmost_col = float('inf')
        
        for existing_month, mapping in self.column_mapping.items():
            existing_order = self.MONTH_ORDER.get(existing_month, 0)
            
            if target_order > existing_order:
                if mapping["date_col"] < leftmost_col:
                    leftmost_col = mapping["date_col"]
                    insertion_point = mapping["date_col"]
        
        if insertion_point is None:
            leftmost_col = float('inf')
            for mapping in self.column_mapping.values():
                leftmost_col = min(leftmost_col, mapping["date_col"])
            
            insertion_point = leftmost_col if leftmost_col != float('inf') else self.parent_column + 1
        
        return insertion_point
    
    def _shift_column_mappings_after_insertion(self, insertion_col: int, cols_inserted: int):
        """Update existing column mappings after inserting new columns"""
        for month, mapping in self.column_mapping.items():
            if mapping["date_col"] >= insertion_col:
                old_start, old_end = mapping["merged_range"]
                mapping["merged_range"] = (old_start + cols_inserted, old_end + cols_inserted)
                mapping["date_col"] += cols_inserted
                mapping["amount_col"] += cols_inserted
    
    def _find_or_create_parent_row(self, parent_name: str) -> int:
        """Find existing parent row or create new one"""
        for row in range(2, self.worksheet.max_row + 1):
            cell_value = self.worksheet.cell(row=row, column=self.parent_column).value
            if cell_value and str(cell_value).strip().upper() == parent_name.upper():
                return row
        
        new_row = self.worksheet.max_row + 1
        parent_cell = self.worksheet.cell(row=new_row, column=self.parent_column, value=parent_name)
        parent_cell.fill = self.new_parent_fill
        return new_row
    
    def _find_next_available_row_in_month(self, month_name: str, preferred_row: int) -> int:
        """Always use the parent's exact row - no searching for empty rows"""
        return preferred_row
    
    def get_conflict_summary(self) -> Dict[str, Any]:
        """Get summary of conflicts for user feedback"""
        if not self.conflict_cells:
            return {"total_conflicts": 0, "by_type": {}, "by_parent": {}, "by_month": {}}
        
        by_type = {"date_conflict": 0, "amount_conflict": 0}
        by_parent = {}
        by_month = {}
        
        for conflict_info in self.conflict_cells:
            conflict_type = conflict_info['type']
            by_type[conflict_type] = by_type.get(conflict_type, 0) + 1
            
            parent = conflict_info['parent']
            by_parent[parent] = by_parent.get(parent, 0) + 1
            
            month = conflict_info['month']
            by_month[month] = by_month.get(month, 0) + 1
        
        return {
            "total_conflicts": len(self.conflict_cells),
            "by_type": by_type,
            "by_parent": by_parent,
            "by_month": by_month,
            "details": self.conflict_cells
        }
    
    def get_highlighting_summary(self) -> Dict[str, Any]:
        """Get summary of highlighted cells for user feedback"""
        if not self.updated_cells:
            return {"total_highlighted": 0, "by_type": {}, "by_parent": {}, "by_month": {}}
        
        by_type = {"date": 0, "amount": 0}
        by_parent = {}
        by_month = {}
        
        for cell_info in self.updated_cells:
            cell_type = cell_info['type']
            by_type[cell_type] = by_type.get(cell_type, 0) + 1
            
            parent = cell_info['parent']
            by_parent[parent] = by_parent.get(parent, 0) + 1
            
            month = cell_info['month']
            by_month[month] = by_month.get(month, 0) + 1
        
        return {
            "total_highlighted": len(self.updated_cells),
            "by_type": by_type,
            "by_parent": by_parent,
            "by_month": by_month,
            "details": self.updated_cells
        }
    
    def preview_changes(self, table_data: List[List[str]], fee_record_file_path: str) -> Dict[str, Any]:
        """Preview what changes will be made without actually modifying the file"""
        try:
            temp_workbook = openpyxl.load_workbook(fee_record_file_path)
            temp_worksheet = temp_workbook.active
            
            preview_info = {
                "total_rows": len(table_data),
                "new_months": [],
                "affected_parents": set(),
                "potential_conflicts": 0
            }
            
            existing_months = set()
            
            if hasattr(temp_worksheet, 'merged_cells'):
                merged_ranges = list(temp_worksheet.merged_cells.ranges)
                
                for merged_range in merged_ranges:
                    if merged_range.min_row <= 1 <= merged_range.max_row:
                        header_cell = temp_worksheet.cell(row=1, column=merged_range.min_col)
                        if header_cell.value:
                            header_text = str(header_cell.value).strip().upper()
                            if header_text in self.MONTH_ORDER:
                                existing_months.add(header_text)
            
            for col in range(1, temp_worksheet.max_column + 1):
                header_cell = temp_worksheet.cell(row=1, column=col)
                if header_cell.value:
                    header_text = str(header_cell.value).strip().upper()
                    if header_text in self.MONTH_ORDER:
                        existing_months.add(header_text)
            
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
            
            if len(row) < 6:
                errors.append(f"Row {row_num}: Missing columns (expected 6)")
                continue
            
            if not row[2] or not row[2].strip():
                errors.append(f"Row {row_num}: Missing parent name")
            
            if not row[4] or not row[4].strip():
                errors.append(f"Row {row_num}: Missing month")
            elif row[4].strip() not in self.MONTH_MAPPING:
                errors.append(f"Row {row_num}: Invalid month {row[4]}")
            
            if row[5] and row[5].strip():
                try:
                    float(row[5].replace(',', '').replace('$', '').replace('RM', ''))
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid amount format {row[5]}")
        
        return errors