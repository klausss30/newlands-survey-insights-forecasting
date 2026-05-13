from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


BASE_DIR = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent


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

    final_output = BASE_DIR / "data" / "processed" / "newlands_analysis_ready_filtered.csv"
    qc_output = BASE_DIR / "data" / "processed" / "qc_summary.csv"
    removed_output = BASE_DIR / "data" / "processed" / "removed_incomplete_responses.csv"
    completeness_output = BASE_DIR / "data" / "processed" / "row_completeness_report.csv"
    low_completeness_output = BASE_DIR / "data" / "processed" / "low_completeness_candidates.csv"

    with TemporaryDirectory(prefix="newlands_pipeline_") as temp_dir:
        temp_path = Path(temp_dir)
        merged_output = temp_path / "merged_newlands_surveys_clean.csv"
        analysis_ready_output = temp_path / "newlands_analysis_ready.csv"

        pipeline_steps = [
            (
                "merge raw survey files",
                [
                    args.python,
                    str(SCRIPTS_DIR / "merge_newlands_surveys.py"),
                    "--output",
                    str(merged_output),
                ],
            ),
            (
                "apply schema casting",
                [
                    args.python,
                    str(SCRIPTS_DIR / "apply_schema_to_merged_csv.py"),
                    "--input",
                    str(merged_output),
                    "--output",
                    str(analysis_ready_output),
                ],
            ),
            (
                "generate row completeness report",
                [
                    args.python,
                    str(SCRIPTS_DIR / "generate_row_completeness_report.py"),
                    "--input",
                    str(analysis_ready_output),
                    "--output",
                    str(completeness_output),
                    "--low-output",
                    str(low_completeness_output),
                ],
            ),
            (
                "filter incomplete responses",
                [
                    args.python,
                    str(SCRIPTS_DIR / "filter_incomplete_responses.py"),
                    "--input",
                    str(analysis_ready_output),
                    "--output",
                    str(final_output),
                    "--removed-output",
                    str(removed_output),
                ],
            ),
            (
                "generate QC summary",
                [
                    args.python,
                    str(SCRIPTS_DIR / "generate_qc_summary.py"),
                    "--input",
                    str(final_output),
                    "--output",
                    str(qc_output),
                ],
            ),
        ]

        for label, command in pipeline_steps:
            print(f"Running step: {label}", flush=True)
            subprocess.run(command, check=True)

    print("\nPipeline complete. Key outputs:")
    print(f"- {final_output}")
    print(f"- {qc_output}")
    print(f"- {BASE_DIR / 'metadata' / 'data_dictionary.csv'}")
    print(f"- {BASE_DIR / 'metadata' / 'mapping_log.csv'}")


if __name__ == "__main__":
    main()
