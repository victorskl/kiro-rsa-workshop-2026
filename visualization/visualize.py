#!/usr/bin/env python3
"""
Diabetic Readmission Data Visualization
Generates charts from diabetic_readmission.csv and saves them to charts/
"""

import os
import ast
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ── Setup ──────────────────────────────────────────────────────────────────────
CHARTS_DIR = "charts"
DATA_FILE   = "diabetic/data/diabetic_readmission.csv"
INFER_PROB  = "diabetic/data/inference_results_with_probabilities.csv"
INFER_PRED  = "diabetic/data/inference_results.csv"

os.makedirs(CHARTS_DIR, exist_ok=True)
sns.set_theme(style="whitegrid", palette="muted")

READMIT_COLORS = {"no": "#4C9BE8", ">30": "#F4A261", "<30": "#E76F51"}

def save(fig, name):
    path = os.path.join(CHARTS_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → {path}")


# ── Load data ──────────────────────────────────────────────────────────────────
print("Loading data…")
df = pd.read_csv(DATA_FILE)

# Ordinal age mapping (stored as bin midpoints for numeric charts)
AGE_ORDER = ["0","5","15","25","35","45","55","65","75","85","95"]
df["age_label"] = df["age"].astype(str)

# Readmission label order
READMIT_ORDER = ["no", ">30", "<30"]


# ── 1. Readmission class distribution (bar) ───────────────────────────────────
print("\n[1/9] Readmission class distribution")
counts = df["readmitted"].value_counts().reindex(READMIT_ORDER).dropna()
fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(counts.index, counts.values,
              color=[READMIT_COLORS[k] for k in counts.index], edgecolor="white")
ax.bar_label(bars, fmt="%,.0f", padding=4, fontsize=10)
ax.set_title("Readmission Class Distribution", fontsize=14, fontweight="bold")
ax.set_xlabel("Readmission Outcome")
ax.set_ylabel("Number of Patients")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
save(fig, "01_readmission_distribution.png")


# ── 2. Readmission by gender (grouped bar) ────────────────────────────────────
print("[2/9] Readmission by gender")
gender_ct = (df.groupby(["gender", "readmitted"])
               .size()
               .unstack(fill_value=0)
               .reindex(columns=READMIT_ORDER))
fig, ax = plt.subplots(figsize=(8, 5))
gender_ct.plot(kind="bar", ax=ax,
               color=[READMIT_COLORS[c] for c in READMIT_ORDER],
               edgecolor="white", width=0.6)
ax.set_title("Readmission by Gender", fontsize=14, fontweight="bold")
ax.set_xlabel("Gender")
ax.set_ylabel("Number of Patients")
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.legend(title="Readmitted", bbox_to_anchor=(1.01, 1), loc="upper left")
save(fig, "02_readmission_by_gender.png")


# ── 3. Readmission by race (stacked %) ───────────────────────────────────────
print("[3/9] Readmission by race")
race_ct = (df.groupby(["race", "readmitted"])
             .size()
             .unstack(fill_value=0)
             .reindex(columns=READMIT_ORDER))
race_pct = race_ct.div(race_ct.sum(axis=1), axis=0) * 100
fig, ax = plt.subplots(figsize=(9, 5))
race_pct.plot(kind="bar", stacked=True, ax=ax,
              color=[READMIT_COLORS[c] for c in READMIT_ORDER],
              edgecolor="white", width=0.6)
ax.set_title("Readmission Rate by Race (% of group)", fontsize=14, fontweight="bold")
ax.set_xlabel("Race")
ax.set_ylabel("Percentage (%)")
ax.set_xticklabels(ax.get_xticklabels(), rotation=20, ha="right")
ax.legend(title="Readmitted", bbox_to_anchor=(1.01, 1), loc="upper left")
save(fig, "03_readmission_by_race.png")


# ── 4. Readmission by age group (stacked %) ──────────────────────────────────
print("[4/9] Readmission by age group")
age_ct = (df.groupby(["age", "readmitted"])
            .size()
            .unstack(fill_value=0)
            .reindex(columns=READMIT_ORDER))
age_pct = age_ct.div(age_ct.sum(axis=1), axis=0) * 100
fig, ax = plt.subplots(figsize=(10, 5))
age_pct.plot(kind="bar", stacked=True, ax=ax,
             color=[READMIT_COLORS[c] for c in READMIT_ORDER],
             edgecolor="white", width=0.7)
ax.set_title("Readmission Rate by Age Group (% of group)", fontsize=14, fontweight="bold")
ax.set_xlabel("Age (decade midpoint)")
ax.set_ylabel("Percentage (%)")
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
ax.legend(title="Readmitted", bbox_to_anchor=(1.01, 1), loc="upper left")
save(fig, "04_readmission_by_age.png")


# ── 5. Time in hospital distribution (histogram) ─────────────────────────────
print("[5/9] Time in hospital distribution")
fig, ax = plt.subplots(figsize=(9, 5))
for label, grp in df.groupby("readmitted"):
    ax.hist(grp["time_in_hospital"], bins=14, alpha=0.6,
            label=label, color=READMIT_COLORS[label], edgecolor="white")
ax.set_title("Time in Hospital Distribution by Readmission", fontsize=14, fontweight="bold")
ax.set_xlabel("Days in Hospital")
ax.set_ylabel("Number of Patients")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.legend(title="Readmitted")
save(fig, "05_time_in_hospital.png")


# ── 6. Num lab procedures vs num medications (scatter) ───────────────────────
print("[6/9] Lab procedures vs medications scatter")
fig, ax = plt.subplots(figsize=(8, 6))
for label in READMIT_ORDER:
    sub = df[df["readmitted"] == label]
    ax.scatter(sub["num_lab_procedures"], sub["num_medications"],
               alpha=0.15, s=10, label=label, color=READMIT_COLORS[label])
ax.set_title("Lab Procedures vs. Medications", fontsize=14, fontweight="bold")
ax.set_xlabel("Number of Lab Procedures")
ax.set_ylabel("Number of Medications")
ax.legend(title="Readmitted", markerscale=3)
save(fig, "06_lab_procedures_vs_medications.png")


# ── 7. Correlation heatmap (numeric features) ────────────────────────────────
print("[7/9] Correlation heatmap")
num_cols = ["time_in_hospital", "num_lab_procedures", "num_procedures",
            "num_medications", "number_outpatient", "number_emergency",
            "number_inpatient", "number_diagnoses"]
corr = df[num_cols].corr()
fig, ax = plt.subplots(figsize=(9, 7))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0,
            linewidths=0.5, ax=ax, square=True)
