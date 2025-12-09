"""
German Federal Funding Catalog Analysis Pipeline
Analyzes Suchliste.csv and outputs JSON files for web visualization.
"""

import pandas as pd
import numpy as np
import json
import os
import re
from datetime import datetime
from collections import Counter
from pathlib import Path

# Configuration
CSV_FILE = "Suchliste.csv"
OUTPUT_DIR = "output"
ENCODING = "cp1252"

def log(message):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def create_output_dir():
    """Create output directory if it doesn't exist."""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    log(f"Output directory ready: {OUTPUT_DIR}")

def clean_value(val):
    """Clean the =\"...\" format from values."""
    if isinstance(val, str):
        val = val.strip()
        if val.startswith('="') and val.endswith('"'):
            return val[2:-1]
    return val

def parse_german_number(val):
    """Parse German number format (1.234,56) to float."""
    if pd.isna(val) or val == '' or val == 'nan':
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    try:
        # Clean the value first
        val = clean_value(str(val))
        # Remove thousand separators and replace decimal comma
        val = val.replace('.', '').replace(',', '.')
        return float(val)
    except (ValueError, AttributeError):
        return 0.0

def parse_german_date(val):
    """Parse German date format (DD.MM.YYYY) to datetime."""
    if pd.isna(val) or val == '' or val == 'nan':
        return None
    try:
        val = clean_value(str(val))
        return datetime.strptime(val, "%d.%m.%Y")
    except (ValueError, AttributeError):
        return None

def load_and_clean_data():
    """Load CSV and clean all data."""
    log("Loading CSV file...")
    df = pd.read_csv(CSV_FILE, sep=';', encoding=ENCODING, low_memory=False)
    log(f"Loaded {len(df):,} rows")
    
    # Clean column names
    new_cols = {}
    for col in df.columns:
        clean_name = col.strip()
        if clean_name.startswith('="') and clean_name.endswith('"'):
            clean_name = clean_name[2:-1]
        # Handle duplicate column names from pandas
        if '.1' in clean_name or 'Unnamed' in clean_name:
            continue
        new_cols[col] = clean_name
    
    # Keep only the columns we need
    cols_to_keep = [c for c in df.columns if c in new_cols]
    df = df[cols_to_keep].copy()
    df.rename(columns=new_cols, inplace=True)
    
    log("Cleaning values...")
    # Clean string values
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(clean_value)
    
    # Parse funding amounts
    log("Parsing funding amounts...")
    df['Fördersumme'] = df['Fördersumme in EUR'].apply(parse_german_number)
    
    # Parse dates
    log("Parsing dates...")
    df['StartDate'] = df['Laufzeit von'].apply(parse_german_date)
    df['EndDate'] = df['Laufzeit bis'].apply(parse_german_date)
    
    # Extract year for time-based analysis
    df['StartYear'] = df['StartDate'].apply(lambda x: x.year if x else None)
    df['EndYear'] = df['EndDate'].apply(lambda x: x.year if x else None)
    
    # Calculate project duration in months
    def calc_duration(row):
        if row['StartDate'] and row['EndDate']:
            delta = row['EndDate'] - row['StartDate']
            return max(delta.days / 30.44, 0)  # Average days per month
        return None
    df['DurationMonths'] = df.apply(calc_duration, axis=1)
    
    log(f"Data cleaning complete. {len(df):,} projects ready for analysis.")
    return df

