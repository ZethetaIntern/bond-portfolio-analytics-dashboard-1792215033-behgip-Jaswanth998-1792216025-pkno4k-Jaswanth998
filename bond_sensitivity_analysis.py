from pathlib import Path
import pandas as pd

# Project paths
PROJECT_DIR = Path.cwd()
DATA_DIR = PROJECT_DIR / "02_Raw_Data"
OUTPUT_DIR = PROJECT_DIR / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load bond portfolio data
file_path = DATA_DIR / "bond_portfolio_data.csv"

if not file_path.exists():
    raise FileNotFoundError(f"Dataset not found: {file_path}")

df = pd.read_csv(file_path)

print("=" * 60)
print("BOND PORTFOLIO SENSITIVITY ANALYSIS")
print("=" * 60)

# Required columns
required_columns = [
    "BondID",
    "MarketValue_INR",
    "ModifiedDuration",
    "Convexity",
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

# Convert required fields to numeric
for col in required_columns[1:]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Check data quality
print("\nPortfolio records:", len(df))
print("\nMissing values:")
print(df[required_columns].isnull().sum())

# Calculate estimated price sensitivity
# Assumes a parallel change in yield.
# Yield changes are expressed in decimal form.

for shock_bps in [50, 100, 200]:
    delta_y = shock_bps / 10000

    df[f"EstimatedChange_Up{shock_bps}bps_INR"] = (
        df["MarketValue_INR"]
        * (
            -df["ModifiedDuration"] * delta_y
            + 0.5 * df["Convexity"] * delta_y**2
        )
    )

    df[f"EstimatedChange_Down{shock_bps}bps_INR"] = (
        df["MarketValue_INR"]
        * (
            df["ModifiedDuration"] * delta_y
            + 0.5 * df["Convexity"] * delta_y**2
        )
    )

# Save results
output_file = OUTPUT_DIR / "bond_sensitivity_analysis.csv"
df.to_csv(output_file, index=False)

print("\nPortfolio sensitivity estimates:")

sensitivity_columns = [
    "MarketValue_INR",
    "EstimatedChange_Up50bps_INR",
    "EstimatedChange_Down50bps_INR",
    "EstimatedChange_Up100bps_INR",
    "EstimatedChange_Down100bps_INR",
    "EstimatedChange_Up200bps_INR",
    "EstimatedChange_Down200bps_INR",
]

print(df[sensitivity_columns].sum().to_string())

print("\nResults saved to:")
print(output_file)

print("\nBond sensitivity analysis completed.")