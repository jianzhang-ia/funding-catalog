"""Comprehensive data completeness check"""
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

def parse_duration(row):
    try:
        start = parse_date(row['Laufzeit von'])
        end = parse_date(row['Laufzeit bis'])
        if start and end:
            return (end.year - start.year) * 12 + (end.month - start.month)
    except:
        pass
    return None

total = len(df)
print(f"TOTAL PROJECTS: {total:,}")
print("=" * 60)

# 2. Countries other than Deutschland?
print("\n[2] COUNTRIES (Staat column)")
print("-" * 40)
countries = df['Staat'].value_counts()
print(f"Unique values: {len(countries)}")
for country, count in countries.items():
    pct = 100 * count / total
    print(f"  {country}: {count:,} ({pct:.2f}%)")

# 3/6/7. Valid years?
print("\n[3/6/7] VALID START YEARS")
print("-" * 40)
df['StartDate'] = df['Laufzeit von'].apply(parse_date)
df['StartYear'] = df['StartDate'].apply(lambda x: x.year if x else None)
valid_years = df['StartYear'].notna().sum()
missing_years = total - valid_years
print(f"With valid StartYear: {valid_years:,} ({100*valid_years/total:.2f}%)")
print(f"Missing StartYear: {missing_years:,} ({100*missing_years/total:.2f}%)")
if missing_years > 0:
    print("\nSample entries with missing year:")
    missing = df[df['StartYear'].isna()].head(3)
    for _, row in missing.iterrows():
        print(f"  - Laufzeit von: '{row['Laufzeit von']}', FKZ: {row['FKZ']}")

# 8. Valid duration?
print("\n[8] VALID DURATION DATA")
print("-" * 40)
df['DurationMonths'] = df.apply(parse_duration, axis=1)
valid_duration = (df['DurationMonths'].notna() & (df['DurationMonths'] > 0)).sum()
missing_duration = total - valid_duration
print(f"With valid DurationMonths > 0: {valid_duration:,} ({100*valid_duration/total:.2f}%)")
print(f"Missing/invalid duration: {missing_duration:,} ({100*missing_duration/total:.2f}%)")
if missing_duration > 0:
    print("\nSample entries with missing/invalid duration:")
    invalid = df[~(df['DurationMonths'].notna() & (df['DurationMonths'] > 0))].head(3)
    for _, row in invalid.iterrows():
        print(f"  - Laufzeit von: '{row['Laufzeit von']}', bis: '{row['Laufzeit bis']}', FKZ: {row['FKZ']}")

# 5. How many Thema entries?
print("\n[5] THEMA (project titles) ENTRIES")
print("-" * 40)
thema_count = df['Thema'].notna().sum()
print(f"With Thema: {thema_count:,} ({100*thema_count/total:.2f}%)")
print(f"Current sample limit: 50,000 (should process all {thema_count:,})")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
