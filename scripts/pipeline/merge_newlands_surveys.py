from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import pandas as pd
except ImportError as exc:
    raise ImportError(
        "This script requires pandas. Install it with: pip install -r requirements.txt"
    ) from exc


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "merged_newlands_surveys_clean.csv"


SOURCE_TO_FINAL = {
    "1_postcode": "postcode",
    "2_age_range": "age_range",
    "3_gender": "gender",
    "4_language": "language",
    "5_belonging": "belonging",
    "6_cultural_activities": "cultural_activities",
    "7_te_reo": "te_reo",
    "8_cultural_knowledge": "cultural_knowledge",
    "9_trust_nz_government": "trust_nz_government",
    "10_trust_local_council": "trust_local_council",
    "11_trust_nz_police": "trust_nz_police",
    "12_safety": "safety",
    "13_discrimination": "discrimination",
    "14_loneliness": "loneliness",
    "15_independence": "independence",
    "16_support_in_crisis": "support_in_crisis",
    "17_level_of_control": "level_of_control",
    "18_volunteering_time": "volunteering_time",
    "19_paid_working_hours": "paid_working_hours",
    "20_job_satisfaction": "job_satisfaction",
    "21_work_life_balance": "work_life_balance",
    "22_leisure_time": "leisure_time",
    "23_be_yourself_in_nz": "be_yourself_in_nz",
    "24_be_yourself_in_newlands": "be_yourself_in_newlands",
    "25_life_satisfaction": "life_satisfaction",
    "26_meaning_and_purpose": "meaning_and_purpose",
    "27_family_wellbeing": "family_wellbeing",
    "28_access_to_natural_environment": "access_to_natural_environment",
    "29_work_travel_time": "work_travel_time",
    "30_basic_life_skills": "basic_life_skills",
    "31_newlands_resident": "newlands_resident",
    "32_home_disaster_ready": "home_disaster_ready",
    "33_neigbourhood_support_group": "neighbourhood_support_group",
    "34_out_of_newlands_during_day": "out_of_newlands_during_day",
    "35_place_out_of_newland_disaster_ready": "place_out_of_newlands_disaster_ready",
    "38_satisfaction_income": "satisfaction_income",
    "39_confident_in_finding_a_new_job": "confident_in_finding_a_new_job",
    "40_personal_mental_health": "personal_mental_health",
    "41_confident_water_safety": "confident_water_safety",
    "42_optimal_use_of_land": "optimal_use_of_land",
    "37_vote_local_elections_2019": "vote_local_elections_2019",
    "36_vote_general_election_2020": "vote_general_election_2020",
    "45_voted_local_elections_2022": "voted_local_elections_2022",
    "44_voted_general_elections_2023": "voted_general_elections_2023",
}


FINAL_COLUMNS = [
    "date",
    "postcode",
    "age_range",
    "gender",
    "language",
    "belonging",
    "cultural_activities",
    "te_reo",
    "cultural_knowledge",
    "trust_nz_government",
    "trust_local_council",
    "trust_nz_police",
    "safety",
    "discrimination",
    "loneliness",
    "independence",
    "support_in_crisis",
    "level_of_control",
    "volunteering_time",
    "paid_working_hours",
    "job_satisfaction",
    "work_life_balance",
    "leisure_time",
    "be_yourself_in_nz",
    "be_yourself_in_newlands",
    "life_satisfaction",
    "meaning_and_purpose",
    "family_wellbeing",
    "access_to_natural_environment",
    "work_travel_time",
    "basic_life_skills",
    "newlands_resident",
    "home_disaster_ready",
    "neighbourhood_support_group",
    "out_of_newlands_during_day",
    "place_out_of_newlands_disaster_ready",
    "satisfaction_income",
    "confident_in_finding_a_new_job",
    "confident_water_safety",
    "optimal_use_of_land",
    "personal_mental_health",
    "vote_local_elections_2019",
    "vote_general_election_2020",
    "voted_local_elections_2022",
    "voted_general_elections_2023",
]


