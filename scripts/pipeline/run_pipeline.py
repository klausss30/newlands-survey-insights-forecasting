from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent


PIPELINE_STEPS = [
    ("merge raw survey files", SCRIPTS_DIR / "merge_newlands_surveys.py"),
    ("apply schema casting", SCRIPTS_DIR / "apply_schema_to_merged_csv.py"),
    ("generate row completeness report", SCRIPTS_DIR / "generate_row_completeness_report.py"),
    ("filter incomplete responses", SCRIPTS_DIR / "filter_incomplete_responses.py"),
    ("generate QC summary", SCRIPTS_DIR / "generate_qc_summary.py"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full Newlands survey data cleaning pipeline.")
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable to use for running the pipeline scripts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    for label, script_path in PIPELINE_STEPS:
        print(f"Running step: {label}")
        subprocess.run([args.python, str(script_path)], check=True)

    print("\nPipeline complete. Key outputs:")
    print(f"- {BASE_DIR / 'data' / 'processed' / 'newlands_analysis_ready_filtered.csv'}")
    print(f"- {BASE_DIR / 'data' / 'processed' / 'qc_summary.csv'}")
    print(f"- {BASE_DIR / 'metadata' / 'data_dictionary.csv'}")
    print(f"- {BASE_DIR / 'metadata' / 'mapping_log.csv'}")


if __name__ == "__main__":
    main()
