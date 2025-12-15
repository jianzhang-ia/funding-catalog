"""Check all charts for data omissions/limits"""
import json
import os

print("="*70)
print("CHART OMISSION AUDIT")
print("="*70)

# Load all JSON files
json_files = {}
for filename in os.listdir('web/data'):
    if filename.endswith('.json'):
        with open(f'web/data/{filename}', 'r', encoding='utf-8') as f:
            json_files[filename] = json.load(f)

print("\n1. MINISTRY FUNDING")
ministries = json_files['ministry_funding.json']['ministries']
print(f"   Shown: {len(ministries)} ministries, {sum(m['project_count'] for m in ministries):,} projects")
print(f"   -> OK: All ministries shown")

print("\n2. TOP RECIPIENTS")
recipients = json_files['top_recipients.json']
print(f"   Top by funding: {len(recipients['top_by_funding'])} entries")
print(f"   Total unique: {recipients['unique_recipients']:,}")
print(f"   -> NEEDS FOOTNOTE: Top 30 of {recipients['unique_recipients']:,} recipients")

print("\n3. GEOGRAPHIC - CITIES")
cities = json_files['geographic_distribution.json']['top_cities']
print(f"   Shown: {len(cities)} cities")
print(f"   -> NEEDS FOOTNOTE: Top {len(cities)} cities only")

print("\n4. KEYWORDS")
keywords = json_files['topic_analysis.json']['keywords']
print(f"   Shown: {len(keywords)} keywords")
print(f"   -> Should note: Top {len(keywords)} keywords shown")

print("\n5. FUNDING PROFILES")
fp = json_files['funding_types.json']['funding_profiles']
total = sum(f['project_count'] for f in fp)
print(f"   Shown: {len(fp)} profiles, {total:,} projects")
print(f"   -> NEEDS FOOTNOTE: 2,918 projects with empty profile omitted")

print("\n6. JOINT PROJECTS TOP LIST")
top_joint = json_files['joint_projects.json']['top_joint_projects']
print(f"   Shown: {len(top_joint)} top joint projects")
print(f"   -> NEEDS FOOTNOTE: Top {len(top_joint)} joint projects shown")

print("\n7. CLASSIFICATIONS (Leistungsplansystematik)")
cls = json_files['topic_analysis.json']['classifications']
print(f"   Shown: {len(cls)} classifications")
print(f"   -> Should note: Top {len(cls)} classifications")

print("\n" + "="*70)
print("CHARTS THAT NEED FOOTNOTES:")
print("="*70)
print("""
ALREADY HAVE:
  - Geographic (Bundesland): *92 projects with unassigned Bundesland
  - Projektträger: *Showing top 12 of 41 project sponsors

NEED TO ADD:
  1. Top Recipients: *Showing top 30 of ~84K recipients
  2. Top Cities: *Showing top 30 cities  
  3. Funding Profile: *2,918 projects without profile classification
  4. Joint Projects chart/table if any
  5. Keywords/Topics if space allows
""")
