import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
from .base_matcher import BaseMatcher

class ParentMatcher(BaseMatcher):
    """
    Matcher specifically designed for matching parent names from transaction data
    to parent names in fee records.
    """
    
    def __init__(self, threshold=70):
        """
        Initialize the ParentMatcher.
        
        Args:
            threshold (int): Minimum similarity score for a match (0-100)
        """
        super().__init__(threshold)
    
    def clean_name(self, name):
        """
        Clean and normalize a parent name for matching.
        
        Args:
            name (str): Raw parent name to clean
            
        Returns:
            str: Cleaned parent name
        """
        if pd.isna(name) or not isinstance(name, str):
            return ""
        
        name = str(name).upper().strip()
        
        # Remove Excel formatting
        name = self._clean_excel_formatting(name)
        
        # Remove common prefixes and suffixes
        prefixes_suffixes = ['BINTI', 'BIN', 'A/P', 'D/O', 'MR', 'MRS', 'MS', 'DR']
        for prefix in prefixes_suffixes:
            name = re.sub(rf'\b{prefix}\b', '', name)
        
        # Clean up separators and whitespace
        name = re.sub(r'[-_]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def extract_names_from_text(self, text):
        """
        Extract potential parent names from transaction text.
        
        Args:
            text (str): Transaction text to extract names from
            
        Returns:
            list: List of potential parent names
        """
        if pd.isna(text) or not isinstance(text, str):
            return []
        
        text = str(text).strip()
        
        # Remove Excel formatting
        text = self._clean_excel_formatting(text)
        
        potential_names = []
        
        # Method 1: Split by large spaces (common in transaction formats)
        big_space_parts = re.split(r'\s{5,}', text)
        if len(big_space_parts) > 1:
            parent_part = big_space_parts[0].strip()
            if parent_part:
                cleaned = self.clean_name(parent_part)
                if len(cleaned) > 3:
                    potential_names.append(cleaned)
        
        # Method 2: Split by commas and common separators
        parts = text.split(',')
        for part in parts:
            part = part.strip()
            if part:
                sub_parts = re.split(r'[/\\|]', part)
                for sub_part in sub_parts:
                    cleaned = self.clean_name(sub_part)
                    if len(cleaned) > 3:
                        potential_names.append(cleaned)
        
        # Method 3: Extract first capitalized section
        first_name_match = re.match(r'^([A-Z\s\-\/\.&@]+?)(?:\s{3,}|\s+[a-z])', text)
        if first_name_match:
            first_name = first_name_match.group(1).strip()
            cleaned = self.clean_name(first_name)
            if len(cleaned) > 3:
                potential_names.append(cleaned)
        
        # Method 4: Clean the whole text as fallback
        whole_cleaned = self.clean_name(text)
        if len(whole_cleaned) > 3:
            potential_names.append(whole_cleaned)
        
        return self._remove_duplicates(potential_names)
    
    def find_best_match(self, target_name, parent_list):
        """
        Find the best match for a target name in the parent list.
        
        Args:
            target_name (str): Name to find a match for
            parent_list (list): List of parent names to search in
            
        Returns:
            tuple: (best_match, best_score) or (None, 0) if no match found
        """
        if not target_name or not parent_list:
            return None, 0
        
        cleaned_target = self.clean_name(target_name)
        
        if not cleaned_target:
            return None, 0
        
        cleaned_parents = [self.clean_name(parent) for parent in parent_list]
        
        best_match = None
        best_score = 0
        best_original = None
        
        # Exact match check
        for i, cleaned_parent in enumerate(cleaned_parents):
            if cleaned_target == cleaned_parent:
                return parent_list[i], 100
        
        # Prefix/suffix match check
        for i, cleaned_parent in enumerate(cleaned_parents):
            if cleaned_parent.startswith(cleaned_target) or cleaned_target.startswith(cleaned_parent):
                score = 95
                if score > best_score:
                    best_match = cleaned_parent
                    best_score = score
                    best_original = parent_list[i]
        
        # Common words check
        target_words = set(cleaned_target.split())
        for i, cleaned_parent in enumerate(cleaned_parents):
            parent_words = set(cleaned_parent.split())
            if target_words and parent_words:
                common_words = target_words.intersection(parent_words)
                if len(common_words) >= 2:
                    score = (len(common_words) / max(len(target_words), len(parent_words))) * 90
                    if score > best_score:
                        best_match = cleaned_parent
                        best_score = score
                        best_original = parent_list[i]
        
        # Fuzzy matching with multiple algorithms
        fuzzy_methods = [
            (fuzz.ratio, "ratio"),
            (fuzz.partial_ratio, "partial"),
            (fuzz.token_sort_ratio, "token_sort"),
            (fuzz.token_set_ratio, "token_set")
        ]
        
        for scorer, method_name in fuzzy_methods:
            fuzzy_match = process.extractOne(cleaned_target, cleaned_parents, scorer=scorer)
            if fuzzy_match and fuzzy_match[1] > best_score and fuzzy_match[1] >= self.threshold:
                original_index = cleaned_parents.index(fuzzy_match[0])
                best_match = fuzzy_match[0]
                best_score = fuzzy_match[1]
                best_original = parent_list[original_index]
        
        # Substring match as last resort
        if best_score < self.threshold:
            for i, cleaned_parent in enumerate(cleaned_parents):
                if cleaned_target in cleaned_parent or cleaned_parent in cleaned_target:
                    score = min(len(cleaned_target), len(cleaned_parent)) / max(len(cleaned_target), len(cleaned_parent)) * 85
                    if score > best_score and score >= self.threshold:
                        best_match = cleaned_parent
                        best_score = score
                        best_original = parent_list[i]
        
        if best_original and best_score >= self.threshold:
            return best_original, best_score
        
        return None, 0
    
    def match(self, reference_columns, parent_names):
        """
        Match parent names from transaction references to fee record parent names.
        
        Args:
            reference_columns (list): List of reference strings from transaction
            parent_names (list): List of parent names from fee record (first column)
        
        Returns:
            tuple: (best_match, best_score) or (None, 0) if no match found
        """
        # Extract all potential names from all reference columns
        all_potential_names = []
        for ref_col in reference_columns:
            potential_names = self.extract_names_from_text(ref_col)
            all_potential_names.extend(potential_names)
        
        # Remove duplicates
        unique_names = self._remove_duplicates(all_potential_names)
        
        # Finds best match across all potential names
        best_match = None
        best_score = 0
        
        for potential_name in unique_names:
            match, score = self.find_best_match(potential_name, parent_names)
            if match and score > best_score:
                best_match = match
                best_score = score
        
        return best_match, best_score