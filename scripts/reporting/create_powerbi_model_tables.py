from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError as exc:
    raise ImportError(
        "This script requires pandas. Install it with: pip install -r requirements.txt"
    ) from exc

BASE_DIR = Path(__file__).resolve().parents[2]
PIPELINE_DIR = BASE_DIR / "scripts" / "pipeline"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from merge_newlands_surveys import FINAL_COLUMNS


INPUT_FILE = BASE_DIR / "data" / "processed" / "newlands_analysis_ready_filtered.csv"
PILLAR_MAPPING_FILE = BASE_DIR / "metadata" / "pillar_mapping.csv"
OUTPUT_DIR = BASE_DIR / "data" / "powerbi"

FACT_RESPONSES_FILE = OUTPUT_DIR / "fact_survey_responses.csv"
FACT_SCORES_LONG_FILE = OUTPUT_DIR / "fact_survey_scores_long.csv"
DIM_METRIC_FILE = OUTPUT_DIR / "dim_metric.csv"
DIM_PILLAR_FILE = OUTPUT_DIR / "dim_pillar.csv"
DIM_YEAR_FILE = OUTPUT_DIR / "dim_year.csv"

DIMENSION_COLUMNS = [
    "response_id",
    "date",
    "year",
    "postcode",
    "age_range",
    "gender",
    "newlands_resident",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create Power BI-ready fact and dimension tables from the final Newlands survey dataset."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=INPUT_FILE,
        help="Input final analysis-ready CSV.",
    )
    parser.add_argument(
        "--pillar-mapping",
        type=Path,
        default=PILLAR_MAPPING_FILE,
        help="CSV mapping metric columns to pillars.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory for generated Power BI model CSV files.",
    )
    return parser.parse_args()


