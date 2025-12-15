"""Explore future data and plan forecasting"""
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

def parse_german_number(val):
    try:
        val = clean_val(str(val))
        val = val.replace('.', '').replace(',', '.')
        return float(val)
    except:
        return 0.0

def parse_german_date(val):
    try:
        val = clean_val(str(val))
        parts = val.split('.')
        if len(parts) == 3:
            return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
    except:
        pass
    return None

df['Fördersumme'] = df['Fördersumme in EUR'].apply(parse_german_number)
df['StartDate'] = df['Laufzeit von'].apply(parse_german_date)
df['StartYear'] = df['StartDate'].apply(lambda x: x.year if x else None)

print("="*60)
print("DATA EXPLORATION FOR FORECASTING")
print("="*60)

# Current time is December 2025
current_year = 2025

print(f"\nCurrent year: {current_year}")
print(f"Total projects: {len(df):,}")

# Year distribution
print("\n" + "-"*40)
print("YEAR DISTRIBUTION:")
print("-"*40)
yearly = df.groupby('StartYear').agg({
    'Fördersumme': ['sum', 'count']
}).reset_index()
yearly.columns = ['year', 'funding', 'projects']

# Past data (before 2025)
past = yearly[yearly['year'] < current_year]
print(f"\nHistorical years (before {current_year}): {len(past)}")
print(f"  Year range: {int(past['year'].min())} - {int(past['year'].max())}")
print(f"  Total funding: €{past['funding'].sum()/1e9:.2f}B")
print(f"  Total projects: {int(past['projects'].sum()):,}")

# Current year
current = yearly[yearly['year'] == current_year]
if len(current) > 0:
    print(f"\nCurrent year ({current_year}):")
    print(f"  Funding: €{current['funding'].iloc[0]/1e9:.2f}B")
    print(f"  Projects: {int(current['projects'].iloc[0]):,}")

# Future data (after 2025)
future = yearly[yearly['year'] > current_year]
print(f"\nFuture years (after {current_year}): {len(future)}")
if len(future) > 0:
    print(f"  Year range: {int(future['year'].min())} - {int(future['year'].max())}")
    print(f"  Total funding already approved: €{future['funding'].sum()/1e9:.2f}B")
    print(f"  Projects already approved: {int(future['projects'].sum()):,}")
    print("\n  Breakdown by year:")
    for _, row in future.iterrows():
        print(f"    {int(row['year'])}: {int(row['projects']):,} projects, €{row['funding']/1e6:.1f}M")

# Recent trends (last 10 years)
recent = yearly[(yearly['year'] >= current_year - 10) & (yearly['year'] < current_year)]
print(f"\nRecent trends ({current_year-10} - {current_year-1}):")
if len(recent) > 0:
    avg_funding = recent['funding'].mean()
    avg_projects = recent['projects'].mean()
    print(f"  Avg yearly funding: €{avg_funding/1e9:.2f}B")
    print(f"  Avg yearly projects: {int(avg_projects):,}")
    
    # Trend direction
    if len(recent) >= 2:
        first_half = recent.head(len(recent)//2)['funding'].mean()
        second_half = recent.tail(len(recent)//2)['funding'].mean()
        trend = "increasing" if second_half > first_half else "decreasing"
        print(f"  Trend direction: {trend}")

print("\n" + "="*60)
print("RECOMMENDATION FOR FORECASTING")
print("="*60)
print("""
1. Use Prophet for time series forecasting
2. Historical data: 1968-2024 as training
3. Current year 2025: Include as known data
4. Already approved future (2026-2035): Use as constraints/validation
5. Forecast horizon: 2026-2035 (10 years)
6. Show both forecast and approved as comparison
""")
