# Newlands Community Survey Analytics

## Project Summary

This project turns five years of Newlands community survey data into a clean, reusable analytics asset for community resilience reporting, Power BI dashboards, correlation analysis, and future impact modelling.

The original survey files covered 2019, 2020, 2022, 2024, and 2025. They were not immediately analysis-ready because question formats changed over time, response scales were inconsistent, some answers used text categories, and some responses were only partially completed.

I built a reproducible Python pipeline to clean, harmonise, validate, and filter the data into a final analysis-ready dataset. I also added Power BI-ready model tables and a correlation analysis workflow to explore relationships between survey metrics across six resilience areas.

This is not only a data cleaning project. The main purpose is to create a trusted data foundation that can support future insight generation, modelling, and scenario analysis, including later work on how a new road or infrastructure change may affect the community.

## Why This Project Matters

Community survey data can be difficult to use when each survey round changes slightly. Without a consistent structure, it is hard to compare years, build dashboards, or model relationships between community indicators.

This project addresses that problem by:

- combining five years of raw survey data into one consistent dataset
- standardising question names, response formats, and value scales
- documenting how raw fields map to final analysis fields
- identifying incomplete responses before analysis
- producing quality-control outputs for transparency
- preparing Power BI fact and dimension tables
- exploring relationships between metrics within each resilience area

The result is a reusable data layer that can support reporting, modelling, and future decision-making.

## Data Overview

- Survey years: `2019`, `2020`, `2022`, `2024`, `2025`
- Raw survey responses: `1073`
- Final filtered responses: `609`
- Removed incomplete responses: `464`
- Final analysis fields: `44`
- Resilience areas: `6`

The final filtered dataset is:

- [data/processed/newlands_analysis_ready_filtered.csv](data/processed/newlands_analysis_ready_filtered.csv)

## What I Built

I developed an end-to-end data workflow with three main parts.

### 1. Data Cleaning Pipeline

The pipeline:

1. reads the raw survey CSV files
2. standardises raw column names
3. maps source fields into a fixed final schema
4. harmonises response formats across years
5. converts later-year `0-10` scores to a shared `0-100` scale
6. maps text responses into numeric values where appropriate
7. converts interval-style answers into representative numeric values
8. encodes yes/no fields as binary values
9. removes `postcode` from the analysis schema
10. fills blank `gender` values as `Do not wish to state`
11. removes rows with blank `age_range`
12. applies year-specific row-completeness rules
13. saves removed incomplete rows for audit
14. generates quality-control summaries

### 2. Power BI Model Tables

I created Power BI-ready tables to make dashboard development easier:

- `fact_survey_responses`
- `fact_survey_scores_long`
- `dim_metric`
- `dim_pillar`
- `dim_year`

These outputs support a simple star-schema style reporting model.

### 3. Resilience Area Correlation Analysis

I added a separate analysis script to explore relationships between survey metrics within each resilience area.

The script calculates:

- Pearson correlation
- Spearman correlation
- valid sample size for each metric pair
- relationship strength labels
- missingness by metric
- within-area heatmaps
- a Markdown interpretation report

This helps identify which metrics are closely related, which are more independent, and which may need caution because of missing data.

## Analytical Approach

Several analytical decisions were needed to make the data comparable across years.

### Cross-Year Harmonisation

Earlier survey years mainly used `0-100` numeric scores. Later years introduced `0-10` scales, text categories, and interval responses.

Examples of standardisation:

- `0-10` scores in 2024 and 2025 were scaled to `0-100`
- text categories such as `No`, `Once or twice`, and `Many times` were mapped to numeric values
- interval answers such as `21 - 30`, `31 - 40`, and `50+ hours` were converted into representative numeric values
- yes/no responses were encoded as `1` and `0`
- age bands were standardised into consistent ordered categories
- blank gender values were standardised to `Do not wish to state`
- `postcode` was removed from the analysis-ready schema

### Incomplete Response Handling

Some rows only contained minimal demographic information or too many missing values for the relevant survey year. These rows were removed from the final analysis dataset.

Rows were removed if `age_range` was blank. Rows were also treated as incomplete if they only contained values in:

- `date`
- `age_range`
- `gender`

Additional row-completeness rules are applied by survey year:

- `2019` and `2020`: count missing values through `place_out_of_newlands_disaster_ready`; remove rows with 3 or more missing values
- `2022`: count missing values through `optimal_use_of_land`; remove rows with 3 or more missing values
- `2024`: ignore `vote_general_election_2020`, `vote_local_elections_2019`, and `location`; remove rows with 3 or more missing values
- `2025`: ignore `meaning_and_purpose`, `vote_general_election_2020`, `vote_local_elections_2019`, `personal_mental_health`, and `location`; remove rows with 3 or more missing values

Removed rows are saved in `data/processed/removed_incomplete_responses.csv`.

This reduced the dataset from `1073` rows to `609` final usable rows.

### Correlation Analysis

Correlation was explored within each resilience area rather than only across all variables at once. This makes the results easier to interpret and more useful for future modelling.

Spearman correlation was used as the main relationship measure because many survey fields are ordinal-like, binary, or harmonised survey scores. Pearson correlation is also included as a secondary linear measure.

## Key Findings

The first correlation analysis shows that the six resilience areas have different internal structures.

### Social Resilience Area

The Social area has the strongest internal relationships.

Notable relationships include:

- `be_yourself_in_nz` and `be_yourself_in_newlands` are strongly correlated
- `life_satisfaction`, `meaning_and_purpose`, `family_wellbeing`, and `personal_mental_health` are closely related
- this area is likely to be important for future wellbeing or impact modelling

However, `personal_mental_health` has high missingness, so it should be used carefully.

