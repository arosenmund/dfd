import argparse
import json
import os
from typing import List

from app.services.detector import evaluate_detection


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_report(
    filename: str,
    verdict: str,
    confidence: float,
    reasons: List[str],
    output_folder: str = "detections",
) -> None:
    os.makedirs(output_folder, exist_ok=True)
    base = os.path.basename(filename).replace(".json", "")
    out_path = os.path.join(output_folder, f"{base}_detection.txt")

    with open(out_path, "w", encoding="utf-8") as file:
        file.write(f"File: {filename}\n")
        file.write(f"Verdict: {verdict.upper()}\n")
        file.write(f"Confidence: {confidence:.1f}%\n\n")
        if reasons:
            file.write("Reasons:\n")
            for reason in reasons:
                file.write(f"✔ {reason}\n")
        else:
            file.write("No detection rules triggered.\n")
    print(f"[+] Detection report saved to: {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Detect if a .mp4 metadata file is fake based on real/fake summary comparison."
    )
    parser.add_argument("real_summary", help="Path to real videos' metadata summary (JSON)")
    parser.add_argument("fake_summary", help="Path to fake videos' metadata summary (JSON)")
    parser.add_argument("target_file", help="Path to metadata of the video file to classify (JSON)")

    args = parser.parse_args()

    real_summary = load_json(args.real_summary)
    fake_summary = load_json(args.fake_summary)
    target_metadata = load_json(args.target_file)

    result = evaluate_detection(real_summary, fake_summary, target_metadata)

    print(f"\n📂 File: {args.target_file}")
    print(f"→ DETECTED AS: {result['verdict']}")
    print(f"→ Confidence: {result['confidence']:.1f}%")

    if result["findings"]:
        print("\nReasons:")
        for reason in result["findings"]:
            print("✔", reason)
    else:
        print("✔ No rules triggered")

    write_report(args.target_file, result["verdict"], result["confidence"], result["findings"])
