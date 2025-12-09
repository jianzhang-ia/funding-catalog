# German Federal Funding Catalog Analysis Dashboard

An interactive data visualization dashboard for the German Federal Funding Catalog (Förderkatalog), featuring over 317,000 research and development projects funded by federal ministries.

![Dashboard Preview](web/screenshot.png)

## Features

- **8 Comprehensive Analyses**: Ministry funding, geographic distribution, temporal trends, top recipients, research topics, project duration, funding types, and joint projects
- **Interactive Visualizations**: Built with Chart.js for smooth, responsive charts
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
├── Suchliste.csv              # Source data (not included)
├── analyze_funding.py         # Main analysis script
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
│   └── joint_projects.json
│
└── web/                       # Web dashboard
    ├── index.html
    ├── css/
    │   └── style.css
    ├── js/
    │   └── main.js
    └── data/                  # Copy of output JSON for web
        └── *.json
```

## Updating with New Data

When a new `Suchliste.csv` becomes available:

```bash
# Option 1: Use the update pipeline (recommended)
python update_pipeline.py --csv path/to/new/Suchliste.csv

# Option 2: Manual steps
python analyze_funding.py
cp output/*.json web/data/
```

The update pipeline will:
1. Validate the CSV file format
2. Run the complete analysis
3. Copy JSON files to `web/data/`
4. Update the timestamp

## Analyses Included

| Analysis | Description |
|----------|-------------|
| **Ministry Funding** | Total funding distribution across federal ministries |
| **Geographic Distribution** | Funding by German federal state (Bundesland) |
| **Temporal Trends** | Yearly funding totals and project counts over time |
| **Top Recipients** | Organizations receiving the most funding |
| **Research Topics** | Classification by Leistungsplansystematik and keyword extraction |
| **Project Duration** | Distribution of project lengths by ministry |
| **Funding Types** | Breakdown by Förderart and Förderprofil |
| **Joint Projects** | Analysis of collaborative vs individual projects |

## Data Source

The data comes from the [German Federal Funding Catalog (Förderkatalog)](https://foerderkatalog.de), which contains:

- Projects from BMFTR, BMWE, BMV, BMLEH, BMUKN, and BMJV
- New projects added 60 days after approval
- Not 100% coverage; each ministry decides which funding areas to include

### CSV Encoding

The source file uses **Windows-1252 (CP1252)** encoding with:
- Semicolon (`;`) delimiters
- `="value"` format for text fields
- German number format (`1.234,56` → 1234.56)
- German date format (`DD.MM.YYYY`)

## Deployment

The web dashboard is fully static and can be deployed to:

- **GitHub Pages**: Push the `web/` folder
- **Netlify/Vercel**: Deploy the `web/` directory
- **Any web server**: Just serve the `web/` folder

No backend required – all data is pre-computed JSON.

## License

This project is open source. The data belongs to the German Federal Government and is publicly available.

## Contributing

Contributions welcome! Please open an issue or pull request.
