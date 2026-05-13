from __future__ import annotations

import argparse
from pathlib import Path

try:
    import pandas as pd
except ImportError as exc:
    raise ImportError(
        "This script requires pandas. Install it with: pip install -r requirements.txt"
    ) from exc

from merge_newlands_surveys import FINAL_COLUMNS


BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_FILE = BASE_DIR / "data" / "processed" / "newlands_analysis_ready.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "row_completeness_report.csv"
LOW_COMPLETENESS_OUTPUT = BASE_DIR / "data" / "processed" / "low_completeness_candidates.csv"

PREVIEW_COLUMNS = [
    "date",
    "age_range",
    "gender",
]
# These fields identify demographic-only records for review before filtering.
MINIMAL_FIELDS = set(PREVIEW_COLUMNS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a row-level completeness report for the analysis-ready survey dataset."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=INPUT_FILE,
        help="Input CSV file to evaluate.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_FILE,
        help="Output CSV path for the full row completeness report.",
    )
    parser.add_argument(
        "--low-output",
        type=Path,
        default=LOW_COMPLETENESS_OUTPUT,
        help="Output CSV path for low-completeness candidate rows.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Completeness threshold below which a row is flagged as a low-completeness candidate.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    df = pd.read_csv(args.input, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    df = df.reindex(columns=FINAL_COLUMNS, fill_value="")

    non_blank_mask = df.apply(lambda col: col.astype(str).str.strip() != "")
    non_missing_count = non_blank_mask.sum(axis=1)
    total_fields = len(FINAL_COLUMNS)
    missing_count = total_fields - non_missing_count
    completeness_pct = (non_missing_count / total_fields * 100).round(2)

    report_df = pd.DataFrame(
        {
            "row_number": range(1, len(df) + 1),
            "non_missing_count": non_missing_count.astype(int),
            "missing_count": missing_count.astype(int),
            "completeness_pct": completeness_pct,
        }
    )

    for column in PREVIEW_COLUMNS:
        report_df[column] = df[column]

    # Low-completeness rows are review candidates; the filtering script applies the final removal rule.
    report_df["low_completeness_flag"] = completeness_pct < (args.threshold * 100)
    non_blank_columns = non_blank_mask.apply(
        lambda row: {col for col, has_value in row.items() if has_value},
        axis=1,
    )
    report_df["minimal_demographics_only_flag"] = non_blank_columns.map(
        lambda cols: bool(cols) and cols.issubset(MINIMAL_FIELDS)
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(args.output, index=False, encoding="utf-8-sig")

    low_df = report_df[
        report_df["low_completeness_flag"] | report_df["minimal_demographics_only_flag"]
    ].copy()
    low_df.to_csv(args.low_output, index=False, encoding="utf-8-sig")

    print(f"Wrote {len(report_df)} rows to {args.output}")
    print(
        f"Wrote {len(low_df)} low-completeness candidate rows to {args.low_output} "
        f"using threshold {args.threshold:.2f}"
    )


if __name__ == "__main__":
    main()
