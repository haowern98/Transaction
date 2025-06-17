import pandas as pd
import numpy as np
import openpyxl
from matchers import ParentMatcher, ChildMatcher

def process_fee_matching_gui(fee_record_file, transaction_file):
    """
    Process fee matching for GUI - returns structured data
    
    Args:
        fee_record_file (str): Path to the fee record Excel file
        transaction_file (str): Path to the transaction CSV file
    
    Returns:
        dict: Dictionary containing results and statistics
    """
    try:
        # Read fee record file
        fee_df = pd.read_excel(fee_record_file)
        
        # Read transaction file
        import csv
        all_rows = []
        with open(transaction_file, 'r', encoding='utf-8', newline='') as f:
            csv_reader = csv.reader(f)
            for row_num, row in enumerate(csv_reader):
                all_rows.append(row)
        
        # Remove completely empty rows
        filtered_rows = []
        for row in all_rows:
            if any(str(cell).strip() for cell in row):
                filtered_rows.append(row)
        
        max_cols = max(len(row) for row in filtered_rows) if filtered_rows else 0
        
        padded_rows = []
        for row in filtered_rows:
            padded_row = row + [''] * (max_cols - len(row))
            padded_rows.append(padded_row)
        
        columns = [f'Col_{i}' for i in range(max_cols)]
        trans_df = pd.DataFrame(padded_rows, columns=columns)
        trans_df.reset_index(drop=True, inplace=True)
        
        # Get parent and child names
        parent_names = fee_df.iloc[:, 0].dropna().tolist()
        child_names = fee_df.iloc[:, 1].dropna().tolist() if len(fee_df.columns) > 1 else []
        
        # Initialize matchers
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
            
            # Extract reference columns
            reference_columns = []
            for col_idx in [5, 6, 7, 8]:
                if len(trans_df.columns) > col_idx:
                    col_name = f'Col_{col_idx}'
                    col_val = row[col_name]
                    if pd.notna(col_val) and str(col_val).strip():
                        reference_columns.append(str(col_val))
            
            if reference_columns:
                transaction_ref = " | ".join(reference_columns)
            
            # Extract amount
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
            
            # Match parent names
            best_parent_match, parent_score = parent_matcher.match(reference_columns, parent_names)
            
            # Match child names
            best_child_match, child_score = child_matcher.match(reference_columns, fee_df, best_parent_match)
            
            # Count matches
            if best_parent_match:
                parent_matched_count += 1
            if best_child_match:
                child_matched_count += 1
            
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
        
        # Return results dictionary
        return {
            'results': all_results,
            'total_processed': total_processed,
            'matched_count': matched_count,
            'unmatched_count': unmatched_count,
            'parent_matched_count': parent_matched_count,
            'child_matched_count': child_matched_count,
            'parent_names_count': len(parent_names),
            'child_names_count': len(child_names)
        }
        
    except Exception as e:
        raise Exception(f"Processing error: {str(e)}")


# Keep the original function for backward compatibility if needed
def process_fee_matching():
    """Original console version - now just calls GUI version with hardcoded paths"""
    fee_record_file = r"C:\Users\user\Downloads\Parent-Student Matching Pair.xlsx"
    transaction_file = r"C:\Users\user\Downloads\Fee Statements\3985094904Statement (9).csv"
    
    try:
        results = process_fee_matching_gui(fee_record_file, transaction_file)
        
        # Simple summary output (no table)
        print(f"Processing completed:")
        print(f"Total: {results['total_processed']}")
        print(f"Matched: {results['matched_count']}")
        print(f"Unmatched: {results['unmatched_count']}")
        print(f"Match rate: {(results['matched_count']/results['total_processed']*100):.1f}%")
        
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


if __name__ == "__main__":
    print("Use gui_launcher.py to start the GUI application")
    print("Or call process_fee_matching_gui() directly from your code")