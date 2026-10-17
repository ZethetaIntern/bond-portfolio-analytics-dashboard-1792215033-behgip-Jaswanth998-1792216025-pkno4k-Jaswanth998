from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Project paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "02_Raw_Data"
OUTPUT_DIR = PROJECT_DIR / "outputs"

INPUT_FILE = DATA_DIR / "bond_portfolio_data.csv"
OUTPUT_FILE = OUTPUT_DIR / "bond_price_predictions.csv"

# Features and target
FEATURES = [
    "ModifiedDuration",
    "Convexity",
    "YieldToMaturity",
    "CouponRate",
    "YearsToMaturity",
]

TARGET = "CleanPrice"


def main():
    print("=" * 60)
    print("BOND PRICE PREDICTION - MACHINE LEARNING")
    print("=" * 60)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)

    required_columns = FEATURES + [TARGET]
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Ensure the model receives numeric data.
    for col in required_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=required_columns)

    if len(df) < 10:
        raise ValueError("Not enough valid rows to train and test the model.")

    X = df[FEATURES]
    y = df[TARGET]

    # Keep a separate test set for evaluation.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
    )

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        random_state=42,
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = mean_squared_error(y_test, predictions) ** 0.5
    r2 = r2_score(y_test, predictions)

    print(f"\nValid records: {len(df)}")
    print(f"Training records: {len(X_train)}")
    print(f"Testing records: {len(X_test)}")

    print("\nModel evaluation:")
    print(f"Mean Absolute Error (MAE): {mae:.4f}")
    print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")
    print(f"R-squared (R²): {r2:.4f}")

    # Save predictions for the held-out test records.
    results = X_test.copy()
    results["ActualCleanPrice"] = y_test
    results["PredictedCleanPrice"] = predictions
    results["PredictionError"] = y_test - predictions

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUTPUT_FILE, index=False)

    print(f"\nPredictions saved to:\n{OUTPUT_FILE}")
    print("\nMachine learning model completed.")


if __name__ == "__main__":
    main()