"""Check Leistungsplansystematik and Projektträger values"""
import pandas as pd

df = pd.read_csv('Suchliste.csv', sep=';', encoding='cp1252', low_memory=False)

def clean_val(v):
    if isinstance(v, str) and v.startswith('="') and v.endswith('"'):
        return v[2:-1]
    return v

df.columns = [clean_val(c.strip()) for c in df.columns]
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].apply(clean_val)

print('='*60)
print('LEISTUNGSPLANSYSTEMATIK (Top 10):')
print('='*60)
lps = df['Leistungsplansystematik'].value_counts().head(10)
print(lps)

# Also check for Klartext column
print('\nKlartext Leistungsplansystematik (Top 10 by code):')
for code in lps.index[:5]:
    klartext = df[df['Leistungsplansystematik'] == code]['Klartext Leistungsplansystematik'].iloc[0]
    print(f"  {code}: {klartext}")

print('\n' + '='*60)
print('PROJEKTTRÄGER (Top 15):')
print('='*60)
pt = df['PT'].value_counts().head(15)
print(pt)
