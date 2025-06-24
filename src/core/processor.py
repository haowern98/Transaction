"""
Core processing logic for fee matching
Handles the main business logic for matching transaction data to fee records
"""
import csv
import pandas as pd
from matchers import ParentMatcher, ChildMatcher, MonthMatcher


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
        
        # Read and process transaction file
        trans_df = _read_transaction_file(transaction_file)
        
        # Get parent and child names from fee record
        parent_names = fee_df.iloc[:, 0].dropna().tolist()
        child_names = fee_df.iloc[:, 1].dropna().tolist() if len(fee_df.columns) > 1 else []
        
        # Initialize matchers
        parent_matcher = ParentMatcher(threshold=70)
        child_matcher = ChildMatcher(threshold=70)
        month_matcher = MonthMatcher(threshold=70)
        
        # Process each transaction
        results = _process_transactions(trans_df, fee_df, parent_matcher, child_matcher, month_matcher, parent_names)
        
        # Calculate statistics
        stats = _calculate_statistics(results)
        
        return {
            'results': results,
            **stats,
            'parent_names_count': len(parent_names),
            'child_names_count': len(child_names)
        }
        
    except Exception as e:
        raise Exception(f"Processing error: {str(e)}")


def _read_transaction_file(transaction_file):
    """Read and normalize transaction CSV file"""
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
    
    # Normalize row lengths
    max_cols = max(len(row) for row in filtered_rows) if filtered_rows else 0
    padded_rows = []
    for row in filtered_rows:
        padded_row = row + [''] * (max_cols - len(row))
        padded_rows.append(padded_row)
    
    # Create DataFrame
    columns = [f'Col_{i}' for i in range(max_cols)]
    trans_df = pd.DataFrame(padded_rows, columns=columns)
    trans_df.reset_index(drop=True, inplace=True)
    
    return trans_df


def _process_transactions(trans_df, fee_df, parent_matcher, child_matcher, month_matcher, parent_names):
    """Process each transaction row and perform matching"""
    all_results = []
    
    for idx, row in trans_df.iterrows():
        # Extract transaction data
        transaction_date = _extract_transaction_date(row, trans_df.columns)
        reference_columns = _extract_reference_columns(row, trans_df.columns)
        amount = _extract_amount(row, trans_df.columns)
        
        # Skip if no meaningful transaction reference
        if not any(ref.strip() for ref in reference_columns):
            continue
        
        # Skip if no valid amount
        if amount <= 0:
            all_results.append(_create_empty_result(idx, "", "", 0))
            continue
        
        # Create display reference
        transaction_ref = " | ".join(ref for ref in reference_columns if ref.strip())
        
        # Perform matching
        best_parent_match, parent_score = parent_matcher.match(reference_columns, parent_names)
        best_child_match, child_score = child_matcher.match(reference_columns, fee_df, best_parent_match)
        extracted_month, month_score = month_matcher.match(reference_columns, transaction_date)
        
        # Create result
        has_match = best_parent_match or best_child_match
        result = {
            'index': idx,
            'parent_from_transaction': transaction_ref,
            'transaction_date': transaction_date,
            'matched_parent': best_parent_match.strip() if best_parent_match else "NO MATCH FOUND",
            'matched_child': best_child_match.strip() if best_child_match else "NO CHILD MATCH FOUND",
            'month_paying_for': extracted_month if extracted_month else "NO MONTH FOUND",
            'amount': amount,
            'matched': has_match
        }
        
        all_results.append(result)
    
    return all_results


def _extract_transaction_date(row, columns):
    """Extract transaction date from first column"""
    if len(columns) > 0:
        date_val = row['Col_0']
        if pd.notna(date_val) and str(date_val).strip():
            raw_date = str(date_val).strip()
            # Clean Excel formatting
            if raw_date.startswith('="'):
                raw_date = raw_date[2:]
            if raw_date.endswith('"'):
                raw_date = raw_date[:-1]
            # Skip header rows
            if raw_date == "Trn. Date":
                return ""
            return raw_date
    return ""


def _extract_reference_columns(row, columns):
    """Extract reference data from columns 5-8"""
    reference_columns = []
    for col_idx in [5, 6, 7, 8]:
        if len(columns) > col_idx:
            col_name = f'Col_{col_idx}'
            col_val = row[col_name]
            if pd.notna(col_val) and str(col_val).strip():
                reference_columns.append(str(col_val))
    return reference_columns


def _extract_amount(row, columns):
    """Extract amount from column 4"""
    if len(columns) > 4:
        col_4_val = row['Col_4']
        if pd.notna(col_4_val) and str(col_4_val).strip():
            amount_str = str(col_4_val)
            try:
                amount_str = amount_str.replace(',', '').replace('$', '').replace('RM', '').strip()
                if amount_str and amount_str != 'nan':
                    return float(amount_str)
            except (ValueError, AttributeError):
                pass
    return 0


def _create_empty_result(idx, parent_from_transaction, transaction_date, amount):
    """Create an empty result record"""
    return {
        'index': idx,
        'parent_from_transaction': parent_from_transaction,
        'transaction_date': transaction_date,
        'matched_parent': "",
        'matched_child': "",
        'month_paying_for': "",
        'amount': amount,
        'matched': False
    }


def _calculate_statistics(results):
    """Calculate matching statistics"""
    total_processed = len(results)
    matched_count = sum(1 for r in results if r['matched'])
    unmatched_count = total_processed - matched_count
    parent_matched_count = sum(1 for r in results if r['matched_parent'] != "NO MATCH FOUND" and r['matched_parent'])
    child_matched_count = sum(1 for r in results if r['matched_child'] != "NO CHILD MATCH FOUND" and r['matched_child'])
    
    return {
        'total_processed': total_processed,
        'matched_count': matched_count,
        'unmatched_count': unmatched_count,
        'parent_matched_count': parent_matched_count,
        'child_matched_count': child_matched_count
    }


def process_fee_matching():
    """Console version - calls GUI version with hardcoded paths"""
    fee_record_file = r"C:\Users\user\Downloads\Parent-Student Matching Pair.xlsx"
    transaction_file = r"C:\Users\user\Downloads\Fee Statements\3985094904Statement (9).csv"
    
    try:
        results = process_fee_matching_gui(fee_record_file, transaction_file)
        
        # Simple summary output
        print(f"Processing completed:")
        print(f"Total: {results['total_processed']}")
        print(f"Matched: {results['matched_count']}")
        print(f"Unmatched: {results['unmatched_count']}")
        print(f"Match rate: {(results['matched_count']/results['total_processed']*100):.1f}%")
        
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False