ax.set_title("Feature Correlation Heatmap", fontsize=14, fontweight="bold")
ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right", fontsize=9)
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=9)
save(fig, "07_correlation_heatmap.png")


# ── 8. Box plots – key numeric features by readmission ───────────────────────
print("[8/9] Box plots of key features")
box_cols = ["time_in_hospital", "num_lab_procedures",
            "num_medications", "number_diagnoses"]
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
axes = axes.flatten()
for i, col in enumerate(box_cols):
    data = [df[df["readmitted"] == lbl][col].values for lbl in READMIT_ORDER]
    bp = axes[i].boxplot(data, labels=READMIT_ORDER, patch_artist=True,
                         medianprops=dict(color="black", linewidth=2))
    for patch, lbl in zip(bp["boxes"], READMIT_ORDER):
        patch.set_facecolor(READMIT_COLORS[lbl])
    axes[i].set_title(col.replace("_", " ").title(), fontsize=11)
    axes[i].set_xlabel("Readmitted")
fig.suptitle("Key Feature Distributions by Readmission Outcome",
             fontsize=14, fontweight="bold", y=1.01)
fig.tight_layout()
save(fig, "08_boxplots_by_readmission.png")


# ── 9. Inference probability distribution (violin) ───────────────────────────
print("[9/9] Inference probability distributions")
try:
    infer_df = pd.read_csv(INFER_PROB, header=None, names=["probs", "labels"])
    infer_df["probs"]  = infer_df["probs"].apply(ast.literal_eval)
    infer_df["labels"] = infer_df["labels"].apply(ast.literal_eval)

    # Explode into one row per class probability
    rows = []
    for _, row in infer_df.iterrows():
        for prob, lbl in zip(row["probs"], row["labels"]):
            rows.append({"label": lbl, "probability": prob})
    prob_long = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(8, 5))
    order = ["<30", ">30", "no"]
    palette = {k: READMIT_COLORS[k] for k in order}
    sns.violinplot(data=prob_long, x="label", y="probability",
                   order=order, palette=palette, inner="quartile", ax=ax)
    ax.set_title("Predicted Probability Distribution per Class\n(Autopilot Inference)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Predicted Class")
    ax.set_ylabel("Predicted Probability")
    save(fig, "09_inference_probability_violin.png")
except Exception as e:
    print(f"  Skipped inference chart: {e}")


print(f"\nDone! All charts saved to ./{CHARTS_DIR}/")
