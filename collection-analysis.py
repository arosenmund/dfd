import argparse

from app.services.collection_analysis import (
    analyze_dataframe,
    load_json_metadata,
    save_analysis_to_files,
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze folder of JSON metadata files from MP4 extractions."
    )
    parser.add_argument("json_folder", help="Path to folder containing JSON files")
    parser.add_argument(
        "output_base", help="Path base for saving output (without extension)"
    )

    args = parser.parse_args()

    dataframe = load_json_metadata(args.json_folder)
    stats_summary = analyze_dataframe(dataframe)
    save_analysis_to_files(stats_summary, args.output_base)
