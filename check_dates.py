"""Check for invalid start dates in the dataset"""
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

# Check raw start date values
dates = df['Laufzeit von']
print(f'Total projects: {len(df):,}')
print()

# Check how many parse to valid dates
valid_count = 0
invalid_samples = []
for d in dates:
    try:
        if pd.isna(d) or str(d).strip() == '':
            invalid_samples.append(repr(d))
        else:
            parts = str(d).split('.')
            if len(parts) == 3:
                year = int(parts[2])
                valid_count += 1
            else:
                invalid_samples.append(repr(d))
    except:
        invalid_samples.append(repr(d))

print(f'Valid start dates: {valid_count:,}')
print(f'Invalid/missing start dates: {len(df) - valid_count:,}')
print()
if len(df) - valid_count > 0:
    print('Sample invalid dates (unique values):')
    for s in list(set(invalid_samples))[:10]:
        print(f'  {s}')
else:
    print('All projects have valid start dates!')
