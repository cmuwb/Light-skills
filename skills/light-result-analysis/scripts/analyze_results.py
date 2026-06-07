"""analyze_results.py - one-command result-table analysis (Light m06).

Input: a results CSV with one column naming the method/group and one or more
numeric metric columns. Produces:
  * EDA summary per group (n, mean, std, median, min, max, 95% CI of mean),
  * automatic group-comparison test chosen by data shape:
        2 groups,  both ~normal (Shapiro)  -> Welch t-test
        2 groups,  non-normal              -> Mann-Whitney U
        >=3 groups, all ~normal            -> one-way ANOVA + Tukey HSD
        >=3 groups, non-normal             -> Kruskal-Wallis (+ Dunn-ish note)
  * Cohen's d effect size for every pairwise comparison,
  * BH-FDR correction across all reported p-values,
  * machine-readable summary.json + human-readable summary.md.

Usage:
  python analyze_results.py results.csv --group method --metric acc
  python analyze_results.py results.csv --group method --metric acc f1 auroc
  python analyze_results.py            # no args -> generate synthetic CSV & run

Reuses verified stats from significance_test.py (which reuses code_assets).
"""
import argparse
import json
import os
import sys
import itertools
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from significance_test import (  # noqa: E402
    welch_t, cohens_d, interpret_d, mean_diff_ci, benjamini_hochberg,
)

ALPHA = 0.05


def _normal(x, alpha=0.05):
    """Shapiro-Wilk normality; True if cannot reject normality (or n<3)."""
    from scipy import stats
    x = np.asarray(x, float)
    if len(x) < 3:
        return True
    try:
        return stats.shapiro(x).pvalue > alpha
    except Exception:
        return True


def eda_summary(df, group, metric):
    """Per-group descriptive stats including a 95% CI of the mean."""
    from scipy import stats
    rows = []
    for g, sub in df.groupby(group):
        x = sub[metric].dropna().to_numpy(float)
        n = len(x)
        if n == 0:
            continue
        mean = float(x.mean())
        sd = float(x.std(ddof=1)) if n > 1 else 0.0
        if n > 1:
            se = sd / np.sqrt(n)
            tcrit = stats.t.ppf(0.975, n - 1)
            ci = (mean - tcrit * se, mean + tcrit * se)
        else:
            ci = (mean, mean)
        rows.append({
            "group": str(g), "n": n, "mean": mean, "std": sd,
            "median": float(np.median(x)), "min": float(x.min()),
            "max": float(x.max()), "ci95_low": float(ci[0]), "ci95_high": float(ci[1]),
            "normal": bool(_normal(x)),
        })
    return sorted(rows, key=lambda r: r["mean"], reverse=True)


def group_test(df, group, metric):
    """Pick and run the omnibus test appropriate for #groups and normality."""
    from scipy import stats
    groups, data = [], []
    for g, sub in df.groupby(group):
        x = sub[metric].dropna().to_numpy(float)
        if len(x) > 0:
            groups.append(str(g)); data.append(x)
    k = len(groups)
    all_normal = all(_normal(x) for x in data)
    out = {"n_groups": k, "all_normal": bool(all_normal), "groups": groups}

    if k < 2:
        out.update(test="none", note="need >=2 groups", p=None)
        return out
    if k == 2:
        if all_normal:
            t, dfree, p = welch_t(data[0], data[1])
            out.update(test="welch_t", statistic=float(t), df=float(dfree), p=float(p))
        else:
            u, p = stats.mannwhitneyu(data[0], data[1], alternative="two-sided")
            out.update(test="mann_whitney_u", statistic=float(u), p=float(p))
        return out
    # k >= 3
    if all_normal:
        f, p = stats.f_oneway(*data)
        out.update(test="anova_oneway", statistic=float(f), p=float(p))
        out["posthoc"] = _tukey(data, groups)
    else:
        h, p = stats.kruskal(*data)
        out.update(test="kruskal_wallis", statistic=float(h), p=float(p))
        out["posthoc_note"] = "non-normal multi-group: pairwise Mann-Whitney below, BH-FDR corrected"
    return out


