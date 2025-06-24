import pandas as pd
import re
from .base_matcher import BaseMatcher
from .date_utils import (normalize_month_name, extract_month_from_date_string, 
                        find_months_in_text, get_month_from_context)

class MonthMatcher(BaseMatcher):
    """
    Matcher specifically designed for extracting month information from transaction data.
    Extracts the month that the fee is being paid for.
    """
    
    def __init__(self, threshold=70):
        """
        Initialize the MonthMatcher.
        
        Args:
            threshold (int): Minimum similarity score for a match (0-100)
                           Note: For month matching, this is less relevant as we're
                           doing pattern extraction rather than fuzzy matching
        """
        super().__init__(threshold)
    
    def clean_name(self, name):
        """
        Clean and normalize text for month extraction.
        
        Args:
            name (str): Raw text to clean
            
        Returns:
            str: Cleaned text
        """
        if pd.isna(name) or not isinstance(name, str):
            return ""
        
        name = str(name).strip()
        
        # Remove Excel formatting
        name = self._clean_excel_formatting(name)
        
        # Convert to lowercase for processing
        name = name.lower()
        
        # Clean up extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def extract_names_from_text(self, text):
        """
        Extract potential month names from transaction text.
        
        Args:
            text (str): Transaction text to extract months from
            
        Returns:
            list: List of potential months in 3-letter format
        """
        if pd.isna(text) or not isinstance(text, str):
            return []
        
        text = str(text).strip()
        
        # Remove Excel formatting
        text = self._clean_excel_formatting(text)
        
        # Use the utility function to find months with context awareness
        found_months = get_month_from_context(text)
        
        if found_months:
            return [found_months]
        
        # Fallback: try to find any months in the text
        all_months = find_months_in_text(text)
        return all_months[:1]  # Return only the first found month
    
    def extract_month_from_reference_columns(self, reference_columns):
        """
        Extract month from transaction reference columns.
        
        Args:
            reference_columns (list): List of reference strings from transaction
            
        Returns:
            str: Extracted month in 3-letter format or None
        """
        if not reference_columns:
            return None
        
        # Process each reference column
        all_potential_months = []
        
        for ref_col in reference_columns:
            potential_months = self.extract_names_from_text(ref_col)
            all_potential_months.extend(potential_months)
        
        # Remove duplicates while preserving order
        unique_months = []
        for month in all_potential_months:
            if month not in unique_months:
                unique_months.append(month)
        
        if unique_months:
            return unique_months[0]  # Return the first (most likely) month
        
        return None
    
    def extract_month_from_transaction_date(self, transaction_date):
        """
        Extract month from transaction date as fallback.
        
        Args:
            transaction_date (str): Transaction date string
            
        Returns:
            str: Month in 3-letter format or None
        """
        if not transaction_date:
            return None
        
        return extract_month_from_date_string(transaction_date)
    
    def match(self, reference_columns, transaction_date=None):
        """
        Extract month from transaction references with fallback to transaction date.
        
        Args:
            reference_columns (list): List of reference strings from transaction
            transaction_date (str): Transaction date string (fallback)
            
        Returns:
            tuple: (extracted_month, confidence_score) or (None, 0) if no month found
        """
        # Try to extract month from reference columns first
        extracted_month = self.extract_month_from_reference_columns(reference_columns)
        
        if extracted_month:
            # High confidence if found in reference
            return extracted_month, 95
        
        # Fallback to transaction date
        if transaction_date:
            extracted_month = self.extract_month_from_transaction_date(transaction_date)
            if extracted_month:
                # Medium confidence if extracted from date
                return extracted_month, 80
        
        # No month found
        return None, 0
    
    def extract_month_with_details(self, reference_columns, transaction_date=None):
        """
        Extract month with detailed information about the source.
        
        Args:
            reference_columns (list): List of reference strings from transaction
            transaction_date (str): Transaction date string (fallback)
            
        Returns:
            dict: Dictionary with month, source, and confidence information
        """
        result = {
            'month': None,
            'source': None,
            'confidence': 0,
            'raw_text': None
        }
        
        # Try reference columns first
        if reference_columns:
            for i, ref_col in enumerate(reference_columns):
                potential_months = self.extract_names_from_text(ref_col)
                if potential_months:
                    result['month'] = potential_months[0]
                    result['source'] = f'reference_column_{i}'
                    result['confidence'] = 95
                    result['raw_text'] = ref_col
                    return result
        
        # Fallback to transaction date
        if transaction_date:
            month_from_date = self.extract_month_from_transaction_date(transaction_date)
            if month_from_date:
                result['month'] = month_from_date
                result['source'] = 'transaction_date'
                result['confidence'] = 80
                result['raw_text'] = transaction_date
                return result
        
        # No month found
        result['source'] = 'not_found'
        return result
    
    def validate_month(self, month_str):
        """
        Validate if a month string is a valid month.
        
        Args:
            month_str (str): Month string to validate
            
        Returns:
            bool: True if valid month, False otherwise
        """
        if not month_str:
            return False
        
        valid_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        return month_str in valid_months
    
    def get_month_number(self, month_str):
        """
        Convert 3-letter month to month number.
        
        Args:
            month_str (str): Month in 3-letter format
            
        Returns:
            int: Month number (1-12) or None
        """
        month_to_number = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
            'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
            'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        return month_to_number.get(month_str)
    
    def compare_with_transaction_date(self, extracted_month, transaction_date):
        """
        Compare extracted month with transaction date for validation.
        
        Args:
            extracted_month (str): Extracted month in 3-letter format
            transaction_date (str): Transaction date string
            
        Returns:
            dict: Comparison result with validation info
        """
        result = {
            'month_matches_date': False,
            'month_difference': None,
            'validation_notes': []
        }
        
        if not extracted_month or not transaction_date:
            result['validation_notes'].append("Missing month or date for comparison")
            return result
        
        # Extract month from transaction date
        date_month = self.extract_month_from_transaction_date(transaction_date)
        
        if not date_month:
            result['validation_notes'].append("Could not extract month from transaction date")
            return result
        
        # Compare months
        if extracted_month == date_month:
            result['month_matches_date'] = True
            result['month_difference'] = 0
            result['validation_notes'].append("Month matches transaction date")
        else:
            result['month_matches_date'] = False
            
            # Calculate month difference
            extracted_num = self.get_month_number(extracted_month)
            date_num = self.get_month_number(date_month)
            
            if extracted_num and date_num:
                result['month_difference'] = abs(extracted_num - date_num)
                
                if result['month_difference'] == 1:
                    result['validation_notes'].append("Month is 1 month different from transaction date")
                elif result['month_difference'] <= 3:
                    result['validation_notes'].append(f"Month is {result['month_difference']} months different from transaction date")
                else:
                    result['validation_notes'].append("Month is significantly different from transaction date")
        
        return result