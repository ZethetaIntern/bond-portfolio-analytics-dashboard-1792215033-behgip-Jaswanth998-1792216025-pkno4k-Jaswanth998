from pathlib import Path
import pandas as pd

# Project paths
PROJECT_DIR = Path(
    r"E:\Data Analyst\ZeTheta Projects\Project 1B Data Analyst Convexity Sensitivity AI Agent"
)

DATA_DIR = PROJECT_DIR / "02_Raw_Data"

DATASETS = [
    "bond_portfolio_data.csv",
    "monte_carlo_scenarios.csv",
    "yield_curve_history.csv",
]


def inspect_dataset(filename):
    file_path = DATA_DIR / filename

    print("\n" + "=" * 60)
    print(f"DATASET: {filename}")
    print("=" * 60)

    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        return

    try:
        df = pd.read_csv(file_path)

        print(f"Number of rows: {df.shape[0]}")
        print(f"Number of columns: {df.shape[1]}")

        print("\nColumn names:")
        print(df.columns.tolist())

        print("\nFirst five rows:")
        print(df.head().to_string(index=False))

        print("\nMissing values:")
        print(df.isnull().sum().to_string())

        print("\nDuplicate rows:", df.duplicated().sum())

    except Exception as error:
        print(f"Error reading dataset: {error}")


if __name__ == "__main__":
    for dataset in DATASETS:
        inspect_dataset(dataset)

    print("\nData validation completed.")