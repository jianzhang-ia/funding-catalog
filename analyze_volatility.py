"""Analyze historical data volatility to improve forecast model"""
import pandas as pd
import numpy as np
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

# Aggregate by year
yearly = df.groupby('StartYear').agg({
    'Fördersumme': 'sum'
}).reset_index()
yearly.columns = ['year', 'funding']
yearly = yearly.dropna()
yearly['year'] = yearly['year'].astype(int)
yearly = yearly.sort_values('year')

print("="*60)
print("HISTORICAL DATA VOLATILITY ANALYSIS")
print("="*60)

# Focus on recent data (last 20 years)
recent = yearly[yearly['year'] >= 2005]
print(f"\nRecent data (2005-2025): {len(recent)} years")

# Calculate year-over-year changes
recent = recent.copy()
recent['yoy_change'] = recent['funding'].pct_change() * 100
recent['yoy_abs_change'] = recent['funding'].diff()

print("\nYear-over-Year Changes:")
for _, row in recent.iterrows():
    if pd.notna(row['yoy_change']):
        sign = "+" if row['yoy_change'] > 0 else ""
        print(f"  {int(row['year'])}: €{row['funding']/1e9:.1f}B ({sign}{row['yoy_change']:.1f}%)")

# Volatility metrics
print("\n" + "-"*40)
print("VOLATILITY METRICS")
print("-"*40)
yoy_std = recent['yoy_change'].dropna().std()
yoy_mean = recent['yoy_change'].dropna().mean()
max_gain = recent['yoy_change'].dropna().max()
max_loss = recent['yoy_change'].dropna().min()

print(f"Average YoY change: {yoy_mean:.1f}%")
print(f"Std Dev of YoY changes: {yoy_std:.1f}%")
print(f"Max gain: +{max_gain:.1f}%")
print(f"Max loss: {max_loss:.1f}%")

# Identify major events/anomalies
print("\n" + "-"*40)
print("MAJOR ANOMALIES/EVENTS")
print("-"*40)
threshold = yoy_std * 1.5
anomalies = recent[abs(recent['yoy_change']) > threshold]
for _, row in anomalies.iterrows():
    print(f"  {int(row['year'])}: {row['yoy_change']:+.1f}% change")

# Trend analysis
print("\n" + "-"*40)
print("TREND ANALYSIS")
print("-"*40)
# Simple linear regression
from numpy.polynomial import polynomial as P
years_arr = recent['year'].values
funding_arr = recent['funding'].values
coeffs = np.polyfit(years_arr, funding_arr, 1)
slope = coeffs[0]
intercept = coeffs[1]
print(f"Linear trend: {slope/1e9:.2f}B per year")
print(f"R² of linear fit: {np.corrcoef(years_arr, funding_arr)[0,1]**2:.3f}")

# Check for cyclical patterns
print("\n" + "-"*40)
print("OBSERVATIONS FOR FORECASTING")
print("-"*40)
print("""
1. HIGH VOLATILITY: Historical data shows large YoY swings
2. COVID SPIKE: 2020-2021 shows unusual peak (stimulus?)
3. 2025 DROP: Current year shows significant decline from peak
4. CYCLICAL: Possible 5-7 year cycles visible in data

Current Prophet model issues:
- Too smooth (uses default changepoint_prior_scale=0.1)
- Doesn't capture cyclicality
- Starting from 2025 low point, projecting linear growth
- Confidence interval may be too narrow
""")

print("\n" + "="*60)
print("RECOMMENDATIONS FOR IMPROVED FORECAST")
print("="*60)
print("""
1. INCREASE FLEXIBILITY
   - Increase changepoint_prior_scale from 0.1 to 0.3-0.5
   - Add more changepoints to capture recent trends

2. HANDLE ANOMALIES
   - Mark 2020-2021 COVID period as outliers
   - Consider using robust regression

3. ADD CYCLICALITY (Optional)
   - Prophet can detect multi-year cycles with yearly_seasonality
   - Or add custom seasonality with period=5 or 7 years

4. WIDEN CONFIDENCE INTERVALS
   - Use historical volatility to adjust uncertainty
   - interval_width=0.9 instead of 0.8

5. ENSEMBLE APPROACH
   - Combine Prophet with simple models (moving average, linear)
   - Weight by recent performance

6. USE RECENT TREND ONLY
   - Train on 2005-2025 data only, not from 1968
   - Older data may not reflect current funding patterns
""")
