from abc import ABC, abstractmethod
import pandas as pd
import re

class BaseMatcher(ABC):
    """
    Base class for all name matching algorithms.
    Provides common functionality and enforces consistent interface.
    """
    
    def __init__(self, threshold=70):
        """
        Initialize the matcher with a similarity threshold.
        
        Args:
            threshold (int): Minimum similarity score for a match (0-100)
        """
        self.threshold = threshold
    
    @abstractmethod
    def match(self, reference_columns, target_names):
        """
        Match names from reference columns against target names.
        
        Args:
            reference_columns (list): List of reference strings to extract names from
            target_names (list): List of target names to match against
            
        Returns:
            tuple: (best_match, best_score) or (None, 0) if no match found
        """
        pass
    
    @abstractmethod
    def clean_name(self, name):
        """
        Clean and normalize a name for matching.
        
        Args:
            name (str): Raw name to clean
            
        Returns:
            str: Cleaned name
        """
        pass
    
    @abstractmethod
    def extract_names_from_text(self, text):
        """
        Extract potential names from text.
        
        Args:
            text (str): Text to extract names from
            
        Returns:
            list: List of potential names
        """
        pass
    
    def _remove_duplicates(self, names):
        """
        Remove duplicate names while preserving order.
        
        Args:
            names (list): List of names that may contain duplicates
            
        Returns:
            list: List with duplicates removed
        """
        seen = set()
        unique_names = []
        for name in names:
            if name not in seen:
                seen.add(name)
                unique_names.append(name)
        return unique_names
    
    def _clean_excel_formatting(self, text):
        """
        Remove Excel-specific formatting from text.
        
        Args:
            text (str): Text that may contain Excel formatting
            
        Returns:
            str: Text with Excel formatting removed
        """
        if pd.isna(text) or not isinstance(text, str):
            return ""
        
        text = str(text).strip()
        
        # Remove Excel formula quotes
        if text.startswith('="'):
            text = text[2:]
        if text.endswith('"'):
            text = text[:-1]
            
        return text