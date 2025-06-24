"""
Date utilities and month name mappings for month extraction
"""
import re
from datetime import datetime
from typing import Optional, Dict, List

# Month mappings - all variations to standard 3-letter format
MONTH_MAPPINGS = {
    # Full month names
    'january': 'Jan', 'february': 'Feb', 'march': 'Mar', 'april': 'Apr',
    'may': 'May', 'june': 'Jun', 'july': 'Jul', 'august': 'Aug',
    'september': 'Sep', 'october': 'Oct', 'november': 'Nov', 'december': 'Dec',
    
    # Short forms
    'jan': 'Jan', 'feb': 'Feb', 'mar': 'Mar', 'apr': 'Apr',
    'may': 'May', 'jun': 'Jun', 'jul': 'Jul', 'aug': 'Aug',
    'sep': 'Sep', 'oct': 'Oct', 'nov': 'Nov', 'dec': 'Dec',
    
    # Alternative short forms
    'sept': 'Sep', 'juno': 'Jun', 'june': 'Jun', 'july': 'Jul',
    
    # Numeric months (as strings)
    '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
    '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
    '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec',
    
    # Single digit numeric months
    '1': 'Jan', '2': 'Feb', '3': 'Mar', '4': 'Apr',
    '5': 'May', '6': 'Jun', '7': 'Jul', '8': 'Aug',
    '9': 'Sep',
}

# Common month patterns in text
MONTH_PATTERNS = [
    # Standard month names (case insensitive)
    r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
    r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\b',
    
    # Month with year patterns
    r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\s*20\d{2}\b',
    r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s*20\d{2}\b',
    
    # Numeric month patterns
    r'\b(0?[1-9]|1[0-2])\/(20\d{2})\b',  # MM/YYYY
    r'\b(0?[1-9]|1[0-2])\-(20\d{2})\b',  # MM-YYYY
    
    # Month fee patterns
    r'fee\s+for\s+([a-z]+)',
    r'([a-z]+)\s+fee',
    r'tuition\s+([a-z]+)',
    r'([a-z]+)\s+tuition',
]

def normalize_month_name(month_text: str) -> Optional[str]:
    """
    Normalize various month formats to standard 3-letter format.
    
    Args:
        month_text (str): Raw month text
        
    Returns:
        str: Normalized month in 3-letter format (e.g., "Jun") or None
    """
    if not month_text:
        return None
        
    # Clean and lowercase the input
    clean_month = str(month_text).strip().lower()
    
    # Remove common prefixes/suffixes
    clean_month = re.sub(r'[^\w]', '', clean_month)  # Remove non-word characters
    
    # Direct lookup in mappings
    if clean_month in MONTH_MAPPINGS:
        return MONTH_MAPPINGS[clean_month]
    
    # Try partial matching for longer month names
    for key, value in MONTH_MAPPINGS.items():
        if len(key) > 3 and clean_month.startswith(key[:3]):
            return value
        if len(clean_month) > 3 and key.startswith(clean_month[:3]):
            return value
    
    return None

def extract_month_from_date_string(date_string: str) -> Optional[str]:
    """
    Extract month from various date string formats.
    
    Args:
        date_string (str): Date string in various formats
        
    Returns:
        str: Month in 3-letter format or None
    """
    if not date_string:
        return None
    
    date_str = str(date_string).strip()
    
    # Remove Excel formatting
    if date_str.startswith('="'):
        date_str = date_str[2:]
    if date_str.endswith('"'):
        date_str = date_str[:-1]
    
    # Try common date formats
    date_formats = [
        '%d/%m/%Y',    # DD/MM/YYYY
        '%m/%d/%Y',    # MM/DD/YYYY
        '%Y-%m-%d',    # YYYY-MM-DD
        '%d-%m-%Y',    # DD-MM-YYYY
        '%m-%d-%Y',    # MM-DD-YYYY
        '%d/%m/%y',    # DD/MM/YY
        '%m/%d/%y',    # MM/DD/YY
        '%Y/%m/%d',    # YYYY/MM/DD
    ]
    
    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, date_format)
            month_num = parsed_date.month
            return MONTH_MAPPINGS.get(str(month_num).zfill(2))
        except ValueError:
            continue
    
    # Try to extract numeric month from partial dates
    numeric_patterns = [
        r'(\d{1,2})/\d{1,2}/\d{2,4}',  # M/D/Y or MM/DD/YYYY
        r'\d{1,2}/(\d{1,2})/\d{2,4}',  # D/M/Y or DD/MM/YYYY
        r'(\d{1,2})-\d{1,2}-\d{2,4}',  # M-D-Y
        r'\d{1,2}-(\d{1,2})-\d{2,4}',  # D-M-Y
    ]
    
    for pattern in numeric_patterns:
        match = re.search(pattern, date_str)
        if match:
            month_candidate = match.group(1)
            if month_candidate and 1 <= int(month_candidate) <= 12:
                return MONTH_MAPPINGS.get(month_candidate.zfill(2))
    
    return None

def find_months_in_text(text: str) -> List[str]:
    """
    Find all potential months mentioned in text.
    
    Args:
        text (str): Text to search for months
        
    Returns:
        List[str]: List of found months in 3-letter format
    """
    if not text:
        return []
    
    found_months = []
    text_lower = text.lower()
    
    # Try each pattern
    for pattern in MONTH_PATTERNS:
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            # Extract the month part from the match
            month_text = match.group(1) if match.groups() else match.group(0)
            normalized = normalize_month_name(month_text)
            if normalized and normalized not in found_months:
                found_months.append(normalized)
    
    # Also try word-by-word search
    words = re.findall(r'\b\w+\b', text_lower)
    for word in words:
        normalized = normalize_month_name(word)
        if normalized and normalized not in found_months:
            found_months.append(normalized)
    
    return found_months

def get_month_from_context(text: str, context_words: List[str] = None) -> Optional[str]:
    """
    Extract month considering context words that might indicate fee periods.
    
    Args:
        text (str): Text to search
        context_words (List[str]): Words that might indicate fee context
        
    Returns:
        str: Most likely month or None
    """
    if context_words is None:
        context_words = ['fee', 'tuition', 'payment', 'for', 'month', 'term']
    
    found_months = find_months_in_text(text)
    
    if not found_months:
        return None
    
    if len(found_months) == 1:
        return found_months[0]
    
    # If multiple months found, try to pick the most relevant based on context
    text_lower = text.lower()
    
    # Score months based on proximity to context words
    month_scores = {}
    for month in found_months:
        score = 0
        month_pos = text_lower.find(month.lower())
        
        for context_word in context_words:
            context_pos = text_lower.find(context_word)
            if context_pos >= 0 and month_pos >= 0:
                # Closer context words give higher scores
                distance = abs(context_pos - month_pos)
                if distance < 20:  # Within 20 characters
                    score += max(0, 20 - distance)
        
        month_scores[month] = score
    
    # Return month with highest score, or first one if tie
    if month_scores:
        best_month = max(month_scores.items(), key=lambda x: x[1])
        return best_month[0]
    
    return found_months[0]  # Fallback to first found month