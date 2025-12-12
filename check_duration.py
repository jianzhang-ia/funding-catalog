"""Check DurationMonths completeness"""
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

def parse_date(val):
    try:
        parts = str(val).split('.')
        if len(parts) == 3:
            return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
    except:
        pass
    return None

df['StartDate'] = df['Laufzeit von'].apply(parse_date)
df['EndDate'] = df['Laufzeit bis'].apply(parse_date)

def calc_duration(row):
    if row['StartDate'] and row['EndDate']:
        delta = row['EndDate'] - row['StartDate']
        return max(delta.days / 30.44, 0)
    return None

df['DurationMonths'] = df.apply(calc_duration, axis=1)

total = len(df)
valid = df['DurationMonths'].notna().sum()
missing = total - valid

print(f'Total projects: {total:,}')
print(f'With valid DurationMonths: {valid:,} ({100*valid/total:.2f}%)')
print(f'Missing DurationMonths: {missing:,} ({100*missing/total:.2f}%)')

if missing > 0:
    print('\nSample entries with missing duration:')
    missing_df = df[df['DurationMonths'].isna()].head(5)
    for _, row in missing_df.iterrows():
        print(f"  - Start: '{row['Laufzeit von']}', End: '{row['Laufzeit bis']}', FKZ: {row['FKZ']}")
