import os
import re
import json
import argparse

def extract_full_metadata_from_mp4(filepath):
    with open(filepath, "rb") as f:
        content = f.read()

    text_content = content.decode('utf-8', errors='ignore')

    extracted = {}

    patterns = {
        "x264_core_revision": r"core\s+\d+\s+(r\d+)",
        "x264_core_commit": r"core\s+\d+\s+r\d+\s+(\w+)",
        "codec_year": r"Copyleft\s+2003-(\d+)",
        "rc_mode": r"rc=(\w+)",
        "bitrate": r"bitrate=(\d+)",
        "ref_frames": r"ref=(\d+)",
        "subme": r"subme=(\d+)",
        "keyint": r"keyint=(\d+)",
        "keyint_min": r"keyint_min=(\d+)",
        "scenecut": r"scenecut=(\d+)",
        "rc_lookahead": r"rc_lookahead=(\d+)",
        "vbv_maxrate": r"vbv_maxrate=(\d+)",
        "vbv_bufsize": r"vbv_bufsize=(\d+)",
        "nal_hrd": r"nal_hrd=(\w+)",
        "filler": r"filler=(\d+)",
        "threads": r"threads=(\d+)",
        "lookahead_threads": r"lookahead_threads=(\d+)",
        "me_range": r"me_range=(\d+)",
        "analyse": r"analyse=(0x[\da-fA-F]+:0x[\da-fA-F]+)",
        "chroma_qp_offset": r"chroma_qp_offset=(-?\d+)",
        "open_gop": r"open_gop=(\d+)",
        "bframes": r"bframes=(\d+)",
        "b_pyramid": r"b_pyramid=(\d+)",
        "b_adapt": r"b_adapt=(\d+)",
        "direct": r"direct=(\d+)",
        "weightb": r"weightb=(\d+)",
        "weightp": r"weightp=(\d+)"
    }

    for key, regex in patterns.items():
        match = re.search(regex, text_content)
        if match:
            try:
                value = match.group(1)
            except IndexError:
                value = match.group(0)
            if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                value = int(value)
            extracted[key] = value
        else:
            extracted[key] = "missing"

    return extracted

def scan_directory_for_mp4s(input_directory, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    files_found = False
    for filename in os.listdir(input_directory):
        if filename.lower().endswith(".mp4"):
            files_found = True
            full_path = os.path.join(input_directory, filename)
            print(f"[+] Processing: {filename}")
            metadata = extract_full_metadata_from_mp4(full_path)

            json_filename = os.path.splitext(filename)[0] + ".json"
            json_path = os.path.join(output_directory, json_filename)
            with open(json_path, "w") as f:
                json.dump(metadata, f, indent=4)
            print(f"    → Saved metadata to: {json_path}")

    if not files_found:
        print(f"[!] No MP4 files found in {input_directory}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract MP4 encoding metadata from a folder of videos.")
    parser.add_argument("input_directory", help="Path to the folder containing MP4 files")
    parser.add_argument("output_directory", help="Path to save JSON metadata files")

    args = parser.parse_args()

    scan_directory_for_mp4s(args.input_directory, args.output_directory)