def load_inputs(input_file: Path, pillar_mapping_file: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    if not pillar_mapping_file.exists():
        raise FileNotFoundError(f"Pillar mapping file not found: {pillar_mapping_file}")

    df = pd.read_csv(input_file, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    df = df.reindex(columns=FINAL_COLUMNS, fill_value="")

    pillar_mapping = pd.read_csv(
        pillar_mapping_file,
        dtype={"column_name": str, "pillar_id": int, "pillar_name": str},
        keep_default_na=False,
        encoding="utf-8-sig",
    )
    return df, pillar_mapping


def validate_mapping(df: pd.DataFrame, pillar_mapping: pd.DataFrame) -> None:
    required_columns = {
        "column_name",
        "pillar_id",
        "pillar_name",
        "metric_label",
        "metric_type",
        "direction",
    }
    missing_mapping_columns = required_columns - set(pillar_mapping.columns)
    if missing_mapping_columns:
        raise ValueError(f"Pillar mapping is missing columns: {sorted(missing_mapping_columns)}")

    duplicate_metrics = pillar_mapping[pillar_mapping["column_name"].duplicated()]["column_name"].tolist()
    if duplicate_metrics:
        raise ValueError(f"Pillar mapping contains duplicate metrics: {duplicate_metrics}")

    missing_from_data = sorted(set(pillar_mapping["column_name"]) - set(df.columns))
    if missing_from_data:
        raise ValueError(f"Pillar mapping references columns not found in input data: {missing_from_data}")

    derived_dimension_columns = {"response_id", "year"}
    input_dimension_columns = set(DIMENSION_COLUMNS) - derived_dimension_columns
    missing_dimension_columns = sorted(input_dimension_columns - set(df.columns))
    if missing_dimension_columns:
        raise ValueError(f"Input data is missing dimension columns: {missing_dimension_columns}")


def build_fact_responses(df: pd.DataFrame) -> pd.DataFrame:
    fact_responses = df.copy()
    fact_responses.insert(0, "response_id", range(1, len(fact_responses) + 1))
    parsed_dates = pd.to_datetime(fact_responses["date"], format="%d/%m/%Y", errors="coerce")
    fact_responses.insert(2, "year", parsed_dates.dt.year.astype("Int64").astype(str).replace("<NA>", ""))
    return fact_responses


def build_dim_year(fact_responses: pd.DataFrame) -> pd.DataFrame:
    years = sorted(
        year for year in fact_responses["year"].dropna().unique().tolist() if str(year).strip()
    )
    dim_year = pd.DataFrame({"year": years})
    dim_year["year_label"] = dim_year["year"].astype(str)
    return dim_year[["year", "year_label"]]


def build_dim_pillar(pillar_mapping: pd.DataFrame) -> pd.DataFrame:
    dim_pillar = (
        pillar_mapping[["pillar_id", "pillar_name"]]
        .drop_duplicates()
        .sort_values("pillar_id")
        .reset_index(drop=True)
    )
    dim_pillar["pillar_sort_order"] = dim_pillar["pillar_id"]
    return dim_pillar[["pillar_id", "pillar_name", "pillar_sort_order"]]


def build_dim_metric(pillar_mapping: pd.DataFrame) -> pd.DataFrame:
    dim_metric = pillar_mapping.copy()
    dim_metric = dim_metric.rename(columns={"column_name": "metric_name"})
    dim_metric["metric_sort_order"] = range(1, len(dim_metric) + 1)
    return dim_metric[
        [
            "metric_name",
            "metric_label",
            "metric_type",
            "direction",
            "pillar_id",
            "pillar_name",
            "metric_sort_order",
        ]
    ]


def build_fact_scores_long(
    fact_responses: pd.DataFrame,
    dim_metric: pd.DataFrame,
) -> pd.DataFrame:
    metric_columns = dim_metric["metric_name"].tolist()

    long_df = fact_responses.melt(
        id_vars=DIMENSION_COLUMNS,
        value_vars=metric_columns,
        var_name="metric_name",
        value_name="metric_value",
    )

    long_df["metric_value"] = pd.to_numeric(long_df["metric_value"], errors="coerce")
    long_df = long_df.merge(
        dim_metric[["metric_name", "pillar_id"]],
        on="metric_name",
        how="left",
        validate="many_to_one",
    )

    return long_df[
        [
            "response_id",
            "date",
            "year",
            "postcode",
            "age_range",
            "gender",
            "newlands_resident",
            "pillar_id",
            "metric_name",
            "metric_value",
        ]
    ]


def write_outputs(
    output_dir: Path,
    fact_responses: pd.DataFrame,
    fact_scores_long: pd.DataFrame,
    dim_metric: pd.DataFrame,
    dim_pillar: pd.DataFrame,
    dim_year: pd.DataFrame,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    fact_responses.to_csv(output_dir / FACT_RESPONSES_FILE.name, index=False, encoding="utf-8-sig")
    fact_scores_long.to_csv(output_dir / FACT_SCORES_LONG_FILE.name, index=False, encoding="utf-8-sig")
    dim_metric.to_csv(output_dir / DIM_METRIC_FILE.name, index=False, encoding="utf-8-sig")
    dim_pillar.to_csv(output_dir / DIM_PILLAR_FILE.name, index=False, encoding="utf-8-sig")
    dim_year.to_csv(output_dir / DIM_YEAR_FILE.name, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    df, pillar_mapping = load_inputs(args.input, args.pillar_mapping)
    validate_mapping(df, pillar_mapping)

    fact_responses = build_fact_responses(df)
    dim_year = build_dim_year(fact_responses)
    dim_pillar = build_dim_pillar(pillar_mapping)
    dim_metric = build_dim_metric(pillar_mapping)
    fact_scores_long = build_fact_scores_long(fact_responses, dim_metric)

    write_outputs(args.output_dir, fact_responses, fact_scores_long, dim_metric, dim_pillar, dim_year)

    print(f"Wrote {len(fact_responses)} rows to {args.output_dir / FACT_RESPONSES_FILE.name}")
    print(f"Wrote {len(fact_scores_long)} rows to {args.output_dir / FACT_SCORES_LONG_FILE.name}")
    print(f"Wrote {len(dim_metric)} rows to {args.output_dir / DIM_METRIC_FILE.name}")
    print(f"Wrote {len(dim_pillar)} rows to {args.output_dir / DIM_PILLAR_FILE.name}")
    print(f"Wrote {len(dim_year)} rows to {args.output_dir / DIM_YEAR_FILE.name}")


if __name__ == "__main__":
    main()
