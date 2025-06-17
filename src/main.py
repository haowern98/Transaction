import pandas as pd
import numpy as np
import openpyxl
from matchers import ParentMatcher

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
        
        # Initialize the parent matcher
        parent_matcher = ParentMatcher(threshold=70)
        
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
            
            display_parent = transaction_ref
            
            # Use the parent matcher class
            best_match, best_score = parent_matcher.match(reference_columns, parent_names)
            
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
        
        separator_line = "=" * 130
        print(f"\n{separator_line}")
        print(f"{'Index':<6} | {'Parent Name (Transaction File)':<60} | {'Matched Name (Fee Record)':<40} | {'Amount':<10}")
        print(separator_line)
        
        for result in all_results:
            index = result['index']
            parent_name = str(result['parent_from_transaction'])[:59] if result['parent_from_transaction'] else ""
            matched_name = str(result['matched_parent'])[:39] if result['matched_parent'] else ""
            amount = result['amount']
            
            if amount == "":
                empty_line = f"{index:<6} | {'':<60} | {'':<40} | {'':<10}"
                print(empty_line)
            else:
                data_line = f"{index:<6} | {parent_name:<60} | {matched_name:<40} | {amount:<10.2f}"
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