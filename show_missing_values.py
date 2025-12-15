"""Show sample entries with missing values for manual verification"""
import pandas as pd

def clean_val(v):
    if isinstance(v, str) and v.startswith('="') and v.endswith('"'):
        return v[2:-1]
    return v

print("[INFO] Loading source CSV...")
df = pd.read_csv('Suchliste.csv', sep=';', encoding='cp1252', low_memory=False)

# Clean columns
new_cols = {}
for col in df.columns:
    clean_name = col.strip()
    if clean_name.startswith('="') and clean_name.endswith('"'):
        clean_name = clean_name[2:-1]
    if '.1' not in clean_name and 'Unnamed' not in clean_name:
        new_cols[col] = clean_name

cols_to_keep = [c for c in df.columns if c in new_cols]
df = df[cols_to_keep].copy()
df.rename(columns=new_cols, inplace=True)

for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].apply(clean_val)

print(f"[INFO] Total rows: {len(df):,}")

# =========================================================================
# 1. GEOGRAPHIC - Missing Staat (Country)
# =========================================================================
print("\n" + "="*70)
print("1. GEOGRAPHIC - Projects with missing Staat (Country)")
print("="*70)

# Check for null/empty
geo_missing = df[df['Staat'].isna() | (df['Staat'] == '') | (df['Staat'].str.strip() == '')]
print(f"\nTotal missing: {len(geo_missing)}")

if len(geo_missing) > 0:
    print("\nSample entries (first 10):")
    print("-"*70)
    cols_to_show = ['FKZ', 'Staat', 'Bundesland', 'Ort', 'Zuwendungsempfänger', 'Thema']
    for i, (_, row) in enumerate(geo_missing.head(10).iterrows()):
        print(f"\nEntry {i+1}:")
        print(f"  FKZ: {row['FKZ']}")
        print(f"  Staat: '{row['Staat']}' (empty/null)")
        print(f"  Bundesland: {row['Bundesland']}")
        print(f"  Ort: {row['Ort']}")
        print(f"  Empfänger: {str(row['Zuwendungsempfänger'])[:60]}...")
        print(f"  Thema: {str(row['Thema'])[:60]}...")

# =========================================================================
# 2. FÖRDERPROFIL - Missing Funding Profile
# =========================================================================
print("\n" + "="*70)
print("2. FÖRDERPROFIL - Projects with missing Förderprofil")
print("="*70)

fp_missing = df[df['Förderprofil'].isna() | (df['Förderprofil'] == '') | (df['Förderprofil'].str.strip() == '')]
print(f"\nTotal missing: {len(fp_missing)}")

if len(fp_missing) > 0:
    print("\nSample entries (first 10):")
    print("-"*70)
    for i, (_, row) in enumerate(fp_missing.head(10).iterrows()):
        print(f"\nEntry {i+1}:")
        print(f"  FKZ: {row['FKZ']}")
        print(f"  Förderprofil: '{row['Förderprofil']}' (empty/null)")
        print(f"  Ressort: {row['Ressort']}")
        print(f"  Empfänger: {str(row['Zuwendungsempfänger'])[:60]}...")
        print(f"  Thema: {str(row['Thema'])[:60]}...")

# =========================================================================
# 3. PROJEKTTRÄGER - Missing PT
# =========================================================================
print("\n" + "="*70)
print("3. PROJEKTTRÄGER - Projects with missing PT")
print("="*70)

pt_missing = df[df['PT'].isna() | (df['PT'] == '') | (df['PT'].str.strip() == '')]
print(f"\nTotal missing: {len(pt_missing)}")

if len(pt_missing) > 0:
    print("\nSample entries (first 10):")
    print("-"*70)
    for i, (_, row) in enumerate(pt_missing.head(10).iterrows()):
        print(f"\nEntry {i+1}:")
        print(f"  FKZ: {row['FKZ']}")
        print(f"  PT: '{row['PT']}' (empty/null)")
        print(f"  Ressort: {row['Ressort']}")
        print(f"  Empfänger: {str(row['Zuwendungsempfänger'])[:60]}...")
        print(f"  Thema: {str(row['Thema'])[:60]}...")

# =========================================================================
# Summary
# =========================================================================
print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"\nTotal projects: {len(df):,}")
print(f"Missing Staat: {len(geo_missing):,}")
print(f"Missing Förderprofil: {len(fp_missing):,}")
print(f"Missing PT: {len(pt_missing):,}")