SCHEMA_DICT = {
    "date": {"field_type": "date", "analysis_role": "time"},
    "postcode": {"field_type": "integer", "analysis_role": "identifier_grouping"},
    "age_range": {"field_type": "ordered_categorical", "analysis_role": "demographic"},
    "gender": {"field_type": "categorical", "analysis_role": "demographic"},
    "language": {"field_type": "integer", "analysis_role": "score"},
    "belonging": {"field_type": "integer", "analysis_role": "score"},
    "cultural_activities": {"field_type": "integer", "analysis_role": "score"},
    "te_reo": {"field_type": "integer", "analysis_role": "score"},
    "cultural_knowledge": {"field_type": "integer", "analysis_role": "score"},
    "trust_nz_government": {"field_type": "integer", "analysis_role": "score"},
    "trust_local_council": {"field_type": "integer", "analysis_role": "score"},
    "trust_nz_police": {"field_type": "integer", "analysis_role": "score"},
    "safety": {"field_type": "integer", "analysis_role": "score"},
    "discrimination": {"field_type": "integer", "analysis_role": "score"},
    "loneliness": {"field_type": "integer", "analysis_role": "score"},
    "independence": {"field_type": "integer", "analysis_role": "score"},
    "support_in_crisis": {"field_type": "integer", "analysis_role": "score"},
    "level_of_control": {"field_type": "integer", "analysis_role": "score"},
    "volunteering_time": {"field_type": "integer", "analysis_role": "score"},
    "paid_working_hours": {"field_type": "integer", "analysis_role": "derived_continuous"},
    "job_satisfaction": {"field_type": "integer", "analysis_role": "score"},
    "work_life_balance": {"field_type": "integer", "analysis_role": "score"},
    "leisure_time": {"field_type": "integer", "analysis_role": "derived_continuous"},
    "be_yourself_in_nz": {"field_type": "integer", "analysis_role": "score"},
    "be_yourself_in_newlands": {"field_type": "integer", "analysis_role": "score"},
    "life_satisfaction": {"field_type": "integer", "analysis_role": "score"},
    "meaning_and_purpose": {"field_type": "integer", "analysis_role": "score"},
    "family_wellbeing": {"field_type": "integer", "analysis_role": "score"},
    "access_to_natural_environment": {"field_type": "integer", "analysis_role": "score"},
    "work_travel_time": {"field_type": "integer", "analysis_role": "derived_continuous"},
    "basic_life_skills": {"field_type": "integer", "analysis_role": "score"},
    "newlands_resident": {"field_type": "integer", "analysis_role": "binary"},
    "home_disaster_ready": {"field_type": "integer", "analysis_role": "binary"},
    "neighbourhood_support_group": {"field_type": "integer", "analysis_role": "binary"},
    "out_of_newlands_during_day": {"field_type": "integer", "analysis_role": "binary"},
    "place_out_of_newlands_disaster_ready": {"field_type": "integer", "analysis_role": "binary"},
    "satisfaction_income": {"field_type": "integer", "analysis_role": "score"},
    "confident_in_finding_a_new_job": {"field_type": "integer", "analysis_role": "score"},
    "confident_water_safety": {"field_type": "integer", "analysis_role": "score"},
    "optimal_use_of_land": {"field_type": "integer", "analysis_role": "score"},
    "personal_mental_health": {"field_type": "integer", "analysis_role": "score"},
    "vote_local_elections_2019": {"field_type": "integer", "analysis_role": "binary"},
    "vote_general_election_2020": {"field_type": "integer", "analysis_role": "binary"},
    "voted_local_elections_2022": {"field_type": "integer", "analysis_role": "binary"},
    "voted_general_elections_2023": {"field_type": "integer", "analysis_role": "binary"},
}


SCORE_COLUMNS = {
    "language",
    "belonging",
    "trust_nz_government",
    "trust_local_council",
    "trust_nz_police",
    "safety",
    "independence",
    "support_in_crisis",
    "level_of_control",
    "job_satisfaction",
    "work_life_balance",
    "be_yourself_in_nz",
    "be_yourself_in_newlands",
    "life_satisfaction",
    "meaning_and_purpose",
    "family_wellbeing",
    "access_to_natural_environment",
    "basic_life_skills",
    "satisfaction_income",
    "confident_in_finding_a_new_job",
    "confident_water_safety",
    "optimal_use_of_land",
    "personal_mental_health",
}


# Text answers are mapped onto the shared 0-100 scale used for year-over-year analysis.
TEXT_MAPPINGS = {
    "cultural_activities": {
        "no": 0,
        "once or twice": 30,
        "many times": 50,
    },
    "te_reo": {
        "very poorly": 0,
        "very poorly, if at all": 0,
        "moderate": 50,
        "moderate ability": 50,
        "very well": 80,
        "fluent speaker": 90,
    },
    "cultural_knowledge": {
        "none": 0,
        "once or twice": 30,
        "many times": 50,
    },
    "discrimination": {
        "none": 0,
        "once or twice": 30,
        "many times": 50,
    },
    "loneliness": {
        "not once": 0,
        "occasionally": 50,
        "frequently": 80,
        "very frequently": 90,
    },
    "volunteering_time": {
        "not at all": 0,
        "occasionally": 50,
        "frequently": 80,
        "very frequently": 90,
    },
}


# Interval answers are converted to representative numeric values for continuous fields.
INTERVAL_MAPPINGS = {
    "jan-20": 20,
    "1 to 20": 20,
    "0 hours": 0,
    "0": 0,
    "0 - 20": 20,
    "0-20": 20,
    "1 - 20": 20,
    "1-20": 20,
    "20 to 30": 25,
    "21 - 30": 25,
    "21-30": 25,
    "31 - 40": 35,
    "31-40": 35,
    "41 - 50": 45,
    "41-50": 45,
    "51 - 60": 55,
    "51-60": 55,
    "50+ hours": 60,
    "50+": 60,
    "60+ minutes": 60,
    "60+": 60,
    "61-70": 60,
    "61 - 70": 60,
    "71-80": 75,
    "71 - 80": 75,
    "80+": 80,
}


