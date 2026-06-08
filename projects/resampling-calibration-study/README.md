# Resampling Silently Degrades Probability Calibration in Tree Ensembles

> An end-to-end empirical study built entirely with the **Light** skill pack — from literature search and idea critique through experiments, figures, and a 6-page IEEE paper. Every number comes from real runs; no data was fabricated.

![Showcase](figures/showcase.png)

## TL;DR

Resampling methods (SMOTE, random over/under-sampling) are standard for class imbalance and are almost always judged by F1 or AUC. This study shows they carry a hidden cost: they **systematically degrade the probability calibration** of tree ensembles, while the discrimination metrics practitioners watch stay flat or even improve — so the damage is invisible to standard evaluation.

- **5** OpenML datasets (imbalance ratio 1.9–70) · **2** ensembles · **7** conditions · **10** seeds
- All resampling families significantly raise ECE (Wilcoxon *p* < 10⁻³, Holm-corrected)
- Undersampling is worst, and its harm explodes with imbalance: ECE 0.008 → 0.395 at IR=70
- A single post-hoc recalibration step cuts ECE by ~66% at a negligible AUC cost (−0.003)

## Honest framing

This is a **consolidation and cautionary extension**, not a brand-new discovery. Dal Pozzolo et al. (2015) already showed undersampling distorts calibration. Our value is breadth (SMOTE + oversampling + class-weight under one protocol), a sampling-ratio sweep, and a **negative result**: the analytic prior-shift correction that fixes undersampling does *not* transfer to SMOTE, because SMOTE distorts the class-conditional density, not just the prior. The paper states this plainly rather than overclaiming — and the same honesty is now baked into the Light skills (see below).

## What's in here

| Path | Contents |
|------|----------|
| [`paper/main.pdf`](paper/main.pdf) | The 6-page IEEE paper (compiles clean: 6 figures, 5 tables, 8 verified refs) |
| [`paper/main.tex`](paper/main.tex), [`paper/refs.bib`](paper/refs.bib) | LaTeX source and bibliography |
| [`src/`](src/) | Data fetch, experiment runner, ρ-sweep, SHAP, prior-correction, figure scripts |
| [`experiments/`](experiments/) | Raw results: 700-row main grid, 250-row ρ-sweep, SHAP shift, E5 prior-correction |
| [`data/processed/`](data/processed/) | The five preprocessed OpenML datasets (parquet) |
| [`docs/`](docs/) | Per-stage records: literature review, ideas, critique verdict, plan, dataset card, analysis |
| [`figures/`](figures/) | All paper figures plus the composite `showcase.png` |

## The figures

| | |
|---|---|
| ![ECE by condition](figures/fig1_ece_by_condition.png) | ![ECE vs imbalance ratio](figures/fig3_ece_vs_ir.png) |
| **Resampling raises ECE; recalibration repairs it.** | **Undersampling damage explodes with imbalance.** |
| ![ECE vs oversampling ratio](figures/fig4_rho_sweep.png) | ![SHAP attribution shift](figures/fig6_shap_shift.png) |
| **Calibration cost grows with the oversampling ratio.** | **Feature attributions are preserved (ρ=0.96) — only the probability scale is harmed.** |

## Reproduce

```bash
pip install numpy pandas scikit-learn matplotlib scipy shap
python src/fetch_data.py          # pull + preprocess the 5 OpenML datasets
python src/run_experiments.py     # main 700-row grid
python src/run_rho_sweep.py       # E4: oversampling-ratio sweep
python src/run_prior_correct.py   # E5: analytic prior correction (negative result)
python src/run_shap.py            # SHAP attribution shift
python src/make_figures.py && python src/make_figures_extra.py && python src/make_showcase.py
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```

## How Light built this — and learned from it

Every stage used a dedicated Light skill: literature-search → idea-generation → idea-critique → research-plan → data-engineering → experiments → result-analysis → figure-drawing → paper-drafting → citation → typesetting, with self-review as the output gate.

The most useful outcome was a **failure caught and fixed in the skills themselves**. The core finding turned out to overlap heavily with prior work that wasn't surfaced until the paper was nearly done. In response, the novelty-collision checks in `idea-generation`, `idea-critique`, and `self-review` were hardened, and `paper-drafting` gained guidance on honestly reframing genuinely incremental work. The skill pack got better by doing the work and being honest about where it fell short.

> Part of the [Light](../../README.md) research skill pack.
