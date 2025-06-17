import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
from .base_matcher import BaseMatcher

class ChildMatcher(BaseMatcher):
    """
    Matcher specifically designed for matching child names from transaction data
    to child names in fee records.
    """
    
    def __init__(self, threshold=70):
        """
        Initialize the ChildMatcher.
        
        Args:
            threshold (int): Minimum similarity score for a match (0-100)
        """
        super().__init__(threshold)
    
    def clean_name(self, name):
        """
        Clean and normalize a child name for matching.
        
        Args:
            name (str): Raw child name to clean
            
        Returns:
            str: Cleaned child name
        """
        if pd.isna(name) or not isinstance(name, str):
            return ""
        
        name = str(name).upper().strip()
        
        # Remove Excel formatting
        name = self._clean_excel_formatting(name)
        
        # Remove common prefixes and suffixes for children
        prefixes_suffixes = ['STUDENT', 'CHILD', 'SON', 'DAUGHTER', 'BINTI', 'BIN', 'A/P', 'D/O']
        for prefix in prefixes_suffixes:
            name = re.sub(rf'\b{prefix}\b', '', name)
        
        # Clean up separators and whitespace
        name = re.sub(r'[-_]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def extract_names_from_text(self, text):
        """
        Extract potential child names from transaction text.
        
        Args:
            text (str): Transaction text to extract names from
            
        Returns:
            list: List of potential child names
        """
        if pd.isna(text) or not isinstance(text, str):
            return []
        
        text = str(text).strip()
        
        # Remove Excel formatting
        text = self._clean_excel_formatting(text)
        
        potential_names = []
        
        # Method 1: Split by large spaces and take remaining parts
        big_space_parts = re.split(r'\s{5,}', text)
        if len(big_space_parts) > 1:
            # Skip first part (likely parent name) and process remaining
            for i in range(1, len(big_space_parts)):
                child_part = big_space_parts[i].strip()
                if child_part:
                    cleaned = self.clean_name(child_part)
                    if len(cleaned) > 2:
                        potential_names.append(cleaned)
        
        # Method 2: Split by commas and common separators
        parts = text.split(',')
        for part in parts:
            part = part.strip()
            if part:
                sub_parts = re.split(r'[/\\|]', part)
                for sub_part in sub_parts:
                    cleaned = self.clean_name(sub_part)
                    if len(cleaned) > 2:
                        potential_names.append(cleaned)
        
        # Method 3: Look for capitalized words after common patterns
        child_patterns = [
            r'(?:STUDENT|CHILD|FOR)\s+([A-Z\s\-\.&@]+?)(?:\s{3,}|$)',
            r'(?:,\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:\s{3,})([A-Z\s\-\.&@]+?)(?:\s{3,}|$)'
        ]
        
        for pattern in child_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                child_name = match.group(1).strip()
                cleaned = self.clean_name(child_name)
                if len(cleaned) > 2:
                    potential_names.append(cleaned)
        
        # Method 4: Extract words that look like names (mixed case or all caps short words)
        words = text.split()
        for i, word in enumerate(words):
            if len(word) > 2 and (word.isupper() or word.istitle()):
                # Try to build a name from consecutive name-like words
                name_parts = [word]
                for j in range(i + 1, min(i + 3, len(words))):
                    next_word = words[j]
                    if len(next_word) > 1 and (next_word.isupper() or next_word.istitle()):
                        name_parts.append(next_word)
                    else:
                        break
                
                potential_name = ' '.join(name_parts)
                cleaned = self.clean_name(potential_name)
                if len(cleaned) > 2:
                    potential_names.append(cleaned)
        
        return self._remove_duplicates(potential_names)
    
    def find_best_match(self, target_name, child_list):
        """
        Find the best match for a target name in the child list.
        
        Args:
            target_name (str): Name to find a match for
            child_list (list): List of child names to search in
            
        Returns:
            tuple: (best_match, best_score) or (None, 0) if no match found
        """
        if not target_name or not child_list:
            return None, 0
        
        cleaned_target = self.clean_name(target_name)
        
        if not cleaned_target:
            return None, 0
        
        cleaned_children = [self.clean_name(child) for child in child_list]
        
        best_match = None
        best_score = 0
        best_original = None
        
        # Exact match check
        for i, cleaned_child in enumerate(cleaned_children):
            if cleaned_target == cleaned_child:
                return child_list[i], 100
        
        # Prefix/suffix match check
        for i, cleaned_child in enumerate(cleaned_children):
            if cleaned_child.startswith(cleaned_target) or cleaned_target.startswith(cleaned_child):
                score = 95
                if score > best_score:
                    best_match = cleaned_child
                    best_score = score
                    best_original = child_list[i]
        
        # Common words check
        target_words = set(cleaned_target.split())
        for i, cleaned_child in enumerate(cleaned_children):
            child_words = set(cleaned_child.split())
            if target_words and child_words:
                common_words = target_words.intersection(child_words)
                if len(common_words) >= 1:  # Lower threshold for child names
                    score = (len(common_words) / max(len(target_words), len(child_words))) * 85
                    if score > best_score:
                        best_match = cleaned_child
                        best_score = score
                        best_original = child_list[i]
        
        # Fuzzy matching with multiple algorithms
        fuzzy_methods = [
            (fuzz.ratio, "ratio"),
            (fuzz.partial_ratio, "partial"),
            (fuzz.token_sort_ratio, "token_sort"),
            (fuzz.token_set_ratio, "token_set")
        ]
        
        for scorer, method_name in fuzzy_methods:
            fuzzy_match = process.extractOne(cleaned_target, cleaned_children, scorer=scorer)
            if fuzzy_match and fuzzy_match[1] > best_score and fuzzy_match[1] >= self.threshold:
                original_index = cleaned_children.index(fuzzy_match[0])
                best_match = fuzzy_match[0]
                best_score = fuzzy_match[1]
                best_original = child_list[original_index]
        
        # Substring match as last resort
        if best_score < self.threshold:
            for i, cleaned_child in enumerate(cleaned_children):
                if cleaned_target in cleaned_child or cleaned_child in cleaned_target:
                    score = min(len(cleaned_target), len(cleaned_child)) / max(len(cleaned_target), len(cleaned_child)) * 80
                    if score > best_score and score >= self.threshold:
                        best_match = cleaned_child
                        best_score = score
                        best_original = child_list[i]
        
        if best_original and best_score >= self.threshold:
            return best_original, best_score
        
        return None, 0
    
    def remove_parent_portions(self, reference_columns, matched_parent_name):
        """
        Remove the portions of text that were identified as parent names.
        
        Args:
            reference_columns (list): Original reference strings
            matched_parent_name (str): The actual matched parent name from fee record
            
        Returns:
            list: Reference columns with parent name portions removed
        """
        leftover_columns = []
        
        for ref_col in reference_columns:
            # Clean Excel formatting first
            leftover_text = self._clean_excel_formatting(ref_col)
            
            if matched_parent_name:
                # Clean the matched parent name
                cleaned_parent = self.clean_name(matched_parent_name)
                
                # Try to find the parent name portion in the original text
                # Split by large spaces first (common pattern)
                big_space_parts = re.split(r'\s{5,}', leftover_text)
                if len(big_space_parts) > 1:
                    # First part is likely parent, remove it
                    leftover_text = ' '.join(big_space_parts[1:])
                else:
                    # Try to remove parent words from the text
                    parent_words = cleaned_parent.split()
                    for word in parent_words:
                        if len(word) > 2:
                            leftover_text = re.sub(rf'\b{re.escape(word)}\b', '', leftover_text, flags=re.IGNORECASE)
            
            # Clean up the leftover text
            leftover_text = re.sub(r'\s+', ' ', leftover_text).strip()
            if leftover_text and len(leftover_text) > 2:
                leftover_columns.append(leftover_text)
        
        return leftover_columns
    
    def match(self, reference_columns, child_names, matched_parent_name=None):
        """
        Match child names from transaction references to fee record child names.
        
        Args:
            reference_columns (list): List of reference strings from transaction
            child_names (list): List of child names from fee record (second column)
            matched_parent_name (str): The matched parent name to remove from text
        
        Returns:
            tuple: (best_match, best_score) or (None, 0) if no match found
        """
        # Remove parent name portions if provided
        if matched_parent_name:
            leftover_columns = self.remove_parent_portions(reference_columns, matched_parent_name)
        else:
            # Clean Excel formatting from all columns
            leftover_columns = [self._clean_excel_formatting(col) for col in reference_columns]
        
        # Extract all potential child names from leftover text
        all_potential_names = []
        for leftover_col in leftover_columns:
            potential_names = self.extract_names_from_text(leftover_col)
            all_potential_names.extend(potential_names)
        
        # Remove duplicates
        unique_names = self._remove_duplicates(all_potential_names)
        
        # Find best match across all potential names
        best_match = None
        best_score = 0
        
        for potential_name in unique_names:
            match, score = self.find_best_match(potential_name, child_names)
            if match and score > best_score:
                best_match = match
                best_score = score
        
        return best_match, best_score