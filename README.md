# German Federal Funding Catalog Analysis Dashboard

An interactive data visualization dashboard for the German Federal Funding Catalog (Förderkatalog), featuring over 317,000 research and development projects funded by federal ministries.

🔗 **[Live Demo](https://jianzhang-ia.github.io/funding-catalog/)**

## Features

- **14 Interactive Charts**: Ministry funding, geographic distribution, temporal trends, monthly patterns, decade comparisons, top recipients, and more
- **Cross-Validated Data**: All figures verified against raw CSV data
- **Modern Design**: Bright gradient background, glassmorphism cards, and smooth animations
- **Static Deployment**: All analysis is pre-computed; the webpage can be hosted on any static file server
- **Easy Updates**: Simple pipeline script to refresh data when new CSV becomes available

## Quick Start

### Prerequisites

- Python 3.8+
- pandas library (`pip install pandas`)

### Installation

1. Clone or download this repository
2. Place your `Suchliste.csv` file in the root directory
3. Run the analysis pipeline:

```bash
python analyze_funding.py
```

4. Copy output files to web directory (or use the update pipeline):

```bash
python update_pipeline.py
```

5. Start a local web server:

```bash
cd web
python -m http.server 8000
```

6. Open your browser to `http://localhost:8000`

## Project Structure

```
Funding/
├── Suchliste.csv              # Source data (not included, ~189MB)
├── analyze_funding.py         # Main analysis script
├── validate_analysis.py       # Cross-reference validation
├── update_pipeline.py         # Automated update script
├── README.md                  # This file
│
├── output/                    # Analysis output (JSON files)
│   ├── summary_stats.json
│   ├── ministry_funding.json
│   ├── geographic_distribution.json
│   ├── temporal_trends.json
│   ├── top_recipients.json
│   ├── topic_analysis.json
│   ├── duration_analysis.json
│   ├── funding_types.json
│   ├── projekttraeger.json
│   └── joint_projects.json
│
├── web/                       # Web dashboard
│   ├── index.html
│   ├── css/style.css
│   ├── js/main.js
│   └── data/*.json
│
└── docs/                      # GitHub Pages deployment (copy of web/)
```

## Data Notes

### Data Protection ("Keine Anzeige")

Some recipient names in the dataset are anonymized as **"Keine Anzeige aufgrund datenschutzrechtlicher Bestimmungen"** (No display due to data protection regulations).

**Important**: These entries represent **multiple protected recipients grouped together** – not a single entity. Only the recipient **name** is hidden; all other data (funding amount, location, ministry, project topic, etc.) remains fully available. These entries are included in all statistics and rankings.

### CSV Encoding

The source file uses **Windows-1252 (CP1252)** encoding with:
- Semicolon (`;`) delimiters
- `="value"` format for text fields
- German number format (`1.234,56` → 1234.56)
- German date format (`DD.MM.YYYY`)

## Analyses Included

| Analysis | Description |
|----------|-------------|
| **Ministry Funding** | Total funding distribution across federal ministries (Ressort) |
| **Geographic Distribution** | Funding by German federal state (Bundesland) and city |
| **Temporal Trends** | Yearly funding totals with time range filters |
| **Monthly Distribution** | Seasonal patterns - when projects start |
| **Ministry by Decade** | How funding shares shifted from 2000s to 2020s |
| **Top Recipients** | Organizations receiving the most funding (Zuwendungsempfänger) |
| **Projektträger** | Project sponsors managing administration |
| **Research Topics** | Classification by Leistungsplansystematik |
| **Project Duration** | Distribution of project lengths (Laufzeit) |
| **Funding Types** | Breakdown by Förderart and Förderprofil |
| **Joint Projects** | Analysis of Verbundprojekt patterns |

## Data Source

The data comes from the [German Federal Funding Catalog (Förderkatalog)](https://foerderkatalog.de), which contains:

- Projects from BMFTR, BMWE, BMV, BMLEH, BMUKN, and BMJV
- New projects added 60 days after approval
- Not 100% coverage; each ministry decides which funding areas to include

## Deployment

The web dashboard is fully static and can be deployed to:

- **GitHub Pages**: Use the `/docs` folder (already configured)
- **Netlify/Vercel**: Deploy the `web/` directory
- **Any web server**: Just serve the `web/` folder

No backend required – all data is pre-computed JSON.

## License

This project is open source. The data belongs to the German Federal Government and is publicly available.

## Contributing

Contributions welcome! Please open an issue or pull request.