### Economic Resilience Area

The Economic area shows moderate relationships between:

- `job_satisfaction`
- `satisfaction_income`
- `confident_in_finding_a_new_job`

However, `work_travel_time` does not strongly correlate with most other economic measures. This is useful for future road impact analysis because travel time may still be an important feature even if it does not currently move closely with job or income satisfaction.

### Environment Resilience Area

The Environment area shows moderate relationships between:

- `confident_water_safety`
- `optimal_use_of_land`
- `access_to_natural_environment`

Some environment metrics have high missingness, so these findings need to be interpreted with caution.

### Governance Resilience Area

Governance appears to contain two different themes:

- trust in institutions, such as central government and local council
- civic participation, such as voting behaviour

These should probably not be combined into one simple governance score without further analysis.

### Cultural Resilience Area

The Cultural area has weaker internal relationships. The clearest relationship is between `cultural_activities` and `cultural_knowledge`.

Other cultural variables appear to capture different parts of cultural experience, so they may be better analysed individually.

### Disaster Resilience Area

The Disaster area has weak internal relationships. Its variables appear to represent different types of preparedness rather than one single concept.

This means a simple average score may not be the best way to represent this area.

## Key Outputs

### Final Analysis Dataset

- [data/processed/newlands_analysis_ready_filtered.csv](data/processed/newlands_analysis_ready_filtered.csv)

The final filtered dataset for analysis, reporting, and future modelling.

### Quality-Control Summary

- [data/processed/qc_summary.csv](data/processed/qc_summary.csv)

Summarises missingness, uniqueness, value ranges, and sample values for each final field.

### Metadata

- [metadata/data_dictionary.csv](metadata/data_dictionary.csv)
- [metadata/mapping_log.csv](metadata/mapping_log.csv)
- [metadata/pillar_mapping.csv](metadata/pillar_mapping.csv)

These files document the final schema, source-to-final field mapping, and resilience area mapping.

### Power BI Tables

- [data/powerbi/fact_survey_responses.csv](data/powerbi/fact_survey_responses.csv)
- [data/powerbi/fact_survey_scores_long.csv](data/powerbi/fact_survey_scores_long.csv)
- [data/powerbi/dim_metric.csv](data/powerbi/dim_metric.csv)
- [data/powerbi/dim_pillar.csv](data/powerbi/dim_pillar.csv)
- [data/powerbi/dim_year.csv](data/powerbi/dim_year.csv)

These tables are designed for dashboarding and reporting.

### Correlation Analysis Outputs

- [outputs/correlation_analysis/pillar_correlation_pairs.csv](outputs/correlation_analysis/pillar_correlation_pairs.csv)
- [outputs/correlation_analysis/pillar_metric_missingness_summary.csv](outputs/correlation_analysis/pillar_metric_missingness_summary.csv)
- [outputs/correlation_analysis/pillar_metric_relationship_summary.csv](outputs/correlation_analysis/pillar_metric_relationship_summary.csv)
- [outputs/correlation_analysis/pillar_correlation_report.md](outputs/correlation_analysis/pillar_correlation_report.md)

The correlation output folder also includes heatmaps for each resilience area.

## Repository Structure

```text
.
├── data
│   ├── powerbi
│   │   ├── dim_metric.csv
│   │   ├── dim_pillar.csv
│   │   ├── dim_year.csv
│   │   ├── fact_survey_responses.csv
│   │   └── fact_survey_scores_long.csv
│   ├── processed
│   │   ├── newlands_analysis_ready_filtered.csv
│   │   ├── removed_incomplete_responses.csv
│   │   └── qc_summary.csv
│   └── raw
│       ├── 2019 - Newlands Survey - prep.csv
│       ├── 2020 - Newlands Survey - prep.csv
│       ├── 2022 - Newlands Survey - prep.csv
│       ├── 2024 - Newlands Survey - prep.csv
│       └── 2025 - Newlands Survey - prep.csv
├── metadata
│   ├── data_dictionary.csv
│   ├── mapping_log.csv
│   └── pillar_mapping.csv
├── outputs
│   └── correlation_analysis
├── scripts
│   ├── analysis
│   │   └── explore_pillar_correlations.py
│   ├── modelling
│   ├── pipeline
│   │   ├── apply_schema_to_merged_csv.py
│   │   ├── filter_incomplete_responses.py
│   │   ├── generate_qc_summary.py
│   │   ├── generate_row_completeness_report.py
│   │   ├── merge_newlands_surveys.py
│   │   └── run_pipeline.py
│   └── reporting
│       └── create_powerbi_model_tables.py
├── requirements.txt
└── README.md
```

## How To Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the full cleaning pipeline:

```bash
python scripts/pipeline/run_pipeline.py
```

Generate the resilience area correlation analysis:

```bash
python scripts/analysis/explore_pillar_correlations.py
```

Generate Power BI model tables:

```bash
python scripts/reporting/create_powerbi_model_tables.py
```

If needed, specify a Python interpreter explicitly:

```bash
python scripts/pipeline/run_pipeline.py --python python
```

## Tools Used

- Python
- pandas
- numpy
- scipy
- matplotlib
- seaborn
- Power BI-ready data modelling

## Future Work

Possible next steps include:

- year-over-year trend analysis
- feature selection for modelling
- resilience area score development
- predictive modelling
- scenario analysis for future infrastructure changes
- road impact modelling using travel time, location, and additional external data

## Limitations

- Correlation shows relationship, not causation.
- Some metrics only appear in later survey years.
- Some variables have high missingness and should be used carefully.
- A future road impact model would need additional assumptions or external data, such as road location, affected areas, travel patterns, and before/after timing.
