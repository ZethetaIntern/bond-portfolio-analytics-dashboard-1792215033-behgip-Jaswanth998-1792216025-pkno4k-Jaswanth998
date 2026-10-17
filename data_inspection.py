from pathlib import Path
import pandas as pd

# Project paths
PROJECT_DIR = Path(
    r"E:\Data Analyst\ZeTheta Projects\Project 1B Data Analyst Convexity Sensitivity AI Agent"
)

DATA_DIR = PROJECT_DIR / "02_Raw_Data"


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

        print(f"\nNumber of rows: {df.shape[0]}")
        print(f"Number of columns: {df.shape[1]}")

        print("\nColumn names:")
        print(df.columns.tolist())

        print("\nFirst five rows:")
        print(df.head().to_string(index=False))

        print("\nMissing values:")
        print(df.isnull().sum().to_string())

    except Exception as error:
        print(f"Error reading dataset: {error}")


if __name__ == "__main__":
    inspect_dataset("bond_portfolio_data.csv")
    inspect_dataset("monte_carlo_scenarios.csv")
    inspect_dataset("yield_curve_history.csv")