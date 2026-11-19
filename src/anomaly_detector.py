import pandas as pd
import numpy as np
import logging
from datetime import datetime


def detect_statistical_anomalies(df: pd.DataFrame, profile: dict, config: dict) -> list:
    """
    Numeric columns mein statistical outliers dhundta hai using Z-score method.
    Z-score batata hai ki ek value, average se kitni standard deviations door hai.
    Agar |Z-score| > 3, to wo value 'unusual' maani jaati hai.
    """
    anomalies = []
    z_threshold = config.get("anomaly_detection", {}).get("z_score_threshold", 3)

    for col, col_profile in profile["column_profiles"].items():
        # Sirf numeric columns pe ye check chalega
        if "mean" not in col_profile or col_profile["mean"] is None:
            continue

        mean = col_profile["mean"]
        std = col_profile["std"]

        # Agar std deviation 0 hai (sab values same hain), skip karo
        if std is None or std == 0:
            continue

        col_data = df[col].dropna()
        q1, q3 = col_data.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr

        for idx, value in col_data.items():
            z_score = (value - mean) / std
            is_iqr_outlier = iqr > 0 and (value < lower_fence or value > upper_fence)

            if abs(z_score) > z_threshold or is_iqr_outlier:
                anomalies.append({
                    "row_index": idx,
                    "column": col,
                    "value": float(value),
                    "z_score": round(float(z_score), 2),
                    "column_mean": round(mean, 2),
                    "column_std": round(std, 2),
                    "detected_at": str(datetime.now())
                })

    # Detect duplicate rows and repeated identifier values as data-quality anomalies.
    duplicate_rows = df.index[df.duplicated(keep="first")].tolist()
    for idx in duplicate_rows:
        anomalies.append({
            "row_index": idx, "column": "__row__", "value": "duplicate row",
            "z_score": None, "column_mean": None, "column_std": None,
            "detected_at": str(datetime.now()),
        })

    for col in df.columns:
        if col.lower() == "id" or col.lower().endswith("_id"):
            duplicate_ids = df.index[df[col].notna() & df[col].duplicated(keep="first")].tolist()
            for idx in duplicate_ids:
                anomalies.append({
                    "row_index": idx, "column": col, "value": str(df.at[idx, col]),
                    "z_score": None, "column_mean": None, "column_std": None,
                    "detected_at": str(datetime.now()),
                })

    logging.info(f"Anomaly detection complete: {len(anomalies)} anomalies found")
    return anomalies


def detect_volume_anomaly(current_row_count: int, previous_row_count: int, config: dict) -> dict:
    """
    Compare karta hai ki aaj ka data pichli baar se kitna alag hai size mein.
    Agar achanak bahut zyada rows kam/zyada ho jayein, ye suspicious hai.
    """
    if previous_row_count == 0:
        return {"is_anomaly": False, "reason": "No previous data to compare"}

    change_pct = ((current_row_count - previous_row_count) / previous_row_count) * 100
    threshold = config.get("anomaly_detection", {}).get("volume_change_threshold_pct", 50)

    is_anomaly = abs(change_pct) > threshold

    return {
        "is_anomaly": is_anomaly,
        "current_rows": current_row_count,
        "previous_rows": previous_row_count,
        "change_percentage": round(change_pct, 2),
        "reason": f"Row count changed by {round(change_pct, 2)}%" if is_anomaly else "Normal variation"
    }
