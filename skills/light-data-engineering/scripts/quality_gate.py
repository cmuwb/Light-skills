"""quality_gate.py — validate a CSV against a YAML rule file. Pass/fail report.

Pure pandas + PyYAML. No heavy external dependency (no Great Expectations /
Frictionless needed) so it runs anywhere. Reproducible data gate for pipelines.

Rule file (YAML) shape:
    dataset:
      min_rows: 100
      max_rows: 1000000
      no_duplicate_rows: true
    columns:
      age:
        dtype: int          # int | float | numeric | string | bool | datetime
        required: true       # column must exist
        non_null: true       # no missing values
        min: 0
        max: 120
      status:
        enum: [active, churned, paused]
      email:
        regex: "^[^@]+@[^@]+\\.[^@]+$"
      user_id:
        unique: true

Exit code 0 = all pass, 1 = any failure (CI-friendly).

Usage:
    python quality_gate.py --csv data.csv --rules rules.yaml [--out report.md]
    python quality_gate.py --selftest
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import argparse
import io
import re
import numpy as np
import pandas as pd
import yaml


def _is_dtype(series, want):
    s = series.dropna()
    if want == "numeric":
        return pd.api.types.is_numeric_dtype(series)
    if want == "int":
        if pd.api.types.is_integer_dtype(series):
            return True
        if pd.api.types.is_float_dtype(series):       # allow whole-valued floats
            return bool(np.all(np.equal(np.mod(s.values, 1), 0))) if len(s) else True
        return False
    if want == "float":
        return pd.api.types.is_float_dtype(series)
    if want == "bool":
        return pd.api.types.is_bool_dtype(series)
    if want == "datetime":
        if pd.api.types.is_datetime64_any_dtype(series):
            return True
        try:
            pd.to_datetime(s, errors="raise")
            return True
        except Exception:
            return False
    if want == "string":
        return pd.api.types.is_object_dtype(series) or \
            isinstance(series.dtype, pd.CategoricalDtype) or \
            pd.api.types.is_string_dtype(series)
    return True  # unknown type spec -> don't fail on it


def validate(df, rules):
    """Return (results, all_passed). Each result: dict(check, target, status, detail)."""
    results = []

    def add(check, target, ok, detail=""):
        results.append({"check": check, "target": target,
                        "status": "PASS" if ok else "FAIL", "detail": detail})
        return ok

    ds = rules.get("dataset", {}) or {}
    n = len(df)
    if "min_rows" in ds:
        add("min_rows", "<dataset>", n >= ds["min_rows"],
            f"{n} rows (need >= {ds['min_rows']})")
    if "max_rows" in ds:
        add("max_rows", "<dataset>", n <= ds["max_rows"],
            f"{n} rows (need <= {ds['max_rows']})")
    if ds.get("no_duplicate_rows"):
        d = int(df.duplicated().sum())
        add("no_duplicate_rows", "<dataset>", d == 0, f"{d} duplicate rows")

    cols = rules.get("columns", {}) or {}
    for col, spec in cols.items():
        spec = spec or {}
        present = col in df.columns
        if spec.get("required"):
            add("required", col, present, "missing column" if not present else "present")
        if not present:
            continue
        s = df[col]

        if "dtype" in spec:
            ok = _is_dtype(s, spec["dtype"])
            add("dtype", col, ok, f"want {spec['dtype']}, got {s.dtype}")
        if spec.get("non_null"):
            nn = int(s.isna().sum())
            add("non_null", col, nn == 0, f"{nn} nulls")
        if spec.get("unique"):
            dup = int(s.duplicated().sum())
            add("unique", col, dup == 0, f"{dup} duplicate values")
        if "min" in spec:
            sv = pd.to_numeric(s, errors="coerce")
            bad = int((sv < spec["min"]).sum())
            add("min", col, bad == 0, f"{bad} values < {spec['min']}")
        if "max" in spec:
            sv = pd.to_numeric(s, errors="coerce")
            bad = int((sv > spec["max"]).sum())
            add("max", col, bad == 0, f"{bad} values > {spec['max']}")
        if "enum" in spec:
            allowed = set(spec["enum"])
            bad_vals = set(s.dropna().unique()) - allowed
            add("enum", col, len(bad_vals) == 0,
                f"unexpected: {sorted(map(str, bad_vals))[:10]}" if bad_vals else "ok")
        if "regex" in spec:
            pat = re.compile(spec["regex"])
            nonmatch = int(s.dropna().astype(str).apply(
                lambda v: pat.search(v) is None).sum())
            add("regex", col, nonmatch == 0, f"{nonmatch} non-matching values")

    all_passed = all(r["status"] == "PASS" for r in results)
    return results, all_passed


def render(results, all_passed):
    L = ["# Data Quality Gate Report", ""]
    n_pass = sum(r["status"] == "PASS" for r in results)
    L.append(f"**Result: {'PASS' if all_passed else 'FAIL'}**  "
             f"({n_pass}/{len(results)} checks passed)")
    L.append("")
    L.append("| check | target | status | detail |")
    L.append("| --- | --- | --- | --- |")
    for r in results:
        mark = "PASS" if r["status"] == "PASS" else "**FAIL**"
        L.append(f"| {r['check']} | `{r['target']}` | {mark} | {r['detail']} |")
    L.append("")
    return "\n".join(L)


SYNTH_RULES = {
    "dataset": {"min_rows": 5, "no_duplicate_rows": True},
    "columns": {
        "age": {"dtype": "int", "required": True, "non_null": True, "min": 0, "max": 120},
        "status": {"enum": ["active", "churned"]},
        "email": {"regex": r"^[^@]+@[^@]+\.[^@]+$"},
        "user_id": {"unique": True, "required": True},
        "missing_col": {"required": True},
    },
}


def make_synth_bad():
    return pd.DataFrame({
        "age": [25, 40, 200, -3, 33, 33],        # 200>max, -3<min
        "status": ["active", "churned", "frozen", "active", "active", "active"],  # frozen not in enum
        "email": ["a@b.com", "bad", "c@d.org", "e@f.io", "g@h.co", "g@h.co"],     # 'bad' fails regex
        "user_id": [1, 2, 3, 4, 5, 5],           # dup id
    })  # also: no 'missing_col', and row [33,active,g@h.co,5]... duplicates handled by id


def make_synth_good():
    return pd.DataFrame({
        "age": [25, 40, 30, 33, 50],
        "status": ["active", "churned", "active", "active", "churned"],
        "email": ["a@b.com", "c@d.org", "e@f.io", "g@h.co", "i@j.net"],
        "user_id": [1, 2, 3, 4, 5],
        "missing_col": [1, 2, 3, 4, 5],
    })


def main():
    ap = argparse.ArgumentParser(description="Validate CSV against YAML rules")
    ap.add_argument("--csv")
    ap.add_argument("--rules")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        bad = make_synth_bad()
        res, ok = validate(bad, SYNTH_RULES)
        print(render(res, ok))
        fails = {(r["check"], r["target"]) for r in res if r["status"] == "FAIL"}
        for expected in [("max", "age"), ("min", "age"), ("enum", "status"),
                         ("regex", "email"), ("unique", "user_id"),
                         ("required", "missing_col")]:
            assert expected in fails, f"gate missed {expected}"
        assert not ok, "bad data should not pass"
        good, gok = make_synth_good(), None
        gres, gok = validate(make_synth_good(), SYNTH_RULES)
        assert gok, "clean data should pass: " + \
            str([r for r in gres if r["status"] == "FAIL"])
        print("[selftest] PASS — every rule fired on bad data; clean data passed.")
        return

    if not (args.csv and args.rules):
        ap.error("provide --csv and --rules, or --selftest")
    df = pd.read_csv(args.csv)
    with io.open(args.rules, encoding="utf-8") as fh:
        rules = yaml.safe_load(fh)
    res, ok = validate(df, rules)
    report = render(res, ok)
    if args.out:
        with io.open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"Wrote report to {args.out}", file=sys.stderr)
    else:
        print(report)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
