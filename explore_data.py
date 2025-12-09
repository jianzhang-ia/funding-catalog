"""
Script to explore the Suchliste.csv dataset structure
"""
import pandas as pd

output_lines = []

def log(text):
    print(text)
    output_lines.append(text)

# Read raw header
with open('Suchliste.csv', 'r', encoding='cp1252') as f:
    header = f.readline()
    cols = header.strip().split(';')
    log("Raw columns:")
    for i, col in enumerate(cols):
        log(f'{i}: {col}')
    log(f'\nTotal columns: {len(cols)}')

log("\n" + "="*50 + "\n")

# Read a sample line to understand format
with open('Suchliste.csv', 'r', encoding='cp1252') as f:
    lines = [f.readline() for _ in range(5)]
    log("First 5 lines:")
    for i, line in enumerate(lines):
        log(f"Line {i}: {line[:200]}...")

log("\n" + "="*50 + "\n")

# Clean the column names (remove =" and ")
def clean_csv():
    """Read the CSV and clean the ="" format"""
    df = pd.read_csv('Suchliste.csv', sep=';', encoding='cp1252', low_memory=False)
    
    # Clean column names
    new_cols = {}
    for col in df.columns:
        clean_name = col.strip()
        if clean_name.startswith('="') and clean_name.endswith('"'):
            clean_name = clean_name[2:-1]
        new_cols[col] = clean_name
    df.rename(columns=new_cols, inplace=True)
    
    # Clean values (remove =" and ")
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(lambda x: str(x)[2:-1] if isinstance(x, str) and str(x).startswith('="') and str(x).endswith('"') else x)
    
    return df

log("Loading and cleaning data...")
df = clean_csv()

log("\nCleaned columns:")
for i, col in enumerate(df.columns):
    log(f'{i}: {col}')

log(f'\nDataFrame shape: {df.shape}')
log(f'Total projects: {len(df):,}')

log("\nColumn data types:")
for col in df.columns:
    log(f'  {col}: {df[col].dtype}')

log("\nSample data (first 3 rows):")
log(df.head(3).to_string())

# Basic statistics
log("\n" + "="*50)
log("BASIC STATISTICS")
log("="*50)

log(f"\nUnique ministries (Ressort): {df['Ressort'].nunique()}")
log(df['Ressort'].value_counts().to_string())

log(f"\nUnique states (Bundesland): {df['Bundesland'].nunique()}")
log(df['Bundesland'].value_counts().head(20).to_string())

# Save output
with open('explore_output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))
    
log("\nOutput saved to explore_output.txt")