def _tukey(data, groups):
    """Tukey HSD via statsmodels if available, else None."""
    try:
        from statsmodels.stats.multicomp import pairwise_tukeyhsd
        vals = np.concatenate(data)
        labels = np.concatenate([[g] * len(d) for g, d in zip(groups, data)])
        res = pairwise_tukeyhsd(vals, labels, alpha=ALPHA)
        out = []
        for row in res.summary().data[1:]:
            out.append({"group1": row[0], "group2": row[1], "meandiff": float(row[2]),
                        "p_adj": float(row[3]), "lower": float(row[4]),
                        "upper": float(row[5]), "reject": bool(row[6])})
        return out
    except Exception:
        return None


def pairwise(df, group, metric):
    """All pairwise comparisons with Cohen's d, mean-diff CI, and a p-value
    (test matched to per-pair normality). p-values get BH-FDR across all pairs."""
    from scipy import stats
    groups, data = [], {}
    for g, sub in df.groupby(group):
        x = sub[metric].dropna().to_numpy(float)
        if len(x) > 0:
            groups.append(str(g)); data[str(g)] = x
    comps = []
    for g1, g2 in itertools.combinations(groups, 2):
        a, b = data[g1], data[g2]
        normal = _normal(a) and _normal(b)
        if normal:
            _, _, p = welch_t(a, b)
            test = "welch_t"
        else:
            _, p = stats.mannwhitneyu(a, b, alternative="two-sided")
            test = "mann_whitney_u"
        d = cohens_d(a, b, correction=True)
        diff, ci = mean_diff_ci(a, b, equal_var=False)
        comps.append({"group1": g1, "group2": g2, "test": test, "p": float(p),
                      "cohens_d": float(d), "effect": interpret_d(d),
                      "mean_diff": float(diff), "diff_ci95": [float(ci[0]), float(ci[1])]})
    if comps:
        rej, q = benjamini_hochberg([c["p"] for c in comps], ALPHA)
        for c, r, qq in zip(comps, rej, q):
            c["q_fdr"] = float(qq); c["significant_fdr"] = bool(r)
    return comps


def analyze_metric(df, group, metric):
    return {"metric": metric, "eda": eda_summary(df, group, metric),
            "omnibus": group_test(df, group, metric),
            "pairwise": pairwise(df, group, metric)}


def run(csv_path, group, metrics, outdir):
    df = pd.read_csv(csv_path)
    if group not in df.columns:
        raise SystemExit(f"group column '{group}' not in CSV columns {list(df.columns)}")
    if not metrics:
        metrics = [c for c in df.columns if c != group and pd.api.types.is_numeric_dtype(df[c])]
    report = {"csv": os.path.abspath(csv_path), "group": group,
              "n_rows": int(len(df)), "metrics": metrics, "alpha": ALPHA,
              "results": [analyze_metric(df, group, m) for m in metrics]}
    os.makedirs(outdir, exist_ok=True)
    jpath = os.path.join(outdir, "summary.json")
    mpath = os.path.join(outdir, "summary.md")
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    with open(mpath, "w", encoding="utf-8") as f:
        f.write(_render_md(report))
    return report, jpath, mpath


