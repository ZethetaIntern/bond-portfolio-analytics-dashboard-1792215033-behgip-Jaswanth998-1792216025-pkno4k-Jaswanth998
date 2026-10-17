from pathlib import Path
import pandas as pd

# Project paths
PROJECT_DIR = Path(
    r"E:\Data Analyst\ZeTheta Projects\Project 1B Data Analyst Convexity Sensitivity AI Agent"
)

DATA_DIR = PROJECT_DIR / "02_Raw_Data"
OUTPUT_DIR = PROJECT_DIR / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load bond portfolio dataset
file_path = DATA_DIR / "bond_portfolio_data.csv"

if not file_path.exists():
    print(f"ERROR: Dataset not found: {file_path}")
else:
    df = pd.read_csv(file_path)

    print("=" * 60)
    print("BOND PORTFOLIO ANALYSIS")
    print("=" * 60)

    print(f"\nNumber of bonds: {len(df)}")

    print("\nColumn names:")
    print(df.columns.tolist())

    print("\nFirst five records:")
    print(df.head().to_string(index=False))

    print("\nMissing values:")
    print(df.isnull().sum().to_string())

    print("\nDuplicate rows:", df.duplicated().sum())

    report_path = OUTPUT_DIR / "bond_portfolio_analysis.csv"
    df.describe(include="all").transpose().to_csv(report_path)

    print(f"\nInitial analysis saved to: {report_path}")