def save_json(data, filename):
    """Save data to JSON file."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    log(f"Saved: {filename}")

# ============================================================================
# Analysis Functions
# ============================================================================

def analyze_ministry_funding(df):
    """Analysis 1: Funding by Ministry (Ressort)."""
    log("Analyzing funding by ministry...")
    
    ministry_stats = df.groupby('Ressort').agg({
        'Fördersumme': ['sum', 'mean', 'count'],
        'FKZ': 'count'
    }).reset_index()
    
    ministry_stats.columns = ['ministry', 'total_funding', 'avg_funding', 'project_count', 'project_count2']
    ministry_stats = ministry_stats.drop('project_count2', axis=1)
    ministry_stats = ministry_stats.sort_values('total_funding', ascending=False)
    
    # Ministry full names (German Federal Ministries)
    ministry_names = {
        'BMFTR': 'Bundesministerium für Forschung, Technologie und Raumfahrt',
        'BMWE': 'Bundesministerium für Wirtschaft und Energie',
        'BMV': 'Bundesministerium für Verkehr',
        'BMLEH': 'Bundesministerium für Landwirtschaft, Ernährung und Heimat',
        'BMUKN': 'Bundesministerium für Umwelt, Klimaschutz und Naturschutz',
        'BMJV': 'Bundesministerium der Justiz und für Verbraucherschutz',
        'BMJV_BLE': 'BMJV - Bundesanstalt für Landwirtschaft und Ernährung'
    }
    
    result = {
        'ministries': [],
        'total_funding': float(df['Fördersumme'].sum()),
        'total_projects': int(len(df))
    }
    
    for _, row in ministry_stats.iterrows():
        result['ministries'].append({
            'code': row['ministry'],
            'name': ministry_names.get(row['ministry'], row['ministry']),
            'total_funding': float(row['total_funding']),
            'avg_funding': float(row['avg_funding']),
            'project_count': int(row['project_count'])
        })
    
    save_json(result, 'ministry_funding.json')
    return result

def analyze_geographic_distribution(df):
    """Analysis 2: Geographic Distribution by Bundesland."""
    log("Analyzing geographic distribution...")
    
    # Filter to Germany only
    df_de = df[df['Staat'] == 'Deutschland'].copy()
    
    state_stats = df_de.groupby('Bundesland').agg({
        'Fördersumme': ['sum', 'mean', 'count']
    }).reset_index()
    
    state_stats.columns = ['state', 'total_funding', 'avg_funding', 'project_count']
    state_stats = state_stats.sort_values('total_funding', ascending=False)
    
    # Top cities
    city_stats = df_de.groupby(['Ort', 'Bundesland']).agg({
        'Fördersumme': 'sum',
        'FKZ': 'count'
    }).reset_index()
    city_stats.columns = ['city', 'state', 'total_funding', 'project_count']
    city_stats = city_stats.sort_values('total_funding', ascending=False).head(30)
    
    result = {
        'states': [],
        'top_cities': [],
        'total_domestic_funding': float(df_de['Fördersumme'].sum()),
        'total_domestic_projects': int(len(df_de))
    }
    
    for _, row in state_stats.iterrows():
        if row['state'] and row['state'] != 'nan':
            result['states'].append({
                'name': row['state'],
                'total_funding': float(row['total_funding']),
                'avg_funding': float(row['avg_funding']),
                'project_count': int(row['project_count'])
            })
    
    for _, row in city_stats.iterrows():
        result['top_cities'].append({
            'city': row['city'],
            'state': row['state'],
            'total_funding': float(row['total_funding']),
            'project_count': int(row['project_count'])
        })
    
    save_json(result, 'geographic_distribution.json')
    return result

def analyze_temporal_trends(df):
    """Analysis 3: Funding trends over time with extended temporal patterns."""
    log("Analyzing temporal trends...")
    
    # Filter valid years
    df_valid = df[df['StartYear'].notna() & (df['StartYear'] >= 1980) & (df['StartYear'] <= 2030)].copy()
    
    # Extract month for seasonal analysis
    df_valid['StartMonth'] = df_valid['StartDate'].apply(lambda x: x.month if x else None)
    
    yearly_stats = df_valid.groupby('StartYear').agg({
        'Fördersumme': ['sum', 'mean', 'count']
    }).reset_index()
    yearly_stats.columns = ['year', 'total_funding', 'avg_funding', 'project_count']
    yearly_stats = yearly_stats.sort_values('year')
    
    # By ministry and year
    ministry_yearly = df_valid.groupby(['StartYear', 'Ressort']).agg({
        'Fördersumme': 'sum'
    }).reset_index()
    ministry_yearly.columns = ['year', 'ministry', 'funding']
    
    # Pivot for easier charting
    ministry_pivot = ministry_yearly.pivot(index='year', columns='ministry', values='funding').fillna(0)
    
    # Monthly distribution (seasonal patterns)
    monthly_stats = df_valid[df_valid['StartMonth'].notna()].groupby('StartMonth').agg({
        'Fördersumme': ['sum', 'count']
    }).reset_index()
    monthly_stats.columns = ['month', 'total_funding', 'project_count']
    
    # Ministry share by decade
    df_valid['Decade'] = (df_valid['StartYear'] // 10 * 10).astype('Int64')
    decade_ministry = df_valid.groupby(['Decade', 'Ressort'])['Fördersumme'].sum().reset_index()
    decade_totals = df_valid.groupby('Decade')['Fördersumme'].sum()
    
    # Year-over-year growth (last 15 years)
    recent_years = yearly_stats[yearly_stats['year'] >= 2010].copy()
    yoy_growth = []
    prev_funding = None
    for _, row in recent_years.iterrows():
        growth_pct = None
        if prev_funding and prev_funding > 0:
            growth_pct = ((row['total_funding'] - prev_funding) / prev_funding) * 100
        yoy_growth.append({
            'year': int(row['year']),
            'funding': float(row['total_funding']),
            'growth_pct': float(growth_pct) if growth_pct else None
        })
        prev_funding = row['total_funding']
    
    result = {
        'yearly_totals': [],
        'ministry_yearly': {},
        'monthly_distribution': [],
        'decade_ministry_share': {},
        'year_over_year_growth': yoy_growth,
        'years': sorted(df_valid['StartYear'].dropna().unique().tolist())
    }
    
    # Yearly totals with average funding
    for _, row in yearly_stats.iterrows():
        result['yearly_totals'].append({
            'year': int(row['year']),
            'total_funding': float(row['total_funding']),
            'avg_funding': float(row['avg_funding']),
            'project_count': int(row['project_count'])
        })
    
    # Ministry by year
    for ministry in ministry_pivot.columns:
        result['ministry_yearly'][ministry] = []
        for year in ministry_pivot.index:
            result['ministry_yearly'][ministry].append({
                'year': int(year),
                'funding': float(ministry_pivot.loc[year, ministry])
            })
    
    # Monthly distribution
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for _, row in monthly_stats.iterrows():
        month_idx = int(row['month']) - 1
        result['monthly_distribution'].append({
            'month': int(row['month']),
            'month_name': month_names[month_idx] if 0 <= month_idx < 12 else str(int(row['month'])),
            'total_funding': float(row['total_funding']),
            'project_count': int(row['project_count'])
        })
    
    # Ministry share by decade
    for decade in [1990, 2000, 2010, 2020]:
        decade_data = decade_ministry[decade_ministry['Decade'] == decade]
        total = decade_totals.get(decade, 1)
        result['decade_ministry_share'][str(decade)] = []
        for _, row in decade_data.sort_values('Fördersumme', ascending=False).iterrows():
            share = (row['Fördersumme'] / total * 100) if total > 0 else 0
            result['decade_ministry_share'][str(decade)].append({
                'ministry': row['Ressort'],
                'funding': float(row['Fördersumme']),
                'share_pct': float(share)
            })
    
    save_json(result, 'temporal_trends.json')
    return result

def analyze_top_recipients(df):
    """Analysis 4: Top funding recipients."""
    log("Analyzing top recipients...")
    
    recipient_stats = df.groupby('Zuwendungsempfänger').agg({
        'Fördersumme': ['sum', 'mean', 'count']
    }).reset_index()
    recipient_stats.columns = ['recipient', 'total_funding', 'avg_funding', 'project_count']
    
    # Top by total funding
    top_by_funding = recipient_stats.sort_values('total_funding', ascending=False).head(50)
    
    # Top by project count
    top_by_count = recipient_stats.sort_values('project_count', ascending=False).head(50)
    
    result = {
        'top_by_funding': [],
        'top_by_count': [],
        'unique_recipients': int(recipient_stats['recipient'].nunique())
    }
    
    for _, row in top_by_funding.iterrows():
        result['top_by_funding'].append({
            'name': row['recipient'],
            'total_funding': float(row['total_funding']),
            'avg_funding': float(row['avg_funding']),
            'project_count': int(row['project_count'])
        })
    
    for _, row in top_by_count.iterrows():
        result['top_by_count'].append({
            'name': row['recipient'],
            'total_funding': float(row['total_funding']),
            'project_count': int(row['project_count'])
        })
    
    save_json(result, 'top_recipients.json')
    return result

def analyze_topics(df):
    """Analysis 5: Research topic analysis."""
    log("Analyzing research topics...")
    
    # By Leistungsplansystematik (classification)
    classification_stats = df.groupby('Leistungsplansystematik').agg({
        'Fördersumme': 'sum',
        'FKZ': 'count',
        'Klartext Leistungsplansystematik': 'first'
    }).reset_index()
    classification_stats.columns = ['code', 'total_funding', 'project_count', 'description']
    classification_stats = classification_stats.sort_values('total_funding', ascending=False).head(50)
    
    # Extract keywords from Thema (project title)
    log("Extracting keywords from project titles...")
    all_words = []
    stopwords = {'und', 'der', 'die', 'das', 'für', 'zur', 'zum', 'von', 'mit', 'im', 'in', 'auf', 
                 'aus', 'bei', 'des', 'ein', 'eine', 'einer', 'einem', 'einen', 'als', 'an', 'nach',
                 'über', 'durch', 'sowie', 'wird', 'werden', 'wurde', 'wurden', 'ist', 'sind', 
                 'hat', 'haben', 'kann', 'können', 'soll', 'sollen', 'muss', 'müssen', 'teil',
                 'phase', 'projekt', 'verbundprojekt', 'teilprojekt', 'vorhaben', 'entwicklung'}
    
    for thema in df['Thema'].dropna().head(50000):  # Sample for performance
        words = re.findall(r'\b[A-ZÄÖÜa-zäöüß]{4,}\b', str(thema))
        for word in words:
            word_lower = word.lower()
            if word_lower not in stopwords and len(word_lower) > 4:
                all_words.append(word_lower)
    
    word_counts = Counter(all_words).most_common(100)
    
    result = {
        'classifications': [],
        'keywords': []
    }
    
    for _, row in classification_stats.iterrows():
        if row['code'] and row['code'] != 'nan':
            result['classifications'].append({
                'code': row['code'],
                'description': row['description'] if row['description'] and row['description'] != 'nan' else row['code'],
                'total_funding': float(row['total_funding']),
                'project_count': int(row['project_count'])
            })
    
    for word, count in word_counts:
        result['keywords'].append({
            'word': word.capitalize(),
            'count': count
        })
    
    save_json(result, 'topic_analysis.json')
    return result

def analyze_duration(df):
    """Analysis 6: Project duration analysis."""
    log("Analyzing project durations...")
    
    df_valid = df[df['DurationMonths'].notna() & (df['DurationMonths'] > 0) & (df['DurationMonths'] < 360)].copy()
    
    # Duration by ministry
    duration_by_ministry = df_valid.groupby('Ressort')['DurationMonths'].agg(['mean', 'median', 'std', 'count']).reset_index()
    duration_by_ministry.columns = ['ministry', 'mean_months', 'median_months', 'std_months', 'count']
    
    # Duration histogram (bins)
    bins = [0, 6, 12, 24, 36, 60, 120, 360]
    labels = ['<6 months', '6-12 months', '1-2 years', '2-3 years', '3-5 years', '5-10 years', '>10 years']
    df_valid['duration_bin'] = pd.cut(df_valid['DurationMonths'], bins=bins, labels=labels)
    duration_dist = df_valid['duration_bin'].value_counts().sort_index()
    
    result = {
        'by_ministry': [],
        'distribution': [],
        'overall_stats': {
            'mean_months': float(df_valid['DurationMonths'].mean()),
            'median_months': float(df_valid['DurationMonths'].median()),
            'total_analyzed': int(len(df_valid))
        }
    }
    
    for _, row in duration_by_ministry.iterrows():
        result['by_ministry'].append({
            'ministry': row['ministry'],
            'mean_months': float(row['mean_months']),
            'median_months': float(row['median_months']),
            'project_count': int(row['count'])
        })
    
    for label, count in duration_dist.items():
        result['distribution'].append({
            'range': str(label),
            'count': int(count)
        })
    
    save_json(result, 'duration_analysis.json')
    return result

def analyze_funding_types(df):
    """Analysis 7: Funding type analysis."""
    log("Analyzing funding types...")
    
    # By Förderart
    foerderart_stats = df.groupby('Förderart').agg({
        'Fördersumme': 'sum',
        'FKZ': 'count'
    }).reset_index()
    foerderart_stats.columns = ['type', 'total_funding', 'project_count']
    foerderart_stats = foerderart_stats.sort_values('total_funding', ascending=False)
    
    # By Förderprofil
    profil_stats = df.groupby('Förderprofil').agg({
        'Fördersumme': 'sum',
        'FKZ': 'count'
    }).reset_index()
    profil_stats.columns = ['profile', 'total_funding', 'project_count']
    profil_stats = profil_stats.sort_values('total_funding', ascending=False)
    
    result = {
        'funding_types': [],
        'funding_profiles': []
    }
    
    for _, row in foerderart_stats.iterrows():
        if row['type'] and row['type'] != 'nan':
            result['funding_types'].append({
                'name': row['type'],
                'total_funding': float(row['total_funding']),
                'project_count': int(row['project_count'])
            })
    
    for _, row in profil_stats.iterrows():
        if row['profile'] and row['profile'] != 'nan':
            result['funding_profiles'].append({
                'name': row['profile'],
                'total_funding': float(row['total_funding']),
                'project_count': int(row['project_count'])
            })
    
    save_json(result, 'funding_types.json')
    return result

def analyze_projekttraeger(df):
    """Analysis 9: Projektträger (Project Sponsors) analysis.
    
    Projektträger are organizations that manage project administration
    on behalf of the ministries.
    """
    log("Analyzing Projektträger (Project Sponsors)...")
    
    # Project sponsor full names
    pt_names = {
        'BF': 'DLR Projektträger (ehem. Beratungsfirma)',
        'VDI/VDE': 'VDI/VDE Innovation + Technik GmbH',
        'PT-DLR': 'DLR Projektträger',
        'FZ-Jül': 'Forschungszentrum Jülich',
        'GSI': 'GSI Helmholtzzentrum für Schwerionenforschung',
        'PTJ': 'Projektträger Jülich',
        'PTKA': 'Karlsruher Institut für Technologie (KIT)',
        'TÜV': 'TÜV Rheinland Consulting GmbH',
        'PT-SW': 'DLR Projektträger Software',
        'LF': 'Landwirtschaftliche Fakultät',
        'BLE': 'Bundesanstalt für Landwirtschaft und Ernährung',
        'FNR': 'Fachagentur Nachwachsende Rohstoffe e.V.'
    }
    
    # By Projektträger (PT)
    pt_stats = df.groupby('PT').agg({
        'Fördersumme': ['sum', 'mean', 'count'],
        'Ressort': lambda x: list(x.unique())[:3]  # Top ministries for this PT
    }).reset_index()
    pt_stats.columns = ['pt', 'total_funding', 'avg_funding', 'project_count', 'ministries']
    pt_stats = pt_stats.sort_values('total_funding', ascending=False).head(20)
    
    # PT by ministry breakdown
    pt_ministry = df.groupby(['PT', 'Ressort']).agg({
        'Fördersumme': 'sum',
        'FKZ': 'count'
    }).reset_index()
    pt_ministry.columns = ['pt', 'ministry', 'funding', 'projects']
    
    result = {
        'projekttraeger': [],
        'unique_count': int(df['PT'].nunique()),
        'pt_ministry_breakdown': []
    }
    
    for _, row in pt_stats.iterrows():
        if row['pt'] and row['pt'] != 'nan' and str(row['pt']).strip():
            result['projekttraeger'].append({
                'code': row['pt'],
                'name': pt_names.get(row['pt'], row['pt']),
                'total_funding': float(row['total_funding']),
                'avg_funding': float(row['avg_funding']),
                'project_count': int(row['project_count']),
                'ministries': row['ministries']
            })
    
    # Get top PT-Ministry combinations
    pt_ministry_top = pt_ministry.sort_values('funding', ascending=False).head(30)
    for _, row in pt_ministry_top.iterrows():
        if row['pt'] and row['pt'] != 'nan' and str(row['pt']).strip():
            result['pt_ministry_breakdown'].append({
                'pt': row['pt'],
                'ministry': row['ministry'],
                'funding': float(row['funding']),
                'projects': int(row['projects'])
            })
    
    save_json(result, 'projekttraeger.json')
    return result

def analyze_joint_projects(df):
    """Analysis 8: Joint project (Verbundprojekt) analysis."""
    log("Analyzing joint projects...")
    
    # Count joint vs individual projects
    df['is_joint'] = df['Verbundprojekt'].apply(lambda x: bool(x and x != 'nan' and str(x).strip()))
    
    joint_counts = df['is_joint'].value_counts()
    joint_funding = df.groupby('is_joint')['Fördersumme'].sum()
    
    # Top joint project names
    joint_projects = df[df['is_joint']].groupby('Verbundprojekt').agg({
        'Fördersumme': 'sum',
        'FKZ': 'count',
        'Bundesland': lambda x: list(x.unique())[:5]  # Sample of states involved
    }).reset_index()
    joint_projects.columns = ['name', 'total_funding', 'subproject_count', 'states']
    joint_projects = joint_projects.sort_values('total_funding', ascending=False).head(30)
    
    result = {
        'summary': {
            'joint_project_count': int(joint_counts.get(True, 0)),
            'individual_project_count': int(joint_counts.get(False, 0)),
            'joint_funding': float(joint_funding.get(True, 0)),
            'individual_funding': float(joint_funding.get(False, 0))
        },
        'top_joint_projects': []
    }
    
    for _, row in joint_projects.iterrows():
        result['top_joint_projects'].append({
            'name': row['name'],
            'total_funding': float(row['total_funding']),
            'subproject_count': int(row['subproject_count']),
            'states_involved': row['states']
        })
    
    save_json(result, 'joint_projects.json')
    return result

def generate_summary(df, ministry_data, geo_data, temporal_data, recipient_data):
    """Generate overall summary statistics."""
    log("Generating summary statistics...")
    
    result = {
        'generated_at': datetime.now().isoformat(),
        'data_source': CSV_FILE,
        'total_projects': int(len(df)),
        'total_funding': float(df['Fördersumme'].sum()),
        'unique_recipients': int(df['Zuwendungsempfänger'].nunique()),
        'unique_ministries': int(df['Ressort'].nunique()),
        'date_range': {
            'earliest_start': df['StartDate'].min().isoformat() if df['StartDate'].min() else None,
            'latest_start': df['StartDate'].max().isoformat() if df['StartDate'].max() else None
        },
        'ministry_count': len(ministry_data['ministries']),
        'state_count': len(geo_data['states']),
        'highlights': {
            'top_ministry': ministry_data['ministries'][0]['code'] if ministry_data['ministries'] else None,
            'top_state': geo_data['states'][0]['name'] if geo_data['states'] else None,
            'top_recipient': recipient_data['top_by_funding'][0]['name'] if recipient_data['top_by_funding'] else None,
            'avg_project_funding': float(df['Fördersumme'].mean()),
            'median_project_funding': float(df['Fördersumme'].median())
        }
    }
    
    save_json(result, 'summary_stats.json')
    return result

def main():
    """Run the complete analysis pipeline."""
    start_time = datetime.now()
    log("=" * 60)
    log("German Federal Funding Catalog Analysis Pipeline")
    log("=" * 60)
    
    create_output_dir()
    
    # Load and clean data
    df = load_and_clean_data()
    
    # Run all analyses
    log("\n" + "=" * 60)
    log("Running analyses...")
    log("=" * 60 + "\n")
    
    ministry_data = analyze_ministry_funding(df)
    geo_data = analyze_geographic_distribution(df)
    temporal_data = analyze_temporal_trends(df)
    recipient_data = analyze_top_recipients(df)
    analyze_topics(df)
    analyze_duration(df)
    analyze_funding_types(df)
    analyze_projekttraeger(df)
    analyze_joint_projects(df)
    
    # Generate summary
    generate_summary(df, ministry_data, geo_data, temporal_data, recipient_data)
    
    # Done
    elapsed = datetime.now() - start_time
    log("\n" + "=" * 60)
    log(f"Analysis complete! Elapsed time: {elapsed.total_seconds():.1f} seconds")
    log(f"Output files saved to: {OUTPUT_DIR}/")
    log("=" * 60)

if __name__ == "__main__":
    main()
