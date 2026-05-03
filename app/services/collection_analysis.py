import json
import os
from typing import Any, Dict, List

import pandas as pd


def load_json_metadata(directory: str) -> pd.DataFrame:
    """Load JSON metadata files from a directory into a DataFrame."""

    records: List[Dict[str, Any]] = []
    for filename in os.listdir(directory):
        if not filename.lower().endswith(".json"):
            continue
        full_path = os.path.join(directory, filename)
        with open(full_path, "r", encoding="utf-8") as file:
            metadata: Dict[str, Any] = json.load(file)
        metadata["_filename"] = filename
        records.append(metadata)
    if not records:
        raise ValueError(f"No JSON metadata files found in {directory}")
    return pd.DataFrame(records)


def _is_numeric_series(series: pd.Series) -> bool:
    if pd.api.types.is_numeric_dtype(series):
        return True
    non_missing = [value for value in series if value not in ("missing", None)]
    if not non_missing:
        return False
    try:
        pd.Series(non_missing, dtype="float64")
    except ValueError:
        return False
    return True


def analyze_dataframe(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    numeric_fields: List[str] = []
    categorical_fields: List[str] = []
    stats_summary: Dict[str, Dict[str, Any]] = {}

    for column in df.columns:
        if column == "_filename":
            continue
        if _is_numeric_series(df[column]):
            numeric_fields.append(column)
        else:
            categorical_fields.append(column)

    df_clean = df.replace("missing", pd.NA)

    for field in numeric_fields:
        if field not in df_clean:
            continue
        series = df_clean[field].dropna().astype(float)
        if series.empty:
            continue
        stats_summary[field] = {
            "type": "numeric",
            "mean": float(series.mean()),
            "median": float(series.median()),
            "range": float(series.max() - series.min()),
            "missing": int(df_clean[field].isna().sum()),
        }

    for field in categorical_fields:
        if field not in df_clean:
            continue
        freq = df_clean[field].value_counts(dropna=False).to_dict()
        safe_freq = {
            ("missing" if pd.isna(key) else str(key)): int(value)
            for key, value in freq.items()
        }
        stats_summary[field] = {
            "type": "categorical",
            "frequencies": safe_freq,
            "missing": int(df_clean[field].isna().sum()),
        }

    return stats_summary


def analyze_records(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    if not records:
        raise ValueError("No metadata records supplied for analysis")
    dataframe = pd.DataFrame(records)
    return analyze_dataframe(dataframe)


def analyze_metadata(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Backward-compatible alias for existing CLI scripts."""

    return analyze_dataframe(df)


def clean_for_json(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {key: clean_for_json(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [clean_for_json(value) for value in obj]
    if hasattr(obj, "item"):
        return obj.item()
    return obj


def save_analysis_to_files(stats_summary: Dict[str, Dict[str, Any]], output_path_base: str) -> None:
    json_path = output_path_base + ".json"
    cleaned_summary = clean_for_json(stats_summary)
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(cleaned_summary, file, indent=4)

    flat_records: List[Dict[str, Any]] = []
    for field, data in stats_summary.items():
        if data["type"] == "numeric":
            flat_records.append(
                {
                    "field": field,
                    "type": "numeric",
                    "mean": float(data["mean"]),
                    "median": float(data["median"]),
                    "range": float(data["range"]),
                    "missing": int(data["missing"]),
                }
            )
        elif data["type"] == "categorical":
            for category_value, frequency in data["frequencies"].items():
                flat_records.append(
                    {
                        "field": field,
                        "type": "categorical",
                        "value": category_value,
                        "frequency": int(frequency),
                        "missing": int(data["missing"]),
                    }
                )

    csv_path = output_path_base + ".csv"
    pd.DataFrame(flat_records).to_csv(csv_path, index=False)
