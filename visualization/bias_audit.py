#!/usr/bin/env python3
"""
Bias audit for diabetic_readmission.csv
Checks: representation, outcome rates, missing data by group.
Saves charts to charts/  (PNG only, no raw patient rows printed).
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

CHARTS_DIR = "charts"
DATA_FILE  = "diabetic/data/diabetic_readmission.csv"
os.makedirs(CHARTS_DIR, exist_ok=True)

# ── Load ────────────────────────────────────────────────────────────────────────
df = pd.read_csv(DATA_FILE)
N  = len(df)

# Binary readmission flag (any readmission)
df["readmitted_any"] = df["readmitted"].isin(["<30", ">30"])

OVERALL_RATE = df["readmitted_any"].mean() * 100
print(f"Dataset: {N:,} rows | Overall readmission rate: {OVERALL_RATE:.1f}%\n")

# Shared palette
RACE_PALETTE   = ["#4C9BE8","#F4A261","#E76F51","#57CC99","#C77DFF"]
GENDER_PALETTE = ["#F4A261","#4C9BE8","#AAAAAA"]


# ════════════════════════════════════════════════════════════════════════════════
# 1. REPRESENTATION
# ════════════════════════════════════════════════════════════════════════════════
print("── 1. Representation ──")

rep_race   = df["race"].value_counts().sort_values(ascending=False)
rep_gender = df["gender"].value_counts()
rep_age    = df["age"].value_counts().sort_index()

# Flag small groups (< 2 % of dataset)
SMALL_THRESHOLD = 0.02 * N
flagged_race = rep_race[rep_race < SMALL_THRESHOLD].index.tolist()
print(f"  Race groups < 2% of dataset: {flagged_race}")
print(f"  Gender breakdown: {rep_gender.to_dict()}")

# Chart 1a – Race representation
fig, ax = plt.subplots(figsize=(8, 5))
pcts = rep_race / N * 100
bars = ax.bar(pcts.index, pcts.values,
              color=RACE_PALETTE[:len(pcts)], edgecolor="white")
ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9)
ax.axhline(2, color="red", linestyle="--", linewidth=1, label="2% flag threshold")
ax.set_title("Patient Representation by Race", fontsize=14, fontweight="bold")
ax.set_xlabel("Race")
ax.set_ylabel("% of Dataset")
ax.set_xticklabels(pcts.index, rotation=15, ha="right")
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "bias_01_representation_race.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("  Saved → charts/bias_01_representation_race.png")

# Chart 1b – Age representation
fig, ax = plt.subplots(figsize=(9, 5))
pcts_age = rep_age / N * 100
bars = ax.bar(pcts_age.index.astype(str), pcts_age.values, color="#4C9BE8", edgecolor="white", width=0.6)
ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=8.5)
ax.axhline(2, color="red", linestyle="--", linewidth=1, label="2% flag threshold")
ax.set_title("Patient Representation by Age Group", fontsize=14, fontweight="bold")
ax.set_xlabel("Age (decade midpoint)")
ax.set_ylabel("% of Dataset")
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "bias_02_representation_age.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("  Saved → charts/bias_02_representation_age.png")


# ════════════════════════════════════════════════════════════════════════════════
# 2. OUTCOMES – readmission rate per group vs overall
# ════════════════════════════════════════════════════════════════════════════════
print("\n── 2. Outcome Rates ──")
FLAG_DELTA = 5.0  # percentage points

def outcome_table(col):
    tbl = (df.groupby(col)["readmitted_any"]
             .agg(total="count", readmitted="sum")
             .assign(rate=lambda x: x["readmitted"] / x["total"] * 100,
                     delta=lambda x: x["rate"] - OVERALL_RATE))
    return tbl

race_out   = outcome_table("race").sort_values("rate", ascending=False)
gender_out = outcome_table("gender").sort_values("rate", ascending=False)
age_out    = outcome_table("age").sort_values("age")

print("\n  Readmission rate by race:")
print(race_out[["total","rate","delta"]].to_string())
print("\n  Readmission rate by gender:")
print(gender_out[["total","rate","delta"]].to_string())

flagged_race_out   = race_out[race_out["delta"].abs() > FLAG_DELTA].index.tolist()
flagged_gender_out = gender_out[gender_out["delta"].abs() > FLAG_DELTA].index.tolist()
flagged_age_out    = age_out[age_out["delta"].abs() > FLAG_DELTA].index.tolist()

print(f"\n  Flagged race groups (|delta| > {FLAG_DELTA}pp): {flagged_race_out}")
print(f"  Flagged gender groups: {flagged_gender_out}")
print(f"  Flagged age groups: {flagged_age_out}")

# Chart 2a – Readmission rate by race (dot + overall line)
fig, ax = plt.subplots(figsize=(8, 5))
colors = ["#E76F51" if abs(d) > FLAG_DELTA else "#4C9BE8"
          for d in race_out["delta"]]
ax.barh(race_out.index, race_out["rate"], color=colors, edgecolor="white", height=0.55)
ax.axvline(OVERALL_RATE, color="black", linestyle="--", linewidth=1.5,
           label=f"Overall {OVERALL_RATE:.1f}%")
for i, (rate, delta) in enumerate(zip(race_out["rate"], race_out["delta"])):
    ax.text(rate + 0.3, i, f"{rate:.1f}%  (Δ{delta:+.1f}pp)", va="center", fontsize=9)
ax.set_title("Readmission Rate by Race\n(red = >5pp from overall)", fontsize=13, fontweight="bold")
ax.set_xlabel("Readmission Rate (%)")
ax.set_xlim(0, race_out["rate"].max() + 10)
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "bias_03_outcomes_race.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("\n  Saved → charts/bias_03_outcomes_race.png")

# Chart 2b – Readmission rate by age (bar + overall line)
fig, ax = plt.subplots(figsize=(10, 5))
colors_age = ["#E76F51" if abs(d) > FLAG_DELTA else "#4C9BE8"
              for d in age_out["delta"]]
bars = ax.bar(age_out.index.astype(str), age_out["rate"],
              color=colors_age, edgecolor="white", width=0.6)
ax.axhline(OVERALL_RATE, color="black", linestyle="--", linewidth=1.5,
           label=f"Overall {OVERALL_RATE:.1f}%")
for bar, rate, delta in zip(bars, age_out["rate"], age_out["delta"]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
            f"{rate:.1f}%\nΔ{delta:+.1f}", ha="center", va="bottom", fontsize=8)
ax.set_title("Readmission Rate by Age Group\n(red = >5pp from overall)", fontsize=13, fontweight="bold")
ax.set_xlabel("Age (decade midpoint)")
ax.set_ylabel("Readmission Rate (%)")
ax.set_ylim(0, age_out["rate"].max() + 10)
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "bias_04_outcomes_age.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("  Saved → charts/bias_04_outcomes_age.png")


# ════════════════════════════════════════════════════════════════════════════════
# 3. MISSING DATA – 'none' encoded as string in lab columns
# ════════════════════════════════════════════════════════════════════════════════
print("\n── 3. Missing Data by Group ──")

LAB_COLS = ["max_glu_serum", "a1c_result"]

def missing_rate(col, group_col):
    """% of rows where lab col == 'none', grouped by demographic."""
    return (df.groupby(group_col)[col]
              .apply(lambda s: (s == "none").mean() * 100)
              .rename(col))

miss_race   = pd.concat([missing_rate(c, "race")   for c in LAB_COLS], axis=1)
miss_gender = pd.concat([missing_rate(c, "gender") for c in LAB_COLS], axis=1)
miss_age    = pd.concat([missing_rate(c, "age")    for c in LAB_COLS], axis=1)

print("\n  Missing lab values (%) by race:")
print(miss_race.to_string())
print("\n  Missing lab values (%) by gender:")
print(miss_gender.to_string())

# Chart 3 – Heatmap of missing lab data by race and gender
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

for ax, (group_col, tbl) in zip(axes, [("race", miss_race), ("gender", miss_gender)]):
    im = ax.imshow(tbl.values, cmap="YlOrRd", aspect="auto", vmin=0, vmax=100)
    ax.set_xticks(range(len(LAB_COLS)))
    ax.set_xticklabels(LAB_COLS, rotation=20, ha="right", fontsize=10)
    ax.set_yticks(range(len(tbl)))
    ax.set_yticklabels(tbl.index, fontsize=10)
    ax.set_title(f"Missing Lab Data (%) by {group_col.title()}", fontsize=12, fontweight="bold")
    for r in range(len(tbl)):
        for c in range(len(LAB_COLS)):
            ax.text(c, r, f"{tbl.values[r, c]:.1f}%", ha="center", va="center",
                    fontsize=10, color="black" if tbl.values[r, c] < 70 else "white")
    plt.colorbar(im, ax=ax, label="% missing")

fig.suptitle("Missing Lab Measurements by Demographic Group", fontsize=13, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "bias_05_missing_data_heatmap.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("\n  Saved → charts/bias_05_missing_data_heatmap.png")

# Chart 4 – Missing lab data by age group (line chart)
fig, ax = plt.subplots(figsize=(10, 5))
for col, color in zip(LAB_COLS, ["#4C9BE8", "#E76F51"]):
    vals = (df.groupby("age")[col]
              .apply(lambda s: (s == "none").mean() * 100))
    ax.plot(vals.index.astype(str), vals.values, marker="o", label=col,
            color=color, linewidth=2, markersize=6)
ax.set_title("Missing Lab Measurements by Age Group", fontsize=13, fontweight="bold")
ax.set_xlabel("Age (decade midpoint)")
ax.set_ylabel("% missing")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
ax.set_ylim(0, 105)
ax.legend(title="Lab test", fontsize=10)
ax.grid(axis="y", linestyle="--", alpha=0.5)
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "bias_06_missing_data_by_age.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("  Saved → charts/bias_06_missing_data_by_age.png")


# ════════════════════════════════════════════════════════════════════════════════
# Summary printout (no raw rows)
# ════════════════════════════════════════════════════════════════════════════════
print("\n══ AUDIT SUMMARY ══")
print(f"  Total patients : {N:,}")
print(f"  Overall readmission rate: {OVERALL_RATE:.1f}%")
print(f"\n  Representation flags (< 2% of data): {flagged_race}")
print(f"\n  Outcome flags by race  (|Δ| > 5pp): {flagged_race_out}")
print(f"  Outcome flags by gender (|Δ| > 5pp): {flagged_gender_out}")
print(f"  Outcome flags by age   (|Δ| > 5pp): {flagged_age_out}")
print(f"\n  Overall missing rate — max_glu_serum: {(df['max_glu_serum']=='none').mean()*100:.1f}%")
print(f"  Overall missing rate — a1c_result   : {(df['a1c_result']=='none').mean()*100:.1f}%")
print(f"\n  Charts saved to ./{CHARTS_DIR}/")
