"""
CSV cleaning utility for processing model outputs.
Combines functionality from cleanup.py and cleanup_claude.py
"""
import pandas as pd
import re
import os

def extract_number_from_cell(cell):
    """Extract a number from a cell value."""
    if pd.isna(cell):
        return None
        
    # If cell is already a number
    if isinstance(cell, (int, float)):
        return int(cell)
    
    # Convert to string and clean
    cell_str = str(cell).strip().strip('"')
    
    # Try to find any number at the start of string
    match = re.match(r'\d+', cell_str)
    if match:
        return int(match.group(0))
    
    # If no match at start, try to find any number in the string
    match = re.findall(r'\d+', cell_str)
    if match:
        return int(match[0])
    
    return None

def clean_csv(input_file, output_file):
    """Clean a CSV file by extracting numeric scores."""
    print(f"Processing: {input_file}")
    
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # Create new dataframe with Model and Iteration
    cleaned_df = pd.DataFrame()
    cleaned_df['Model'] = df['Model']
    cleaned_df['Iteration'] = df['Iteration']
    
    # Initialize Q1-Q17 columns
    for i in range(1, 18):
        cleaned_df[f'Q{i}'] = None

    # Process each row
    for idx, row in df.iterrows():
        numbers = []
        
        # Check if this is a Claude model (different parsing needed)
        is_claude = 'claude' in str(row['Model']).lower() or 'anthropic' in input_file.lower()
        
        if is_claude:
            # Claude format: look for numbers in columns after text
            for col in df.columns[3:]:  # Skip Model, Iteration, and text columns
                if pd.notna(row[col]):
                    try:
                        num = int(float(row[col]))
                        numbers.append(num)
                    except (ValueError, TypeError):
                        continue
        else:
            # OpenAI/Mistral format: extract numbers from all columns
            for col in df.columns[2:]:  # Skip Model and Iteration columns
                num = extract_number_from_cell(row[col])
                if num is not None:
                    numbers.append(num)
        
        # Assign numbers to columns
        if len(numbers) >= 17:
            for i, num in enumerate(numbers[:17], 1):  # Take first 17 numbers
                cleaned_df.at[idx, f'Q{i}'] = num
        else:
            print(f"Warning: Row {idx} has {len(numbers)} numbers instead of 17")
            print(f"Numbers found: {numbers}")

    # Convert all question columns to Int64
    for i in range(1, 18):
        cleaned_df[f'Q{i}'] = cleaned_df[f'Q{i}'].astype('Int64')
    
    # Save to new CSV file
    cleaned_df.to_csv(output_file, index=False)
    print(f"Cleaned data saved to: {output_file}")

def main():
    """Main function to clean all CSV files."""
    # Process both OpenAI and Claude folders
    input_folders = ['output_csvs_openai', 'output_csvs_anthropic']
    output_folders = ['output_csvs_openai_cleaned', 'output_csvs_anthropic_cleaned']

    for input_folder, output_folder in zip(input_folders, output_folders):
        if not os.path.exists(input_folder):
            print(f"Warning: {input_folder} does not exist, skipping...")
            continue
            
        os.makedirs(output_folder, exist_ok=True)
        
        csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]
        if not csv_files:
            print(f"No CSV files found in {input_folder}")
            continue
            
        print(f"Processing {len(csv_files)} files from {input_folder}")
        
        for filename in csv_files:
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            try:
                clean_csv(input_path, output_path)
            except Exception as e:
                print(f"Error cleaning {filename}: {str(e)}")

if __name__ == "__main__":
    main()
