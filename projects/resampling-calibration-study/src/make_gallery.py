"""Gallery of diverse, modern figures for the showcase README.
Five distinct chart types, all from real experiment data:
  g1 radar  - 5-metric tradeoff (Base/SMOTE/RUS/+Isotonic)
  g2 violin - ECE distribution across seeds per condition
  g3 slope  - per-dataset ECE repair (SMOTE -> +calibration)
  g4 bubble - imbalance ratio vs ECE inflation, size = dataset n
  g5 diverge- ECE delta vs baseline, RF vs gradient boosting
Outputs figures/g1_radar.png ... g5_diverge.png
"""
import sys
from pathlib import Path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"; EXP = ROOT / "experiments"
INK = "#0f172a"; MUTED = "#64748b"; GRID = "#e2e8f0"
# modern vivid palette
C = {"base": "#2563eb", "smote": "#f59e0b", "ros": "#10b981",
     "rus": "#ef4444", "cw": "#8b5cf6", "iso": "#06b6d4", "platt": "#ec4899"}
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.edgecolor": MUTED, "axes.linewidth": 0.8,
    "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlecolor": INK,
    "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "figure.dpi": 150, "savefig.dpi": 200, "savefig.bbox": "tight",
})
N = {"pima": 768, "credit_g": 1000, "phoneme": 5404, "adult": 48842, "yeast_ml8": 2417}
D = pd.read_csv(EXP / "results.csv")
print("setup ok")


def g1_radar():
    """Radar: 5-metric tradeoff, normalized so higher=better on every axis."""
    conds = [("E0_none", "Baseline", C["base"]), ("E1_smote", "SMOTE", C["smote"]),
             ("E1_rus", "Undersample", C["rus"]), ("E3_smote_iso", "SMOTE+Isotonic", C["iso"])]
    # metrics: AUC, F1, PR-AUC higher better; ECE, Brier lower better -> invert
    raw = D.groupby("condition")[["auc", "f1", "pr_auc", "ece", "brier"]].mean()
    axes_lab = ["AUC", "F1", "PR-AUC", "Calibration\n(1-ECE)", "Brier\n(inverted)"]
    norm = pd.DataFrame(index=raw.index)
    for c in ["auc", "f1", "pr_auc"]:
        norm[c] = (raw[c] - raw[c].min()) / (raw[c].max() - raw[c].min() + 1e-9)
    for c in ["ece", "brier"]:
        norm[c] = (raw[c].max() - raw[c]) / (raw[c].max() - raw[c].min() + 1e-9)
    ang = np.linspace(0, 2 * np.pi, len(axes_lab), endpoint=False).tolist()
    ang += ang[:1]
    fig, ax = plt.subplots(figsize=(5.6, 5.6), subplot_kw=dict(polar=True))
    for cond, lab, col in conds:
        v = norm.loc[cond].tolist(); v += v[:1]
        ax.plot(ang, v, "o-", lw=2, color=col, label=lab, ms=4)
        ax.fill(ang, v, color=col, alpha=0.08)
    ax.set_xticks(ang[:-1]); ax.set_xticklabels(axes_lab, fontsize=9)
    ax.set_yticks([0.25, 0.5, 0.75]); ax.set_yticklabels([], fontsize=7)
    ax.set_ylim(0, 1); ax.grid(color=GRID)
    ax.set_title("Five-metric tradeoff: calibration\nis the axis that collapses",
                 pad=28, fontsize=12.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=4,
              frameon=False, fontsize=8.5, columnspacing=1.1, handletextpad=0.4)
    fig.savefig(FIG / "g1_radar.png", facecolor="white"); plt.close(fig)
    print("[OK] g1_radar")


