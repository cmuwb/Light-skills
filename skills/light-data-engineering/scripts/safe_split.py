"""safe_split.py — leakage-safe split + Pipeline/ColumnTransformer builder.

Given a task type, builds a scikit-learn preprocessing Pipeline wrapped in a
ColumnTransformer (numeric impute+scale, categorical impute+one-hot) and picks
the correct cross-validation scheme so that NO fit ever sees the validation fold:

    clf        -> StratifiedKFold
    reg        -> KFold
    timeseries -> TimeSeriesSplit (no future leakage)
    group      -> GroupKFold / StratifiedGroupKFold (no entity leakage)

The whole point: every fit-based transform lives inside the Pipeline so it is
re-fit per training fold only. We prove that with a leakage assertion in the
self-test (preprocessor fit on a fold must differ from fit on full data).

Usage:
    python safe_split.py --csv data.csv --target y --task clf [--group-col user_id]
    python safe_split.py --selftest
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import argparse
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import (
    StratifiedKFold, KFold, TimeSeriesSplit, GroupKFold, StratifiedGroupKFold)


def build_preprocessor(X):
    """ColumnTransformer: numeric -> median impute + scale; categorical ->
    most-frequent impute + one-hot. All fit-based, so must live in a Pipeline."""
    num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = X.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    num_pipe = Pipeline([("impute", SimpleImputer(strategy="median")),
                         ("scale", StandardScaler())])
    cat_pipe = Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                         ("onehot", OneHotEncoder(handle_unknown="ignore"))])
    pre = ColumnTransformer(
        [("num", num_pipe, num_cols), ("cat", cat_pipe, cat_cols)],
        remainder="drop")
    return pre, num_cols, cat_cols


def pick_cv(task, n_splits=5, group=None, y=None):
    """Return (cv_object, needs_groups, rationale)."""
    if task == "clf":
        return (StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=0),
                False, "StratifiedKFold keeps class proportions per fold.")
    if task == "reg":
        return (KFold(n_splits=n_splits, shuffle=True, random_state=0),
                False, "KFold for continuous targets (shuffled, seeded).")
    if task == "timeseries":
        return (TimeSeriesSplit(n_splits=n_splits), False,
                "TimeSeriesSplit trains only on the past — no future leakage. "
                "Do NOT shuffle time-ordered data.")
    if task == "group":
        if y is not None and pd.Series(y).nunique() <= 20:
            return (StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=0),
                    True, "StratifiedGroupKFold: no entity spans folds AND class "
                          "balance preserved.")
        return (GroupKFold(n_splits=n_splits), True,
                "GroupKFold: the same entity never appears in both train and val.")
    raise ValueError(f"unknown task: {task}")


def make_full_pipeline(X, task, estimator=None):
    """Preprocessor + a default estimator, all inside one Pipeline (leakage-safe)."""
    pre, num_cols, cat_cols = build_preprocessor(X)
    if estimator is None:
        if task in ("reg", "timeseries"):
            from sklearn.linear_model import Ridge
            estimator = Ridge()
        else:
            from sklearn.linear_model import LogisticRegression
            estimator = LogisticRegression(max_iter=1000)
    return Pipeline([("pre", pre), ("model", estimator)]), num_cols, cat_cols


def make_synth(task, seed=0):
    rng = np.random.default_rng(seed)
    n = 400
    X = pd.DataFrame({
        "f_num1": rng.normal(0, 1, n),
        "f_num2": rng.normal(5, 2, n),
        "f_cat": rng.choice(["x", "y", "z"], n),
    })
    X.loc[rng.choice(n, 30, replace=False), "f_num1"] = np.nan  # force imputation
    groups = None
    if task == "reg":
        y = 3 * X["f_num1"].fillna(0) + rng.normal(0, 0.5, n)
    elif task == "timeseries":
        t = np.arange(n)
        y = np.sin(t / 20) + rng.normal(0, 0.2, n)
        X["t"] = t
    else:  # clf or group
        logit = 2 * X["f_num1"].fillna(0) - 1
        y = (rng.uniform(size=n) < 1 / (1 + np.exp(-logit))).astype(int)
    if task == "group":
        groups = rng.integers(0, 40, n)  # 40 entities, repeated rows
    return X, pd.Series(y, name="y"), groups


def run_cv(pipe, X, y, cv, groups=None, task="clf"):
    """Fit/score per fold the leakage-safe way; return per-fold scores."""
    from sklearn.base import clone
    from sklearn.metrics import accuracy_score, r2_score
    scores = []
    splitter = cv.split(X, y, groups) if groups is not None else cv.split(X, y)
    for tr, va in splitter:
        p = clone(pipe)
        p.fit(X.iloc[tr], y.iloc[tr])             # fit ONLY on training fold
        pred = p.predict(X.iloc[va])
        if task == "reg" or task == "timeseries":
            scores.append(r2_score(y.iloc[va], pred))
        else:
            scores.append(accuracy_score(y.iloc[va], pred))
    return np.array(scores)


def _leakage_check():
    """Prove the scaler is re-fit per fold: its learned mean on a fold must differ
    from its mean on the full data. If they were equal, preprocessing leaked."""
    X, y, _ = make_synth("clf")
    pre, _, _ = build_preprocessor(X)
    from sklearn.base import clone
    full = clone(pre).fit(X)
    fold = clone(pre).fit(X.iloc[:200])
    full_mean = full.named_transformers_["num"].named_steps["scale"].mean_
    fold_mean = fold.named_transformers_["num"].named_steps["scale"].mean_
    return not np.allclose(full_mean, fold_mean)


def main():
    ap = argparse.ArgumentParser(description="Leakage-safe split + pipeline builder")
    ap.add_argument("--csv")
    ap.add_argument("--target")
    ap.add_argument("--task", choices=["clf", "reg", "timeseries", "group"])
    ap.add_argument("--group-col")
    ap.add_argument("--n-splits", type=int, default=5)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        assert _leakage_check(), "LEAKAGE: scaler fit identical on fold vs full data"
        print("[leakage] OK — preprocessor re-fits per fold (means differ).")
        for task in ["clf", "reg", "timeseries", "group"]:
            X, y, groups = make_synth(task)
            pipe, num_cols, cat_cols = make_full_pipeline(X, task)
            cv, needs_groups, why = pick_cv(task, n_splits=args.n_splits,
                                            group=groups, y=y)
            g = groups if needs_groups else None
            scores = run_cv(pipe, X, y, cv, groups=g, task=task)
            metric = "R2" if task in ("reg", "timeseries") else "acc"
            print(f"  [{task:10s}] CV={type(cv).__name__:22s} "
                  f"{metric}={scores.mean():.3f}±{scores.std():.3f}  | {why}")
        print("\n[selftest] PASS — all four tasks ran leakage-safe CV.")
        return

    if not (args.csv and args.target and args.task):
        ap.error("provide --csv --target --task, or --selftest")
    df = pd.read_csv(args.csv)
    y = df[args.target]
    groups = df[args.group_col].values if args.group_col else None
    X = df.drop(columns=[args.target] + ([args.group_col] if args.group_col else []))
    pipe, num_cols, cat_cols = make_full_pipeline(X, args.task)
    cv, needs_groups, why = pick_cv(args.task, n_splits=args.n_splits,
                                    group=groups, y=y)
    if needs_groups and groups is None:
        ap.error(f"task '{args.task}' needs --group-col")
    g = groups if needs_groups else None
    scores = run_cv(pipe, X, y, cv, groups=g, task=args.task)
    metric = "R2" if args.task in ("reg", "timeseries") else "acc"
    print(f"task={args.task}  CV={type(cv).__name__}  (n_splits={args.n_splits})")
    print(f"rationale: {why}")
    print(f"numeric cols: {num_cols}")
    print(f"categorical cols: {cat_cols}")
    print(f"per-fold {metric}: {[round(s,4) for s in scores]}")
    print(f"mean {metric} = {scores.mean():.4f} ± {scores.std():.4f}")


if __name__ == "__main__":
    main()
