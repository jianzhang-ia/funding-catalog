"""
Update Pipeline for German Federal Funding Catalog
Automates the process of analyzing new CSV data and updating the web dashboard.

Usage:
    python update_pipeline.py [--csv path/to/Suchliste.csv]
"""

import os
import sys
import shutil
import argparse
from datetime import datetime
from pathlib import Path

# Configuration
DEFAULT_CSV = "Suchliste.csv"
OUTPUT_DIR = "output"
WEB_DATA_DIR = "web/data"
LOG_FILE = "update_log.txt"

def log(message, also_print=True):
    """Log message to file and optionally print."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    if also_print:
        print(log_entry)
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry + "\n")

def validate_csv(csv_path):
    """Validate that the CSV file exists and has expected structure."""
    log(f"Validating CSV file: {csv_path}")
    
    if not os.path.exists(csv_path):
        log(f"ERROR: CSV file not found: {csv_path}")
        return False
    
    # Check file size
    size_mb = os.path.getsize(csv_path) / (1024 * 1024)
    log(f"CSV file size: {size_mb:.1f} MB")
    
    if size_mb < 1:
        log("WARNING: CSV file seems too small. Please verify it contains the full dataset.")
    
    # Check header
    try:
        with open(csv_path, 'r', encoding='cp1252') as f:
            header = f.readline()
            if '="FKZ"' not in header:
                log("ERROR: CSV file does not have expected header format.")
                return False
    except Exception as e:
        log(f"ERROR: Could not read CSV file: {e}")
        return False
    
    log("CSV validation passed.")
    return True

def run_analysis(csv_path):
    """Run the analysis pipeline."""
    log("Running analysis pipeline...")
    
    # Import and run the analysis
    import analyze_funding
    
    # Update the CSV path if different from default
    original_csv = analyze_funding.CSV_FILE
    analyze_funding.CSV_FILE = csv_path
    
    try:
        analyze_funding.main()
        log("Analysis completed successfully.")
        return True
    except Exception as e:
        log(f"ERROR: Analysis failed: {e}")
        return False
    finally:
        analyze_funding.CSV_FILE = original_csv

def copy_to_web():
    """Copy analysis output files to web data directory."""
    log("Copying output files to web data directory...")
    
    # Ensure web data directory exists
    Path(WEB_DATA_DIR).mkdir(parents=True, exist_ok=True)
    
    # Copy all JSON files
    json_files = list(Path(OUTPUT_DIR).glob("*.json"))
    
    if not json_files:
        log("ERROR: No JSON files found in output directory.")
        return False
    
    for json_file in json_files:
        dest = Path(WEB_DATA_DIR) / json_file.name
        shutil.copy2(json_file, dest)
        log(f"  Copied: {json_file.name}")
    
    log(f"Copied {len(json_files)} files to {WEB_DATA_DIR}")
    return True

def update_timestamp():
    """Create/update a timestamp file for deployment tracking."""
    timestamp_file = Path(WEB_DATA_DIR) / "last_update.txt"
    timestamp = datetime.now().isoformat()
    
    with open(timestamp_file, 'w') as f:
        f.write(timestamp)
    
    log(f"Timestamp updated: {timestamp}")

def main():
    parser = argparse.ArgumentParser(
        description="Update German Federal Funding Catalog Dashboard"
    )
    parser.add_argument(
        '--csv',
        default=DEFAULT_CSV,
        help=f"Path to Suchliste.csv file (default: {DEFAULT_CSV})"
    )
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help="Skip CSV validation step"
    )
    
    args = parser.parse_args()
    
    log("=" * 60)
    log("German Federal Funding Catalog - Update Pipeline")
    log("=" * 60)
    
    start_time = datetime.now()
    
    # Step 1: Validate CSV
    if not args.skip_validation:
        if not validate_csv(args.csv):
            log("Pipeline aborted due to validation failure.")
            sys.exit(1)
    
    # Step 2: Run analysis
    if not run_analysis(args.csv):
        log("Pipeline aborted due to analysis failure.")
        sys.exit(1)
    
    # Step 3: Copy to web directory
    if not copy_to_web():
        log("Pipeline aborted due to copy failure.")
        sys.exit(1)
    
    # Step 4: Update timestamp
    update_timestamp()
    
    # Done
    elapsed = datetime.now() - start_time
    log("=" * 60)
    log(f"Pipeline completed successfully in {elapsed.total_seconds():.1f} seconds")
    log("=" * 60)
    log("")
    log("Next steps:")
    log("  1. Start local server: cd web && python -m http.server 8000")
    log("  2. Open browser: http://localhost:8000")
    log("")

if __name__ == "__main__":
    main()
