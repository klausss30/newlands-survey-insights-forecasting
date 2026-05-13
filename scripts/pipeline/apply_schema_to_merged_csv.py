from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

try:
    import pandas as pd
except ImportError as exc:
    raise ImportError(
        "This script requires pandas. Install it with: pip install -r requirements.txt"
    ) from exc

from merge_newlands_surveys import FINAL_COLUMNS, SCHEMA_DICT, clean_string


BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_FILE = BASE_DIR / "data" / "processed" / "merged_newlands_surveys_clean.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "newlands_analysis_ready.csv"


# Normalize age bands so grouping and sorting stay consistent across survey years.
ORDERED_AGE_RANGES = {
    "15 - 18": "15-18",
    "15-18": "15-18",
    "18 - 24": "18-24",
    "18-24": "18-24",
    "25 - 34": "25-34",
    "25-34": "25-34",
    "35 - 44": "35-44",
    "35-44": "35-44",
    "45 - 54": "45-54",
    "45-54": "45-54",
    "55 - 64": "55-64",
    "55-64": "55-64",
    "65 - 74": "65-74",
    "65-74": "65-74",
    "75 - 84": "75-84",
    "75-84": "75-84",
    "85": "85+",
    "85+": "85+",
}


def cast_date(value: str) -> str:
    value = clean_string(value)
    if not value:
        return ""
    return datetime.strptime(value, "%d/%m/%Y").strftime("%d/%m/%Y")


def cast_integer(value: str) -> str:
    value = clean_string(value)
    if not value:
        return ""
    return str(int(round(float(value))))


def cast_categorical(value: str) -> str:
    value = clean_string(value)
    if not value:
        return ""
    lowered = value.lower()
    if lowered == "yes":
        return "Yes"
    if lowered == "no":
        return "No"
    return value


def cast_gender(value: str) -> str:
    value = clean_string(value)
    if not value:
        return "Do not wish to state"
    return cast_categorical(value)


def cast_ordered_categorical(column: str, value: str) -> str:
    value = clean_string(value)
    if not value:
        return ""
    if column == "age_range":
        return ORDERED_AGE_RANGES.get(value, value)
    return value


def cast_value(column: str, value: str) -> str:
    field_type = SCHEMA_DICT[column]["field_type"]

    if field_type == "date":
        return cast_date(value)
    if column == "gender":
        return cast_gender(value)
    if field_type == "integer":
        return cast_integer(value)
    if field_type == "categorical":
        return cast_categorical(value)
    if field_type == "ordered_categorical":
        return cast_ordered_categorical(column, value)
    return clean_string(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply schema casting to merged Newlands survey CSV.")
    parser.add_argument(
        "--input",
        type=Path,
        default=INPUT_FILE,
        help="Input merged CSV file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_FILE,
        help="Output CSV path for the schema-cast file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    df = pd.read_csv(args.input, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    df = df.reindex(columns=FINAL_COLUMNS, fill_value="")

    for column in FINAL_COLUMNS:
        df[column] = df[column].map(lambda value: cast_value(column, value))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False, encoding="utf-8-sig")

    print(f"Wrote {len(df)} rows to {args.output}")


if __name__ == "__main__":
    main()
