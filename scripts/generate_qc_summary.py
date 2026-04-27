from __future__ import annotations

import argparse
from pathlib import Path

try:
    import pandas as pd
except ImportError as exc:
    raise ImportError(
        "This script requires pandas. Install it with: pip install -r requirements.txt"
    ) from exc

from merge_newlands_surveys import FINAL_COLUMNS, SCHEMA_DICT


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "processed" / "newlands_analysis_ready_filtered.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "qc_summary.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate QC summary for the analysis-ready survey dataset.")
    parser.add_argument(
        "--input",
        type=Path,
        default=INPUT_FILE,
        help="Input CSV file to summarize.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_FILE,
        help="Output CSV path for QC summary.",
    )
    return parser.parse_args()


def summarize_column(df: pd.DataFrame, column: str) -> dict[str, str]:
    series = df[column].fillna("").astype(str)
    non_blank = series[series.str.strip() != ""]
    missing_count = int((series.str.strip() == "").sum())
    unique_count = int(non_blank.nunique())
    sample_values = " | ".join(non_blank.drop_duplicates().head(5).tolist())

    summary = {
        "column": column,
        "field_type": SCHEMA_DICT[column]["field_type"],
        "analysis_role": SCHEMA_DICT[column]["analysis_role"],
        "row_count": str(len(series)),
        "missing_count": str(missing_count),
        "missing_pct": f"{(missing_count / len(series) * 100):.2f}" if len(series) else "",
        "unique_count": str(unique_count),
        "min_value": "",
        "max_value": "",
        "sample_values": sample_values,
    }

    if SCHEMA_DICT[column]["field_type"] == "integer":
        numeric = pd.to_numeric(non_blank, errors="coerce").dropna()
        if not numeric.empty:
            summary["min_value"] = str(int(numeric.min()))
            summary["max_value"] = str(int(numeric.max()))
    else:
        if not non_blank.empty:
            summary["min_value"] = non_blank.min()
            summary["max_value"] = non_blank.max()

    return summary


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    df = pd.read_csv(args.input, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    df = df.reindex(columns=FINAL_COLUMNS, fill_value="")

    summary_rows = [summarize_column(df, column) for column in FINAL_COLUMNS]
    summary_df = pd.DataFrame(summary_rows)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"Wrote {len(summary_df)} rows to {args.output}")


if __name__ == "__main__":
    main()
