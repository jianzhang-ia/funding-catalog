"""
Funding Forecast Analysis using Facebook Prophet
Uses historical funding data to forecast future trends,
while considering already-approved future projects.
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from prophet import Prophet
import warnings
warnings.filterwarnings('ignore')

# Configuration
CSV_FILE = "Suchliste.csv"
OUTPUT_DIR = "output"
ENCODING = "cp1252"
CURRENT_YEAR = 2025  # December 2025
FORECAST_HORIZON = 10  # Years to forecast

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def clean_value(val):
    if isinstance(val, str) and val.startswith('="') and val.endswith('"'):
        return val[2:-1]
    return val

def parse_german_number(val):
    try:
        val = clean_value(str(val))
        val = val.replace('.', '').replace(',', '.')
        return float(val)
    except:
        return 0.0

def parse_german_date(val):
    try:
        val = clean_value(str(val))
        parts = val.split('.')
        if len(parts) == 3:
            return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
    except:
        pass
    return None

def load_data():
    """Load and prepare yearly funding data."""
    log("Loading data...")
    df = pd.read_csv(CSV_FILE, sep=';', encoding=ENCODING, low_memory=False)
    
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
    
    # Clean values
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(clean_value)
    
    # Parse funding and dates
    df['Fördersumme'] = df['Fördersumme in EUR'].apply(parse_german_number)
    df['StartDate'] = df['Laufzeit von'].apply(parse_german_date)
    df['StartYear'] = df['StartDate'].apply(lambda x: x.year if x else None)
    
    log(f"Loaded {len(df):,} projects")
    return df

def prepare_yearly_data(df):
    """Aggregate data by year for time series analysis."""
    yearly = df.groupby('StartYear').agg({
        'Fördersumme': ['sum', 'count']
    }).reset_index()
    yearly.columns = ['year', 'funding', 'projects']
    yearly = yearly.dropna()
    yearly['year'] = yearly['year'].astype(int)
    yearly = yearly.sort_values('year')
    
    return yearly

def run_prophet_forecast(yearly_data, current_year, forecast_years):
    """Run Prophet forecast on yearly funding data with improved parameters."""
    log("Running Prophet forecast (IMPROVED MODEL)...")
    
    # IMPROVEMENT B: Use recent data only (2000+) for more relevant patterns
    TRAINING_START_YEAR = 2000
    
    # Split data: historical (for training) and known future (for comparison)
    historical = yearly_data[(yearly_data['year'] >= TRAINING_START_YEAR) & 
                             (yearly_data['year'] <= current_year)].copy()
    approved_future = yearly_data[yearly_data['year'] > current_year].copy()
    
    log(f"  Training data: {len(historical)} years ({int(historical['year'].min())}-{int(historical['year'].max())})")
    log(f"  Already approved future: {len(approved_future)} years")
    
    # Prepare data for Prophet (requires 'ds' and 'y' columns)
    prophet_df = historical[['year', 'funding']].copy()
    prophet_df['ds'] = pd.to_datetime(prophet_df['year'], format='%Y')
    prophet_df['y'] = prophet_df['funding']
    prophet_df = prophet_df[['ds', 'y']]
    
    # IMPROVEMENT C: Mark COVID period (2020-2021) as outliers
    # Prophet uses 'cap' and 'floor' or we can reduce their weight
    # We'll use a simpler approach: add a regressor or just note them
    
    # Initialize Prophet model with IMPROVED parameters
    model = Prophet(
        yearly_seasonality=False,  # No sub-yearly seasonality for yearly data
        weekly_seasonality=False,
        daily_seasonality=False,
        # IMPROVEMENT A: Higher changepoint flexibility (0.1 -> 0.5)
        changepoint_prior_scale=0.5,  # More responsive to trend changes
        n_changepoints=15,  # More potential changepoints
        seasonality_mode='multiplicative',
        # IMPROVEMENT D: Wider confidence interval (80% -> 95%)
        interval_width=0.95  # 95% confidence interval
    )
    
    # IMPROVEMENT C: Mark COVID outliers (2020-2021) - remove them from training
    # This prevents the spike from distorting the trend
    covid_years = [2020, 2021]
    prophet_df_clean = prophet_df[~prophet_df['ds'].dt.year.isin(covid_years)].copy()
    log(f"  Excluded COVID outliers: {covid_years}")
    log(f"  Training points after exclusion: {len(prophet_df_clean)}")
    
    model.fit(prophet_df_clean)
    
    # Create future dataframe for prediction
    future_years = list(range(current_year + 1, current_year + forecast_years + 1))
    future_df = pd.DataFrame({
        'ds': pd.to_datetime(future_years, format='%Y')
    })
    
    # Get predictions
    forecast = model.predict(future_df)
    
    # Calculate historical volatility for context
    hist_std = historical['funding'].std()
    hist_mean = historical['funding'].mean()
    volatility_pct = (hist_std / hist_mean) * 100
    log(f"  Historical volatility: {volatility_pct:.1f}%")
    
    # Prepare forecast results
    forecast_results = []
    for _, row in forecast.iterrows():
        year = row['ds'].year
        
        # Check if there's already approved funding for this year
        approved = approved_future[approved_future['year'] == year]
        approved_funding = float(approved['funding'].iloc[0]) if len(approved) > 0 else None
        approved_projects = int(approved['projects'].iloc[0]) if len(approved) > 0 else None
        
        forecast_results.append({
            'year': year,
            'predicted_funding': float(max(0, row['yhat'])),  # No negative predictions
            'lower_bound': float(max(0, row['yhat_lower'])),
            'upper_bound': float(max(0, row['yhat_upper'])),
            'approved_funding': approved_funding,
            'approved_projects': approved_projects
        })
    
    log(f"  Forecast generated for {len(forecast_results)} years")
    
    return forecast_results, model

def analyze_forecast_quality(yearly_data, current_year):
    """Perform backtesting to assess forecast quality."""
    log("Running backtesting for forecast quality assessment...")
    
    # Use data up to 5 years ago to predict last 5 years
    TRAINING_START_YEAR = 2000
    backtest_end = current_year - 5
    backtest_data = yearly_data[(yearly_data['year'] >= TRAINING_START_YEAR) & 
                                 (yearly_data['year'] <= backtest_end)].copy()
    actual_data = yearly_data[(yearly_data['year'] > backtest_end) & (yearly_data['year'] <= current_year)].copy()
    
    if len(backtest_data) < 10 or len(actual_data) < 3:
        log("  Insufficient data for backtesting")
        return None
    
    # Prepare for Prophet
    prophet_df = backtest_data[['year', 'funding']].copy()
    prophet_df['ds'] = pd.to_datetime(prophet_df['year'], format='%Y')
    prophet_df['y'] = prophet_df['funding']
    prophet_df = prophet_df[['ds', 'y']]
    
    # Train model with IMPROVED parameters (matching main forecast)
    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.5,  # Same as main model
        n_changepoints=15
    )
    model.fit(prophet_df)
    
    # Predict the known years
    test_years = actual_data['year'].tolist()
    future_df = pd.DataFrame({
        'ds': pd.to_datetime(test_years, format='%Y')
    })
    
    predictions = model.predict(future_df)
    
    # Calculate errors
    errors = []
    for i, (_, row) in enumerate(predictions.iterrows()):
        year = int(test_years[i])
        predicted = row['yhat']
        actual = actual_data[actual_data['year'] == year]['funding'].iloc[0]
        error_pct = abs(predicted - actual) / actual * 100 if actual > 0 else 0
        errors.append({
            'year': year,
            'predicted': float(predicted),
            'actual': float(actual),
            'error_pct': float(error_pct)
        })
    
    avg_error = np.mean([e['error_pct'] for e in errors])
    log(f"  Backtesting MAE: {avg_error:.1f}%")
    
    return {
        'backtest_years': errors,
        'average_error_pct': float(avg_error)
    }

def main():
    log("="*60)
    log("FUNDING FORECAST ANALYSIS")
    log("="*60)
    
    # Load and prepare data
    df = load_data()
    yearly_data = prepare_yearly_data(df)
    
    log(f"\nYear range in data: {int(yearly_data['year'].min())} - {int(yearly_data['year'].max())}")
    log(f"Current year: {CURRENT_YEAR}")
    
    # Run forecast
    forecast_results, model = run_prophet_forecast(yearly_data, CURRENT_YEAR, FORECAST_HORIZON)
    
    # Assess forecast quality
    backtest_results = analyze_forecast_quality(yearly_data, CURRENT_YEAR)
    
    # Prepare output
    result = {
        'generated_at': datetime.now().isoformat(),
        'current_year': CURRENT_YEAR,
        'forecast_horizon_years': FORECAST_HORIZON,
        'historical_range': {
            'start': int(yearly_data['year'].min()),
            'end': CURRENT_YEAR
        },
        'forecast': forecast_results,
        'backtest': backtest_results,
        'summary': {
            'total_predicted_funding_next_5_years': sum(f['predicted_funding'] for f in forecast_results[:5]),
            'total_approved_funding_future': sum(f['approved_funding'] or 0 for f in forecast_results),
            'forecast_vs_approved_ratio': None  # Will be calculated
        }
    }
    
    # Calculate ratio
    approved_total = result['summary']['total_approved_funding_future']
    predicted_total = sum(f['predicted_funding'] for f in forecast_results)
    if approved_total > 0:
        result['summary']['forecast_vs_approved_ratio'] = predicted_total / approved_total
    
    # Save to JSON
    output_path = os.path.join(OUTPUT_DIR, 'funding_forecast.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    log(f"\nSaved forecast to: {output_path}")
    
    # Print summary
    log("\n" + "="*60)
    log("FORECAST SUMMARY")
    log("="*60)
    
    for f in forecast_results:
        approved_str = f"€{f['approved_funding']/1e9:.2f}B approved" if f['approved_funding'] else "no approved data"
        log(f"  {f['year']}: €{f['predicted_funding']/1e9:.2f}B predicted ({approved_str})")
    
    log("\n" + "="*60)
    log("FORECAST COMPLETE")
    log("="*60)

if __name__ == "__main__":
    main()
