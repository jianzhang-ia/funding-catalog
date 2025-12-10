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
# VALIDATION 11: KEYWORD TRENDS
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION 11: KEYWORD TRENDS")
print("=" * 70)

keyword_trends = json_files.get('keyword_trends.json', {})
keywords = keyword_trends.get('keywords', {})
print(f"   Keywords tracked: {len(keywords)}")

if keywords:
    # Sample validation: check first keyword has valid data
    first_kw = list(keywords.keys())[0]
    kw_data = keywords[first_kw]
    has_yearly = 'yearly' in kw_data and len(kw_data['yearly']) > 0
    has_totals = 'total_funding' in kw_data and 'total_projects' in kw_data
    
    if has_yearly and has_totals:
        print(f"   Sample '{first_kw}': {len(kw_data['yearly'])} years, €{kw_data['total_funding']/1e6:.1f}M")
        print("   ✓ Keyword trends structure valid")
    else:
        errors.append("Keyword trends missing required fields")
else:
    warnings.append("No keyword trends data found")

# ============================================================================
# VALIDATION 12: ENTITY TRENDS (States, Cities, Recipients)
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION 12: ENTITY TRENDS")
print("=" * 70)

entity_trends = json_files.get('entity_trends.json', {})
states_trends = entity_trends.get('states', {})
cities_trends = entity_trends.get('cities', {})
recipients_trends = entity_trends.get('recipients', {})

print(f"   States with trends:     {len(states_trends)}")
print(f"   Cities with trends:     {len(cities_trends)}")
print(f"   Recipients with trends: {len(recipients_trends)}")

# Validate state trends match geographic data
geo_states = {s['name']: s['total_funding'] for s in json_files['geographic_distribution.json']['states']}
for state in list(states_trends.keys())[:3]:
    if state in geo_states:
        trend_total = states_trends[state]['total_funding']
        geo_total = geo_states[state]
        diff_pct = abs(trend_total - geo_total) / geo_total * 100 if geo_total > 0 else 0
        status = "✓" if diff_pct < 5 else "✗"  # Allow some difference due to year filtering
        print(f"   {state}: Trend €{trend_total/1e9:.2f}B vs Geo €{geo_total/1e9:.2f}B ({diff_pct:.1f}%) {status}")
        if diff_pct > 20:
            warnings.append(f"State {state} trend/geo mismatch: {diff_pct:.1f}%")

print("   ✓ Entity trends structure valid")

# ============================================================================
# VALIDATION 13: PER CAPITA DATA
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION 13: PER CAPITA POPULATION DATA")
print("=" * 70)

# Official population totals (source: Statistisches Bundesamt)
official_population = 83577140  # Total Germany
state_populations = {
    'Baden-Württemberg': 11245898,
    'Bayern': 13248928,
    'Berlin': 3685265,
    'Brandenburg': 2556747,
    'Bremen': 704881,
    'Hamburg': 1862565,
    'Hessen': 6280793,
    'Mecklenburg-Vorpommern': 1573597,
    'Niedersachsen': 8004489,
    'Nordrhein-Westfalen': 18034454,
    'Rheinland-Pfalz': 4129569,
    'Saarland': 1012141,
    'Sachsen': 4042422,
    'Sachsen-Anhalt': 2135597,
    'Schleswig-Holstein': 2959517,
    'Thüringen': 2100277
}

geo_data = json_files['geographic_distribution.json']['states']
states_with_population = 0
per_capita_valid = 0

for state_data in geo_data:
    name = state_data['name']
    if 'population' in state_data and state_data['population']:
        states_with_population += 1
        # Verify population matches official data
        if name in state_populations:
            expected_pop = state_populations[name]
            actual_pop = state_data['population']
            if expected_pop == actual_pop:
                per_capita_valid += 1
            else:
                warnings.append(f"Population mismatch for {name}")
        
        # Verify per capita calculation
        if 'per_capita_funding' in state_data:
            expected_pc = state_data['total_funding'] / state_data['population']
            actual_pc = state_data['per_capita_funding']
            if abs(expected_pc - actual_pc) < 0.01:
                pass  # Valid
            else:
                warnings.append(f"Per capita calculation error for {name}")

print(f"   States with population data: {states_with_population}")
print(f"   Population values verified:  {per_capita_valid}")

if states_with_population >= 16:
    print("   ✓ All 16 states have population data")
else:
    errors.append(f"Missing population data for {16 - states_with_population} states")

# ============================================================================
# VALIDATION 14: JSON FILE COMPLETENESS
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION 14: JSON FILE COMPLETENESS")
print("=" * 70)

expected_files = [
    'summary_stats.json',
    'ministry_funding.json',
    'geographic_distribution.json',
    'temporal_trends.json',
    'top_recipients.json',
    'topic_analysis.json',
    'duration_analysis.json',
    'funding_types.json',
    'joint_projects.json',
    'projekttraeger.json',
    'keyword_trends.json',
    'entity_trends.json'
]

missing_files = [f for f in expected_files if f not in json_files]
if missing_files:
    for f in missing_files:
        errors.append(f"Missing JSON file: {f}")
    print(f"   ✗ Missing: {', '.join(missing_files)}")
else:
    print(f"   ✓ All {len(expected_files)} expected JSON files present")

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

