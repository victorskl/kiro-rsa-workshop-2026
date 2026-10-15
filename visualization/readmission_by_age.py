#!/usr/bin/env python3
"""
Plot readmission rate (% of patients readmitted) by age group.
Saves chart to charts/readmission_rate_by_age.png
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

CHARTS_DIR = "charts"
DATA_FILE  = "diabetic/data/diabetic_readmission.csv"

os.makedirs(CHARTS_DIR, exist_ok=True)

# ── Load & compute ─────────────────────────────────────────────────────────────
df = pd.read_csv(DATA_FILE)

# "Readmitted" = either "<30" or ">30" (i.e. not "no")
df["readmitted_any"] = df["readmitted"].isin(["<30", ">30"])

age_stats = (
    df.groupby("age")["readmitted_any"]
    .agg(total="count", readmitted="sum")
    .assign(rate=lambda x: x["readmitted"] / x["total"] * 100)
    .sort_index()
)

# ── Plot ───────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))

bars = ax.bar(
    age_stats.index,
    age_stats["rate"],
    color="#4C9BE8",
    edgecolor="white",
    width=0.6,
    zorder=2,
)

# Annotate each bar with the rate
for bar, rate, total in zip(bars, age_stats["rate"], age_stats["total"]):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.5,
        f"{rate:.1f}%\n(n={total:,})",
        ha="center",
        va="bottom",
        fontsize=8.5,
        color="#333333",
    )

ax.set_title("Readmission Rate by Age Group", fontsize=15, fontweight="bold", pad=14)
ax.set_xlabel("Age Group", fontsize=12)
ax.set_ylabel("Readmission Rate (%)", fontsize=12)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
ax.set_ylim(0, age_stats["rate"].max() * 1.25)
ax.tick_params(axis="x", rotation=0)
ax.grid(axis="y", linestyle="--", alpha=0.5, zorder=1)
ax.set_axisbelow(True)

fig.tight_layout()
out_path = os.path.join(CHARTS_DIR, "readmission_rate_by_age.png")
fig.savefig(out_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved → {out_path}")
