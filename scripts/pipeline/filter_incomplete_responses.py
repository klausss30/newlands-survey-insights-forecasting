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
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "newlands_analysis_ready_filtered.csv"
REMOVED_ROWS_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "removed_incomplete_responses.csv"
)

# Rows with only these fields are treated as incomplete because they have no substantive survey answers.
MINIMAL_FIELDS = ["date", "age_range", "gender"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove survey rows that only contain minimal demographic fields and no substantive responses."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=INPUT_FILE,
        help="Input analysis-ready CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_FILE,
        help="Output CSV path for the filtered analysis-ready dataset.",
    )
    parser.add_argument(
        "--removed-output",
        type=Path,
        default=REMOVED_ROWS_FILE,
        help="Output CSV path for removed rows.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    df = pd.read_csv(args.input, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    df = df.reindex(columns=FINAL_COLUMNS, fill_value="")

    non_blank_mask = df.apply(lambda col: col.astype(str).str.strip() != "")
    non_blank_columns = non_blank_mask.apply(lambda row: {col for col, has_value in row.items() if has_value}, axis=1)
    minimal_set = set(MINIMAL_FIELDS)

    # Keep fully blank rows out of this rule; only partially started demographic-only rows are removed.
    minimal_only_mask = non_blank_columns.map(lambda cols: bool(cols) and cols.issubset(minimal_set))
    missing_age_range_mask = df["age_range"].astype(str).str.strip() == ""
    remove_mask = minimal_only_mask | missing_age_range_mask

    removed_df = df[remove_mask].copy()
    filtered_df = df[~remove_mask].copy()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.removed_output.parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_csv(args.output, index=False, encoding="utf-8-sig")
    removed_df.to_csv(args.removed_output, index=False, encoding="utf-8-sig")

    print(f"Wrote {len(filtered_df)} rows to {args.output}")
    print(f"Removed {len(removed_df)} rows to {args.removed_output}")


if __name__ == "__main__":
    main()
