import pandas as pd
import numpy as np
import openpyxl
from matchers import ParentMatcher, ChildMatcher

def process_fee_matching():
    fee_record_file = r"C:\Users\user\Downloads\Parent-Student Matching Pair.xlsx"
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
            
            # Remove completely empty rows
            filtered_rows = []
            for row in all_rows:
                if any(str(cell).strip() for cell in row):  # Keep row if any cell has content
                    filtered_rows.append(row)
            
            print(f"After filtering empty rows: {len(filtered_rows)} rows")
            
            max_cols = max(len(row) for row in filtered_rows) if filtered_rows else 0
            
            padded_rows = []
            for row in filtered_rows:
                padded_row = row + [''] * (max_cols - len(row))
                padded_rows.append(padded_row)
            
            columns = [f'Col_{i}' for i in range(max_cols)]
            trans_df = pd.DataFrame(padded_rows, columns=columns)
            
            # Reset index to ensure clean sequential indexing
            trans_df.reset_index(drop=True, inplace=True)
            
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
        
        # Get parent names from first column and child names from second column
        parent_names = fee_df.iloc[:, 0].dropna().tolist()
        child_names = fee_df.iloc[:, 1].dropna().tolist() if len(fee_df.columns) > 1 else []
        
        print(f"Found {len(parent_names)} parent names in fee record")
        print(f"Found {len(child_names)} child names in fee record")
        
        # Initialize both matchers
        parent_matcher = ParentMatcher(threshold=70)
        child_matcher = ChildMatcher(threshold=70)
        
        matched_count = 0
        unmatched_count = 0
        parent_matched_count = 0
        child_matched_count = 0
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
                    'matched_child': "",
                    'amount': "",                   
                    'matched': False
                })
                continue
            
            display_parent = transaction_ref
            
            # First, match parent names
            best_parent_match, parent_score = parent_matcher.match(reference_columns, parent_names)
            
            # Then, match child names using leftover text after parent removal
            # Only search among children that belong to the matched parent
            best_child_match, child_score = child_matcher.match(reference_columns, fee_df, best_parent_match)
            
            # Count matches separately
            if best_parent_match:
                parent_matched_count += 1
            if best_child_match:
                child_matched_count += 1
            
            # Determine if we consider this a successful match
            has_match = best_parent_match or best_child_match
            
            if has_match:
                matched_count += 1
            else:
                unmatched_count += 1
            
            all_results.append({
                'index': idx,
                'parent_from_transaction': display_parent,
                'matched_parent': best_parent_match.strip() if best_parent_match else "NO MATCH FOUND",
                'matched_child': best_child_match.strip() if best_child_match else "NO CHILD MATCH FOUND",
                'amount': amount,
                'matched': has_match
            })
        
        total_processed = matched_count + unmatched_count
        match_rate = (matched_count / total_processed * 100) if total_processed > 0 else 0
        parent_match_rate = (parent_matched_count / total_processed * 100) if total_processed > 0 else 0
        child_match_rate = (child_matched_count / total_processed * 100) if total_processed > 0 else 0
        
        print(f"\n=== MATCHING SUMMARY ===")
        print(f"Total transactions processed: {total_processed}")
        print(f"Successfully matched (either parent or child): {matched_count}")
        print(f"Unmatched transactions: {unmatched_count}")
        print(f"Overall match rate: {match_rate:.1f}%")
        print(f"")
        print(f"Parent matches: {parent_matched_count} ({parent_match_rate:.1f}%)")
        print(f"Child matches: {child_matched_count} ({child_match_rate:.1f}%)")
        
        separator_line = "=" * 180
        print(f"\n{separator_line}")
        print(f"{'Index':<6} | {'Parent Name (Transaction File)':<80} | {'Matched Parent (Fee Record)':<30} | {'Matched Child (Fee Record)':<30} | {'Amount':<10}")
        print(separator_line)
        
        for result in all_results:
            index = result['index']
            parent_name = str(result['parent_from_transaction'])[:79] if result['parent_from_transaction'] else ""
            matched_parent = str(result['matched_parent'])[:29] if result['matched_parent'] else ""
            matched_child = str(result['matched_child'])[:29] if result['matched_child'] else ""
            amount = result['amount']
            
            if amount == "":
                empty_line = f"{index:<6} | {'':<80} | {'':<30} | {'':<30} | {'':<10}"
                print(empty_line)
            else:
                data_line = f"{index:<6} | {parent_name:<80} | {matched_parent:<30} | {matched_child:<30} | {amount:<10.2f}"
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