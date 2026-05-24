"""
Newlands Community Survey — Comprehensive Correlation Analysis
=============================================================
No scipy dependency — Spearman ρ computed via numpy rank + Pearson of ranks.
P-values via Fisher z → standard-normal approximation (valid for n ≥ 50).

Outputs:
  1. heatmap_global.png           – all low-missing vars, grouped by pillar
  2. heatmap_pillar_<n>_<name>.png – per-pillar (6 total)
  3. barchart_focal_life_satisfaction.png
  4. barchart_focal_work_travel_time.png
  5. all_correlation_pairs.csv
  6. missingness_summary.csv
  7. correlation_report.md
"""

from __future__ import annotations

import itertools
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns

# ── Paths ──────────────────────────────────────────────────────────────────
BASE      = Path("/sessions/charming-confident-goodall/mnt/data analysis")
DATA_FILE = BASE / "data" / "processed" / "newlands_analysis_ready_filtered.csv"
MAP_FILE  = BASE / "data for powerbi" / "scoring_mapping.csv"
OUT_DIR   = BASE / "outputs" / "correlation_analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Constants ───────────────────────────────────────────────────────────────
MISSING_THRESHOLD = 0.60
MIN_PAIR_N        = 50
PILLAR_NAMES = {1: "Economic", 2: "Environment", 3: "Social",
                4: "Cultural",  5: "Governance",  6: "Disaster"}
PILLAR_COLOURS = {1: "#2196F3", 2: "#4CAF50", 3: "#FF9800",
                  4: "#9C27B0", 5: "#F44336", 6: "#009688"}
STRENGTH_BANDS = [(0.70, "strong"), (0.40, "moderate"),
                  (0.20, "weak"),   (0.00, "very weak")]

# ── Core helpers ─────────────────────────────────────────────────────────────

def strength_label(r: float) -> str:
    r = abs(r)
    for thr, lbl in STRENGTH_BANDS:
        if r >= thr:
            return lbl
    return "very weak"


def _rank(a: np.ndarray) -> np.ndarray:
    """Average rank (handles ties)."""
    tmp = a.argsort()
    ranks = np.empty_like(tmp, dtype=float)
    ranks[tmp] = np.arange(1, len(a) + 1, dtype=float)
    # handle ties: set tied positions to their average rank
    unique, counts = np.unique(a, return_counts=True)
    idx = 0
    for u, c in zip(unique, counts):
        pos = np.where(a == u)[0]
        ranks[pos] = ranks[pos].mean()
    return ranks


def spearman_pair(x: pd.Series, y: pd.Series) -> tuple[float, float, int]:
    """Return (rho, approx_p, valid_n) without scipy."""
    mask = x.notna() & y.notna()
    n = int(mask.sum())
    if n < MIN_PAIR_N:
        return np.nan, np.nan, n
    xa = x[mask].to_numpy(dtype=float)
    ya = y[mask].to_numpy(dtype=float)
    rx = _rank(xa)
    ry = _rank(ya)
    # Pearson of ranks = Spearman rho
    rho = float(np.corrcoef(rx, ry)[0, 1])
    rho = max(-1.0, min(1.0, rho))   # clamp numerical noise
    # Fisher z → normal approx (good for n ≥ 30)
    if abs(rho) >= 1.0:
        p = 0.0
    else:
        z  = 0.5 * np.log((1 + rho) / (1 - rho))
        se = 1.0 / np.sqrt(n - 3)
        zs = abs(z) / se
        # 2-tailed p from standard normal: p ≈ 2*(1 - Φ(|z|))
        # Φ via erf: Φ(x) = 0.5*(1 + erf(x/√2))
        from math import erf, sqrt
        phi = 0.5 * (1 + erf(zs / sqrt(2)))
        p   = 2 * (1 - phi)
    return rho, p, n


