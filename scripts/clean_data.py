import pandas as pd
RAW_PATH = "data/raw/SM_Pred_Training_Data.csv"
OUTPUT_PATH = "data/processed/cleaned_SM_data.csv"
PLATFORM_METRICS = {
    "instagram": ["reach", "impressions", "likes", "comments", "shares", "saves", "profile_visits", "follows"],
    "tiktok": ["impressions", "likes", "comments", "shares", "saves"],
    "facebook": ["reach", "impressions", "likes", "comments", "shares", "profile_visists"],
    "linkedin": ["reach", "impressions", "likes", "comments", "shares", "profile_visits"]
}


def load_data(path):
    """Load the raw data from a CSV file."""
    return pd.read_csv(path, encoding='latin1')

def standardize_columns(df):
    """Standardize column names to lowercase and replace spaces with underscores."""
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ","_")
        .str.replace("-","_")
    )
    return df

def parse_mixed_dates(series):
    """
    Parse dates with mixed formats safely.
    Supports:
    - YYYY/MM/DD
    - DD/MM/YYYY
    - MM/DD/YYYY
    """
    parsed_dates = pd.to_datetime(
        series,
        errors="coerce",
        infer_datetime_format=True,
        dayfirst=True
    )

    return parsed_dates


def enforce_data_types(df):
    df["date_posted"] = parse_mixed_dates(df["date_posted"])

    for platform, metrics in PLATFORM_METRICS.items():
        mask = df["platform"].str.lower() == platform

        for col in metrics:
            if col in df.columns:
                df.loc[mask, col] = pd.to_numeric(
                    df.loc[mask, col], errors="coerce"
                ).fillna(0)

    return df


def clean_text_columns(df):
    text_cols = ["caption", "hashtags", "post_description"]

    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    return df


def main():
    df = load_data(RAW_PATH)
    df = standardize_columns(df)
    df = enforce_data_types(df)
    df = clean_text_columns(df)
    print(df.head())
    df.to_csv(OUTPUT_PATH, index=False)

if __name__ == "__main__":
    main()