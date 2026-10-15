# Bias Audit Report — Diabetic Readmission Dataset

**Dataset:** `diabetic/data/diabetic_readmission.csv`  
**Rows:** 69,570 patients | **Columns:** 16  
**Audit date:** 2026-10-15  
**Script:** `bias_audit.py`

---

## 1. Representation

**Chart:** `charts/bias_01_representation_race.png`, `charts/bias_02_representation_age.png`

| Race | Count | % of dataset |
|---|---|---|
| Caucasian | 53,491 | 76.9% |
| African American | 12,887 | 18.5% |
| Hispanic | 1,517 | 2.2% |
| **Other** | **1,178** | **1.7% ⚠️** |
| **Asian** | **497** | **0.7% ⚠️** |

**Flags:** `other` and `asian` are both below the 2% representation threshold. Any model trained on this data will have seen very few examples from these groups, making predictions for them less reliable.

**Age distribution** is heavily skewed toward older patients. Groups aged 5–35 and 95 each represent less than 4% of the dataset. The core working-age and early-elderly groups (55–85) make up ~80% of records.

**Gender** is roughly balanced (female 53.2%, male 46.8%). One record is labelled `unknown/invalid` — too small to be meaningful.

---

## 2. Outcome Rates

**Chart:** `charts/bias_03_outcomes_race.png`, `charts/bias_04_outcomes_age.png`

**Overall readmission rate: 40.2%**

### By Race

| Race | Readmission rate | Δ vs overall |
|---|---|---|
| Caucasian | 41.0% | +0.8 pp |
| African American | 38.5% | −1.7 pp |
| Hispanic | 35.3% | −4.9 pp |
| **Other** | **33.2%** | **−7.0 pp ⚠️** |
| **Asian** | **29.8%** | **−10.4 pp ⚠️** |

`other` and `asian` are flagged (> 5 pp below the overall rate). Because these groups are also underrepresented (see section 1), this gap is harder to interpret — it may reflect genuine clinical differences, unmeasured confounders, or simply noisy estimates from small samples.

### By Age

Groups with very few patients (age 5, 15, 25) show the largest swings from the overall rate, which is expected given small sample sizes. Age 35 is also flagged (−5+ pp). At the other end, age 95 shows elevated readmission relative to adjacent groups. Clinically, the oldest and youngest patients are the highest-risk groups; the dataset may not capture enough cases to model them well.

### By Gender

No meaningful gender flag. The single `unknown/invalid` record shows 0% readmission, which is a statistical artefact of n=1.

---

## 3. Missing Data

**Chart:** `charts/bias_05_missing_data_heatmap.png`, `charts/bias_06_missing_data_by_age.png`

Both lab measurements have very high overall missing rates encoded as the string value `"none"`:

| Lab test | Overall missing |
|---|---|
| `max_glu_serum` | 95.1% |
| `a1c_result` | 81.9% |

### Missing rates by race (`max_glu_serum`)

| Race | % missing |
|---|---|
| African American | **97.6%** |
| Other | 95.4% |
| Asian | 95.6% |
| Caucasian | 94.6% |
| Hispanic | 91.6% |

African American patients have a notably higher `max_glu_serum` missing rate (97.6%) compared to Caucasian patients (94.6%), a ~3 pp gap. Although both rates are very high, the differential matters: any analysis relying on this feature may produce outcomes that systematically differ by race.

Missing rates are broadly consistent across gender and age groups. The `a1c_result` column shows a similar pattern, with Hispanic patients having slightly lower missingness (74.0%) than other groups.

---

## 4. Summary of Flags

| Check | Flagged groups | Severity |
|---|---|---|
| Representation < 2% | `asian`, `other` | Medium — small samples, unreliable estimates |
| Outcome rate > 5pp below overall | `asian` (−10pp), `other` (−7pp) | Medium — correlated with underrepresentation |
| Outcome rate by age | ages 5, 15, 25, 35, 95 | Low-Medium — small samples at extremes |
| Differential missing data | African American (`max_glu_serum` 97.6%) | Medium — could introduce racial bias in lab-feature models |

---

## 5. Limitations

1. **Race categories are coarse.** The five groups collapse substantial diversity. "Other" and "Hispanic" particularly can mask within-group variation.
2. **Lab data is near-absent.** With 95% and 82% missingness, `max_glu_serum` and `a1c_result` are effectively unusable as predictors without imputation strategies, and any imputation carries its own bias risk.
3. **Causality cannot be established.** This audit identifies statistical associations, not causes. A lower readmission rate for Asian patients does not mean they receive better care; it may reflect coding practices, socioeconomic factors, or care-seeking behaviour not captured in the dataset.
4. **Age is encoded as decade midpoints.** Fine-grained age effects are not visible; within-decade heterogeneity is hidden.
5. **Single-institution or aggregated data.** Without knowing the data source(s), it is unclear how representative this sample is of broader diabetic populations.
6. **No intersectional analysis.** This audit examines race, gender, and age independently. Interactions between groups (e.g., young Asian women) are not assessed and could reveal additional disparities.