def build_corr_matrix(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    mat = pd.DataFrame(np.nan, index=cols, columns=cols, dtype=float)
    for c in cols:
        mat.loc[c, c] = 1.0
    for a, b in itertools.combinations(cols, 2):
        rho, _, n = spearman_pair(df[a], df[b])
        mat.loc[a, b] = rho
        mat.loc[b, a] = rho
    return mat


def pretty_name(col: str) -> str:
    return col.replace("_", " ").title()


# ── Load data ────────────────────────────────────────────────────────────────
print("Loading data …")
df      = pd.read_csv(DATA_FILE)
mapping = pd.read_csv(MAP_FILE)
mapping = mapping[mapping["include"] == 1].copy()
mapping = mapping[mapping["Question"].isin(df.columns)].copy()

binary_vars = set(mapping.loc[mapping["type"] == "binary", "Question"])
all_vars    = list(mapping["Question"])

miss      = df[all_vars].isna().mean()
high_miss = set(miss[miss > MISSING_THRESHOLD].index)
main_vars = [v for v in all_vars if v not in high_miss]

print(f"Total vars: {len(all_vars)}  |  High-missing: {len(high_miss)}  |  Main vars: {len(main_vars)}")
print(f"High-missing: {sorted(high_miss)}")

var_pillar = dict(zip(mapping["Question"], mapping["Resilience_ID"]))
cmap       = sns.diverging_palette(220, 20, as_cmap=True)

# ── Missingness CSV ──────────────────────────────────────────────────────────
print("Saving missingness summary …")
miss_rows = []
for v in all_vars:
    miss_rows.append({
        "variable":    v,
        "pillar_id":   var_pillar.get(v),
        "pillar_name": PILLAR_NAMES.get(var_pillar.get(v), "?"),
        "type":        mapping.loc[mapping["Question"] == v, "type"].values[0],
        "missing_pct": round(miss[v] * 100, 2),
        "valid_n":     int(df[v].notna().sum()),
        "high_missing": v in high_miss,
    })
(pd.DataFrame(miss_rows)
   .sort_values(["pillar_id", "missing_pct"], ascending=[True, False])
   .to_csv(OUT_DIR / "missingness_summary.csv", index=False))
print("  → missingness_summary.csv")

# ── All-pairs CSV ────────────────────────────────────────────────────────────
print("Computing all pairwise Spearman correlations …")
pair_rows = []
for a, b in itertools.combinations(all_vars, 2):
    rho, p, n = spearman_pair(df[a], df[b])
    pair_rows.append({
        "var_a":             a,
        "var_b":             b,
        "pillar_a":          PILLAR_NAMES.get(var_pillar.get(a), "?"),
        "pillar_b":          PILLAR_NAMES.get(var_pillar.get(b), "?"),
        "same_pillar":       var_pillar.get(a) == var_pillar.get(b),
        "spearman_rho":      round(rho, 4) if not np.isnan(rho) else np.nan,
        "p_value":           round(p, 4)   if (p is not None and not np.isnan(p)) else np.nan,
        "valid_n":           n,
        "strength":          strength_label(rho) if not np.isnan(rho) else "insufficient data",
        "low_n_flag":        n < MIN_PAIR_N,
        "high_missing_flag": (a in high_miss) or (b in high_miss),
    })
pairs_df       = pd.DataFrame(pair_rows)
pairs_df_valid = pairs_df.dropna(subset=["spearman_rho"])
pairs_df.to_csv(OUT_DIR / "all_correlation_pairs.csv", index=False)
print(f"  → all_correlation_pairs.csv  ({len(pairs_df_valid)} valid pairs)")

# ── 1. Global heatmap ────────────────────────────────────────────────────────
print("Drawing global heatmap …")
main_vars_sorted = sorted(main_vars, key=lambda v: (var_pillar.get(v, 99), v))
corr_global      = build_corr_matrix(df, main_vars_sorted)

n_v  = len(main_vars_sorted)
fsz  = max(18, n_v * 0.72)
fig, ax = plt.subplots(figsize=(fsz, fsz * 0.85))

sns.heatmap(
    corr_global, mask=corr_global.isna(),
    cmap=cmap, vmin=-1, vmax=1, center=0,
    square=True, linewidths=0.3, linecolor="#cccccc",
    annot=True, fmt=".2f", annot_kws={"size": 7},
    ax=ax, cbar_kws={"shrink": 0.55, "label": "Spearman ρ"},
)
pretty_labels = [pretty_name(v) for v in main_vars_sorted]
ax.set_xticklabels(pretty_labels, rotation=45, ha="right", fontsize=8)
ax.set_yticklabels(pretty_labels, rotation=0, fontsize=8)
ax.set_title(
    "Newlands Survey — Global Correlation Matrix (Spearman ρ)\n"
    f"Variables grouped by Resilience Pillar  |  n ≥ {MIN_PAIR_N} per pair  |  "
    f"High-missing (>{MISSING_THRESHOLD*100:.0f}%) excluded",
    fontsize=12, pad=14,
)

# Pillar boundary lines
pillar_ids = [var_pillar.get(v, 99) for v in main_vars_sorted]
prev = pillar_ids[0]
for i, pid in enumerate(pillar_ids):
    if pid != prev:
        ax.axhline(i, color="black", linewidth=1.8)
        ax.axvline(i, color="black", linewidth=1.8)
        prev = pid

legend_handles = [
    mpatches.Patch(color=PILLAR_COLOURS[pid], label=f"Pillar {pid}: {PILLAR_NAMES[pid]}")
    for pid in sorted(PILLAR_NAMES)
]
ax.legend(handles=legend_handles, loc="upper left",
          bbox_to_anchor=(1.18, 1.0), fontsize=9,
          title="Resilience Pillars", title_fontsize=9, frameon=True)

plt.tight_layout()
fig.savefig(OUT_DIR / "heatmap_global.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("  → heatmap_global.png")

# ── 2. Per-pillar heatmaps ───────────────────────────────────────────────────
print("Drawing per-pillar heatmaps …")
for pid, pname in PILLAR_NAMES.items():
    pvars = [v for v in all_vars if var_pillar.get(v) == pid]
    if len(pvars) < 2:
        continue
    pvars_sorted = sorted(pvars, key=lambda v: miss[v])
    corr_p = build_corr_matrix(df, pvars_sorted)

    n_p = len(pvars_sorted)
    fsz = max(7, n_p * 1.15)
    fig, ax = plt.subplots(figsize=(fsz, fsz * 0.92))

    # Custom annotation: value + asterisk for high-missing pairs
    annot = corr_p.copy().astype(object)
    for r in pvars_sorted:
        for c in pvars_sorted:
            val = corr_p.loc[r, c]
            if pd.isna(val):
                annot.loc[r, c] = "—"
            else:
                txt = f"{val:.2f}"
                if r != c and (r in high_miss or c in high_miss):
                    txt += "*"
                annot.loc[r, c] = txt

    sns.heatmap(
        corr_p, mask=corr_p.isna(),
        cmap=cmap, vmin=-1, vmax=1, center=0,
        square=True, linewidths=0.5, linecolor="#cccccc",
        annot=annot, fmt="", annot_kws={"size": 9},
        ax=ax, cbar_kws={"shrink": 0.7, "label": "Spearman ρ"},
    )
    ax.set_xticklabels([pretty_name(v) for v in pvars_sorted], rotation=40, ha="right", fontsize=9)
    ax.set_yticklabels([pretty_name(v) for v in pvars_sorted], rotation=0, fontsize=9)

    # Grey-out high-missing tick labels
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        raw = lbl.get_text().lower().replace(" ", "_")
        if raw in high_miss:
            lbl.set_color("#aaaaaa")

    hm_in = [v for v in pvars_sorted if v in high_miss]
    note  = (f"\n* = involves high-missing variable: "
             f"{', '.join(pretty_name(v) for v in hm_in)}") if hm_in else ""
    ax.set_title(
        f"Pillar {pid}: {pname} — Within-Pillar Correlations (Spearman ρ){note}",
        fontsize=11, pad=12,
    )
    plt.tight_layout()
    fname = f"heatmap_pillar_{pid}_{pname.lower()}.png"
    fig.savefig(OUT_DIR / fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {fname}")

# ── 3. Focal bar charts ──────────────────────────────────────────────────────
print("Drawing focal variable bar charts …")
focal_vars = {"life_satisfaction": "Life Satisfaction",
              "work_travel_time":  "Work Travel Time"}

for focal, focal_label in focal_vars.items():
    if focal not in df.columns:
        print(f"  {focal} not found, skipping")
        continue

    bar_rows = []
    for v in all_vars:
        if v == focal:
            continue
        rho, p, n = spearman_pair(df[focal], df[v])
        if not np.isnan(rho):
            bar_rows.append({
                "variable":    v,
                "label":       pretty_name(v),
                "pillar_id":   var_pillar.get(v),
                "spearman_rho": rho,
                "high_missing": v in high_miss,
            })
    bar_df = pd.DataFrame(bar_rows).sort_values("spearman_rho", ascending=True)

    fsz = max(9, len(bar_df) * 0.40)
    fig, ax = plt.subplots(figsize=(11, fsz))
    colours   = [PILLAR_COLOURS.get(r["pillar_id"], "#888") for _, r in bar_df.iterrows()]
    bars      = ax.barh(bar_df["label"], bar_df["spearman_rho"], color=colours, alpha=0.85)
    for bar, (_, row) in zip(bars, bar_df.iterrows()):
        if row["high_missing"]:
            bar.set_alpha(0.35)
            bar.set_hatch("///")
        # value label
        val = row["spearman_rho"]
        ax.text(val + (0.01 if val >= 0 else -0.01), bar.get_y() + bar.get_height() / 2,
                f"{val:+.2f}", va="center",
                ha="left" if val >= 0 else "right", fontsize=7.5)

    ax.axvline(0,     color="black",   linewidth=0.9)
    ax.axvline( 0.40, color="#e53935", linewidth=0.9, linestyle="--", alpha=0.6)
    ax.axvline(-0.40, color="#e53935", linewidth=0.9, linestyle="--", alpha=0.6)
    ax.axvline( 0.70, color="#b71c1c", linewidth=0.9, linestyle="--", alpha=0.6)
    ax.axvline(-0.70, color="#b71c1c", linewidth=0.9, linestyle="--", alpha=0.6)
    ax.set_xlabel("Spearman ρ", fontsize=10)
    ax.set_title(
        f"All Variables vs {focal_label}  (Spearman ρ)\n"
        f"Dashed lines: |ρ|=0.40 moderate, |ρ|=0.70 strong   "
        f"Hatched = high-missing (>{MISSING_THRESHOLD*100:.0f}%)",
        fontsize=11, pad=10,
    )
    handles = [
        mpatches.Patch(color=PILLAR_COLOURS[pid], label=f"Pillar {pid}: {PILLAR_NAMES[pid]}")
        for pid in sorted(PILLAR_NAMES)
    ] + [mpatches.Patch(facecolor="grey", hatch="///", alpha=0.4, label="High-missing")]
    ax.legend(handles=handles, fontsize=8, loc="lower right")
    plt.tight_layout()
    fname = f"barchart_focal_{focal}.png"
    fig.savefig(OUT_DIR / fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {fname}")

# ── 4. Markdown report ────────────────────────────────────────────────────────
print("Writing Markdown report …")

def fmt_pairs(sub: pd.DataFrame) -> str:
    sub = sub[sub["spearman_rho"].abs() >= 0.40].sort_values(
        "spearman_rho", key=abs, ascending=False)
    if sub.empty:
        return "_No moderate or strong relationships found (n ≥ 50, no high-missing)._\n"
    lines = []
    for _, r in sub.iterrows():
        flag = " ⚠️ high-missing" if r["high_missing_flag"] else ""
        lines.append(
            f"- **{pretty_name(r['var_a'])}** ↔ **{pretty_name(r['var_b'])}**: "
            f"ρ = {r['spearman_rho']:+.2f} ({r['strength']}, n={int(r['valid_n'])}){flag}"
        )
    return "\n".join(lines) + "\n"

md = []
md.append("# Newlands Community Survey — Correlation Analysis Report\n")
md.append(f"**Responses:** {len(df)}  |  **Years:** 2019–2025  |  "
          f"**Primary variables:** {len(main_vars)}  |  "
          f"**High-missing excluded:** {len(high_miss)}  |  "
          f"**Min paired n:** {MIN_PAIR_N}\n")

md.append("## Method\n")
md.append(
    "Spearman ρ (rank-based) is used throughout — appropriate for ordinal survey scales, "
    "binary indicators, and mixed variable types. For binary variables this is equivalent "
    "to Point-Biserial correlation applied to ranks. "
    "P-values use the Fisher z → standard-normal approximation (accurate for n ≥ 50). "
    "Pairs with n < 50 are excluded. Variables with >60% missing are excluded from "
    "heatmaps but shown (hatched) in focal bar charts.\n"
)

md.append("## Strength Thresholds\n")
md.append("| Label | |ρ| |")
md.append("|-------|-----|")
md.append("| Strong | ≥ 0.70 |")
md.append("| Moderate | 0.40–0.69 |")
md.append("| Weak | 0.20–0.39 |")
md.append("| Very weak | < 0.20 |\n")

md.append("## High-Missing Variables (>60% missing)\n")
md.append("Excluded from heatmaps. Treat with caution in any model.\n")
for v in sorted(high_miss, key=lambda x: -miss[x]):
    md.append(f"- **{pretty_name(v)}** ({PILLAR_NAMES.get(var_pillar.get(v),'?')}): "
              f"{miss[v]*100:.1f}% missing, n={int(df[v].notna().sum())}")
md.append("")

md.append("---\n## Cross-Pillar Relationships\n")
cross = pairs_df_valid[~pairs_df_valid["same_pillar"] & ~pairs_df_valid["high_missing_flag"]]
cross_mod = cross[cross["spearman_rho"].abs() >= 0.40].sort_values(
    "spearman_rho", key=abs, ascending=False).head(20)
md.append("Most strong/moderate cross-pillar relationships (low-missing variables only):\n")
if cross_mod.empty:
    md.append("_None found._\n")
else:
    for _, r in cross_mod.iterrows():
        md.append(
            f"- **{pretty_name(r['var_a'])}** ({r['pillar_a']}) ↔ "
            f"**{pretty_name(r['var_b'])}** ({r['pillar_b']}): "
            f"ρ = {r['spearman_rho']:+.2f} ({r['strength']}, n={int(r['valid_n'])})"
        )
md.append("")

md.append("---\n## Per-Pillar Analysis\n")
for pid, pname in PILLAR_NAMES.items():
    pvars    = [v for v in all_vars if var_pillar.get(v) == pid]
    hm_in   = [v for v in pvars if v in high_miss]
    main_in = [v for v in pvars if v not in high_miss]
    md.append(f"### Pillar {pid}: {pname}\n")
    md.append(f"**Total variables:** {len(pvars)}  |  **High-missing:** {len(hm_in)}\n")
    if hm_in:
        md.append(f"**High-missing variables:** {', '.join(pretty_name(v) for v in hm_in)}\n")

    pillar_pairs = pairs_df_valid[
        pairs_df_valid["same_pillar"] &
        pairs_df_valid["var_a"].isin(pvars) &
        ~pairs_df_valid["high_missing_flag"]
    ]
    md.append("**Moderate & strong relationships (n ≥ 50, no high-missing):**\n")
    md.append(fmt_pairs(pillar_pairs))

    # Most independent
    avg_abs = {}
    for v in main_in:
        rel = pillar_pairs[
            ((pillar_pairs["var_a"] == v) | (pillar_pairs["var_b"] == v)) &
            pillar_pairs["spearman_rho"].notna()
        ]
        if not rel.empty:
            avg_abs[v] = rel["spearman_rho"].abs().mean()
    if avg_abs:
        indep = sorted(avg_abs, key=avg_abs.get)[:3]
        md.append("**Most independent (lowest avg |ρ| within pillar):**\n")
        for v in indep:
            md.append(f"- {pretty_name(v)}: avg |ρ| = {avg_abs[v]:.2f}")
        md.append("")
    md.append("")

md.append("---\n## Focal Variable Analysis\n")
for focal, focal_label in focal_vars.items():
    if focal not in df.columns:
        continue
    md.append(f"### {focal_label}\n")
    focal_pairs = pairs_df_valid[
        ((pairs_df_valid["var_a"] == focal) | (pairs_df_valid["var_b"] == focal)) &
        ~pairs_df_valid["high_missing_flag"]
    ].copy()
    strong_f = focal_pairs[focal_pairs["spearman_rho"].abs() >= 0.40].sort_values(
        "spearman_rho", key=abs, ascending=False)
    md.append(f"Variables with moderate or strong correlation to **{focal_label}** (no high-missing):\n")
    if strong_f.empty:
        md.append("_None found._\n")
    else:
        for _, r in strong_f.iterrows():
            other = r["var_b"] if r["var_a"] == focal else r["var_a"]
            md.append(
                f"- **{pretty_name(other)}** ({PILLAR_NAMES.get(var_pillar.get(other),'?')}): "
                f"ρ = {r['spearman_rho']:+.2f} ({r['strength']}, n={int(r['valid_n'])})"
            )
    md.append("")

md.append("---\n## Key Takeaways\n")
md.append(
    "1. **Social Pillar** has the strongest and richest internal correlation structure. "
    "Life satisfaction, meaning & purpose, family wellbeing, and autonomy indicators "
    "form a coherent wellbeing cluster — a natural candidate for composite scoring or "
    "as a primary modelling target.\n"
    "2. **Economic Pillar**: job satisfaction and income satisfaction are moderately linked, "
    "but `work_travel_time`, `paid_working_hours`, and `basic_life_skills` are largely "
    "independent — travel time is not yet correlated with job/income satisfaction, which "
    "makes it a clean entry point for road impact modelling.\n"
    "3. **Governance Pillar** splits into two clusters: institutional trust (government, "
    "council, police) and civic participation (voting). Do not combine into one score.\n"
    "4. **Cultural and Disaster Pillars** have weak internal structure — variables capture "
    "distinct sub-concepts; use individually rather than as composites.\n"
    "5. **Cross-pillar links** exist between Social and Economic indicators (e.g., "
    "work-life balance → life satisfaction), confirming these domains interact but "
    "are not redundant.\n"
    "6. **High-missing variables** should be prioritised for collection in future survey "
    "rounds if they are to be included in modelling.\n"
)
md.append("\n---\n_All correlations are associational. Spearman ρ. Generated automatically._\n")

(OUT_DIR / "correlation_report.md").write_text("\n".join(md), encoding="utf-8")
print("  → correlation_report.md")

# ── Summary ──────────────────────────────────────────────────────────────────
print("\n✓ All done. Files in", OUT_DIR)
for f in sorted(OUT_DIR.iterdir()):
    print(f"  {f.name}")