YES_NO_COLUMNS = {
    "newlands_resident",
    "home_disaster_ready",
    "neighbourhood_support_group",
    "out_of_newlands_during_day",
    "place_out_of_newlands_disaster_ready",
    "vote_local_elections_2019",
    "vote_general_election_2020",
    "voted_local_elections_2022",
    "voted_general_elections_2023",
}


INTERVAL_COLUMNS = {
    "paid_working_hours",
    "work_travel_time",
    "leisure_time",
}


def clean_string(value: Optional[str]) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_column_name(name: str) -> str:
    name = clean_string(name).lower()
    name = name.replace(".", "")
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def parse_date(value: str) -> str:
    value = clean_string(value)
    if not value:
        return ""

    formats = [
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %I:%M %p",
        "%m/%d/%Y %H:%M:%S %p",
        "%m/%d/%Y",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue

    raise ValueError(f"Unrecognized Timestamp format: {value}")


def parse_number(value: str) -> Optional[float]:
    value = clean_string(value)
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def format_number(value: Optional[float]) -> str:
    if value is None:
        return ""
    if float(value).is_integer():
        return str(int(value))
    return str(value)


def encode_yes_no(value: str) -> str:
    value = clean_string(value).lower()
    if not value:
        return ""
    if value == "yes":
        return "1"
    if value == "no":
        return "0"
    raise ValueError(f"Unknown yes/no value: {value}")


def normalize_interval_key(value: str) -> str:
    value = clean_string(value).lower()
    value = value.replace("minutes", "").replace("minute", "")
    value = value.replace("hours", "").replace("hour", "")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def map_interval(value: str, cap: Optional[int] = None) -> str:
    value = clean_string(value)
    if not value:
        return ""

    numeric = parse_number(value)
    if numeric is not None:
        mapped = numeric
    else:
        key = normalize_interval_key(value)
        if key in INTERVAL_MAPPINGS:
            mapped = INTERVAL_MAPPINGS[key]
        else:
            range_match = re.fullmatch(r"(\d+)\s*(?:-|to)\s*(\d+)", key)
            plus_match = re.fullmatch(r"(\d+)\+", key)
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2))
                mapped = end if start <= 1 else round((start + end) / 2 / 5) * 5
            elif plus_match:
                start = int(plus_match.group(1))
                mapped = start
            else:
                raise ValueError(f"Unknown interval value: {value}")

    # Caps keep open-ended ranges comparable across years without overstating high values.
    if cap is not None:
        mapped = min(mapped, cap)
    return format_number(mapped)


def map_text_value(column: str, value: str) -> str:
    value = clean_string(value)
    if not value:
        return ""

    numeric = parse_number(value)
    if numeric is not None:
        return format_number(numeric)

    mapping = TEXT_MAPPINGS[column]
    key = value.lower()
    if key not in mapping:
        raise ValueError(f"Unknown text mapping for {column}: {value}")
    return format_number(mapping[key])


def map_score_value(value: str, year: int) -> str:
    numeric = parse_number(value)
    if numeric is None:
        return ""
    # The 2024 and 2025 surveys use 0-10 scales; earlier years already use 0-100.
    if year in {2024, 2025} and numeric <= 10:
        numeric *= 10
    return format_number(numeric)


def map_postcode(value: str) -> str:
    numeric = parse_number(value)
    if numeric is None:
        return ""
    return format_number(numeric)


def transform_value(column: str, value: str, year: int) -> str:
    if column == "date":
        return parse_date(value)
    if column == "postcode":
        return map_postcode(value)
    if column in {"age_range", "gender"}:
        return clean_string(value)
    if column in YES_NO_COLUMNS:
        return encode_yes_no(value)
    if column == "paid_working_hours":
        return map_interval(value, cap=60)
    if column in {"work_travel_time", "leisure_time"}:
        return map_interval(value, cap=60)
    if column in TEXT_MAPPINGS:
        return map_text_value(column, value)
    if column in SCORE_COLUMNS:
        return map_score_value(value, year)
    return clean_string(value)


def build_output_row(source_row: dict[str, str], year: int) -> dict[str, str]:
    output = {column: "" for column in FINAL_COLUMNS}
    output["date"] = transform_value("date", source_row.get("timestamp", ""), year)

    for source_column, final_column in SOURCE_TO_FINAL.items():
        if final_column not in output:
            continue
        output[final_column] = transform_value(final_column, source_row.get(source_column, ""), year)

    return output


def process_file(file_path: Path) -> pd.DataFrame:
    year = int(file_path.name[:4])
    df = pd.read_csv(file_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    df.columns = [normalize_column_name(column) for column in df.columns]

    rows = [build_output_row(row, year) for row in df.to_dict(orient="records")]
    return pd.DataFrame(rows, columns=FINAL_COLUMNS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge and clean Newlands survey CSV files.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=RAW_DIR,
        help="Directory containing raw survey CSV files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_FILE,
        help="Output CSV path for the merged clean file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    files = sorted(args.input_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {args.input_dir}")

    merged_df = pd.concat([process_file(file_path) for file_path in files], ignore_index=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(args.output, index=False, encoding="utf-8-sig")

    print(f"Wrote {len(merged_df)} rows to {args.output}")


if __name__ == "__main__":
    main()
