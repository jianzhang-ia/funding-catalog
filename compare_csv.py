"""Compare Suchliste.csv with Suchliste_updated.csv to understand new entry patterns"""
import pandas as pd
from datetime import datetime

def clean_val(v):
    if isinstance(v, str) and v.startswith('="') and v.endswith('"'):
        return v[2:-1]
    return v

# Load both CSVs
print("="*60)
print("COMPARING CSV FILES")
print("="*60)

df_old = pd.read_csv('Suchliste.csv', sep=';', encoding='cp1252', low_memory=False)
df_new = pd.read_csv('Suchliste_updated.csv', sep=';', encoding='cp1252', low_memory=False)

print(f"\nOld file: {len(df_old):,} rows")
print(f"New file: {len(df_new):,} rows")
print(f"Difference: {len(df_new) - len(df_old):,} rows")

# Clean columns
for df in [df_old, df_new]:
    new_cols = {}
    for col in df.columns:
        clean_name = col.strip()
        if clean_name.startswith('="') and clean_name.endswith('"'):
            clean_name = clean_name[2:-1]
        if '.1' not in clean_name and 'Unnamed' not in clean_name:
            new_cols[col] = clean_name
    cols_to_keep = [c for c in df.columns if c in new_cols]
    df.drop([c for c in df.columns if c not in cols_to_keep], axis=1, inplace=True)
    df.rename(columns=new_cols, inplace=True)
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(clean_val)

print(f"\nColumns: {list(df_old.columns)[:10]}...")

# Find unique identifier - likely FKZ (Förderkennzeichen)
print("\n" + "-"*40)
print("IDENTIFYING UNIQUE KEY")
print("-"*40)

# Check if FKZ is unique
fkz_unique_old = df_old['FKZ'].nunique()
fkz_total_old = len(df_old)
print(f"FKZ unique values in old: {fkz_unique_old:,} / {fkz_total_old:,}")

fkz_unique_new = df_new['FKZ'].nunique()
fkz_total_new = len(df_new)
print(f"FKZ unique values in new: {fkz_unique_new:,} / {fkz_total_new:,}")

# Find entries in new that are not in old
old_fkz_set = set(df_old['FKZ'].dropna())
new_fkz_set = set(df_new['FKZ'].dropna())

new_entries_fkz = new_fkz_set - old_fkz_set
removed_entries_fkz = old_fkz_set - new_fkz_set

print(f"\nNew FKZ entries: {len(new_entries_fkz):,}")
print(f"Removed FKZ entries: {len(removed_entries_fkz):,}")

# Get the actual new rows
if len(new_entries_fkz) > 0:
    new_rows = df_new[df_new['FKZ'].isin(new_entries_fkz)]
    
    print("\n" + "-"*40)
    print("NEW ENTRIES ANALYSIS")
    print("-"*40)
    
    print(f"\nNew entries: {len(new_rows):,}")
    
    # Check which columns might indicate "newness"
    print("\nSample of new entries (first 5):")
    for i, (_, row) in enumerate(new_rows.head(5).iterrows()):
        print(f"\n  Entry {i+1}:")
        print(f"    FKZ: {row['FKZ']}")
        print(f"    Thema: {row['Thema'][:50] if row['Thema'] else 'N/A'}...")
        print(f"    Laufzeit von: {row['Laufzeit von']}")
        print(f"    Laufzeit bis: {row['Laufzeit bis']}")
        print(f"    Ressort: {row['Ressort']}")
        print(f"    Zuwendungsempfänger: {row['Zuwendungsempfänger'][:50] if row['Zuwendungsempfänger'] else 'N/A'}")
    
    # Look for patterns in FKZ numbers
    print("\n" + "-"*40)
    print("FKZ PATTERN ANALYSIS")
    print("-"*40)
    
    # Check if FKZ has any ordering pattern
    # FKZ often looks like: 01KI20001 or 03EE5048A
    sample_old = sorted(list(old_fkz_set))[-20:]
    sample_new = sorted(list(new_entries_fkz))[:20] if new_entries_fkz else []
    
    print("\nLast 10 FKZ from old file (sorted):")
    for fkz in sample_old[-10:]:
        print(f"  {fkz}")
    
    print("\nFirst 10 new FKZ entries (sorted):")
    for fkz in list(sample_new)[:10]:
        print(f"  {fkz}")
    
    # Check row ordering
    print("\n" + "-"*40)
    print("ROW ORDERING ANALYSIS")
    print("-"*40)
    
    # Check if new entries are at the end
    new_rows_indices = df_new[df_new['FKZ'].isin(new_entries_fkz)].index.tolist()
    if new_rows_indices:
        print(f"New entries index positions: min={min(new_rows_indices)}, max={max(new_rows_indices)}")
        print(f"Total rows in new file: {len(df_new)}")
        
        if max(new_rows_indices) == len(df_new) - 1:
            print("  -> New entries appear to be appended at the END")
        elif min(new_rows_indices) == 0:
            print("  -> New entries appear to be prepended at the BEGINNING")
        else:
            print("  -> New entries are scattered throughout the file")
    
    # Check for any date-like columns we might have missed
    print("\n" + "-"*40)
    print("ALL COLUMNS IN DATA")
    print("-"*40)
    for col in df_new.columns:
        print(f"  {col}")

else:
    print("\nNo new entries found! Files may be identical.")

print("\n" + "="*60)
print("CONCLUSION")
print("="*60)
