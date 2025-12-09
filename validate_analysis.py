"""
Cross-Reference Validation Script
Verifies all dashboard figures against raw CSV data
"""
import pandas as pd
import json
from datetime import datetime
import os

print("=" * 70)
print("CROSS-REFERENCE VALIDATION REPORT")
print("=" * 70)

# Load raw data
print("\n[1] Loading raw CSV data...")
df = pd.read_csv('Suchliste.csv', sep=';', encoding='cp1252', low_memory=False)

def clean_val(v):
    if isinstance(v, str) and v.startswith('="') and v.endswith('"'):
        return v[2:-1]
    return v

df.columns = [clean_val(c.strip()) for c in df.columns]
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].apply(clean_val)

def parse_num(v):
    try:
        v = clean_val(str(v))
        return float(v.replace('.', '').replace(',', '.'))
    except:
        return 0

df['Funding'] = df['Fördersumme in EUR'].apply(parse_num)
print(f"   Loaded {len(df):,} rows from CSV")

# Load JSON outputs
print("\n[2] Loading JSON outputs...")
json_files = {}
for f in os.listdir('output'):
    if f.endswith('.json'):
        with open(f'output/{f}', 'r', encoding='utf-8') as file:
            json_files[f] = json.load(file)
print(f"   Loaded {len(json_files)} JSON files")

errors = []
warnings = []

# ============================================================================
# VALIDATION 1: Total Funding
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION 1: TOTAL FUNDING")
print("=" * 70)

csv_total = df['Funding'].sum()
json_total = json_files['summary_stats.json']['total_funding']
diff_pct = abs(csv_total - json_total) / csv_total * 100

print(f"   CSV Total:  €{csv_total:,.0f}")
print(f"   JSON Total: €{json_total:,.0f}")
print(f"   Difference: {diff_pct:.4f}%")

if diff_pct > 0.01:
    errors.append(f"Total funding mismatch: {diff_pct:.4f}%")
else:
    print("   ✓ VERIFIED")

# ============================================================================
# VALIDATION 2: Total Projects
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION 2: TOTAL PROJECTS")
print("=" * 70)

csv_projects = len(df)
json_projects = json_files['summary_stats.json']['total_projects']

print(f"   CSV Count:  {csv_projects:,}")
print(f"   JSON Count: {json_projects:,}")

if csv_projects != json_projects:
    errors.append(f"Project count mismatch: CSV={csv_projects}, JSON={json_projects}")
else:
    print("   ✓ VERIFIED")

# ============================================================================
# VALIDATION 3: Ministry Totals
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION 3: MINISTRY FUNDING")
print("=" * 70)

csv_ministry = df.groupby('Ressort')['Funding'].sum().sort_values(ascending=False)
json_ministry = {m['code']: m['total_funding'] for m in json_files['ministry_funding.json']['ministries']}

for ministry, csv_val in csv_ministry.items():
    json_val = json_ministry.get(ministry, 0)
    diff = abs(csv_val - json_val)
    diff_pct = diff / csv_val * 100 if csv_val > 0 else 0
    status = "✓" if diff_pct < 0.01 else "✗"
    print(f"   {ministry}: CSV €{csv_val/1e9:.2f}B, JSON €{json_val/1e9:.2f}B ({diff_pct:.4f}%) {status}")
    if diff_pct > 0.01:
        errors.append(f"Ministry {ministry} mismatch: {diff_pct:.4f}%")

# ============================================================================
# VALIDATION 4: Top Recipients
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION 4: TOP RECIPIENTS")
print("=" * 70)

csv_recipients = df.groupby('Zuwendungsempfänger')['Funding'].sum().sort_values(ascending=False).head(5)
json_recipients = {r['name']: r['total_funding'] for r in json_files['top_recipients.json']['top_by_funding'][:5]}

for recipient, csv_val in csv_recipients.items():
    json_val = json_recipients.get(recipient, 0)
    diff_pct = abs(csv_val - json_val) / csv_val * 100 if csv_val > 0 else 0
    status = "✓" if diff_pct < 0.01 else "✗"
    print(f"   {recipient[:40]}: {diff_pct:.4f}% {status}")
    if diff_pct > 0.01:
        warnings.append(f"Recipient {recipient[:30]} mismatch: {diff_pct:.2f}%")

# ============================================================================
# VALIDATION 5: State Funding
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION 5: STATE (BUNDESLAND) FUNDING")
print("=" * 70)

csv_states = df.groupby('Bundesland')['Funding'].sum().sort_values(ascending=False).head(5)
json_states = {s['name']: s['total_funding'] for s in json_files['geographic_distribution.json']['states']}

