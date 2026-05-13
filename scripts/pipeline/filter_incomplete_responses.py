from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

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
MISSING_VALUE_THRESHOLD = 3

YEAR_RULE_END_COLUMNS = {
    2019: "place_out_of_newlands_disaster_ready",
    2020: "place_out_of_newlands_disaster_ready",
    2022: "optimal_use_of_land",
}

YEAR_RULE_IGNORED_COLUMNS = {
    2024: {
        "vote_general_election_2020",
        "vote_local_elections_2019",
        "location",
    },
    2025: {
        "meaning_and_purpose",
        "vote_general_election_2020",
        "vote_local_elections_2019",
        "personal_mental_health",
        "location",
    },
}


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


def parse_year(date_series: pd.Series) -> pd.Series:
    return pd.to_datetime(date_series, format="%d/%m/%Y", errors="coerce").dt.year.astype("Int64")


def columns_through(end_column: str) -> list[str]:
    if end_column not in FINAL_COLUMNS:
        raise ValueError(f"Completeness rule references unknown column: {end_column}")
    return FINAL_COLUMNS[: FINAL_COLUMNS.index(end_column) + 1]


def columns_excluding(ignored_columns: Iterable[str]) -> list[str]:
    ignored = set(ignored_columns)
    return [column for column in FINAL_COLUMNS if column not in ignored]


def build_year_rule_columns() -> dict[int, list[str]]:
    year_columns = {
        year: columns_through(end_column)
        for year, end_column in YEAR_RULE_END_COLUMNS.items()
    }
    year_columns.update(
        {
            year: columns_excluding(ignored_columns)
            for year, ignored_columns in YEAR_RULE_IGNORED_COLUMNS.items()
        }
    )
    return year_columns


def summarize_missing_columns(row: pd.Series, columns: list[str]) -> str:
    return "; ".join(column for column in columns if str(row[column]).strip() == "")


def build_year_completion_summary(df: pd.DataFrame, years: pd.Series) -> pd.DataFrame:
    year_rule_columns = build_year_rule_columns()
    summary = pd.DataFrame(
        {
            "completion_rule_year": years,
            "completion_rule_field_count": 0,
            "completion_rule_missing_count": 0,
            "completion_rule_missing_columns": "",
        },
        index=df.index,
    )

    for year, columns in year_rule_columns.items():
        year_mask = years == year
        if not year_mask.any():
            continue

        year_missing_mask = df.loc[year_mask, columns].apply(lambda col: col.astype(str).str.strip() == "")
        summary.loc[year_mask, "completion_rule_field_count"] = len(columns)
        summary.loc[year_mask, "completion_rule_missing_count"] = year_missing_mask.sum(axis=1).astype(int)
        summary.loc[year_mask, "completion_rule_missing_columns"] = df.loc[year_mask].apply(
            lambda row: summarize_missing_columns(row, columns),
            axis=1,
        )

    return summary


def main() -> None:
    args = parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    df = pd.read_csv(args.input, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    df = df.reindex(columns=FINAL_COLUMNS, fill_value="")
    years = parse_year(df["date"])

    non_blank_mask = df.apply(lambda col: col.astype(str).str.strip() != "")
    non_blank_columns = non_blank_mask.apply(lambda row: {col for col, has_value in row.items() if has_value}, axis=1)
    minimal_set = set(MINIMAL_FIELDS)
    completion_summary = build_year_completion_summary(df, years)

    # Keep fully blank rows out of this rule; only partially started demographic-only rows are removed.
    minimal_only_mask = non_blank_columns.map(lambda cols: bool(cols) and cols.issubset(minimal_set))
    missing_age_range_mask = df["age_range"].astype(str).str.strip() == ""
    low_completion_mask = completion_summary["completion_rule_missing_count"] >= MISSING_VALUE_THRESHOLD
    remove_mask = minimal_only_mask | missing_age_range_mask | low_completion_mask

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
