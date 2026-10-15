#!/usr/bin/env python3
"""
EDA visualization for diabetic_transformed.csv
Follows the visualize-dataset skill template.
Saves all charts to charts/ as numbered PNGs.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np

# ── Config ─────────────────────────────────────────────────────────────────────
DATA_FILE  = "diabetic/data/diabetic_transformed.csv"
TARGET_COL = "readmitted"
CHARTS_DIR = "charts"
# ──────────────────────────────────────────────────────────────────────────────

os.makedirs(CHARTS_DIR, exist_ok=True)
sns.set_theme(style="whitegrid", palette="muted")

TARGET_COLORS = {"no": "#4C9BE8", ">30": "#F4A261", "<30": "#E76F51"}
TARGET_ORDER  = ["no", ">30", "<30"]

def save(fig, name):
    path = os.path.join(CHARTS_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → {path}")


# ── Load ────────────────────────────────────────────────────────────────────────
print("Loading data…")
df = pd.read_csv(DATA_FILE)

# Race columns are one-hot encoded; reconstruct a single race label for charts
race_cols = ["race_caucasian", "race_african_american", "race_hispanic",
             "race_other", "race_asian"]
race_labels = ["Caucasian", "African American", "Hispanic", "Other", "Asian"]
df["race"] = df[race_cols].idxmax(axis=1).map(dict(zip(race_cols, race_labels)))

# Binary flag columns
df["change_label"]       = df["change"].map({0: "No change", 1: "Med changed"})
df["diabetes_med_label"] = df["diabetes_med"].map({0: "No diabetes med", 1: "On diabetes med"})

# Auto-detect numeric and categorical columns (excluding derived helpers)
num_cols = df.select_dtypes(include="number").columns.tolist()
# Remove one-hot race cols and binary flag cols from numeric list for cleaner charts
num_cols = [c for c in num_cols if c not in race_cols + ["change", "diabetes_med"]]
cat_cols = ["race", "change_label", "diabetes_med_label"]

print(f"  {len(df):,} rows | numeric cols: {num_cols} | target: {TARGET_COL}\n")


# ── 01. Target class distribution (bar) ──────────────────────────────────────
print("[01] Readmission class distribution")
counts = df[TARGET_COL].value_counts().reindex(TARGET_ORDER).dropna()
fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(counts.index, counts.values,
              color=[TARGET_COLORS[k] for k in counts.index], edgecolor="white")
for bar, val in zip(bars, counts.values):
    pct = val / len(df) * 100
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 200,
            f"{val:,}\n({pct:.1f}%)", ha="center", va="bottom", fontsize=10)
ax.set_title("Readmission Class Distribution", fontsize=14, fontweight="bold")
ax.set_xlabel("Readmission Outcome")
ax.set_ylabel("Number of Patients")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.set_ylim(0, counts.max() * 1.2)
save(fig, "t01_readmission_distribution.png")


# ── 02. Target breakdown by race (grouped bar) ───────────────────────────────
print("[02] Readmission by race")
try:
    race_ct = (df.groupby(["race", TARGET_COL])
                 .size()
                 .unstack(fill_value=0)
                 .reindex(columns=TARGET_ORDER))
    fig, ax = plt.subplots(figsize=(10, 5))
    race_ct.plot(kind="bar", ax=ax,
                 color=[TARGET_COLORS[c] for c in TARGET_ORDER],
                 edgecolor="white", width=0.65)
    ax.set_title("Readmission Count by Race", fontsize=14, fontweight="bold")
    ax.set_xlabel("Race")
    ax.set_ylabel("Number of Patients")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=15, ha="right")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.legend(title="Readmitted", bbox_to_anchor=(1.01, 1), loc="upper left")
    save(fig, "t02_readmission_by_race.png")
except Exception as e:
    print(f"  Skipped: {e}")


# ── 03. Readmission rate (%) by medication change (stacked %) ─────────────────
print("[03] Readmission rate by medication change")
try:
    chg_ct  = (df.groupby(["change_label", TARGET_COL])
                 .size()
                 .unstack(fill_value=0)
                 .reindex(columns=TARGET_ORDER))
    chg_pct = chg_ct.div(chg_ct.sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=(7, 5))
    chg_pct.plot(kind="bar", stacked=True, ax=ax,
                 color=[TARGET_COLORS[c] for c in TARGET_ORDER],
                 edgecolor="white", width=0.5)
    ax.set_title("Readmission Rate by Medication Change (% of group)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Medication Change")
    ax.set_ylabel("Percentage (%)")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.legend(title="Readmitted", bbox_to_anchor=(1.01, 1), loc="upper left")
    save(fig, "t03_readmission_by_med_change.png")
except Exception as e:
    print(f"  Skipped: {e}")


# ── 04. Readmission rate (%) by diabetes medication (stacked %) ───────────────
print("[04] Readmission rate by diabetes medication")
try:
    dm_ct  = (df.groupby(["diabetes_med_label", TARGET_COL])
                .size()
                .unstack(fill_value=0)
                .reindex(columns=TARGET_ORDER))
    dm_pct = dm_ct.div(dm_ct.sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=(7, 5))
    dm_pct.plot(kind="bar", stacked=True, ax=ax,
                color=[TARGET_COLORS[c] for c in TARGET_ORDER],
                edgecolor="white", width=0.5)
    ax.set_title("Readmission Rate by Diabetes Medication (% of group)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Diabetes Medication")
    ax.set_ylabel("Percentage (%)")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.legend(title="Readmitted", bbox_to_anchor=(1.01, 1), loc="upper left")
    save(fig, "t04_readmission_by_diabetes_med.png")
except Exception as e:
    print(f"  Skipped: {e}")


# ── 05. Time in hospital distribution by readmission (overlapping histogram) ──
print("[05] Time in hospital distribution")
try:
    fig, ax = plt.subplots(figsize=(9, 5))
    for label in TARGET_ORDER:
        ax.hist(df[df[TARGET_COL] == label]["time_in_hospital"],
                bins=14, alpha=0.55, label=label,
                color=TARGET_COLORS[label], edgecolor="white")
    ax.set_title("Time in Hospital by Readmission Outcome", fontsize=14, fontweight="bold")
    ax.set_xlabel("Days in Hospital")
    ax.set_ylabel("Number of Patients")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.legend(title="Readmitted")
    save(fig, "t05_time_in_hospital.png")
except Exception as e:
    print(f"  Skipped: {e}")


# ── 06. Num lab procedures vs num medications (scatter, colored by target) ────
print("[06] Lab procedures vs medications scatter")
try:
    fig, ax = plt.subplots(figsize=(8, 6))
    for label in TARGET_ORDER:
        sub = df[df[TARGET_COL] == label]
        ax.scatter(sub["num_lab_procedures"], sub["num_medications"],
                   alpha=0.15, s=10, label=label, color=TARGET_COLORS[label])
    ax.set_title("Lab Procedures vs. Medications", fontsize=14, fontweight="bold")
    ax.set_xlabel("Number of Lab Procedures")
    ax.set_ylabel("Number of Medications")
    ax.legend(title="Readmitted", markerscale=3)
    save(fig, "t06_lab_procedures_vs_medications.png")
except Exception as e:
    print(f"  Skipped: {e}")


# ── 07. Correlation heatmap (numeric features) ───────────────────────────────
print("[07] Correlation heatmap")
try:
    corr = df[num_cols].corr()
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0,
                linewidths=0.5, ax=ax, square=True)
    ax.set_title("Feature Correlation Heatmap", fontsize=14, fontweight="bold")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right", fontsize=9)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=9)
    save(fig, "t07_correlation_heatmap.png")
except Exception as e:
    print(f"  Skipped: {e}")


# ── 08. 2×2 box plots — key numeric features by readmission ──────────────────
print("[08] Box plots of key numeric features")
try:
    box_cols = ["time_in_hospital", "num_lab_procedures",
                "num_medications", "number_diagnoses"]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()
    for i, col in enumerate(box_cols):
        data = [df[df[TARGET_COL] == lbl][col].values for lbl in TARGET_ORDER]
        bp = axes[i].boxplot(data, labels=TARGET_ORDER, patch_artist=True,
                             medianprops=dict(color="black", linewidth=2))
        for patch, lbl in zip(bp["boxes"], TARGET_ORDER):
            patch.set_facecolor(TARGET_COLORS[lbl])
        axes[i].set_title(col.replace("_", " ").title(), fontsize=11)
        axes[i].set_xlabel("Readmitted")
    fig.suptitle("Key Feature Distributions by Readmission Outcome",
                 fontsize=14, fontweight="bold", y=1.01)
    fig.tight_layout()
    save(fig, "t08_boxplots_by_readmission.png")
except Exception as e:
    print(f"  Skipped: {e}")


# ── 09. Readmission rate by age group (line + bar combo) ─────────────────────
print("[09] Readmission rate by age group")
try:
    age_ct  = (df.groupby(["age", TARGET_COL])
                 .size()
                 .unstack(fill_value=0)
                 .reindex(columns=TARGET_ORDER))
    age_pct = age_ct.div(age_ct.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(10, 5))
    age_pct.plot(kind="bar", stacked=True, ax=ax,
                 color=[TARGET_COLORS[c] for c in TARGET_ORDER],
                 edgecolor="white", width=0.7)
    ax.set_title("Readmission Rate by Age Group (% of group)",
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("Age (decade midpoint)")
    ax.set_ylabel("Percentage (%)")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.legend(title="Readmitted", bbox_to_anchor=(1.01, 1), loc="upper left")
    save(fig, "t09_readmission_by_age.png")
except Exception as e:
    print(f"  Skipped: {e}")


print(f"\nDone! All charts saved to ./{CHARTS_DIR}/")
