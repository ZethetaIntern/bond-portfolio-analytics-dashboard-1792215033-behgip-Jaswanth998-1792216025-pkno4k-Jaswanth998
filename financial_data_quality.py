from pathlib import Path
import pandas as pd

# Project paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "02_Raw_Data"

DATASETS = [
    "bond_portfolio_data.csv",
    "monte_carlo_scenarios.csv",
    "yield_curve_history.csv",
]


def check_data_quality(filename):
    file_path = DATA_DIR / filename

    print("\n" + "=" * 60)
    print(f"DATA QUALITY REPORT: {filename}")
    print("=" * 60)

    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        return

    try:
        df = pd.read_csv(file_path)

        print(f"Rows: {df.shape[0]}")
        print(f"Columns: {df.shape[1]}")
        print(f"Duplicate rows: {df.duplicated().sum()}")

        print("\nMissing values:")
        print(df.isnull().sum().to_string())

        print("\nData types:")
        print(df.dtypes.to_string())

        print("\nNumeric summary:")
        print(df.describe().to_string())

    except Exception as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    for dataset in DATASETS:
        check_data_quality(dataset)

    print("\nData quality assessment completed.")