for state, csv_val in csv_states.items():
    json_val = json_states.get(state, 0)
    diff_pct = abs(csv_val - json_val) / csv_val * 100 if csv_val > 0 else 0
    status = "✓" if diff_pct < 0.01 else "✗"
    print(f"   {state}: CSV €{csv_val/1e9:.2f}B, JSON €{json_val/1e9:.2f}B ({diff_pct:.4f}%) {status}")
    if diff_pct > 0.01:
        errors.append(f"State {state} mismatch: {diff_pct:.4f}%")

# ============================================================================
# VALIDATION 6: Unique Recipients Count
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION 6: UNIQUE RECIPIENTS")
print("=" * 70)

csv_unique = df['Zuwendungsempfänger'].nunique()
json_unique = json_files['summary_stats.json']['unique_recipients']

print(f"   CSV Unique:  {csv_unique:,}")
print(f"   JSON Unique: {json_unique:,}")

if csv_unique != json_unique:
    warnings.append(f"Unique recipients mismatch: CSV={csv_unique}, JSON={json_unique}")
else:
    print("   ✓ VERIFIED")

# ============================================================================
# VALIDATION 7: Sum of Ministry Funding = Total
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION 7: INTERNAL CONSISTENCY - MINISTRY SUM")
print("=" * 70)

ministry_sum = sum(m['total_funding'] for m in json_files['ministry_funding.json']['ministries'])
total = json_files['summary_stats.json']['total_funding']
diff_pct = abs(ministry_sum - total) / total * 100

print(f"   Sum of Ministries: €{ministry_sum/1e9:.2f}B")
print(f"   Total Funding:     €{total/1e9:.2f}B")
print(f"   Difference:        {diff_pct:.4f}%")

if diff_pct > 0.01:
    errors.append(f"Ministry sum != Total: {diff_pct:.4f}%")
else:
    print("   ✓ INTERNALLY CONSISTENT")

# ============================================================================
# VALIDATION 8: Monthly Distribution Total
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION 8: MONTHLY DISTRIBUTION")
print("=" * 70)

if 'monthly_distribution' in json_files['temporal_trends.json']:
    monthly_data = json_files['temporal_trends.json']['monthly_distribution']
    monthly_sum = sum(m['total_funding'] for m in monthly_data)
    monthly_projects = sum(m['project_count'] for m in monthly_data)
    
    print(f"   Monthly sum:     €{monthly_sum/1e9:.2f}B")
    print(f"   Monthly projects: {monthly_projects:,}")
    print(f"   Jan projects:    {monthly_data[0]['project_count']:,} (should be highest)")
    
    # Verify January is highest
    jan_projects = monthly_data[0]['project_count']
    max_other = max(m['project_count'] for m in monthly_data[1:])
    if jan_projects > max_other:
        print("   ✓ January is highest as expected")
    else:
        warnings.append("January is not the highest month")
else:
    warnings.append("No monthly_distribution found")

# ============================================================================
# VALIDATION 9: Projektträger Top Entry
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION 9: PROJEKTTRÄGER")
print("=" * 70)

csv_pt = df.groupby('PT')['Funding'].sum().sort_values(ascending=False).head(3)
json_pt = json_files['projekttraeger.json']['projekttraeger'][:3]

for i, (pt, csv_val) in enumerate(csv_pt.items()):
    json_entry = json_pt[i]
    json_val = json_entry['total_funding']
    diff_pct = abs(csv_val - json_val) / csv_val * 100 if csv_val > 0 else 0
    status = "✓" if diff_pct < 0.01 else "✗"
    print(f"   {pt}: CSV €{csv_val/1e9:.2f}B, JSON €{json_val/1e9:.2f}B ({diff_pct:.4f}%) {status}")

# ============================================================================
# VALIDATION 10: Decade Ministry Share Consistency
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION 10: DECADE MINISTRY SHARES")
print("=" * 70)

decade_data = json_files['temporal_trends.json'].get('decade_ministry_share', {})
for decade, entries in decade_data.items():
    total_share = sum(e['share_pct'] for e in entries)
    status = "✓" if 99.9 < total_share < 100.1 else "✗"
    print(f"   {decade}s: {total_share:.2f}% total {status}")
    if not (99.9 < total_share < 100.1):
        warnings.append(f"Decade {decade}s shares don't sum to 100%")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)

if errors:
    print(f"\n❌ ERRORS ({len(errors)}):")
    for e in errors:
        print(f"   - {e}")

if warnings:
    print(f"\n⚠️  WARNINGS ({len(warnings)}):")
    for w in warnings:
        print(f"   - {w}")

if not errors and not warnings:
    print("\n✅ ALL VALIDATIONS PASSED")
    print("   All figures are verified and internally consistent.")
else:
    print(f"\nTotal: {len(errors)} errors, {len(warnings)} warnings")
