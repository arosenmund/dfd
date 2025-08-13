import os
import json
import pandas as pd
import argparse

def load_json_metadata(directory):
    data = []
    for filename in os.listdir(directory):
        if filename.lower().endswith(".json"):
            full_path = os.path.join(directory, filename)
            with open(full_path, "r") as f:
                metadata = json.load(f)
                metadata["_filename"] = filename  # Keep track of which file
                data.append(metadata)
    return pd.DataFrame(data)

def analyze_metadata(df):
    numeric_fields = []
    categorical_fields = []
    stats_summary = {}

    # Identify types
    for column in df.columns:
        if column == "_filename":
            continue
        if pd.api.types.is_numeric_dtype(df[column]) or all(str(x).lstrip("-").isdigit() for x in df[column] if x != "missing"):
            numeric_fields.append(column)
        else:
            categorical_fields.append(column)

    # Replace "missing" with NaN
    df_clean = df.replace("missing", pd.NA)

    print("\n=== Numeric Fields Analysis ===\n")
    for field in numeric_fields:
        if field not in df_clean:
            continue
        mean_val = df_clean[field].dropna().astype(float).mean()
        median_val = df_clean[field].dropna().astype(float).median()
        range_val = df_clean[field].dropna().astype(float).max() - df_clean[field].dropna().astype(float).min()
        missing_val = df_clean[field].isna().sum()

        print(f"Field: {field}")
        print(f"  Mean: {mean_val}")
        print(f"  Median: {median_val}")
        print(f"  Range: {range_val}")
        print(f"  Missing: {missing_val}")
        print()

        stats_summary[field] = {
            "type": "numeric",
            "mean": mean_val,
            "median": median_val,
            "range": range_val,
            "missing": missing_val
        }

    print("\n=== Categorical Fields Analysis ===\n")
    for field in categorical_fields:
        if field not in df_clean:
            continue
        freq = df_clean[field].value_counts(dropna=False).to_dict()
        # Fix: convert all keys to str, replace pd.NA with "missing"
        safe_freq = {str(k) if not pd.isna(k) else "missing": v for k, v in freq.items()}
        missing_val = df_clean[field].isna().sum()

        print(f"Field: {field}")
        print(json.dumps(safe_freq, indent=4))
        print()

        stats_summary[field] = {
            "type": "categorical",
            "frequencies": safe_freq,
            "missing": missing_val
        }

    return stats_summary

def clean_for_json(obj):
    """Recursively convert pandas/numpy types into native Python types."""
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    elif hasattr(obj, 'item'):
        return obj.item()
    else:
        return obj

def save_analysis_to_files(stats_summary, output_path_base):
    # Save JSON
    json_path = output_path_base + ".json"
    cleaned_summary = clean_for_json(stats_summary)
    with open(json_path, "w") as f:
        json.dump(cleaned_summary, f, indent=4)
    print(f"[+] Saved JSON summary to {json_path}")

    # Flatten for CSV
    flat_records = []
    for field, data in stats_summary.items():
        if data['type'] == 'numeric':
            flat_records.append({
                "field": field,
                "type": "numeric",
                "mean": float(data["mean"]),
                "median": float(data["median"]),
                "range": float(data["range"]),
                "missing": int(data["missing"])
            })
        elif data['type'] == 'categorical':
            for cat_value, freq in data["frequencies"].items():
                flat_records.append({
                    "field": field,
                    "type": "categorical",
                    "value": cat_value,
                    "frequency": int(freq),
                    "missing": int(data["missing"])
                })

    csv_path = output_path_base + ".csv"
    df_flat = pd.DataFrame(flat_records)
    df_flat.to_csv(csv_path, index=False)
    print(f"[+] Saved CSV summary to {csv_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze folder of JSON metadata files from MP4 extractions.")
    parser.add_argument("json_folder", help="Path to folder containing JSON files")
    parser.add_argument("output_base", help="Path base for saving output (without extension)")

    args = parser.parse_args()

    df = load_json_metadata(args.json_folder)
    stats_summary = analyze_metadata(df)
    save_analysis_to_files(stats_summary, args.output_base)
