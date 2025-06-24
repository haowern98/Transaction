"""
Date filtering functionality for transaction table
Provides date picker dialog, confirmation dialog, and filtering logic
"""
import re
from datetime import datetime, date
from typing import List, Tuple, Optional
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QDateEdit, QMessageBox, QGroupBox,
                            QTextEdit, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont


class DateFilterDialog(QDialog):
    """Dialog for selecting cutoff date and previewing filter results"""
    
    filter_requested = pyqtSignal(object)  # Emits selected date
    
    def __init__(self, table_data, parent=None):
        super().__init__(parent)
        self.table_data = table_data
        self.processor = DateFilterProcessor()
        self.preview_data = []
        
        self.setWindowTitle("Filter Transactions by Date")
        self.setModal(True)
        self.resize(500, 400)
        
        self.setup_ui()
        self.connect_signals()
        self.update_preview()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Instructions
        instruction = QLabel("Select a cutoff date. All transactions on or before this date will be deleted.")
        instruction.setWordWrap(True)
        instruction.setFont(QFont("Arial", 9))
        layout.addWidget(instruction)
        
        # Date selection group
        date_group = QGroupBox("Cutoff Date")
        date_layout = QHBoxLayout(date_group)
        
        date_layout.addWidget(QLabel("Delete transactions up to and including:"))
        
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("dd/MM/yyyy")
        
        # Set default date to latest date in table
        latest_date = self.processor.get_latest_date_in_table(self.table_data)
        if latest_date:
            self.date_picker.setDate(QDate.fromString(latest_date, "dd/MM/yyyy"))
        else:
            self.date_picker.setDate(QDate.currentDate())
            
        date_layout.addWidget(self.date_picker)
        layout.addWidget(date_group)
        
        # Preview group
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_label = QLabel("Calculating preview...")
        self.preview_label.setFont(QFont("Arial", 9, QFont.Bold))
        preview_layout.addWidget(self.preview_label)
        
        # Scrollable preview area
        scroll_area = QScrollArea()
        scroll_area.setMaximumHeight(150)
        scroll_area.setWidgetResizable(True)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Courier", 8))
        scroll_area.setWidget(self.preview_text)
        
        preview_layout.addWidget(scroll_area)
        layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.apply_btn = QPushButton("Apply Filter")
        self.apply_btn.setDefault(True)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.apply_btn)
        layout.addLayout(button_layout)
    
    def connect_signals(self):
        """Connect widget signals"""
        self.date_picker.dateChanged.connect(self.update_preview)
        self.cancel_btn.clicked.connect(self.reject)
        self.apply_btn.clicked.connect(self.apply_filter)
    
    def update_preview(self):
        """Update the preview based on selected date"""
        selected_date = self.date_picker.date().toString("dd/MM/yyyy")
        
        # Get rows that would be deleted
        rows_to_delete, preview_info = self.processor.get_rows_to_delete(
            self.table_data, selected_date
        )
        
        self.preview_data = rows_to_delete
        
        # Update preview label
        count = len(rows_to_delete)
        if count == 0:
            self.preview_label.setText("No transactions will be deleted.")
            self.apply_btn.setEnabled(False)
        else:
            self.preview_label.setText(f"{count} transactions will be deleted.")
            self.apply_btn.setEnabled(True)
        
        # Update preview text
        if count > 0:
            preview_text = f"Transactions to be deleted (showing first 20):\n\n"
            
            # Show sample of transactions that will be deleted
            sample_size = min(20, len(rows_to_delete))
            for i in range(sample_size):
                row_data = rows_to_delete[i]
                trans_ref = row_data[0][:50] + "..." if len(row_data[0]) > 50 else row_data[0]
                trans_date = row_data[1] if len(row_data) > 1 else "No date"
                amount = row_data[5] if len(row_data) > 5 else "No amount"
                
                preview_text += f"• {trans_date} - {trans_ref} - {amount}\n"
            
            if len(rows_to_delete) > sample_size:
                preview_text += f"\n... and {len(rows_to_delete) - sample_size} more transactions"
                
            self.preview_text.setText(preview_text)
        else:
            self.preview_text.setText("No transactions match the filter criteria.")
    
    def apply_filter(self):
        """Apply the filter after confirmation"""
        selected_date = self.date_picker.date().toString("dd/MM/yyyy")
        count = len(self.preview_data)
        
        # Show confirmation dialog
        confirmation = ConfirmationDialog(count, selected_date, self)
        
        if confirmation.exec_() == QDialog.Accepted:
            # Emit the filter request
            self.filter_requested.emit(selected_date)
            self.accept()


