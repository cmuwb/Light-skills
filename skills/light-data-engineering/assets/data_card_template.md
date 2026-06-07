# Dataset Card: {{dataset_name}}

> Datasheet for the dataset. Fill every section honestly. Empty/unknown fields
> must say "unknown" or "not assessed" — never leave a false impression.
> Field names align with Light db04 (数据集卡) for cross-knowledge-base reuse.

## 1. Overview
- **dataset_name**: {{dataset_name}}
- **version / DOI**: {{version}} / {{doi}}
- **domain**: {{domain}}
- **task**: {{task}}  (e.g. classification / regression / detection / segmentation)
- **data_type**: {{data_type}}  (tabular / image / text / time-series / multimodal)
- **size**: {{n_rows}} rows × {{n_cols}} cols  ({{n_bytes}} on disk)
- **format**: {{format}}  (csv / parquet / jsonl / ...)
- **license**: {{license}}  (commercial use? redistribution? attribution?)
- **download_url**: {{download_url}}
- **paper_url / citation**: {{paper_url}}

## 2. Motivation
- Why was this dataset created? What gap does it fill?
- Who funded / created it? (`creator`, `funder`)

## 3. Composition
- What does each instance represent? (a user, an image, a transaction...)
- Column/field dictionary: name, type, unit, meaning, allowed range/values.
- Label definition + how labels were obtained.
- Class balance / target distribution (attach counts).
- Are there splits provided? (`recommended_splits`) How were they made
  (random / stratified / temporal / by-group)? Seed?

## 4. Collection Process
- How was data acquired? (sensors, scraping, survey, logs, synthetic)
- Time window of collection. Sampling strategy. Selection bias risks.
- Was consent obtained? From whom? Under what terms?

## 5. Preprocessing / Cleaning (`preprocessing_steps`)
- Deduplication, type fixes, unit normalization, text cleaning.
- Missing-value handling (mechanism MCAR/MAR/MNAR + strategy).
- Outlier treatment. Filtering rules applied.
- Is the raw data preserved alongside the cleaned data?

## 6. Quality Assessment (run the tooling, paste results)
- **data_doctor.py** report attached? health summary:
- **quality_gate.py** result against `rules.yaml`: PASS / FAIL ( / checks)
- Completeness, consistency, accuracy, timeliness, uniqueness, representativeness.

## 7. Known Issues & Risks
- **known_issues**: {{known_issues}}
- **bias_risk**: {{bias_risk}}  (under-represented groups, label noise, spurious correlations)
- **privacy_risk**: {{privacy_risk}}  (PII present? de-identified how? re-identification risk?)
- Documented leakage hazards (columns that encode the target / future info).

## 8. Recommended Use & Splits
- Intended tasks and metrics (`leaderboard_url` if any).
- **recommended_splits**: scheme + seed (use safe_split.py task = clf/reg/timeseries/group).
- Uses to avoid (out-of-scope, ethically problematic).

## 9. Maintenance
- Maintainer / contact. Update cadence. Versioning policy.
- How to report errors. Will old versions stay available?

## 10. Provenance & Verification
- Sources with checkable links (honor Light CONVENTIONS: no fabricated DOIs).
- `last_checked_date`: {{date}}
- Which fields are verified vs inferred/unknown.
