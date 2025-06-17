import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
import openpyxl

def clean_parent_name(name):
    if pd.isna(name) or not isinstance(name, str):
        return ""
    
    name = str(name).upper().strip()
    
    if name.startswith('="'):
        name = name[2:]
    if name.endswith('"'):
        name = name[:-1]
    
    prefixes_suffixes = ['BINTI', 'BIN', 'A/P', 'D/O', 'MR', 'MRS', 'MS', 'DR']
    for prefix in prefixes_suffixes:
        name = re.sub(rf'\b{prefix}\b', '', name)
    
    name = re.sub(r'[-_]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name

def extract_parent_names_from_transaction(text):
    if pd.isna(text) or not isinstance(text, str):
        return []
    
    text = str(text).strip()
    
    if text.startswith('="'):
        text = text[2:]
    if text.endswith('"'):
        text = text[:-1]
    
    potential_names = []
    
    big_space_parts = re.split(r'\s{5,}', text)
    if len(big_space_parts) > 1:
        parent_part = big_space_parts[0].strip()
        if parent_part:
            cleaned = clean_parent_name(parent_part)
            if len(cleaned) > 3:
                potential_names.append(cleaned)
    
    parts = text.split(',')
    for part in parts:
        part = part.strip()
        if part:
            sub_parts = re.split(r'[/\\|]', part)
            for sub_part in sub_parts:
                cleaned = clean_parent_name(sub_part)
                if len(cleaned) > 3:
                    potential_names.append(cleaned)
    
    first_name_match = re.match(r'^([A-Z\s\-\/\.&@]+?)(?:\s{3,}|\s+[a-z])', text)
    if first_name_match:
        first_name = first_name_match.group(1).strip()
        cleaned = clean_parent_name(first_name)
        if len(cleaned) > 3:
            potential_names.append(cleaned)
    
    whole_cleaned = clean_parent_name(text)
    if len(whole_cleaned) > 3:
        potential_names.append(whole_cleaned)
    
    seen = set()
    unique_names = []
    for name in potential_names:
        if name not in seen:
            seen.add(name)
            unique_names.append(name)
    
    return unique_names

def find_best_match(target_name, parent_list, threshold=70):
    if not target_name or not parent_list:
        return None, 0
    
    cleaned_target = clean_parent_name(target_name)
    
    if not cleaned_target:
        return None, 0
    
    cleaned_parents = [clean_parent_name(parent) for parent in parent_list]
    
    best_match = None
    best_score = 0
    best_original = None
    
    for i, cleaned_parent in enumerate(cleaned_parents):
        if cleaned_target == cleaned_parent:
            return parent_list[i], 100
    
    for i, cleaned_parent in enumerate(cleaned_parents):
        if cleaned_parent.startswith(cleaned_target) or cleaned_target.startswith(cleaned_parent):
            score = 95
            if score > best_score:
                best_match = cleaned_parent
                best_score = score
                best_original = parent_list[i]
    
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
    
    fuzzy_methods = [
        (fuzz.ratio, "ratio"),
        (fuzz.partial_ratio, "partial"),
        (fuzz.token_sort_ratio, "token_sort"),
        (fuzz.token_set_ratio, "token_set")
    ]
    
    for scorer, method_name in fuzzy_methods:
        fuzzy_match = process.extractOne(cleaned_target, cleaned_parents, scorer=scorer)
        if fuzzy_match and fuzzy_match[1] > best_score and fuzzy_match[1] >= threshold:
            original_index = cleaned_parents.index(fuzzy_match[0])
            best_match = fuzzy_match[0]
            best_score = fuzzy_match[1]
            best_original = parent_list[original_index]
    
    if best_score < threshold:
        for i, cleaned_parent in enumerate(cleaned_parents):
            if cleaned_target in cleaned_parent or cleaned_parent in cleaned_target:
                score = min(len(cleaned_target), len(cleaned_parent)) / max(len(cleaned_target), len(cleaned_parent)) * 85
                if score > best_score and score >= threshold:
                    best_match = cleaned_parent
                    best_score = score
                    best_original = parent_list[i]
    
    if best_original and best_score >= threshold:
        return best_original, best_score
    
    return None, 0

def process_fee_matching():
    fee_record_file = r"C:\Users\user\Downloads\2025 Tuition Fee.xlsx"
    transaction_file = r"C:\Users\user\Downloads\Fee Statements\3985094904Statement (9).csv"
    
    print(f"Transaction File:   {transaction_file}")
    
    try:
        print("Reading fee record file...")
        fee_df = pd.read_excel(fee_record_file)
        print(f"Fee record file loaded: {len(fee_df)} rows")
        
        print("Reading transaction file...")
        try:
            import csv
            all_rows = []
            
            with open(transaction_file, 'r', encoding='utf-8', newline='') as f:
                csv_reader = csv.reader(f)
                for row_num, row in enumerate(csv_reader):
                    all_rows.append(row)
            
            print(f"Transaction file loaded: {len(all_rows)} rows")
            
            max_cols = max(len(row) for row in all_rows) if all_rows else 0
            
            padded_rows = []
            for row in all_rows:
                padded_row = row + [''] * (max_cols - len(row))
                padded_rows.append(padded_row)
            
            columns = [f'Col_{i}' for i in range(max_cols)]
            trans_df = pd.DataFrame(padded_rows, columns=columns)
            
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
        
        parent_names = fee_df.iloc[:, 0].dropna().tolist()
        print(f"Found {len(parent_names)} parent names in fee record")
        
        matched_count = 0
        unmatched_count = 0
        all_results = []
        
        for idx, row in trans_df.iterrows():
            transaction_ref = ""
            amount = 0
            
            reference_columns = []
            for col_idx in [5, 6, 7, 8]:
                if len(trans_df.columns) > col_idx:
                    col_name = f'Col_{col_idx}'
                    col_val = row[col_name]
                    if pd.notna(col_val) and str(col_val).strip():
                        reference_columns.append(str(col_val))
            
            if reference_columns:
                transaction_ref = " | ".join(reference_columns)
            
            if len(trans_df.columns) > 4:
                col_4_val = row['Col_4']
                if pd.notna(col_4_val) and str(col_4_val).strip():
                    amount_str = str(col_4_val)
                    try:
                        amount_str = amount_str.replace(',', '').replace('$', '').replace('RM', '').strip()
                        if amount_str and amount_str != 'nan':
                            amount = float(amount_str)
                    except (ValueError, AttributeError):
                        amount = 0
            
            if not transaction_ref.strip():
                continue
            
            if amount <= 0:
                all_results.append({
                    'index': idx,
                    'parent_from_transaction': "",
                    'matched_parent': "",           
                    'amount': "",                   
                    'matched': False
                })
                continue
            
            all_potential_names = []
            for ref_col in reference_columns:
                potential_names = extract_parent_names_from_transaction(ref_col)
                all_potential_names.extend(potential_names)
            
            unique_names = []
            seen = set()
            for name in all_potential_names:
                if name not in seen:
                    seen.add(name)
                    unique_names.append(name)
            
            best_match = None
            best_score = 0
            
            for potential_name in unique_names:
                match, score = find_best_match(potential_name, parent_names, threshold=70)
                if match and score > best_score:
                    best_match = match
                    best_score = score
            
            display_parent = transaction_ref
            
            if best_match:
                matched_count += 1
                all_results.append({
                    'index': idx,
                    'parent_from_transaction': display_parent,
                    'matched_parent': best_match.strip(),
                    'amount': amount,
                    'matched': True
                })
            else:
                unmatched_count += 1
                all_results.append({
                    'index': idx,
                    'parent_from_transaction': display_parent,
                    'matched_parent': "NO MATCH FOUND",
                    'amount': amount,
                    'matched': False
                })
        
        total_processed = matched_count + unmatched_count
        match_rate = (matched_count / total_processed * 100) if total_processed > 0 else 0
        
        print(f"\n=== MATCHING SUMMARY ===")
        print(f"Total transactions processed: {total_processed}")
        print(f"Successfully matched: {matched_count}")
        print(f"Unmatched transactions: {unmatched_count}")
        print(f"Match rate: {match_rate:.1f}%")
        
        separator_line = "=" * 110
        print(f"\n{separator_line}")
        print(f"{'Index':<6} | {'Parent Name (Transaction File)':<40} | {'Matched Name (Fee Record)':<40} | {'Amount':<10}")
        print(separator_line)
        
        for result in all_results:
            index = result['index']
            parent_name = str(result['parent_from_transaction'])[:39] if result['parent_from_transaction'] else ""
            matched_name = str(result['matched_parent'])[:39] if result['matched_parent'] else ""
            amount = result['amount']
            
            if amount == "":
                empty_line = f"{index:<6} | {'':<40} | {'':<40} | {'':<10}"
                print(empty_line)
            else:
                data_line = f"{index:<6} | {parent_name:<40} | {matched_name:<40} | {amount:<10.2f}"
                print(data_line)
        
        print(separator_line)
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("STARTING FEE MATCHING PROGRAM")
    print("=" * 50)
    print("Note: Make sure you have installed: pip install fuzzywuzzy python-levenshtein openpyxl pandas")
    
    # Add debugging to track execution
    import sys
    import time
    
    start_time = time.time()
    print(f"Program started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        print("Calling process_fee_matching()...")
        success = process_fee_matching()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("=" * 50)
        if success:
            print("✓ PROCESS COMPLETED SUCCESSFULLY!")
        else:
            print("✗ PROCESS FAILED!")
        print(f"Total execution time: {duration:.2f} seconds")
        print("=" * 50)
        
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Force clean exit
    print("Program execution finished.")
    print("Press Enter to close this window...")
    input()
    print("Exiting now...")
    sys.exit(0)