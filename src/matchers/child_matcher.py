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
                    # Further split this part for multiple children
                    child_names = self._extract_multiple_children(child_part)
                    potential_names.extend(child_names)
        
        # Method 2: Split by commas and common separators
        parts = text.split(',')
        for part in parts:
            part = part.strip()
            if part:
                sub_parts = re.split(r'[/\\|]', part)
                for sub_part in sub_parts:
                    child_names = self._extract_multiple_children(sub_part)
                    potential_names.extend(child_names)
        
        # Method 3: Look for capitalized words after common patterns
        child_patterns = [
            r'(?:STUDENT|CHILD|FOR)\s+([A-Z\s\-\.&@]+?)(?:\s{3,}|$)',
            r'(?:,\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:\s{3,})([A-Z\s\-\.&@]+?)(?:\s{3,}|$)'
        ]
        
        for pattern in child_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                child_text = match.group(1).strip()
                child_names = self._extract_multiple_children(child_text)
                potential_names.extend(child_names)
        
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
                child_names = self._extract_multiple_children(potential_name)
                potential_names.extend(child_names)
        
        return self._remove_duplicates(potential_names)
    
    def _extract_multiple_children(self, text):
        """
        Extract multiple child names from a single text segment.
        Handles cases like "Isabelle Isalynn Lai", "daniel rayyan n raihan", etc.
        
        Args:
            text (str): Text that may contain multiple child names
            
        Returns:
            list: List of individual child names
        """
        if not text or len(text.strip()) < 2:
            return []
        
        child_names = []
        
        # Split by common separators for multiple children
        separators = [' N ', ' AND ', ' & ', ' + ', ',', '/', '\\', '|']
        
        # Try each separator first
        for separator in separators:
            if separator.upper() in text.upper():
                parts = re.split(re.escape(separator), text, flags=re.IGNORECASE)
                for part in parts:
                    cleaned = self.clean_name(part.strip())
                    if len(cleaned) > 2:
                        child_names.append(cleaned)
                return child_names
        
        # If no separators found, try to identify multiple names in sequence
        # Remove common patterns that aren't part of names first
        cleaned_text = text
        
        # Remove common patterns that aren't part of names
        patterns_to_remove = [
            r'\b(JUNE?|JULY?|JUN|JUL)\s*\d{0,4}\b',  # June25, Jun2025, etc.
            r'\bF\d+\b',  # F4, F5, etc.
            r'\b(FORM|GRADE)\s*\d+\b',  # Form1, Grade2, etc.
            r'\b(TUITION|FEE|FEES|PAYMENT)\b',
            r'\b20\d{2}\b',  # Years like 2025
            r'\b\d{1,2}/\d{1,2}\b',  # Dates like 06/25
        ]
        
        for pattern in patterns_to_remove:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        # Try to split into individual names
        # Look for patterns like "FirstName SecondName ThirdName" and split intelligently
        words = cleaned_text.split()
        
        if len(words) <= 2:
            # Simple case: 1-2 words, treat as single name
            cleaned = self.clean_name(cleaned_text)
            if len(cleaned) > 2:
                child_names.append(cleaned)
        elif len(words) == 3:
            # 3 words: Could be "First Middle Last" or "FirstName SecondName"
            # Try both interpretations
            full_name = self.clean_name(cleaned_text)
            if len(full_name) > 2:
                child_names.append(full_name)
            
            # Also try first word as separate name and last two as another name
            first_name = self.clean_name(words[0])
            last_two = self.clean_name(' '.join(words[1:]))
            
            if len(first_name) > 2 and first_name != full_name:
                child_names.append(first_name)
            if len(last_two) > 2 and last_two != full_name:
                child_names.append(last_two)
                
        elif len(words) >= 4:
            # 4+ words: Likely multiple names
            # Try different combinations
            
            # Combination 1: First word + rest of words
            first_name = self.clean_name(words[0])
            rest_name = self.clean_name(' '.join(words[1:]))
            
            if len(first_name) > 2:
                child_names.append(first_name)
            if len(rest_name) > 2:
                child_names.append(rest_name)
            
            # Combination 2: First two words + rest
            if len(words) >= 4:
                first_two = self.clean_name(' '.join(words[:2]))
                rest_two = self.clean_name(' '.join(words[2:]))
                
                if len(first_two) > 2 and first_two not in child_names:
                    child_names.append(first_two)
                if len(rest_two) > 2 and rest_two not in child_names:
                    child_names.append(rest_two)
            
            # Combination 3: Split in middle
            mid_point = len(words) // 2
            first_half = self.clean_name(' '.join(words[:mid_point]))
            second_half = self.clean_name(' '.join(words[mid_point:]))
            
            if len(first_half) > 2 and first_half not in child_names:
                child_names.append(first_half)
            if len(second_half) > 2 and second_half not in child_names:
                child_names.append(second_half)
        
        # Remove duplicates while preserving order
        unique_names = []
        for name in child_names:
            if name not in unique_names:
                unique_names.append(name)
        
        return unique_names
    
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
            original_text = leftover_text  # Keep original for debugging
            
            if matched_parent_name:
                # Clean the matched parent name
                cleaned_parent = self.clean_name(matched_parent_name)
                
                # Method 1: Split by large spaces first (most reliable)
                big_space_parts = re.split(r'\s{5,}', leftover_text)
                if len(big_space_parts) > 1:
                    # First part is likely parent, keep the rest
                    leftover_text = ' '.join(big_space_parts[1:])
                else:
                    # Method 2: Try to find the parent name in the text and remove it
                    parent_words = cleaned_parent.split()
                    temp_text = leftover_text.upper()
                    
                    # Try to find the complete parent name sequence
                    parent_pattern = r'\b' + r'\s+'.join([re.escape(word) for word in parent_words]) + r'\b'
                    leftover_text = re.sub(parent_pattern, '', temp_text, flags=re.IGNORECASE).strip()
                    
                    # If that didn't work, try removing individual words
                    if leftover_text.upper() == temp_text:
                        for word in parent_words:
                            if len(word) > 2:  # Only remove meaningful words
                                word_pattern = r'\b' + re.escape(word) + r'\b'
                                leftover_text = re.sub(word_pattern, '', leftover_text, flags=re.IGNORECASE)
            
            # Clean up the leftover text
            leftover_text = re.sub(r'\s+', ' ', leftover_text).strip()
            
            # Only add if there's meaningful leftover content
            if leftover_text and len(leftover_text) > 2:
                # Remove common non-name words
                non_name_words = ['JUNE', 'JULY', 'TUITION', 'FEE', 'FEES', 'PAYMENT', 'TRANSFER', '2025', '2024']
                words = leftover_text.split()
                filtered_words = []
                
                for word in words:
                    # Keep word if it's not a common non-name word or if it contains letters and is substantial
                    if (word.upper() not in non_name_words and 
                        any(c.isalpha() for c in word) and 
                        len(word) > 1):
                        filtered_words.append(word)
                
                if filtered_words:
                    leftover_text = ' '.join(filtered_words)
                    leftover_columns.append(leftover_text)
        
        return leftover_columns
    
    def match(self, reference_columns, fee_df, matched_parent_name=None):
        """
        Match child names from transaction references to fee record child names.
        Only searches for children that belong to the matched parent.
        
        Args:
            reference_columns (list): List of reference strings from transaction
            fee_df (DataFrame): The complete fee record DataFrame
            matched_parent_name (str): The matched parent name to constrain search
        
        Returns:
            tuple: (comma_separated_matches, total_score) or (None, 0) if no matches found
        """
        if not matched_parent_name:
            return None, 0
        
        # Get children that belong to the matched parent
        parent_children = self._get_children_for_parent(fee_df, matched_parent_name)
        
        if not parent_children:
            return None, 0
        
        # Remove parent name portions from reference text
        leftover_columns = self.remove_parent_portions(reference_columns, matched_parent_name)
        
        # Extract all potential child names from leftover text
        all_potential_names = []
        for leftover_col in leftover_columns:
            potential_names = self.extract_names_from_text(leftover_col)
            all_potential_names.extend(potential_names)
        
        # Remove duplicates
        unique_names = self._remove_duplicates(all_potential_names)
        
        # Find all matches across all potential names, but only against this parent's children
        all_matches = []
        total_score = 0
        
        for potential_name in unique_names:
            match, score = self.find_best_match(potential_name, parent_children)
            if match and score >= self.threshold:
                # Avoid duplicate matches
                if match not in all_matches:
                    all_matches.append(match)
                    total_score += score
        
        if all_matches:
            # Return comma-separated list of matches
            combined_matches = ", ".join(all_matches)
            average_score = total_score / len(all_matches)
            return combined_matches, average_score
        
        return None, 0
    
    def _get_children_for_parent(self, fee_df, matched_parent_name):
        """
        Get all children names that belong to the specified parent from fee record.
        
        Args:
            fee_df (DataFrame): The complete fee record DataFrame
            matched_parent_name (str): The parent name to find children for
            
        Returns:
            list: List of child names belonging to this parent
        """
        children = []
        
        # Get parent and child columns
        parent_column = fee_df.iloc[:, 0] if len(fee_df.columns) > 0 else []
        child_column = fee_df.iloc[:, 1] if len(fee_df.columns) > 1 else []
        
        # Find all rows where the parent matches
        for idx, parent in enumerate(parent_column):
            if pd.notna(parent) and str(parent).strip() == matched_parent_name.strip():
                # Get the corresponding child name
                if idx < len(child_column) and pd.notna(child_column.iloc[idx]):
                    child_name = str(child_column.iloc[idx]).strip()
                    if child_name and child_name not in children:
                        children.append(child_name)
        
        return children