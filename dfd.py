#dfd

# read json limits and detect based on limits.

# python3 dfd.py ./real-recordings/real-analysis.json ./fake-recordings/fake-analysis.json ./test-samples/RSAC-AARON-D1.json 


import json
import math
import argparse
import os

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def is_valid_number(value):
    return isinstance(value, (int, float)) and not math.isnan(value)

def infer_rules(real_stats, fake_stats):
    rules = []

    for field, real_data in real_stats.items():
        if field not in fake_stats:
            continue
        fake_data = fake_stats[field]

        if real_data["type"] != "numeric" or fake_data["type"] != "numeric":
            continue

        real_mean = real_data.get("mean")
        fake_mean = fake_data.get("mean")

        if not is_valid_number(real_mean) or not is_valid_number(fake_mean):
            continue

        midpoint = (real_mean + fake_mean) / 2

        if fake_mean > real_mean:
            rules.append({
                "field": field,
                "operator": ">=",
                "threshold": midpoint,
                "description": f"{field} is typically higher in fake videos"
            })
        elif fake_mean < real_mean:
            rules.append({
                "field": field,
                "operator": "<=",
                "threshold": midpoint,
                "description": f"{field} is typically lower in fake videos"
            })

    # Categorical rules
    if "rc_mode" in fake_stats and "crf" in fake_stats["rc_mode"].get("frequencies", {}):
        rules.append({
            "field": "rc_mode",
            "operator": "==",
            "value": "crf",
            "description": "Fake videos frequently use crf instead of cbr"
        })

    if "ref_frames" in real_stats and "ref_frames" in fake_stats:
        real_mean = real_stats["ref_frames"].get("mean")
        fake_mean = fake_stats["ref_frames"].get("mean")
        if is_valid_number(real_mean) and is_valid_number(fake_mean) and fake_mean > real_mean:
            rules.append({
                "field": "ref_frames",
                "operator": ">=",
                "threshold": (real_mean + fake_mean) / 2,
                "description": "Fake videos use more reference frames"
            })

    return rules

def apply_rules(rules, file_metadata):
    triggered = []
    for rule in rules:
        field = rule["field"]
        if field not in file_metadata or file_metadata[field] == "missing":
            continue

        value = file_metadata[field]

        if rule["operator"] == ">=" and is_valid_number(value):
            if value >= rule["threshold"]:
                triggered.append(f"{field} ({value}) ≥ threshold ({rule['threshold']:.2f}) → {rule['description']}")
        elif rule["operator"] == "<=" and is_valid_number(value):
            if value <= rule["threshold"]:
                triggered.append(f"{field} ({value}) ≤ threshold ({rule['threshold']:.2f}) → {rule['description']}")
        elif rule["operator"] == "==" and value == rule["value"]:
            triggered.append(f"{field} = {value} → {rule['description']}")

    return triggered

def write_report(filename, verdict, confidence, reasons, output_folder="detections"):
    os.makedirs(output_folder, exist_ok=True)
    base = os.path.basename(filename).replace(".json", "")
    out_path = os.path.join(output_folder, f"{base}_detection.txt")

    with open(out_path, "w") as f:
        f.write(f"File: {filename}\n")
        f.write(f"Verdict: {verdict.upper()}\n")
        f.write(f"Confidence: {confidence:.1f}%\n\n")
        if reasons:
            f.write("Reasons:\n")
            for r in reasons:
                f.write(f"✔ {r}\n")
        else:
            f.write("No detection rules triggered.\n")
    print(f"[+] Detection report saved to: {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect if a .mp4 metadata file is fake based on real/fake summary comparison.")
    parser.add_argument("real_summary", help="Path to real videos' metadata summary (JSON)")
    parser.add_argument("fake_summary", help="Path to fake videos' metadata summary (JSON)")
    parser.add_argument("target_file", help="Path to metadata of the video file to classify (JSON)")

    args = parser.parse_args()

    real = load_json(args.real_summary)
    fake = load_json(args.fake_summary)
    target = load_json(args.target_file)

    rules = infer_rules(real, fake)
    findings = apply_rules(rules, target)

    triggered_count = len(findings)
    total_rules = len(rules)
    confidence = (triggered_count / total_rules) * 100 if total_rules > 0 else 0
    verdict = "FAKE" if triggered_count > 0 else "REAL"

    print(f"\n📂 File: {args.target_file}")
    print(f"→ DETECTED AS: {verdict}")
    print(f"→ Confidence: {confidence:.1f}%")

    if findings:
        print("\nReasons:")
        for reason in findings:
            print("✔", reason)
    else:
        print("✔ No rules triggered")

    write_report(args.target_file, verdict, confidence, findings)
