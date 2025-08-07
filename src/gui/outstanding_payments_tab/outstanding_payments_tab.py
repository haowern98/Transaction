# File: src/gui/outstanding_payments_tab/outstanding_payments_tab.py
"""
Outstanding Payments Tab - Updated with Month Filter and Zoom-Responsive Dropdown
Shows parents, their students, and outstanding months with month selection filter
FIXED: Dropdown menu now scales properly with zoom
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                            QTableWidget, QTableWidgetItem, QPushButton, QLabel, 
                            QHeaderView, QMessageBox, QSizePolicy, QFrame, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from typing import Dict, Any, List
import os

from .payment_analyzer import PaymentAnalyzer
from .payment_export import PaymentExporter


class AnalysisThread(QThread):
    """Background thread for analyzing outstanding payments across all months"""
    
    finished = pyqtSignal(dict)  # analysis_results
    error = pyqtSignal(str)      # error_message
    
    def __init__(self, fee_record_path: str):
        super().__init__()
        self.fee_record_path = fee_record_path
        
    def run(self):
        """Run payment analysis for all months"""
        try:
            analyzer = PaymentAnalyzer()
            
            if not analyzer.load_fee_record(self.fee_record_path):
                self.error.emit("Failed to load fee record file")
                return
            
            # Get all available months
            available_months = analyzer.get_available_months()
            
            if not available_months:
                self.error.emit("No months found in fee record")
                return
            
            # Get all parents first to map parent->student relationships
            all_parents = analyzer.get_all_parents()
            parent_student_map = {}
            for parent_info in all_parents:
                parent_name = parent_info["parent_name"]
                student_name = parent_info["student_name"]
                parent_student_map[parent_name] = student_name
            
            # Analyze each month to find outstanding payments
            all_outstanding = {}  # {parent_name: [list_of_outstanding_months]}
            
            for month in available_months:
                results = analyzer.analyze_month_payments(
                    month, 
                    include_zero_amounts=False,
                    empty_cells_unpaid=True
                )
                
                if 'error' not in results:
                    unpaid_parents = results.get('unpaid_parents', [])
                    month_display = results.get('month_display', month)
                    
                    for parent_data in unpaid_parents:
                        parent_name = parent_data.get('parent_name', '')
                        date_value = parent_data.get('date_value', '')
                        amount_value = parent_data.get('amount_value')
                        
                        # FIXED LOGIC: Only include if BOTH date AND amount are empty
                        date_is_empty = not date_value or date_value.strip() == ''
                        amount_is_empty = amount_value is None
                        
                        # Only add to outstanding if BOTH cells are completely empty
                        if parent_name and date_is_empty and amount_is_empty:
                            if parent_name not in all_outstanding:
                                all_outstanding[parent_name] = []
                            all_outstanding[parent_name].append(month_display)
            
            # Format results with student names
            outstanding_list = []
            for parent_name, months in all_outstanding.items():
                student_name = parent_student_map.get(parent_name, "")
                outstanding_list.append({
                    'parent_name': parent_name,
                    'student_name': student_name,
                    'outstanding_months': months,
                    'outstanding_months_str': ', '.join(sorted(months))
                })
            
            # Sort by parent name
            outstanding_list.sort(key=lambda x: x['parent_name'])
            
            results = {
                'outstanding_parents': outstanding_list,
                'total_parents_with_outstanding': len(outstanding_list),
                'total_months_checked': len(available_months),
                'available_months': available_months,
                'parent_student_map': parent_student_map
            }
            
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))
        finally:
            if 'analyzer' in locals():
                analyzer.close()


class OutstandingPaymentsTab(QWidget):
    """
    Outstanding Payments Tab with Month Filter
    Shows title, description, month filter, and results table
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize components
        self.payment_exporter = PaymentExporter(self)
        self.analysis_thread = None
        self.current_results = {}
        self.all_results = {}  # Store complete unfiltered results
        
        # Month filter state
        self.available_months = []
        self.selected_months = set()  # Empty set means all selected
        self.filter_popup = None
        
        # Get settings manager for fee record path
        try:
            from gui.settings import get_settings_manager
            self.settings_manager = get_settings_manager()
        except ImportError:
            self.settings_manager = None
        
        self.setup_ui()
        self.auto_generate_if_ready()
        
    def setup_ui(self):
        """Setup UI with title, month filter, three-column table with refresh button, and export button"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)  # Same as general settings
        main_layout.setSpacing(0)
        
        # Header section - same style as General Settings
        header_section = self._create_header_section()
        main_layout.addWidget(header_section)
        
        # Add spacing after header
        main_layout.addSpacing(40)
        
        # Results section (takes most space)
        results_section = self._create_results_section()
        main_layout.addWidget(results_section)
        main_layout.setStretchFactor(results_section, 1)
        
        # Export button at bottom center
        export_section = self._create_export_section()
        main_layout.addWidget(export_section)
        
    def _create_header_section(self):
        """Create header with title and description - same style as General Settings"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(11)
        
        # Main title - SAME FONT as General Settings
        title_label = QLabel("Outstanding Payments")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))  # Changed from Tahoma to Arial
        title_label.setStyleSheet("color: #1f1f1f;")
        header_layout.addWidget(title_label)
        
        # Subtitle - SAME FONT as General Settings
        subtitle_label = QLabel("View parents and students who have not made payments for specific months")
        subtitle_label.setFont(QFont("Arial", 8, QFont.Normal))  # Changed from Tahoma to Arial
        subtitle_label.setStyleSheet("color: #1f1f1f;")
        header_layout.addWidget(subtitle_label)
        
        return header_widget
        
    def _create_results_section(self):
        """Create main results table with month filter and refresh button"""
        results_group = QGroupBox("Outstanding Payments Results")
        results_layout = QVBoxLayout(results_group)
        
        # Filter row (top)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Show months:"))
        
        # Create button that looks like combobox but opens custom popup
        self.month_filter_btn = QPushButton("All Months")
        self.month_filter_btn.clicked.connect(self.show_month_filter)
        self.month_filter_btn.setMinimumWidth(120)
        self.month_filter_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 4px 8px;
                border: 1px solid #cccccc;
                background-color: white;
            }
            QPushButton:hover {
                border-color: #0078d4;
            }
            QPushButton::menu-indicator {
                image: none;
                width: 0px;
            }
        """)
        
        # Add dropdown arrow manually
        self.month_filter_btn.setText("All Months ▼")
        
        filter_layout.addWidget(self.month_filter_btn)
        filter_layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh List")
        self.refresh_btn.clicked.connect(self.generate_outstanding_list)
        self.refresh_btn.setToolTip("Refresh the outstanding payments list")
        filter_layout.addWidget(self.refresh_btn)
        
        results_layout.addLayout(filter_layout)
        
        # Status row (below filter)
        self.status_label = QLabel("Checking for outstanding payments...")
        results_layout.addWidget(self.status_label)
        
        # Results table
        self.results_table = QTableWidget()
        self.setup_results_table()
        results_layout.addWidget(self.results_table)
        
        return results_group
        
    def _create_export_section(self):
        """Create single export button centered at bottom"""
        export_widget = QWidget()
        export_layout = QHBoxLayout(export_widget)
        export_layout.setContentsMargins(0, 20, 0, 0)  # Top margin for spacing
        
        # Center the button
        export_layout.addStretch()
        
        # Single export button - DEFAULT STYLING (matches existing project buttons)
        self.export_csv_btn = QPushButton("Export to CSV")
        self.export_csv_btn.clicked.connect(self.export_to_csv)
        self.export_csv_btn.setEnabled(False)
        export_layout.addWidget(self.export_csv_btn)
        
        export_layout.addStretch()
        
        return export_widget
    
    def show_month_filter(self):
        """Show month filter popup with checkboxes"""
        if not self.available_months:
            return
            
        # Create popup if it doesn't exist
        if self.filter_popup is None:
            from PyQt5.QtWidgets import QFrame
            self.filter_popup = QFrame(self)
            self.filter_popup.setFrameStyle(QFrame.StyledPanel)
            self.filter_popup.setWindowFlags(Qt.Popup)
            self.filter_popup.setStyleSheet("""
                QFrame { 
                    background-color: white; 
                    border: 1px solid #cccccc;
                    border-radius: 2px;
                }
                QCheckBox {
                    padding: 3px 8px;
                    spacing: 6px;
                }
                QCheckBox:hover {
                    background-color: #f0f8ff;
                }
                QCheckBox::indicator {
                    width: 13px;
                    height: 13px;
                }
                QCheckBox::indicator:unchecked {
                    border: 1px solid #cccccc;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    border: 1px solid #0078d4;
                    background-color: #0078d4;
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMCAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTggMyBMNCw3IEwyLDUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
                }
            """)
            
            popup_layout = QVBoxLayout(self.filter_popup)
            popup_layout.setContentsMargins(0, 4, 0, 4)
            popup_layout.setSpacing(0)
            
            # All Months checkbox
            self.all_months_cb = QCheckBox("All Months")
            self.all_months_cb.setFont(QFont("Arial", 0, QFont.Bold))
            self.all_months_cb.stateChanged.connect(self.on_all_months_changed)
            popup_layout.addWidget(self.all_months_cb)
            
            # Individual month checkboxes
            self.month_checkboxes = {}
            for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']:
                cb = QCheckBox(month)
                cb.stateChanged.connect(self.on_month_selection_changed)
                self.month_checkboxes[month] = cb
                popup_layout.addWidget(cb)
            
            # Set fixed width to match button
            self.filter_popup.setFixedWidth(150)
            
            # ZOOM FIX: Register popup widgets with zoom system
            try:
                from gui.settings.zoom.zoom_system import get_zoom_system
                zoom_system = get_zoom_system()
                if zoom_system:
                    zoom_system.register_widget(self.filter_popup)
                    zoom_system.register_widget(self.all_months_cb)
                    for cb in self.month_checkboxes.values():
                        zoom_system.register_widget(cb)
                    # FIX: Scale popup width with zoom
                    current_zoom = zoom_system.get_current_zoom()
                    scaled_width = int(150 * current_zoom / 100)
                    self.filter_popup.setFixedWidth(scaled_width)
            except:
                pass
        
        # Update checkbox states and visibility
        self.update_filter_checkboxes()
        
        # ZOOM-AWARE positioning
        button_global_pos = self.month_filter_btn.mapToGlobal(self.month_filter_btn.rect().bottomLeft())
        try:
            from gui.settings.zoom.zoom_system import get_zoom_system
            zoom_system = get_zoom_system()
            zoom_factor = zoom_system.get_current_zoom() / 100 if zoom_system else 1.0
            offset = int(2 * zoom_factor)
        except:
            offset = 2
        self.filter_popup.move(button_global_pos.x(), button_global_pos.y() + offset)
        self.filter_popup.show()
    
    def update_filter_checkboxes(self):
        """Update checkbox states based on current selection"""
        if not self.available_months:
            return
            
        # Show only available months and update their states
        for month, checkbox in self.month_checkboxes.items():
            if month in self.available_months:
                checkbox.setVisible(True)
                checkbox.setChecked(len(self.selected_months) == 0 or month in self.selected_months)
            else:
                checkbox.setVisible(False)
        
        # Update "All Months" checkbox
        available_month_set = set(self.available_months)
        if len(self.selected_months) == 0 or self.selected_months == available_month_set:
            self.all_months_cb.setChecked(True)
        else:
            self.all_months_cb.setChecked(False)
    
    def on_all_months_changed(self, state):
        """Handle All Months checkbox change"""
        if state == Qt.Checked:
            self.selected_months = set()  # Empty means all selected
        else:
            self.selected_months = set()  # Will be filled by individual checkboxes
        
        # Update individual checkboxes
        for month, checkbox in self.month_checkboxes.items():
            if month in self.available_months:
                checkbox.blockSignals(True)
                checkbox.setChecked(state == Qt.Checked)
                checkbox.blockSignals(False)
        
        self.update_filter_display()
        self.apply_month_filter()
    
    def on_month_selection_changed(self):
        """Handle individual month checkbox changes"""
        # Collect selected months
        newly_selected = set()
        for month, checkbox in self.month_checkboxes.items():
            if month in self.available_months and checkbox.isChecked():
                newly_selected.add(month)
        
        self.selected_months = newly_selected
        
        # Update "All Months" checkbox
        available_month_set = set(self.available_months)
        self.all_months_cb.blockSignals(True)
        if len(self.selected_months) == 0 or self.selected_months == available_month_set:
            self.all_months_cb.setChecked(True)
            self.selected_months = set()  # Empty means all selected
        else:
            self.all_months_cb.setChecked(False)
        self.all_months_cb.blockSignals(False)
        
        self.update_filter_display()
        self.apply_month_filter()
    
    def update_filter_display(self):
        """Update the filter button text based on selection"""
        if len(self.selected_months) == 0:  # All selected
            self.month_filter_btn.setText("All Months ▼")
        elif len(self.selected_months) <= 3:
            months_text = ", ".join(sorted(self.selected_months))
            self.month_filter_btn.setText(f"{months_text} ▼")
        else:
            first_three = sorted(list(self.selected_months))[:3]
            remaining = len(self.selected_months) - 3
            months_text = f"{', '.join(first_three)}, +{remaining} more"
            self.month_filter_btn.setText(f"{months_text} ▼")
    
    def apply_month_filter(self):
        """Apply month filter to current results"""
        if not self.all_results:
            return
            
        # Determine which months to include
        months_to_include = set(self.available_months) if len(self.selected_months) == 0 else self.selected_months
        
        # Filter results
        filtered_outstanding = []
        for parent_data in self.all_results.get('outstanding_parents', []):
            parent_outstanding_months = set(parent_data['outstanding_months'])
            
            # Check if this parent has outstanding payments in selected months
            overlapping_months = parent_outstanding_months.intersection(months_to_include)
            
            if overlapping_months:
                # Create filtered version showing only selected months
                filtered_data = parent_data.copy()
                filtered_data['outstanding_months'] = sorted(list(overlapping_months))
                filtered_data['outstanding_months_str'] = ', '.join(sorted(overlapping_months))
                filtered_outstanding.append(filtered_data)
        
        # Update current results
        self.current_results = {
            'outstanding_parents': filtered_outstanding,
            'total_parents_with_outstanding': len(filtered_outstanding),
            'total_months_checked': len(months_to_include)
        }
        
        # Update display
        self.populate_results_table(self.current_results)
        self.update_status_after_filter()
    
    def update_status_after_filter(self):
        """Update status label after applying filter"""
        total_parents = self.current_results.get('total_parents_with_outstanding', 0)
        selected_months_count = len(self.selected_months) if len(self.selected_months) > 0 else len(self.available_months)
        
        if total_parents > 0:
            if len(self.selected_months) == 0:
                self.status_label.setText(
                    f"Found {total_parents} parents with outstanding payments across {selected_months_count} months"
                )
            else:
                self.status_label.setText(
                    f"Found {total_parents} parents with outstanding payments across {selected_months_count} selected months"
                )
            self.export_csv_btn.setEnabled(True)
        else:
            if len(self.selected_months) == 0:
                self.status_label.setText(f"All parents have paid for all {selected_months_count} months - no outstanding payments!")
            else:
                self.status_label.setText(f"All parents have paid for selected months - no outstanding payments!")
            self.export_csv_btn.setEnabled(False)
        
    def setup_results_table(self):
        """Setup the three-column results table: Parent | Student | Outstanding Months"""
        # Set columns: Parent Name | Student Name | Outstanding Months
        headers = ["Parent Name", "Student Name", "Outstanding Months"]
        self.results_table.setColumnCount(len(headers))
        self.results_table.setHorizontalHeaderLabels(headers)
        
        # Configure table properties
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setSortingEnabled(False)  # Disable sorting arrows
        
        # Set column widths
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # Parent Name
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # Student Name
        header.setSectionResizeMode(2, QHeaderView.Stretch)     # Outstanding Months
        
        self.results_table.setColumnWidth(0, 300)  # Parent Name width
        self.results_table.setColumnWidth(1, 250)  # Student Name width
        
    def auto_generate_if_ready(self):
        """Automatically generate outstanding list if fee record is available"""
        fee_record_path = self.get_fee_record_file_path()
        
        if fee_record_path and os.path.exists(fee_record_path):
            self.generate_outstanding_list()
        else:
            if not fee_record_path:
                self.status_label.setText("No fee record file configured. Please set up in Settings → File Paths")
            else:
                self.status_label.setText(f"Fee record file not found: {fee_record_path}")
    
    def load_fee_record_path(self):
        """Load fee record path from settings and refresh"""
        self.auto_generate_if_ready()
    
    def get_fee_record_file_path(self) -> str:
        """Get fee record file path from settings"""
        try:
            if self.settings_manager:
                return self.settings_manager.get_setting('files.fee_record_file', '')
            return ""
        except Exception:
            return ""
    
    def generate_outstanding_list(self):
        """Generate outstanding payments list for all months"""
        fee_record_path = self.get_fee_record_file_path()
        
        if not fee_record_path or not os.path.exists(fee_record_path):
            self.status_label.setText("Fee record file not found. Please check Settings → File Paths.")
            return
        
        # Disable refresh button during analysis
        self.refresh_btn.setEnabled(False)
        
        # Update status
        self.status_label.setText("Analyzing outstanding payments across all months...")
        self.export_csv_btn.setEnabled(False)
        
        # Start analysis thread
        self.analysis_thread = AnalysisThread(fee_record_path)
        self.analysis_thread.finished.connect(self.analysis_finished)
        self.analysis_thread.error.connect(self.analysis_error)
        self.analysis_thread.start()
    
    def analysis_finished(self, results: Dict[str, Any]):
        """Handle completed analysis"""
        self.all_results = results  # Store complete results
        
        # Setup available months and default selection
        self.available_months = [results.get('parent_student_map', {}).get(month, month) 
                               for month in results.get('available_months', [])]
        # Convert full month names to short names for display
        month_name_map = {
            'JANUARY': 'Jan', 'FEBRUARY': 'Feb', 'MARCH': 'Mar', 'APRIL': 'Apr',
            'MAY': 'May', 'JUNE': 'Jun', 'JULY': 'Jul', 'AUGUST': 'Aug', 
            'SEPTEMBER': 'Sep', 'OCTOBER': 'Oct', 'NOVEMBER': 'Nov', 'DECEMBER': 'Dec'
        }
        self.available_months = [month_name_map.get(month, month) for month in results.get('available_months', [])]
        
        self.selected_months = set()  # Default to all selected
        
        # Re-enable refresh button
        self.refresh_btn.setEnabled(True)
        
        # Apply initial filter (shows all)
        self.update_filter_display()
        self.apply_month_filter()
    
    def analysis_error(self, error_message: str):
        """Handle analysis errors"""
        # Re-enable refresh button
        self.refresh_btn.setEnabled(True)
        
        self.status_label.setText(f"Analysis failed: {error_message}")
        self.export_csv_btn.setEnabled(False)
    
    def populate_results_table(self, results: Dict[str, Any]):
        """Populate the three-column results table"""
        outstanding_parents = results.get('outstanding_parents', [])
        
        # Set row count
        self.results_table.setRowCount(len(outstanding_parents))
        
        # Populate table
        for row, parent_data in enumerate(outstanding_parents):
            # Parent Name (Column 0)
            parent_name = parent_data.get('parent_name', '')
            self.results_table.setItem(row, 0, QTableWidgetItem(parent_name))
            
            # Student Name (Column 1)
            student_name = parent_data.get('student_name', '')
            self.results_table.setItem(row, 1, QTableWidgetItem(student_name))
            
            # Outstanding Months (Column 2)
            outstanding_months = parent_data.get('outstanding_months_str', '')
            self.results_table.setItem(row, 2, QTableWidgetItem(outstanding_months))
    
    def export_to_csv(self):
        """Export outstanding payments to CSV including student names"""
        if not self.current_results:
            QMessageBox.warning(self, "Warning", "No results to export.")
            return
        
        # Prepare data for CSV export with student names
        export_data = {
            'outstanding_parents': self.current_results.get('outstanding_parents', []),
            'total_parents': self.current_results.get('total_parents_with_outstanding', 0),
            'summary': f"Outstanding payments report - {self.current_results.get('total_parents_with_outstanding', 0)} parents with outstanding payments"
        }
        
        self.payment_exporter.export_outstanding_payments_csv(export_data, self)