class ConfirmationDialog(QDialog):
    """Confirmation dialog for date filtering operation"""
    
    def __init__(self, delete_count, cutoff_date, parent=None):
        super().__init__(parent)
        self.delete_count = delete_count
        self.cutoff_date = cutoff_date
        
        self.setWindowTitle("Confirm Delete")
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the confirmation dialog UI"""
        layout = QVBoxLayout(self)
        
        # Warning icon and message
        warning_label = QLabel("⚠️ WARNING")
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setFont(QFont("Arial", 12, QFont.Bold))
        warning_label.setStyleSheet("color: red; margin: 10px;")
        layout.addWidget(warning_label)
        
        # Main message
        message = QLabel(
            f"This will permanently delete {self.delete_count} transactions "
            f"dated on or before {self.cutoff_date}.\n\n"
            f"This action can be undone using the Undo button.\n\n"
            f"Do you want to continue?"
        )
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        message.setFont(QFont("Arial", 10))
        layout.addWidget(message)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.delete_btn = QPushButton(f"Delete {self.delete_count} Transactions")
        self.delete_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; font-weight: bold; }")
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.delete_btn)
        layout.addLayout(button_layout)
        
        # Connect signals
        self.cancel_btn.clicked.connect(self.reject)
        self.delete_btn.clicked.connect(self.accept)
        
        # Set default button
        self.cancel_btn.setDefault(True)


class DateFilterProcessor:
    """Logic for processing date filtering operations"""
    
    def __init__(self):
        self.date_column_index = 1  # Transaction Date is column 1
    
    def parse_date(self, date_string: str) -> Optional[datetime]:
        """
        Parse date string in DD/MM/YYYY format
        
        Args:
            date_string: Date string to parse
            
        Returns:
            datetime object or None if parsing fails
        """
        if not date_string or not isinstance(date_string, str):
            return None
        
        date_string = date_string.strip()
        
        # Handle empty or placeholder values
        if not date_string or date_string.upper() in ['NO DATE', 'INVALID', 'N/A', '']:
            return None
        
        # Try DD/MM/YYYY format
        try:
            return datetime.strptime(date_string, "%d/%m/%Y")
        except ValueError:
            pass
        
        # Try other common formats as fallback
        formats = ["%d/%m/%y", "%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"]
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        return None
    
    def get_latest_date_in_table(self, table_data: List[List[str]]) -> Optional[str]:
        """
        Get the latest (most recent) date in the table
        
        Args:
            table_data: List of table rows
            
        Returns:
            Latest date string in DD/MM/YYYY format or None
        """
        latest_date = None
        
        for row in table_data:
            if len(row) > self.date_column_index:
                date_str = row[self.date_column_index]
                parsed_date = self.parse_date(date_str)
                
                if parsed_date:
                    if latest_date is None or parsed_date > latest_date:
                        latest_date = parsed_date
        
        if latest_date:
            return latest_date.strftime("%d/%m/%Y")
        return None
    
    def get_rows_to_delete(self, table_data: List[List[str]], cutoff_date: str) -> Tuple[List[List[str]], dict]:
        """
        Get rows that would be deleted by the filter
        
        Args:
            table_data: List of table rows
            cutoff_date: Cutoff date in DD/MM/YYYY format
            
        Returns:
            Tuple of (rows_to_delete, preview_info)
        """
        cutoff_datetime = self.parse_date(cutoff_date)
        if not cutoff_datetime:
            return [], {"error": "Invalid cutoff date"}
        
        rows_to_delete = []
        invalid_dates = 0
        
        for row in table_data:
            if len(row) <= self.date_column_index:
                continue
                
            date_str = row[self.date_column_index]
            parsed_date = self.parse_date(date_str)
            
            if parsed_date is None:
                invalid_dates += 1
                continue
            
            # Delete if date is on or before cutoff date
            if parsed_date <= cutoff_datetime:
                rows_to_delete.append(row)
        
        preview_info = {
            "total_rows": len(table_data),
            "rows_to_delete": len(rows_to_delete),
            "invalid_dates": invalid_dates,
            "cutoff_date": cutoff_date
        }
        
        return rows_to_delete, preview_info
    
    def get_row_indices_to_delete(self, table_data: List[List[str]], cutoff_date: str) -> List[int]:
        """
        Get indices of rows that should be deleted
        
        Args:
            table_data: List of table rows
            cutoff_date: Cutoff date in DD/MM/YYYY format
            
        Returns:
            List of row indices to delete
        """
        cutoff_datetime = self.parse_date(cutoff_date)
        if not cutoff_datetime:
            return []
        
        indices_to_delete = []
        
        for i, row in enumerate(table_data):
            if len(row) <= self.date_column_index:
                continue
                
            date_str = row[self.date_column_index]
            parsed_date = self.parse_date(date_str)
            
            if parsed_date and parsed_date <= cutoff_datetime:
                indices_to_delete.append(i)
        
        return indices_to_delete
    
    def validate_date_format(self, date_string: str) -> bool:
        """
        Validate if date string can be parsed
        
        Args:
            date_string: Date string to validate
            
        Returns:
            True if valid, False otherwise
        """
        return self.parse_date(date_string) is not None