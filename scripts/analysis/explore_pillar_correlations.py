from __future__ import annotations

import argparse
import itertools
import re
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import seaborn as sns
    from scipy import stats
except ImportError as exc:
    raise ImportError(
        "This script requires pandas, numpy, scipy, matplotlib, and seaborn. "
        "Install them with: pip install -r requirements.txt"
    ) from exc


BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_FILE = BASE_DIR / "data" / "processed" / "newlands_analysis_ready_filtered.csv"
PILLAR_MAPPING_FILE = BASE_DIR / "metadata" / "pillar_mapping.csv"
OUTPUT_DIR = BASE_DIR / "outputs" / "correlation_analysis"


STRENGTH_BANDS = [
    (0.70, "strong"),
    (0.40, "moderate"),
    (0.20, "weak"),
    (0.00, "very weak"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Explore within-pillar correlations for Newlands survey metrics."
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
        help="Directory for correlation outputs.",
    )
    parser.add_argument(
        "--min-pair-n",
        type=int,
        default=30,
        help="Minimum valid pair count for a relationship to be highlighted.",
    )
    return parser.parse_args()


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def classify_strength(correlation: float) -> str:
    if pd.isna(correlation):
        return "not enough data"
    abs_corr = abs(correlation)
    for threshold, label in STRENGTH_BANDS:
        if abs_corr >= threshold:
            return label
    return "very weak"


def load_inputs(input_file: Path, pillar_mapping_file: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    if not pillar_mapping_file.exists():
        raise FileNotFoundError(f"Pillar mapping file not found: {pillar_mapping_file}")

    df = pd.read_csv(input_file, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    mapping = pd.read_csv(pillar_mapping_file, dtype=str, keep_default_na=False, encoding="utf-8-sig")

    required_columns = {
        "column_name",
        "pillar_id",
        "pillar_name",
        "metric_label",
        "metric_type",
        "direction",
    }
    missing_columns = required_columns - set(mapping.columns)
    if missing_columns:
        raise ValueError(f"Pillar mapping is missing columns: {sorted(missing_columns)}")

    missing_metrics = sorted(set(mapping["column_name"]) - set(df.columns))
    if missing_metrics:
        raise ValueError(f"Pillar mapping references columns not in input data: {missing_metrics}")

    duplicate_metrics = mapping[mapping["column_name"].duplicated()]["column_name"].tolist()
    if duplicate_metrics:
        raise ValueError(f"Pillar mapping contains duplicate metrics: {duplicate_metrics}")

    return df, mapping


def build_numeric_metric_frame(df: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    metrics = mapping["column_name"].tolist()
    numeric_df = df[metrics].replace("", np.nan).apply(pd.to_numeric, errors="coerce")
    return numeric_df


def summarize_missingness(numeric_df: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total_rows = len(numeric_df)
    for record in mapping.to_dict(orient="records"):
        column = record["column_name"]
        series = numeric_df[column]
        non_missing = int(series.notna().sum())
        missing = total_rows - non_missing
        rows.append(
            {
                "pillar_id": record["pillar_id"],
                "pillar_name": record["pillar_name"],
                "metric_name": column,
                "metric_label": record["metric_label"],
                "metric_type": record["metric_type"],
                "direction": record["direction"],
                "row_count": total_rows,
                "valid_n": non_missing,
                "missing_count": missing,
                "missing_pct": round(missing / total_rows * 100, 2) if total_rows else np.nan,
                "mean": round(series.mean(), 2) if non_missing else np.nan,
                "median": round(series.median(), 2) if non_missing else np.nan,
                "std": round(series.std(), 2) if non_missing > 1 else np.nan,
                "min": round(series.min(), 2) if non_missing else np.nan,
                "max": round(series.max(), 2) if non_missing else np.nan,
            }
        )
    return pd.DataFrame(rows)


def safe_corr(x: pd.Series, y: pd.Series, method: str) -> float:
    pair = pd.concat([x, y], axis=1).dropna()
    if len(pair) < 2:
        return np.nan
    if pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
        return np.nan
    if method == "pearson":
        return float(pair.iloc[:, 0].corr(pair.iloc[:, 1], method="pearson"))
    if method == "spearman":
        result = stats.spearmanr(pair.iloc[:, 0], pair.iloc[:, 1], nan_policy="omit")
        return float(result.statistic)
    raise ValueError(f"Unknown correlation method: {method}")


def build_pairwise_correlations(
    numeric_df: pd.DataFrame,
    mapping: pd.DataFrame,
    min_pair_n: int,
) -> pd.DataFrame:
    rows = []
    for pillar_name, pillar_mapping in mapping.groupby("pillar_name", sort=False):
        metrics = pillar_mapping["column_name"].tolist()
        metric_meta = pillar_mapping.set_index("column_name").to_dict(orient="index")

        for metric_1, metric_2 in itertools.combinations(metrics, 2):
            pair = numeric_df[[metric_1, metric_2]].dropna()
            valid_n = len(pair)
            pearson = safe_corr(numeric_df[metric_1], numeric_df[metric_2], "pearson")
            spearman = safe_corr(numeric_df[metric_1], numeric_df[metric_2], "spearman")

            rows.append(
                {
                    "pillar_id": metric_meta[metric_1]["pillar_id"],
                    "pillar_name": pillar_name,
                    "metric_1": metric_1,
                    "metric_1_label": metric_meta[metric_1]["metric_label"],
                    "metric_1_type": metric_meta[metric_1]["metric_type"],
                    "metric_1_direction": metric_meta[metric_1]["direction"],
                    "metric_2": metric_2,
                    "metric_2_label": metric_meta[metric_2]["metric_label"],
                    "metric_2_type": metric_meta[metric_2]["metric_type"],
                    "metric_2_direction": metric_meta[metric_2]["direction"],
                    "valid_n": valid_n,
                    "pearson_corr": round(pearson, 4) if not pd.isna(pearson) else np.nan,
                    "spearman_corr": round(spearman, 4) if not pd.isna(spearman) else np.nan,
                    "relationship_strength": classify_strength(spearman),
                    "highlight_flag": valid_n >= min_pair_n and not pd.isna(spearman) and abs(spearman) >= 0.4,
                    "low_pair_n_flag": valid_n < min_pair_n,
                }
            )

    pairwise_df = pd.DataFrame(rows)
    if not pairwise_df.empty:
        pairwise_df["abs_spearman_corr"] = pairwise_df["spearman_corr"].abs()
        pairwise_df = pairwise_df.sort_values(
            ["pillar_id", "abs_spearman_corr", "valid_n"],
            ascending=[True, False, False],
        )
    return pairwise_df


def build_metric_relationship_summary(pairwise_df: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for record in mapping.to_dict(orient="records"):
        metric = record["column_name"]
        related = pairwise_df[(pairwise_df["metric_1"] == metric) | (pairwise_df["metric_2"] == metric)].copy()
        usable = related[~related["spearman_corr"].isna()].copy()
        usable = usable[~usable["low_pair_n_flag"]]

        if usable.empty:
            avg_abs_spearman = np.nan
            max_abs_spearman = np.nan
            strongest_partner = ""
            strongest_spearman = np.nan
            strong_or_moderate_count = 0
        else:
            usable["partner"] = np.where(
                usable["metric_1"] == metric,
                usable["metric_2"],
                usable["metric_1"],
            )
            strongest = usable.sort_values("abs_spearman_corr", ascending=False).iloc[0]
            avg_abs_spearman = round(usable["abs_spearman_corr"].mean(), 4)
            max_abs_spearman = round(strongest["abs_spearman_corr"], 4)
            strongest_partner = strongest["partner"]
            strongest_spearman = strongest["spearman_corr"]
            strong_or_moderate_count = int((usable["abs_spearman_corr"] >= 0.4).sum())

        rows.append(
            {
                "pillar_id": record["pillar_id"],
                "pillar_name": record["pillar_name"],
                "metric_name": metric,
                "metric_label": record["metric_label"],
                "metric_type": record["metric_type"],
                "direction": record["direction"],
                "avg_abs_spearman_within_pillar": avg_abs_spearman,
                "max_abs_spearman_within_pillar": max_abs_spearman,
                "strongest_partner": strongest_partner,
                "strongest_partner_spearman": strongest_spearman,
                "strong_or_moderate_relationship_count": strong_or_moderate_count,
            }
        )
    return pd.DataFrame(rows)


def plot_heatmaps(numeric_df: pd.DataFrame, mapping: pd.DataFrame, output_dir: Path) -> list[Path]:
    sns.set_theme(style="white", font_scale=0.8)
    heatmap_paths = []

    for pillar_name, pillar_mapping in mapping.groupby("pillar_name", sort=False):
        metrics = pillar_mapping["column_name"].tolist()
        if len(metrics) < 2:
            continue

        corr = numeric_df[metrics].corr(method="spearman", min_periods=2)
        labels = pillar_mapping.set_index("column_name").loc[metrics, "metric_label"].tolist()
        corr.index = labels
        corr.columns = labels

        size = max(7, min(16, 0.55 * len(metrics) + 4))
        fig, ax = plt.subplots(figsize=(size, size * 0.85))
        sns.heatmap(
            corr,
            ax=ax,
            cmap="vlag",
            vmin=-1,
            vmax=1,
            center=0,
            square=True,
            linewidths=0.4,
            cbar_kws={"label": "Spearman correlation"},
        )
        ax.set_title(f"{pillar_name} pillar: within-pillar Spearman correlations", pad=14)
        ax.tick_params(axis="x", rotation=45)
        ax.tick_params(axis="y", rotation=0)
        fig.tight_layout()

        output_path = output_dir / f"heatmap_{slugify(pillar_name)}.png"
        fig.savefig(output_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        heatmap_paths.append(output_path)

    return heatmap_paths


def format_corr(value: float) -> str:
    if pd.isna(value):
        return "NA"
    return f"{value:.2f}"


def write_markdown_report(
    output_dir: Path,
    missingness_df: pd.DataFrame,
    pairwise_df: pd.DataFrame,
    metric_summary_df: pd.DataFrame,
    mapping: pd.DataFrame,
    min_pair_n: int,
) -> Path:
    report_path = output_dir / "pillar_correlation_report.md"
    lines = [
        "# Pillar Correlation and Relationship Exploration",
        "",
        "This report explores within-pillar relationships across Newlands survey metrics.",
        "Spearman correlation is used as the main relationship measure because many survey metrics are ordinal-like scores, binary fields, or harmonized survey scales. Pearson correlation is included in the CSV output as a secondary linear measure.",
        "",
        "Relationship bands used in this report:",
        "",
        "- Strong: absolute Spearman correlation >= 0.70",
        "- Moderate: absolute Spearman correlation >= 0.40 and < 0.70",
        "- Weak: absolute Spearman correlation >= 0.20 and < 0.40",
        "- Very weak: absolute Spearman correlation < 0.20",
        "",
        f"Pairs with fewer than {min_pair_n} valid paired responses are flagged as low sample size.",
        "",
    ]

    for pillar_name, pillar_mapping in mapping.groupby("pillar_name", sort=False):
        pillar_pairs = pairwise_df[pairwise_df["pillar_name"] == pillar_name].copy()
        pillar_missing = missingness_df[missingness_df["pillar_name"] == pillar_name].copy()
        pillar_metric_summary = metric_summary_df[metric_summary_df["pillar_name"] == pillar_name].copy()

        lines.extend([f"## {pillar_name}", ""])
        lines.append(f"Metrics in this pillar: {len(pillar_mapping)}")
        lines.append("")

        high_missing = pillar_missing[pillar_missing["missing_pct"] >= 50].sort_values("missing_pct", ascending=False)
        if high_missing.empty:
            lines.append("No metrics in this pillar have missingness above 50%.")
        else:
            lines.append("Metrics with high missingness:")
            for row in high_missing.itertuples(index=False):
                lines.append(f"- {row.metric_label}: {row.missing_pct:.2f}% missing")
        lines.append("")

        highlighted = pillar_pairs[pillar_pairs["highlight_flag"]].sort_values(
            "abs_spearman_corr", ascending=False
        )
        if highlighted.empty:
            lines.append("No moderate or strong relationships met the valid sample threshold.")
        else:
            lines.append("Moderate and strong relationships:")
            for row in highlighted.head(10).itertuples(index=False):
                lines.append(
                    f"- {row.metric_1_label} and {row.metric_2_label}: "
                    f"Spearman {format_corr(row.spearman_corr)}, "
                    f"Pearson {format_corr(row.pearson_corr)}, "
                    f"valid n={row.valid_n}, {row.relationship_strength}"
                )
        lines.append("")

        independent = pillar_metric_summary.sort_values(
            "avg_abs_spearman_within_pillar",
            na_position="last",
        ).head(3)
        lines.append("Most independent metrics by average absolute within-pillar Spearman correlation:")
        for row in independent.itertuples(index=False):
            lines.append(
                f"- {row.metric_label}: average abs Spearman "
                f"{format_corr(row.avg_abs_spearman_within_pillar)}"
            )
        lines.append("")

        direction_notes = pillar_mapping[
            pillar_mapping["direction"].str.contains("problematic|severe", case=False, na=False)
        ]
        if not direction_notes.empty:
            lines.append("Direction notes:")
            for row in direction_notes.itertuples(index=False):
                lines.append(
                    f"- {row.metric_label} should be interpreted carefully: {row.direction}."
                )
            lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df, mapping = load_inputs(args.input, args.pillar_mapping)
    numeric_df = build_numeric_metric_frame(df, mapping)

    missingness_df = summarize_missingness(numeric_df, mapping)
    pairwise_df = build_pairwise_correlations(numeric_df, mapping, args.min_pair_n)
    metric_summary_df = build_metric_relationship_summary(pairwise_df, mapping)
    heatmap_paths = plot_heatmaps(numeric_df, mapping, args.output_dir)
    report_path = write_markdown_report(
        args.output_dir,
        missingness_df,
        pairwise_df,
        metric_summary_df,
        mapping,
        args.min_pair_n,
    )

    missingness_path = args.output_dir / "pillar_metric_missingness_summary.csv"
    pairwise_path = args.output_dir / "pillar_correlation_pairs.csv"
    metric_summary_path = args.output_dir / "pillar_metric_relationship_summary.csv"

    missingness_df.to_csv(missingness_path, index=False, encoding="utf-8-sig")
    pairwise_df.to_csv(pairwise_path, index=False, encoding="utf-8-sig")
    metric_summary_df.to_csv(metric_summary_path, index=False, encoding="utf-8-sig")

    print(f"Wrote metric missingness summary to {missingness_path}")
    print(f"Wrote pairwise correlations to {pairwise_path}")
    print(f"Wrote metric relationship summary to {metric_summary_path}")
    print(f"Wrote Markdown report to {report_path}")
    print(f"Wrote {len(heatmap_paths)} heatmaps to {args.output_dir}")


if __name__ == "__main__":
    main()
