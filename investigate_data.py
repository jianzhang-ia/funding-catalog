"""
Investigate invalid dates and verify recipient data
"""
import pandas as pd

# Load data
df = pd.read_csv('Suchliste.csv', sep=';', encoding='cp1252', low_memory=False)

def clean_val(v):
    if isinstance(v, str) and v.startswith('="') and v.endswith('"'):
        return v[2:-1]
    return v

df.columns = [clean_val(c.strip()) for c in df.columns]
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].apply(clean_val)

# Parse funding
def parse_num(v):
    try:
        v = clean_val(str(v))
        return float(v.replace('.', '').replace(',', '.'))
    except:
        return 0

df['Funding'] = df['Fördersumme in EUR'].apply(parse_num)

# Parse dates
def parse_date(v):
    try:
        v = clean_val(str(v))
        parts = v.split('.')
        if len(parts) == 3:
            return int(parts[2])  # Return year
    except:
        pass
    return None

df['StartYear'] = df['Laufzeit von'].apply(parse_date)

print("=" * 70)
print("INVESTIGATION: Invalid Dates and Recipient Verification")
print("=" * 70)

# ==================================================
# 1. Show examples of invalid/out-of-range dates
# ==================================================
print("\n[1] INVALID/OUT-OF-RANGE DATES")
print("-" * 50)

# Projects with no valid year
no_year = df[df['StartYear'].isna()]
print(f"Projects with missing/invalid start dates: {len(no_year):,}")

# Show examples
print("\nExamples of invalid dates:")
sample = no_year.head(5)
for _, row in sample.iterrows():
    print(f"  - Date: '{row['Laufzeit von']}', FKZ: {row['FKZ']}, Funding: {row['Funding']:,.0f}")

# Projects before 1990
old = df[(df['StartYear'].notna()) & (df['StartYear'] < 1990)]
print(f"\nProjects with start year before 1990: {len(old):,}")
if len(old) > 0:
    sample = old.head(5)
    for _, row in sample.iterrows():
        print(f"  - Year: {int(row['StartYear'])}, FKZ: {row['FKZ']}, Funding: {row['Funding']:,.0f}")

# Projects after 2030
future = df[(df['StartYear'].notna()) & (df['StartYear'] > 2030)]
print(f"\nProjects with start year after 2030: {len(future):,}")
if len(future) > 0:
    sample = future.head(5)
    for _, row in sample.iterrows():
        print(f"  - Year: {int(row['StartYear'])}, FKZ: {row['FKZ']}, Funding: {row['Funding']:,.0f}")

# ==================================================
# 2. Verify the specific recipient
# ==================================================
print("\n" + "=" * 70)
print("[2] RECIPIENT VERIFICATION: Ministerium für Kultur und Wissenschaft")
print("-" * 70)

# Find this recipient
r_df = df[df['Zuwendungsempfänger'].str.contains('Ministerium für Kultur und Wissenschaft', na=False)]
print(f"Found {len(r_df)} projects for this recipient")

print("\nAll projects for this recipient:")
for _, row in r_df.iterrows():
    print(f"  - Start: {row['Laufzeit von']}, Year: {row['StartYear']}, Funding: {row['Funding']:,.0f} EUR")
    print(f"    FKZ: {row['FKZ']}")
    print(f"    Thema: {str(row['Thema'])[:80]}...")
    print()

# Group by year
print("\nGrouped by year:")
yearly = r_df.groupby('StartYear').agg({
    'Funding': 'sum',
    'FKZ': 'count'
}).reset_index()
yearly.columns = ['Year', 'Funding', 'Projects']
for _, row in yearly.iterrows():
    print(f"  Year {int(row['Year'])}: {int(row['Projects'])} project(s), {row['Funding']:,.0f} EUR")
