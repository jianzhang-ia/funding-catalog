"""Check missing month data percentage"""
import pandas as pd
from datetime import datetime

df = pd.read_csv('Suchliste.csv', sep=';', encoding='cp1252', low_memory=False)

def clean_val(v):
    if isinstance(v, str) and v.startswith('="') and v.endswith('"'):
        return v[2:-1]
    return v

df.columns = [clean_val(c.strip()) for c in df.columns]
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].apply(clean_val)

# Parse dates
def parse_date(val):
    try:
        val = clean_val(str(val))
        parts = val.split('.')
        if len(parts) == 3:
            return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
    except:
        pass
    return None

df['StartDate'] = df['Laufzeit von'].apply(parse_date)
df['StartMonth'] = df['StartDate'].apply(lambda x: x.month if x else None)

total = len(df)
with_month = df['StartMonth'].notna().sum()
missing = total - with_month

print(f"Total projects: {total:,}")
print(f"With valid StartMonth: {with_month:,} ({100*with_month/total:.2f}%)")
print(f"Missing StartMonth: {missing:,} ({100*missing/total:.2f}%)")

# Show sample of missing dates
print("\nSample entries with missing month:")
missing_df = df[df['StartMonth'].isna()].head(5)
for _, row in missing_df.iterrows():
    print(f"  - Laufzeit von: '{row['Laufzeit von']}', FKZ: {row['FKZ']}")