def g2_violin():
    """Violin + strip: ECE distribution across all (dataset,model,seed) per condition."""
    conds = ["E0_none", "E1_smote", "E1_ros", "E1_rus", "E2_cw", "E3_smote_platt", "E3_smote_iso"]
    labs = ["Base", "SMOTE", "ROS", "RUS", "CW", "+Platt", "+Iso"]
    cols = [C["base"], C["smote"], C["ros"], C["rus"], C["cw"], C["platt"], C["iso"]]
    data = [D[D.condition == c].ece.values for c in conds]
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    parts = ax.violinplot(data, showmeans=False, showextrema=False, widths=0.8)
    for i, pc in enumerate(parts["bodies"]):
        pc.set_facecolor(cols[i]); pc.set_alpha(0.30); pc.set_edgecolor(cols[i]); pc.set_linewidth(1.2)
    rng = np.random.default_rng(0)
    for i, d in enumerate(data):
        x = rng.normal(i + 1, 0.06, size=len(d))
        ax.scatter(x, d, s=10, color=cols[i], alpha=0.55, ec="white", lw=0.3, zorder=3)
        ax.scatter([i + 1], [np.mean(d)], s=80, color=cols[i], ec="white", lw=1.6, zorder=5, marker="D")
    ax.axhline(np.mean(data[0]), color=MUTED, ls="--", lw=1, zorder=1)
    ax.set_xticks(range(1, len(conds) + 1)); ax.set_xticklabels(labs)
    ax.set_ylabel("Expected Calibration Error")
    ax.set_title("ECE spreads wide under undersampling, tight after recalibration", fontsize=12)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRID, lw=0.7); ax.set_axisbelow(True)
    fig.savefig(FIG / "g2_violin.png", facecolor="white"); plt.close(fig)
    print("[OK] g2_violin")


def g3_slope():
    """Slope chart: per-dataset ECE before (SMOTE) -> after (+isotonic)."""
    order = ["pima", "credit_g", "phoneme", "adult", "yeast_ml8"]
    labs = {"pima": "pima", "credit_g": "credit-g", "phoneme": "phoneme",
            "adult": "adult", "yeast_ml8": "yeast (IR70)"}
    before = D[D.condition == "E1_smote"].groupby("dataset").ece.mean()
    after = D[D.condition == "E3_smote_iso"].groupby("dataset").ece.mean()
    fig, ax = plt.subplots(figsize=(6.0, 4.6))
    pal = [C["smote"], C["ros"], C["cw"], C["base"], C["rus"]]
    for i, ds in enumerate(order):
        b, a = before[ds], after[ds]
        ax.plot([0, 1], [b, a], "-", color=pal[i], lw=2.4, alpha=0.85, zorder=3)
        ax.scatter([0, 1], [b, a], s=70, color=pal[i], ec="white", lw=1.6, zorder=4)
        ax.text(-0.04, b, f"{labs[ds]}  {b:.3f}", ha="right", va="center", fontsize=8.5, color=INK)
        ax.text(1.04, a, f"{a:.3f}", ha="left", va="center", fontsize=8.5, color=INK)
    ax.set_xlim(-0.55, 1.45); ax.set_xticks([0, 1])
    ax.set_xticklabels(["SMOTE\n(uncalibrated)", "SMOTE\n+ Isotonic"], fontsize=10)
    ax.set_ylabel("Expected Calibration Error")
    ax.set_title("One calibration step pulls every dataset down", fontsize=12)
    for s in ("top", "right", "bottom"): ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRID, lw=0.7); ax.set_axisbelow(True)
    ax.tick_params(axis="x", length=0)
    fig.savefig(FIG / "g3_slope.png", facecolor="white"); plt.close(fig)
    print("[OK] g3_slope")


def g4_bubble():
    """Bubble: imbalance ratio (x, log) vs ECE inflation under RUS (y), size=n.
    Four low-IR datasets cluster, so labels use leader lines into open space."""
    base = D[D.condition == "E0_none"].groupby(["dataset", "ir"]).ece.mean()
    rus = D[D.condition == "E1_rus"].groupby(["dataset", "ir"]).ece.mean()
    fig, ax = plt.subplots(figsize=(7.8, 5.2))
    pal = {"pima": C["base"], "credit_g": C["smote"], "phoneme": C["ros"],
           "adult": C["cw"], "yeast_ml8": C["rus"]}
    # label anchor positions (data coords) in the empty upper region + leader lines
    lab_at = {"pima": (1.62, 0.20), "phoneme": (2.0, 0.30),
              "credit_g": (3.0, 0.38), "adult": (5.2, 0.26),
              "yeast_ml8": (24, 0.40)}
    lab_ha = {"pima": "left", "phoneme": "left", "credit_g": "left",
              "adult": "left", "yeast_ml8": "left"}
    for (ds, ir) in base.index:
        infl = rus[(ds, ir)] - base[(ds, ir)]
        sz = 120 + (N[ds] ** 0.5) * 5.5
        ax.scatter(ir, infl, s=sz, color=pal[ds], alpha=0.62, ec="white", lw=2, zorder=3)
        lx, ly = lab_at[ds]
        ax.annotate(f"{ds}  (n={N[ds]:,})", xy=(ir, infl), xytext=(lx, ly),
                    fontsize=8.8, color=INK, fontweight="bold", ha=lab_ha[ds], va="center",
                    arrowprops=dict(arrowstyle="-", color=pal[ds], lw=1.1,
                                    alpha=0.8, connectionstyle="arc3,rad=0.12"))
    ax.set_xscale("log")
    ax.set_xlim(1.55, 130)
    ax.set_ylim(-0.03, 0.46)
    ax.set_xlabel("Imbalance ratio (log scale)")
    ax.set_ylabel("ECE inflation under undersampling")
    ax.set_title("Undersampling damage scales with imbalance\n(bubble area = dataset size)",
                 fontsize=12)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.grid(color=GRID, lw=0.7); ax.set_axisbelow(True)
    fig.savefig(FIG / "g4_bubble.png", facecolor="white"); plt.close(fig)
    print("[OK] g4_bubble")


