import pandas as pd
INPUT_PATH = "data/processed/cleaned_SM_data.csv"
OUTPUT_PATH = "data/processed/metrics_SM_data.csv"

def load_data(path):
    """Load the cleaned data from a CSV file."""
    return pd.read_csv(path)

def safe_divide(numerator, denominator):
    """Safely divide two numbers, returning 0 if the denominator is zero."""
    return numerator / denominator.replace(0, pd.NA)

def compute_metrics(df):
    # Ensure numeric safety
    for col in ["likes", "comments", "shares", "saves", "follows", "impressions"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Total engagement (saves may not exist on all platforms)
    df["total_engagement"] = (
        df["likes"].fillna(0)
        + df["comments"].fillna(0)
        + df["shares"].fillna(0)
        + df.get("saves", 0).fillna(0)
    )

    # Rates (platform-agnostic)
    df["engagement_rate"] = safe_divide(df["total_engagement"], df["impressions"])
    df["save_rate"] = safe_divide(df.get("saves", 0), df["impressions"])
    df["follow_conversion_rate"] = safe_divide(df["follows"], df["impressions"])

    return df


def main():
    df = load_data(INPUT_PATH)
    df = compute_metrics(df)
    print(df[[
        "total_engagement",
        "engagement_rate",
        "save_rate",
        "follow_conversion_rate"
    ]].head())
    df.to_csv(OUTPUT_PATH, index=False)

if __name__ == "__main__":
    main()