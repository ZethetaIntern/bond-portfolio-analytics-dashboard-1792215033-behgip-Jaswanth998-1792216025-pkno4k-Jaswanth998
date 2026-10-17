from pathlib import Path

import pandas as pd

# Project paths
PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_DIR / "02_Raw_Data"
OUTPUT_DIR = PROJECT_DIR / "outputs"

INPUT_FILE = DATA_DIR / "bond_portfolio_data.csv"
OUTPUT_FILE = OUTPUT_DIR / "portfolio_risk_summary.csv"


def main():
    print("=" * 60)
    print("PORTFOLIO RISK ANALYSIS")
    print("=" * 60)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "BondID",
        "MarketValue_INR",
        "ModifiedDuration",
        "Convexity",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Convert required columns to numeric values.
    for column in required_columns[1:]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # Exclude rows with missing values in required fields.
    df = df.dropna(subset=required_columns)

    # Estimate portfolio value sensitivity to yield changes.
    df["EstimatedChange_Up100bps_INR"] = (
        df["MarketValue_INR"]
        * (
            -df["ModifiedDuration"] * 0.01
            + 0.5 * df["Convexity"] * (0.01 ** 2)
        )
    )

    df["EstimatedChange_Down100bps_INR"] = (
        df["MarketValue_INR"]
        * (
            df["ModifiedDuration"] * 0.01
            + 0.5 * df["Convexity"] * (0.01 ** 2)
        )
    )

    summary = pd.DataFrame(
        {
            "Metric": [
                "NumberOfBonds",
                "TotalMarketValue_INR",
                "EstimatedChange_Up100bps_INR",
                "EstimatedChange_Down100bps_INR",
            ],
            "Value": [
                len(df),
                df["MarketValue_INR"].sum(),
                df["EstimatedChange_Up100bps_INR"].sum(),
                df["EstimatedChange_Down100bps_INR"].sum(),
            ],
        }
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary.to_csv(OUTPUT_FILE, index=False)

    print("\nPortfolio risk summary:")
    print(summary.to_string(index=False))

    print(f"\nResults saved to:\n{OUTPUT_FILE}")
    print("\nPortfolio risk analysis completed.")


if __name__ == "__main__":
    main()