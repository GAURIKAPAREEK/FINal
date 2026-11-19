import pandas as pd
import numpy as np
from datetime import datetime


def profile_dataframe(df: pd.DataFrame, config: dict) -> dict:
    """
    DataFrame ka complete health profile banata hai:
    - Har column ka data type
    - Null percentage
    - Unique values count
    - Basic statistics (numeric columns ke liye)
    """
    profile = {
        "profiled_at": str(datetime.now()),
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "column_profiles": {}
    }

    null_warn_threshold = config["profiling"]["null_threshold_warning"]
    null_critical_threshold = config["profiling"]["null_threshold_critical"]

    for col in df.columns:
        col_data = df[col]
        null_count = col_data.isnull().sum()
        null_pct = round(null_count / len(df), 4) if len(df) > 0 else 0

        if null_pct >= null_critical_threshold:
            severity = "CRITICAL"
        elif null_pct >= null_warn_threshold:
            severity = "WARNING"
        else:
            severity = "OK"

        detected_type = str(col_data.dtype)
        if pd.api.types.is_object_dtype(col_data) or pd.api.types.is_string_dtype(col_data):
            non_null = col_data.dropna().astype(str).str.strip()
            if len(non_null) and not pd.to_numeric(non_null, errors="coerce").notna().all():
                parsed_dates = pd.to_datetime(non_null, errors="coerce", format="mixed")
                if parsed_dates.notna().mean() >= 0.8:
                    detected_type = "datetime"

        col_profile = {
            "data_type": detected_type,
            "null_count": int(null_count),
            "null_percentage": null_pct,
            "severity": severity,
            "unique_count": int(col_data.nunique()),
            "is_unique": col_data.nunique() == len(df)
        }

        if pd.api.types.is_numeric_dtype(col_data):
            col_profile.update({
                "min": float(col_data.min()) if not col_data.isnull().all() else None,
                "max": float(col_data.max()) if not col_data.isnull().all() else None,
                "mean": float(col_data.mean()) if not col_data.isnull().all() else None,
                "std": float(col_data.std()) if not col_data.isnull().all() else None
            })

        profile["column_profiles"][col] = col_profile

    profile["overall_quality_score"] = calculate_quality_score(profile)

    return profile


def calculate_quality_score(profile: dict) -> float:
    """Return a continuous completeness score based on missing cells."""
    total_cells = profile.get("total_rows", 0) * profile.get("total_columns", 0)
    missing_cells = sum(
        int(details.get("null_count", 0))
        for details in profile.get("column_profiles", {}).values()
    )
    if total_cells <= 0:
        return 100.0 if profile.get("total_columns", 0) == 0 else 0.0
    return round(max(0.0, (1 - missing_cells / total_cells) * 100), 2)
