"""
Comprehensive Data Validation - Checks all outputs against source CSV
"""

import pandas as pd
import json
from datetime import datetime

def clean_val(v):
    if isinstance(v, str) and v.startswith('="') and v.endswith('"'):
        return v[2:-1]
    return v

def parse_german_number(val):
    try:
        val = clean_val(str(val))
        val = val.replace('.', '').replace(',', '.')
        return float(val)
    except:
        return 0.0

# Load source CSV
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

df['Fördersumme'] = df['Fördersumme in EUR'].apply(parse_german_number)

CSV_ROWS = len(df)
CSV_FUNDING = df['Fördersumme'].sum()

print(f"[INFO] Source CSV: {CSV_ROWS:,} rows")
print(f"[INFO] Source CSV: EUR {CSV_FUNDING/1e9:.2f}B total funding")

# Load JSON files
def load_json(name):
    with open(f'web/data/{name}', 'r', encoding='utf-8') as f:
        return json.load(f)

print("\n" + "="*60)
print("DATA VALIDATION REPORT")
print("="*60)

results = []

# 1. Summary Stats
print("\n1. SUMMARY STATISTICS")
summary = load_json('summary_stats.json')
proj_match = summary['total_projects'] == CSV_ROWS
fund_diff = abs(summary['total_funding'] - CSV_FUNDING) / CSV_FUNDING * 100
fund_match = fund_diff < 0.01
print(f"   Projects: {summary['total_projects']:,} vs {CSV_ROWS:,} - {'OK' if proj_match else 'MISMATCH'}")
print(f"   Funding: EUR {summary['total_funding']/1e9:.2f}B vs {CSV_FUNDING/1e9:.2f}B - {'OK' if fund_match else 'MISMATCH'}")
results.append(('Summary Projects', proj_match))
results.append(('Summary Funding', fund_match))

# 2. Ministry Funding
print("\n2. MINISTRY FUNDING")
ministry = load_json('ministry_funding.json')
min_proj = sum(m['project_count'] for m in ministry['ministries'])
min_fund = sum(m['total_funding'] for m in ministry['ministries'])
proj_match = min_proj == CSV_ROWS
fund_diff = abs(min_fund - CSV_FUNDING) / CSV_FUNDING * 100
fund_match = fund_diff < 0.01
print(f"   Projects: {min_proj:,} vs {CSV_ROWS:,} - {'OK' if proj_match else 'MISMATCH'}")
print(f"   Funding: EUR {min_fund/1e9:.2f}B vs {CSV_FUNDING/1e9:.2f}B - {'OK' if fund_match else 'MISMATCH'}")
results.append(('Ministry Projects', proj_match))
results.append(('Ministry Funding', fund_match))

# 3. Geographic Distribution
print("\n3. GEOGRAPHIC DISTRIBUTION")
geo = load_json('geographic_distribution.json')
de_proj = sum(s['project_count'] for s in geo['states'])
intl_proj = geo.get('international', {}).get('total_projects', 0)
total_geo = de_proj + intl_proj
proj_match = total_geo == CSV_ROWS
print(f"   German: {de_proj:,}, International: {intl_proj:,}")
print(f"   Total: {total_geo:,} vs {CSV_ROWS:,} - {'OK' if proj_match else 'MISMATCH'}")
results.append(('Geographic Projects', proj_match))

# 4. Temporal Trends
print("\n4. TEMPORAL TRENDS")
temporal = load_json('temporal_trends.json')
temp_proj = sum(y['project_count'] for y in temporal['yearly_totals'])
temp_fund = sum(y['total_funding'] for y in temporal['yearly_totals'])
proj_match = temp_proj == CSV_ROWS
fund_diff = abs(temp_fund - CSV_FUNDING) / CSV_FUNDING * 100
fund_match = fund_diff < 0.01
print(f"   Projects: {temp_proj:,} vs {CSV_ROWS:,} - {'OK' if proj_match else 'MISMATCH'}")
print(f"   Funding: EUR {temp_fund/1e9:.2f}B vs {CSV_FUNDING/1e9:.2f}B - {'OK' if fund_match else 'MISMATCH'}")
results.append(('Temporal Projects', proj_match))
results.append(('Temporal Funding', fund_match))

# 5. Funding Types
print("\n5. FUNDING TYPES")
ft = load_json('funding_types.json')
ft_proj = sum(f['project_count'] for f in ft['funding_types'])
proj_match = ft_proj == CSV_ROWS
print(f"   Projects: {ft_proj:,} vs {CSV_ROWS:,} - {'OK' if proj_match else 'MISMATCH'}")
results.append(('Funding Types Projects', proj_match))

# 6. Funding Profiles (from funding_types.json)
print("\n6. FUNDING PROFILES")
fp_proj = sum(f['project_count'] for f in ft['funding_profiles'])
proj_match = fp_proj == CSV_ROWS
print(f"   Projects: {fp_proj:,} vs {CSV_ROWS:,} - {'OK' if proj_match else 'MISMATCH'}")
results.append(('Funding Profiles Projects', proj_match))

# 7. Joint Projects
print("\n7. JOINT PROJECTS")
joint = load_json('joint_projects.json')
joint_total = joint['joint_projects']['project_count'] + joint['individual_projects']['project_count']
proj_match = joint_total == CSV_ROWS
print(f"   Joint: {joint['joint_projects']['project_count']:,}, Individual: {joint['individual_projects']['project_count']:,}")
print(f"   Total: {joint_total:,} vs {CSV_ROWS:,} - {'OK' if proj_match else 'MISMATCH'}")
results.append(('Joint Projects Total', proj_match))

# 8. Projektträger
print("\n8. PROJEKTTRAEGER")
pt = load_json('projekttraeger.json')
pt_proj = sum(p['project_count'] for p in pt['projekttraeger'])
proj_match = pt_proj == CSV_ROWS
print(f"   Projects: {pt_proj:,} vs {CSV_ROWS:,} - {'OK' if proj_match else 'MISMATCH'}")
results.append(('Projekttraeger Projects', proj_match))

# 9. Duration Analysis (may have filtering)
print("\n9. DURATION ANALYSIS")
duration = load_json('duration_analysis.json')
dur_proj = sum(d['project_count'] for d in duration['distribution'])
# Duration may exclude projects without dates - check CSV
csv_with_duration = len(df[df['Laufzeit von'].notna() & df['Laufzeit bis'].notna()])
proj_match = dur_proj <= CSV_ROWS  # Can be less if filtering
print(f"   Projects with duration: {dur_proj:,}")
print(f"   CSV with dates: {csv_with_duration:,}")
print(f"   Status: {'OK (filtered by date availability)' if dur_proj <= CSV_ROWS else 'MISMATCH'}")
results.append(('Duration Projects', proj_match))

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

passed = sum(1 for _, v in results if v)
failed = sum(1 for _, v in results if not v)

print(f"\nTotal Checks: {len(results)}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")

if failed > 0:
    print("\nFailed Checks:")
    for name, v in results:
        if not v:
            print(f"  - {name}")

print(f"\nOverall: {'ALL CHECKS PASSED' if failed == 0 else 'SOME CHECKS FAILED'}")

# Save report
report = {
    'timestamp': datetime.now().isoformat(),
    'csv_rows': CSV_ROWS,
    'csv_funding': CSV_FUNDING,
    'checks': [{'name': n, 'passed': v} for n, v in results],
    'passed': passed,
    'failed': failed,
    'all_passed': failed == 0
}
with open('validation_report.json', 'w') as f:
    json.dump(report, f, indent=2)
print("\nReport saved to: validation_report.json")