def g5_diverge():
    """Diverging bars: ECE delta vs baseline, gradient boosting vs random forest."""
    conds = ["E1_smote", "E1_ros", "E1_rus", "E2_cw", "E3_smote_platt", "E3_smote_iso"]
    labs = ["SMOTE", "ROS", "RUS", "Class-weight", "SMOTE+Platt", "SMOTE+Iso"]
    out = {}
    for mdl in ["histgb", "rf"]:
        sub = D[D.model == mdl]
        base = sub[sub.condition == "E0_none"].ece.mean()
        out[mdl] = [sub[sub.condition == c].ece.mean() - base for c in conds]
    y = np.arange(len(conds)); h = 0.38
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.barh(y + h/2, out["histgb"], height=h, color=C["smote"], label="Gradient boosting", zorder=3)
    ax.barh(y - h/2, out["rf"], height=h, color=C["base"], label="Random forest", zorder=3)
    ax.axvline(0, color=INK, lw=1)
    ax.set_yticks(y); ax.set_yticklabels(labs)
    ax.set_xlabel("ECE change vs. baseline  (← better   worse →)")
    ax.set_title("Resampling harms both ensembles; recalibration helps both", fontsize=11.5)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.grid(axis="x", color=GRID, lw=0.7); ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="lower right", fontsize=9)
    ax.invert_yaxis()
    fig.savefig(FIG / "g5_diverge.png", facecolor="white"); plt.close(fig)
    print("[OK] g5_diverge")


def g6_heatmap():
    """Heatmap: per-condition x per-dataset ECE."""
    conds = ["E0_none", "E1_smote", "E1_ros", "E1_rus", "E2_cw", "E3_smote_platt", "E3_smote_iso"]
    clabs = ["Base", "SMOTE", "ROS", "RUS", "CW", "+Platt", "+Iso"]
    order = ["pima", "credit_g", "phoneme", "adult", "yeast_ml8"]
    rlabs = ["pima", "credit-g", "phoneme", "adult", "yeast (IR70)"]
    M = (D.groupby(["dataset", "condition"]).ece.mean().unstack()[conds].reindex(order).values)
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    im = ax.imshow(M, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=0.4)
    ax.set_xticks(range(len(conds))); ax.set_xticklabels(clabs, fontsize=9, rotation=25, ha="right")
    ax.set_yticks(range(len(order))); ax.set_yticklabels(rlabs, fontsize=9)
    ax.grid(False)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8.5,
                    color="white" if v > 0.22 else INK, fontweight="bold")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03); cb.set_label("ECE", fontsize=9)
    ax.set_title("Every condition × every dataset, at a glance", fontsize=12)
    fig.savefig(FIG / "g6_heatmap.png", facecolor="white"); plt.close(fig)
    print("[OK] g6_heatmap")


