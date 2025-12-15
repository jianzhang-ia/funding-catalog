"""Investigate the EXACT source of discrepancies in Geographic and Projekttraeger"""
import pandas as pd
import json

def cv(v): return v[2:-1] if isinstance(v, str) and v.startswith('="') else v

print("[INFO] Loading source CSV...")
df = pd.read_csv('Suchliste.csv', sep=';', encoding='cp1252', low_memory=False)

# Clean columns
new_cols = {}
for col in df.columns:
    clean_name = cv(col.strip())
    if '.1' not in clean_name and 'Unnamed' not in clean_name:
        new_cols[col] = clean_name
df = df[[c for c in df.columns if c in new_cols]].copy()
df.rename(columns=new_cols, inplace=True)
for col in df.columns:
    if df[col].dtype == 'object': df[col] = df[col].apply(cv)

print(f"[INFO] Total rows: {len(df):,}")

# =========================================================================
# GEOGRAPHIC INVESTIGATION
# =========================================================================
print("\n" + "="*70)
print("GEOGRAPHIC DISTRIBUTION INVESTIGATION")
print("="*70)

# Replicate the exact logic from analyze_geographic_distribution
df_de = df[df['Staat'] == 'Deutschland'].copy()
df_intl = df[df['Staat'] != 'Deutschland'].copy()

print(f"\n1. df['Staat'] == 'Deutschland': {len(df_de):,} projects")
print(f"2. df['Staat'] != 'Deutschland': {len(df_intl):,} projects")
print(f"   SUM: {len(df_de) + len(df_intl):,}")

# What values are in df_intl?
print("\n3. Value counts in df_intl (non-Deutschland) Staat column:")
intl_staat_counts = df_intl['Staat'].value_counts(dropna=False)
print(f"   Unique values: {len(intl_staat_counts)}")
print(f"   NaN count: {df_intl['Staat'].isna().sum()}")
print(f"   Empty string count: {(df_intl['Staat'] == '').sum()}")

# Show first few
print("\n   Top 10 non-DE countries:")
for staat, count in intl_staat_counts.head(10).items():
    print(f"      '{staat}': {count}")

# What gets FILTERED OUT?
empty_mask = df_intl['Staat'].isna() | (df_intl['Staat'] == '') | (df_intl['Staat'].str.strip() == '')
df_intl_empty = df_intl[empty_mask]
df_intl_valid = df_intl[~empty_mask]

print(f"\n4. In df_intl, entries with empty/null Staat: {len(df_intl_empty)}")
print(f"   In df_intl, entries with valid Staat: {len(df_intl_valid)}")

# Compare to JSON output
geo = json.load(open('web/data/geographic_distribution.json'))
de_from_json = sum(s['project_count'] for s in geo['states'])
intl_from_json = geo.get('international', {}).get('total_projects', 0)

print(f"\n5. JSON output comparison:")
print(f"   German states in JSON: {de_from_json:,}")
print(f"   International in JSON: {intl_from_json:,}")
print(f"   JSON Total: {de_from_json + intl_from_json:,}")

# The REAL issue
state_stats_total = df_de.groupby('Bundesland').agg({'FKZ': 'count'}).sum().iloc[0]
print(f"\n6. German projects by Bundesland sum: {state_stats_total:,}")

# Check for empty Bundesland
empty_bundesland = df_de[df_de['Bundesland'].isna() | (df_de['Bundesland'] == '') | (df_de['Bundesland'] == 'nan')]
print(f"   German projects with empty Bundesland: {len(empty_bundesland)}")

# =========================================================================
# PROJEKTTRÄGER INVESTIGATION
# =========================================================================
print("\n" + "="*70)
print("PROJEKTTRÄGER INVESTIGATION")
print("="*70)

# Unique PT count
print(f"\n1. Total unique PT values: {df['PT'].nunique()}")
print(f"   Total projects: {len(df):,}")

# PT value counts
pt_counts = df['PT'].value_counts(dropna=False)
print(f"\n2. PT null/empty:")
print(f"   NaN: {df['PT'].isna().sum()}")
print(f"   Empty string: {(df['PT'] == '').sum()}")

# Sum of TOP 20
top20_sum = pt_counts.head(20).sum()
print(f"\n3. Sum of projects in TOP 20 PT: {top20_sum:,}")
print(f"   Remaining: {len(df) - top20_sum:,}")

# Compare to JSON
pt_json = json.load(open('web/data/projekttraeger.json'))
pt_json_total = sum(p['project_count'] for p in pt_json['projekttraeger'])
print(f"\n4. JSON projekttraeger total: {pt_json_total:,}")

# Show what's in JSON
print(f"\n5. Projekttraeger in JSON ({len(pt_json['projekttraeger'])} entries):")
for p in pt_json['projekttraeger'][:5]:
    print(f"   {p['code']}: {p['project_count']:,} projects")
print("   ...")

# =========================================================================
# SUMMARY
# =========================================================================
print("\n" + "="*70)
print("ROOT CAUSE SUMMARY")
print("="*70)

print("""
GEOGRAPHIC DISCREPANCY:
- The code filters df['Staat'] == 'Deutschland' for German states
- Empty Staat values are in df_intl but get filtered out in output
- Also, German projects with empty Bundesland are filtered out

PROJEKTTRÄGER DISCREPANCY:
- The code only outputs TOP 20 Projekttraeger (.head(20))
- Projects handled by less common PTs are not counted
- This is by design (for chart readability) but affects validation
""")
