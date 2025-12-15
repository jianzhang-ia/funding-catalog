"""Investigate keyword count discrepancy between topic_analysis and keyword_trends"""
import json

# Load both files
with open('web/data/topic_analysis.json', 'r', encoding='utf-8') as f:
    topics = json.load(f)

with open('web/data/keyword_trends.json', 'r', encoding='utf-8') as f:
    trends = json.load(f)

print("="*60)
print("KEYWORD COUNT DISCREPANCY ANALYSIS")
print("="*60)

# Find Bewertung in topics
topic_count = None
for kw in topics['keywords']:
    if kw['word'] == 'Bewertung':
        topic_count = kw['count']
        print(f"\ntopic_analysis.json - Bewertung count: {topic_count}")
        break

# Find Bewertung in trends
if 'Bewertung' in trends:
    trend_data = trends['Bewertung']
    if 'yearly_data' in trend_data:
        yearly_total = sum(y['project_count'] for y in trend_data['yearly_data'])
        print(f"keyword_trends.json - Bewertung yearly total: {yearly_total}")

# Check Analyse too
print("\n" + "-"*40)
for kw in topics['keywords']:
    if kw['word'] == 'Analyse':
        print(f"topic_analysis.json - Analyse count: {kw['count']}")
        break

if 'Analyse' in trends:
    trend_data = trends['Analyse']
    if 'yearly_data' in trend_data:
        yearly_total = sum(y['project_count'] for y in trend_data['yearly_data'])
        print(f"keyword_trends.json - Analyse yearly total: {yearly_total}")

print("\n" + "="*60)
print("ANALYSIS")
print("="*60)
print("""
The discrepancy is likely because:

1. topic_analysis.json counts WORD OCCURRENCES (how many times 
   a word appears in project titles, using text extraction)

2. keyword_trends.json counts PROJECTS (how many projects 
   contain this keyword, possibly using different matching logic)

Let me check the analyze_funding.py functions...
""")