def _render_md(report):
    L = [f"# Result Analysis: `{os.path.basename(report['csv'])}`", "",
         f"- Group column: **{report['group']}**  |  rows: {report['n_rows']}  |  alpha={report['alpha']}",
         f"- Metrics: {', '.join(report['metrics'])}", ""]
    for res in report["results"]:
        m = res["metric"]
        L.append(f"## Metric: `{m}`\n")
        L.append("| group | n | mean | std | 95% CI | normal |")
        L.append("|---|---|---|---|---|---|")
        for r in res["eda"]:
            L.append(f"| {r['group']} | {r['n']} | {r['mean']:.4f} | {r['std']:.4f} "
                     f"| [{r['ci95_low']:.4f}, {r['ci95_high']:.4f}] | {'Y' if r['normal'] else 'N'} |")
        best = res["eda"][0] if res["eda"] else None
        ob = res["omnibus"]
        L.append("")
        if ob.get("p") is not None:
            sig = "significant" if ob["p"] < report["alpha"] else "not significant"
            L.append(f"**Omnibus test**: {ob['test']} -> p = {ob['p']:.4g} ({sig}). "
                     f"normality: {'all normal' if ob['all_normal'] else 'non-normal present'}.")
        if ob.get("posthoc"):
            L.append("\nTukey HSD post-hoc:")
            L.append("\n| g1 | g2 | meandiff | p_adj | reject |\n|---|---|---|---|---|")
            for t in ob["posthoc"]:
                L.append(f"| {t['group1']} | {t['group2']} | {t['meandiff']:.4f} | {t['p_adj']:.4g} | {t['reject']} |")
        L.append("\n**Pairwise (Cohen's d + BH-FDR):**")
        L.append("\n| g1 | g2 | test | p | q(FDR) | sig | d | effect | mean_diff [CI] |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for c in res["pairwise"]:
            ci = c["diff_ci95"]
            L.append(f"| {c['group1']} | {c['group2']} | {c['test']} | {c['p']:.4g} | "
                     f"{c.get('q_fdr', float('nan')):.4g} | {'Y' if c.get('significant_fdr') else 'n'} | "
                     f"{c['cohens_d']:.3f} | {c['effect']} | {c['mean_diff']:.4f} [{ci[0]:.4f}, {ci[1]:.4f}] |")
        if best:
            L.append(f"\n_Top group by mean: **{best['group']}** ({best['mean']:.4f})._\n")
    L.append("\n---\n_Tests auto-selected by Shapiro normality and group count. "
             "Effect sizes are Hedges'-corrected Cohen's d. p-values BH-FDR corrected per metric. "
             "See significance_test.py for the verified primitives._")
    return "\n".join(L)


def _synth_csv(path, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    specs = {"baseline": (0.80, 0.025), "ours": (0.86, 0.022), "ablation": (0.83, 0.030)}
    for method, (mu, sd) in specs.items():
        for _ in range(8):
            acc = float(np.clip(rng.normal(mu, sd), 0, 1))
            f1 = float(np.clip(acc - rng.normal(0.02, 0.01), 0, 1))
            rows.append({"method": method, "seed": _, "acc": round(acc, 4), "f1": round(f1, 4)})
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def main():
    ap = argparse.ArgumentParser(description="Auto result-table statistical analysis")
    ap.add_argument("csv", nargs="?", help="results CSV (omit to run synthetic demo)")
    ap.add_argument("--group", default="method")
    ap.add_argument("--metric", nargs="+", default=None, help="metric column(s)")
    ap.add_argument("--outdir", default=None)
    a = ap.parse_args()

    if not a.csv:
        here = os.path.dirname(os.path.abspath(__file__))
        a.csv = _synth_csv(os.path.join(here, "_synth_results.csv"))
        a.group = "method"; a.metric = a.metric or ["acc", "f1"]
        print(f"[demo] generated synthetic CSV -> {a.csv}")
    outdir = a.outdir or os.path.join(os.path.dirname(os.path.abspath(a.csv)), "analysis_out")
    report, jp, mp = run(a.csv, a.group, a.metric, outdir)
    print(f"wrote {jp}\nwrote {mp}")
    for res in report["results"]:
        ob = res["omnibus"]
        print(f"  [{res['metric']}] {ob.get('test')} p={ob.get('p')}  "
              f"top={res['eda'][0]['group'] if res['eda'] else 'NA'}")
    print("DONE")


if __name__ == "__main__":
    main()



