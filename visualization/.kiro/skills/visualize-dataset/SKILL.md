---
name: visualize-dataset
description: >
  Use this skill whenever the user provides a CSV file and wants to explore,
  understand, or visualize the data. It covers profiling the dataset in plain
  language, generating a standard suite of charts saved as PNG files, and
  suggesting further research questions. Works for any CSV — clinical,
  financial, sales, survey, or otherwise.
---

# Skill: Visualize Dataset

## Overview

This skill turns a raw CSV file into a full exploratory data analysis (EDA):
plain-language summary, statistical profile, and a `charts/` folder of PNG
charts. It is intentionally generic — column names, target variables, and
chart types are all inferred from the data rather than hard-coded.

---

## Step 1 — Understand the File

Before writing any code, read the CSV to understand its structure.

```
head -5 <file>.csv
wc -l <file>.csv
```

Note:
- Number of rows and columns
- Column names and data types (numeric vs. categorical vs. date)
- Whether there is a clear **target / label column** (something being predicted
  or classified — e.g. `readmitted`, `churn`, `fraud`, `price`)
- Whether there are date/time columns that imply a time-series angle

---

## Step 2 — Profile the Data in Plain Language

Run a Python snippet (or ask the agent) to produce a plain-English summary
covering:

| What to report | How |
|---|---|
| Row and column count | `df.shape` |
| Column names and dtypes | `df.dtypes` |
| Target column breakdown | `df[target].value_counts()` with percentages |
| Categorical column distributions | `value_counts()` for each |
| Numeric column stats | `df.describe()` — mean, min, max, median |
| Missing values | `df.isnull().sum()` |
| Key flags | Is the dataset imbalanced? Are there obvious outliers? |

Present this to the user in plain language with tables — avoid jargon.
Explain what each column *means* in context, not just its name.

---

## Step 3 — Install Dependencies

The visualization script requires:

```bash
pip3 install numpy pandas matplotlib seaborn --quiet
```

---

## Step 4 — Generate the Visualization Script

Create `visualize.py` in the project directory. The script must:

1. **Accept the CSV path and target column as variables** at the top so it is
   easy to adapt.
2. **Create a `charts/` directory** automatically with `os.makedirs`.
3. **Detect column types automatically** — split columns into numeric and
   categorical lists using `df.select_dtypes()`.
4. **Save every chart as a numbered PNG** (`01_`, `02_`, … prefix) to `charts/`
   at 150 dpi.
5. **Close each figure after saving** (`plt.close(fig)`) to avoid memory
   accumulation on large datasets.

### Standard Chart Suite

Generate the following charts, adapting titles and axis labels to the actual
column names:

| # | Chart type | What it shows |
|---|---|---|
| 01 | Bar chart | Target column class distribution with count labels |
| 02 | Grouped bar | Target breakdown by the most important categorical column |
| 03 | Stacked % bar | Target rate (%) by second categorical column |
| 04 | Stacked % bar | Target rate (%) by a third categorical column (e.g. age, region) |
| 05 | Overlapping histogram | Distribution of the most important numeric column, split by target |
| 06 | Scatter plot | Two correlated numeric columns, colored by target |
| 07 | Correlation heatmap | Pearson correlation of all numeric columns |
| 08 | 2×2 box plots | Four key numeric columns split by target |
| 09 | Violin plot | (Optional) Predicted probability distributions if inference results exist |

If there is **no clear target column**, replace target-split charts with
univariate distributions and pairplots instead.

### Script Template

```python
#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ── Config — edit these for a new dataset ─────────────────────────────────────
DATA_FILE  = "path/to/file.csv"
TARGET_COL = "target_column_name"       # set to None if no target
CHARTS_DIR = "charts"
# ─────────────────────────────────────────────────────────────────────────────

os.makedirs(CHARTS_DIR, exist_ok=True)
sns.set_theme(style="whitegrid", palette="muted")

def save(fig, name):
    path = os.path.join(CHARTS_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → {path}")

df = pd.read_csv(DATA_FILE)

# Auto-detect column types
num_cols = df.select_dtypes(include="number").columns.tolist()
cat_cols = df.select_dtypes(include="object").columns.tolist()
if TARGET_COL in cat_cols:
    cat_cols.remove(TARGET_COL)
if TARGET_COL in num_cols:
    num_cols.remove(TARGET_COL)

# ... chart generation follows ...
```

---

## Step 5 — Run the Script and Verify Output

```bash
python3 visualize.py
ls charts/
```

Confirm all expected PNG files are present. If any chart fails, the script
should catch the exception, print a warning, and continue — never abort the
whole run for one bad chart.

---

## Step 6 — Summarize Findings

After generating the charts, provide the user with:

1. **What the data shows** — key patterns visible in the charts (imbalance,
   correlations, demographic skews, outliers).
2. **Data quality notes** — missing values, duplicate-row risk, class imbalance,
   small subgroup sizes.
3. **Suggested research questions** — at least 5 questions the data can answer,
   grouped by theme (e.g. clinical, fairness, operational). Flag which questions
   are answerable from the data alone vs. which require external context.

---

## Adapting to a New Dataset

When applying this skill to a different CSV, change these things:

| Thing to change | Where |
|---|---|
| `DATA_FILE` path | Top of `visualize.py` |
| `TARGET_COL` name | Top of `visualize.py` |
| Categorical columns used in charts 02–04 | Chart sections |
| Numeric columns used in charts 05–06, 08 | Chart sections |
| Color palette for target classes | `TARGET_COLORS` dict |
| Chart titles and axis labels | Each chart block |

Everything else — the save helper, dependency install, `charts/` folder,
chart numbering, correlation heatmap — works unchanged across datasets.

---

## Checklist

- [ ] CSV file located and readable
- [ ] Dependencies installed (`numpy`, `pandas`, `matplotlib`, `seaborn`)
- [ ] Data profiled and summarized in plain language
- [ ] `visualize.py` created with correct `DATA_FILE` and `TARGET_COL`
- [ ] All charts saved to `charts/` as numbered PNGs
- [ ] Script runs without fatal errors
- [ ] Findings summary provided to user
- [ ] Research questions suggested
