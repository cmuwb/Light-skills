"""data_doctor.py — CSV in, Markdown health report out.

A no-network, pure pandas/numpy data health checker. Profiles shape, dtypes,
real memory, missing/duplicate rows, constant + high-cardinality columns,
numeric outliers (IQR), and strong correlations. Designed to be the first
thing you run on a new table before any modeling.

Usage:
    python data_doctor.py --csv data.csv [--out report.md] [--target y] \
        [--corr-thresh 0.9] [--card-thresh 0.5] [--sample 200000]

Self-test (no data needed):
    python data_doctor.py --selftest

Writes a Markdown report to --out (default: stdout). Honest by design: every
number is computed from the data, nothing is hardcoded.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import argparse
import io
import numpy as np
import pandas as pd


def _human_bytes(n):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(n) < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"


def _md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join(["---"] * len(headers)) + " |"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def diagnose(df, target=None, corr_thresh=0.9, card_thresh=0.5, outlier_cap=20):
    """Return a dict of findings. Pure computation, no I/O."""
    n_rows, n_cols = df.shape
    f = {"n_rows": n_rows, "n_cols": n_cols}

    # memory
    mem = df.memory_usage(deep=True)
    f["mem_total"] = int(mem.sum())
    f["mem_per_col"] = {c: int(mem[c]) for c in df.columns}

    # dtypes
    f["dtypes"] = {c: str(df[c].dtype) for c in df.columns}

    # missing
    miss = df.isna().sum()
    f["missing"] = {c: (int(miss[c]), float(miss[c] / n_rows) if n_rows else 0.0)
                    for c in df.columns if miss[c] > 0}

    # duplicate rows
    f["dup_rows"] = int(df.duplicated().sum())

    # constant columns (1 unique non-null, or all null)
    f["constant_cols"] = []
    f["allnull_cols"] = []
    for c in df.columns:
        nun = df[c].nunique(dropna=True)
        if nun == 0:
            f["allnull_cols"].append(c)
        elif nun == 1:
            f["constant_cols"].append(c)

    # high-cardinality (object/category): unique ratio over threshold
    f["high_card"] = []
    obj_cols = df.select_dtypes(include=["object", "category", "string"]).columns
    for c in obj_cols:
        non_null = df[c].notna().sum()
        if non_null == 0:
            continue
        ratio = df[c].nunique(dropna=True) / non_null
        if ratio >= card_thresh:
            f["high_card"].append((c, df[c].nunique(dropna=True), round(ratio, 3)))

    # numeric outliers via IQR
    f["outliers"] = []
    num_cols = df.select_dtypes(include=[np.number]).columns
    for c in num_cols:
        s = df[c].dropna()
        if len(s) < 4:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        n_out = int(((s < lo) | (s > hi)).sum())
        if n_out > 0:
            f["outliers"].append((c, n_out, round(100 * n_out / len(s), 2),
                                  round(float(lo), 4), round(float(hi), 4)))
    f["outliers"].sort(key=lambda x: -x[2])
    f["outliers"] = f["outliers"][:outlier_cap]

    # correlations (numeric, abs over threshold, upper triangle)
    f["high_corr"] = []
    if len(num_cols) >= 2:
        corr = df[num_cols].corr(numeric_only=True)
        cols = corr.columns
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                v = corr.iloc[i, j]
                if pd.notna(v) and abs(v) >= corr_thresh:
                    f["high_corr"].append((cols[i], cols[j], round(float(v), 4)))
        f["high_corr"].sort(key=lambda x: -abs(x[2]))

    # target leakage hint: feature near-perfectly correlated with numeric target
    f["leakage_hint"] = []
    if target and target in df.columns and target in num_cols:
        tcorr = df[num_cols].corr(numeric_only=True)[target].drop(target)
        for c, v in tcorr.items():
            if pd.notna(v) and abs(v) >= 0.98:
                f["leakage_hint"].append((c, round(float(v), 4)))
    return f


def render(df, f, target=None):
    """Render findings dict to a Markdown string."""
    L = []
    L.append("# Data Health Report")
    L.append("")
    L.append(f"- Rows: **{f['n_rows']:,}**  |  Columns: **{f['n_cols']}**  "
             f"|  Memory (deep): **{_human_bytes(f['mem_total'])}**")
    if target:
        L.append(f"- Declared target: `{target}`")
    L.append("")

    # severity-ranked issue summary up top
    issues = []
    if f["allnull_cols"]:
        issues.append(("HIGH", f"{len(f['allnull_cols'])} all-null column(s): "
                       f"{', '.join(f['allnull_cols'])}"))
    if f["constant_cols"]:
        issues.append(("HIGH", f"{len(f['constant_cols'])} constant column(s): "
                       f"{', '.join(f['constant_cols'])}"))
    if f["dup_rows"]:
        issues.append(("MED", f"{f['dup_rows']:,} duplicate row(s) "
                       f"({100*f['dup_rows']/max(f['n_rows'],1):.2f}%)"))
    hi_miss = [c for c, (_, r) in f["missing"].items() if r >= 0.5]
    if hi_miss:
        issues.append(("HIGH", f"{len(hi_miss)} column(s) >=50% missing: "
                       f"{', '.join(hi_miss)}"))
    if f["leakage_hint"]:
        issues.append(("HIGH", f"possible target leakage (|corr|>=0.98 to target): "
                       f"{', '.join(c for c, _ in f['leakage_hint'])}"))
    if f["high_corr"]:
        issues.append(("MED", f"{len(f['high_corr'])} highly-correlated numeric pair(s)"))
    if f["high_card"]:
        issues.append(("LOW", f"{len(f['high_card'])} high-cardinality categorical col(s)"))

    L.append("## Issue Summary")
    if issues:
        order = {"HIGH": 0, "MED": 1, "LOW": 2}
        issues.sort(key=lambda x: order[x[0]])
        for sev, msg in issues:
            L.append(f"- **[{sev}]** {msg}")
    else:
        L.append("- No structural issues flagged by the heuristics. Still verify semantics.")
    L.append("")

    # dtypes + memory + missing combined
    L.append("## Columns (dtype / memory / missing)")
    rows = []
    for c in df.columns:
        miss_n, miss_r = f["missing"].get(c, (0, 0.0))
        rows.append([f"`{c}`", f["dtypes"][c], _human_bytes(f["mem_per_col"][c]),
                     f"{miss_n:,}", f"{100*miss_r:.2f}%"])
    L.append(_md_table(["column", "dtype", "memory", "missing", "missing%"], rows))
    L.append("")

    if f["outliers"]:
        L.append("## Numeric Outliers (IQR, top by %)")
        L.append(_md_table(
            ["column", "n_outliers", "%", "lower_fence", "upper_fence"],
            [[f"`{c}`", n, f"{p}%", lo, hi] for c, n, p, lo, hi in f["outliers"]]))
        L.append("")

    if f["high_corr"]:
        L.append("## Highly-Correlated Numeric Pairs")
        L.append(_md_table(["col_a", "col_b", "pearson_r"],
                           [[f"`{a}`", f"`{b}`", v] for a, b, v in f["high_corr"][:30]]))
        L.append("")

    if f["high_card"]:
        L.append("## High-Cardinality Categoricals")
        L.append(_md_table(["column", "n_unique", "unique_ratio"],
                           [[f"`{c}`", n, r] for c, n, r in f["high_card"]]))
        L.append("")

    L.append("## Verdict (fill in after review)")
    L.append("- [ ] Usable as-is  - [ ] Needs cleaning  - [ ] Insufficient  - [ ] Needs more collection")
    L.append("")
    L.append("> Generated by data_doctor.py. Heuristic flags are hypotheses, "
             "not conclusions — confirm against domain knowledge.")
    return "\n".join(L)


def make_synth(seed=0):
    rng = np.random.default_rng(seed)
    n = 500
    df = pd.DataFrame({
        "id": np.arange(n),                              # high cardinality
        "age": rng.normal(45, 12, n).round(1),
        "income": rng.lognormal(10, 0.5, n).round(2),    # outliers
        "city": rng.choice(["A", "B", "C"], n),
        "const": 1,                                      # constant
        "empty": np.nan,                                 # all null
        "score": rng.normal(0, 1, n),
    })
    df["score_copy"] = df["score"] * 2 + 1e-9            # ~perfect corr
    df.loc[rng.choice(n, 60, replace=False), "income"] = np.nan  # missing
    df.loc[rng.choice(n, 5, replace=False), "income"] = 5e6      # extreme outliers
    df = pd.concat([df, df.iloc[:10]], ignore_index=True)        # duplicates
    return df


def main():
    ap = argparse.ArgumentParser(description="CSV -> Markdown data health report")
    ap.add_argument("--csv")
    ap.add_argument("--out")
    ap.add_argument("--target")
    ap.add_argument("--corr-thresh", type=float, default=0.9)
    ap.add_argument("--card-thresh", type=float, default=0.5)
    ap.add_argument("--sample", type=int, default=0,
                    help="random-sample N rows before profiling (0=all)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        df = make_synth()
        f = diagnose(df, target="score", corr_thresh=args.corr_thresh,
                     card_thresh=args.card_thresh)
        md = render(df, f, target="score")
        # assertions prove the detectors actually fire
        assert "empty" in f["allnull_cols"], "all-null detector failed"
        assert "const" in f["constant_cols"], "constant detector failed"
        assert f["dup_rows"] == 10, f"dup count wrong: {f['dup_rows']}"
        assert any(c == "income" for c, *_ in f["outliers"]), "outlier detector failed"
        assert any({a, b} == {"score", "score_copy"} for a, b, _ in f["high_corr"]), \
            "correlation detector failed"
        print(md)
        print("\n[selftest] PASS — all detectors fired on synthetic data.",
              file=sys.stderr)
        return

    if not args.csv:
        ap.error("provide --csv or --selftest")
    df = pd.read_csv(args.csv)
    if args.sample and len(df) > args.sample:
        df = df.sample(args.sample, random_state=0)
    f = diagnose(df, target=args.target, corr_thresh=args.corr_thresh,
                 card_thresh=args.card_thresh)
    md = render(df, f, target=args.target)
    if args.out:
        with io.open(args.out, "w", encoding="utf-8") as fh:
            fh.write(md)
        print(f"Wrote report to {args.out}", file=sys.stderr)
    else:
        print(md)


if __name__ == "__main__":
    main()
