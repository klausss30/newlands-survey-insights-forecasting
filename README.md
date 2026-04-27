# Newlands Survey Insights and Forecasting

## Overview

This project turns five years of Newlands community survey data into a structured analytics asset that can support reporting, dashboarding, and future predictive modeling.

The raw survey files covered 2019, 2020, 2022, 2024, and 2025, but the data was not analysis-ready. Response formats changed across years, scales were inconsistent, some fields used free-text style categories, and incomplete responses needed to be identified and handled before the data could be trusted for downstream analysis.

I built a reproducible Python and pandas pipeline to clean, harmonize, validate, and filter the survey data into a final analysis-ready dataset. The longer-term purpose of the project is to support:

- clearer year-over-year community insights
- Power BI reporting and stakeholder-facing dashboards
- future predictive modeling
- better survey design and reporting decisions in later survey rounds

## Business Impact

This project is designed around a practical analytics use case rather than a one-off cleaning exercise.

By standardizing the raw data into one consistent structure, the project creates a foundation for:

- comparing survey results across multiple years
- identifying which indicators are most useful for reporting and decision-making
- reducing reporting friction by producing a reusable, analysis-ready dataset
- improving future survey design by showing where missingness, inconsistency, or weak response patterns appear
- enabling future forecasting and modeling work on top of a trusted data layer

In other words, the value of the project is not only in cleaning the data, but in making the survey program more useful for future insight generation.

## What I Built

I developed an end-to-end survey processing pipeline that:

1. ingests five raw CSV survey files
2. standardizes raw column names into lowercase snake_case
3. maps raw survey fields into a fixed final schema of 45 columns
4. harmonizes mixed response formats across years
5. applies schema rules for dates, integers, categorical variables, and ordered categorical variables
6. generates field-level quality-control outputs
7. identifies incomplete responses at the row level
8. removes records that only contain minimal demographic fields and no substantive survey answers
9. produces a final filtered dataset ready for analysis

## Data Processing Decisions

### Cross-year harmonization

Earlier survey files used `0-100` numeric scales, while later files introduced `0-10` scales, text categories, and interval-style values. I standardized those formats so the data could be compared across years.

Examples:

- 2019, 2020, and 2022 `0-100` values were retained
- 2024 and 2025 `0-10` values were scaled to `0-100`
- text categories such as `No`, `Once or twice`, and `Many times` were mapped to numeric values
- interval values such as `21 - 30` and `50+ hours` were converted into representative numeric values

### Incomplete response handling

I added a row-level completeness review and filtered out responses that only contained:

- `date`
- `postcode`
- `age_range`
- `gender`

with no substantive survey answers.

This resulted in:

- `1073` rows in the initial analysis-ready dataset
- `1055` rows in the final filtered analysis dataset
- `18` rows removed under the incomplete-response rule

## Key Deliverables

These are the four main outputs I would highlight in a portfolio or CV context.

### 1. Final analysis-ready dataset

- [data/processed/newlands_analysis_ready_filtered.csv](/Users/klaus/Desktop/data%20analysis/data/processed/newlands_analysis_ready_filtered.csv)

This is the final filtered dataset intended for downstream analysis, dashboarding, and future modeling.

### 2. Data dictionary

- [metadata/data_dictionary.csv](/Users/klaus/Desktop/data%20analysis/metadata/data_dictionary.csv)

Defines field meaning, field types, analysis roles, allowed values, and notes.

### 3. Mapping log

- [metadata/mapping_log.csv](/Users/klaus/Desktop/data%20analysis/metadata/mapping_log.csv)

Documents how raw source fields were transformed into final analysis fields.

### 4. QC summary

- [data/processed/qc_summary.csv](/Users/klaus/Desktop/data%20analysis/data/processed/qc_summary.csv)

Summarizes missingness, uniqueness, ranges, and example values for the final filtered dataset.

## Technical Highlights

This project demonstrates:

- multi-file data ingestion
- longitudinal survey harmonization
- schema design
- rule-based recoding
- reproducible pipeline design
- pandas-based data cleaning
- row-level completeness filtering
- QC and validation workflow
- metadata documentation for reproducibility

## Repository Structure

```text
.
├── data
│   ├── processed
│   │   ├── newlands_analysis_ready_filtered.csv
│   │   └── qc_summary.csv
│   └── raw
│       ├── 2019 - Newlands Survey - prep.csv
│       ├── 2020 - Newlands Survey - prep.csv
│       ├── 2022 - Newlands Survey - prep.csv
│       ├── 2024 - Newlands Survey - prep.csv
│       └── 2025 - Newlands Survey - prep.csv
├── metadata
│   ├── data_dictionary.csv
│   └── mapping_log.csv
├── scripts
│   ├── apply_schema_to_merged_csv.py
│   ├── filter_incomplete_responses.py
│   ├── generate_qc_summary.py
│   ├── generate_row_completeness_report.py
│   ├── merge_newlands_surveys.py
│   └── run_pipeline.py
├── requirements.txt
└── README.md
```

## How To Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the full pipeline:

```bash
python scripts/run_pipeline.py
```

If needed, explicitly specify the Python interpreter:

```bash
python scripts/run_pipeline.py --python python
```

## Next Steps

This repository is intended to expand beyond cleaning into:

- Power BI dashboards
- trend analysis across years
- predictive modeling and forecasting
- recommendations for improving future survey structure and reporting outputs

## Notes

- Blank values are preserved as blank rather than imputed.
- `discrimination` and `loneliness` intentionally keep a direction where higher values indicate more severe problems.
- The pipeline is built to be rerun as new survey years are added.