def g7_ridge():
    """Ridgeline (joyplot): ECE density per condition, stacked."""
    from scipy.stats import gaussian_kde
    conds = ["E3_smote_iso", "E3_smote_platt", "E0_none", "E2_cw", "E1_smote", "E1_ros", "E1_rus"]
    labs = ["+Iso", "+Platt", "Base", "CW", "SMOTE", "ROS", "RUS"]
    cols = [C["iso"], C["platt"], C["base"], C["cw"], C["smote"], C["ros"], C["rus"]]
    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    xs = np.linspace(0, 0.55, 300); gap = 0.85
    for i, c in enumerate(conds):
        d = D[D.condition == c].ece.values
        kde = gaussian_kde(d, bw_method=0.35); dens = kde(xs)
        dens = dens / dens.max() * 0.95
        y0 = i * gap
        ax.fill_between(xs, y0, y0 + dens, color=cols[i], alpha=0.7, lw=1.2, ec="white", zorder=len(conds) - i)
        ax.plot(xs, y0 + dens, color="white", lw=1, zorder=len(conds) - i)
        ax.text(-0.01, y0 + 0.1, labs[i], ha="right", va="bottom", fontsize=9.5, fontweight="bold", color=cols[i])
    ax.set_yticks([]); ax.set_xlabel("Expected Calibration Error")
    ax.set_xlim(-0.06, 0.56)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.set_title("Distribution of ECE shifts right as resampling gets aggressive", fontsize=11.5)
    fig.savefig(FIG / "g7_ridge.png", facecolor="white"); plt.close(fig)
    print("[OK] g7_ridge")


def g8_ecdf():
    """ECDF step plot: cumulative distribution of per-run ECE, key conditions.
    Distinct chart family; shows dramatic horizontal separation, all true."""
    conds = [("E3_smote_iso", "SMOTE+Iso", C["iso"]), ("E0_none", "Baseline", C["base"]),
             ("E1_smote", "SMOTE", C["smote"]), ("E1_rus", "Undersample", C["rus"])]
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for cond, lab, col in conds:
        d = np.sort(D[D.condition == cond].ece.values)
        y = np.arange(1, len(d) + 1) / len(d)
        ax.step(np.concatenate([[0], d]), np.concatenate([[0], y]), where="post",
                lw=2.6, color=col, label=lab, zorder=3)
        med = np.median(d)
        ax.scatter([med], [0.5], s=70, color=col, ec="white", lw=1.5, zorder=4)
    ax.set_xlabel("Expected Calibration Error")
    ax.set_ylabel("Cumulative fraction of runs")
    ax.set_xlim(0, 0.5); ax.set_ylim(0, 1.02)
    ax.set_title("Cumulative ECE: undersampling curve sits far to the right",
                 fontsize=11.5)
    ax.legend(frameon=False, loc="lower right", fontsize=9)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.grid(color=GRID, lw=0.7); ax.set_axisbelow(True)
    fig.savefig(FIG / "g8_ecdf.png", facecolor="white"); plt.close(fig)
    print("[OK] g8_ecdf")


def g9_lollipop():
    """Lollipop: datasets ranked by ECE inflation under undersampling."""
    base = D[D.condition == "E0_none"].groupby("dataset").ece.mean()
    rus = D[D.condition == "E1_rus"].groupby("dataset").ece.mean()
    infl = (rus - base).sort_values()
    labs = {"pima": "pima", "credit_g": "credit-g", "phoneme": "phoneme",
            "adult": "adult", "yeast_ml8": "yeast (IR70)"}
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    y = np.arange(len(infl))
    cmap = plt.cm.YlOrRd
    cols = [cmap(0.25 + 0.6 * i / (len(infl) - 1)) for i in range(len(infl))]
    for i, (ds, v) in enumerate(infl.items()):
        ax.plot([0, v], [i, i], color=cols[i], lw=2.6, zorder=2)
        ax.scatter(v, i, s=260, color=cols[i], ec="white", lw=2, zorder=3)
        ax.text(v, i, f"+{v:.2f}", ha="center", va="center", fontsize=8, fontweight="bold", color="white", zorder=4)
    ax.set_yticks(y); ax.set_yticklabels([labs[d] for d in infl.index], fontsize=10)
    ax.set_xlabel("ECE inflation under undersampling (vs. baseline)")
    ax.set_xlim(0, infl.max() * 1.18)
    ax.set_title("Which datasets suffer most? Ranked by calibration damage", fontsize=11.5)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.grid(axis="x", color=GRID, lw=0.7); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
    fig.savefig(FIG / "g9_lollipop.png", facecolor="white"); plt.close(fig)
    print("[OK] g9_lollipop")


if __name__ == "__main__":
    g1_radar(); g2_violin(); g3_slope(); g4_bubble(); g5_diverge()
    g6_heatmap(); g7_ridge(); g8_ecdf(); g9_lollipop()
    print("[DONE] gallery")
