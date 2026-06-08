"""Showcase figure for the GitHub README: a single polished multi-panel
summary of the calibration-under-resampling study. Combines 4 chart types
(grouped bar, line+CI, log-scatter, reliability curves) in one figure.
All numbers come from the real experiment CSVs. Outputs figures/showcase.png
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
from matplotlib.gridspec import GridSpec

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"; EXP = ROOT / "experiments"

# ---- aesthetic theme ----
INK = "#1a1a2e"; MUTED = "#6b7280"; GRID = "#e5e7eb"
C_BASE = "#3b82f6"; C_SMOTE = "#f59e0b"; C_RUS = "#8b5cf6"; C_FIX = "#10b981"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.edgecolor": MUTED, "axes.linewidth": 0.8,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlecolor": INK,
    "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "figure.dpi": 150, "savefig.dpi": 200,
})
print("theme set")


def style(ax):
    ax.set_facecolor("white")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, color=GRID, lw=0.7, alpha=0.9)
    ax.set_axisbelow(True)


def _heatmap(ax, main_df):
    """Per-condition x per-dataset ECE heatmap (the Table IV data)."""
    conds = ["E0_none", "E1_smote", "E1_ros", "E1_rus", "E2_cw",
             "E3_smote_platt", "E3_smote_iso"]
    clabs = ["Base", "SMOTE", "ROS", "RUS", "CW", "+Platt", "+Iso"]
    order = ["pima", "credit_g", "phoneme", "adult", "yeast_ml8"]
    rlabs = ["pima", "credit-g", "phoneme", "adult", "yeast (IR70)"]
    M = (main_df.groupby(["dataset", "condition"]).ece.mean()
         .unstack()[conds].reindex(order).values)
    im = ax.imshow(M, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=0.4)
    ax.set_xticks(range(len(conds))); ax.set_xticklabels(clabs, fontsize=8.5, rotation=30, ha="right")
    ax.set_yticks(range(len(order))); ax.set_yticklabels(rlabs, fontsize=8.5)
    ax.grid(False)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7.5,
                    color="white" if v > 0.22 else INK, fontweight="bold")
    cb = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cb.set_label("ECE", fontsize=9); cb.ax.tick_params(labelsize=8)


def main():
    main_df = pd.read_csv(EXP / "results.csv")
    rho_df = pd.read_csv(EXP / "rho_sweep.csv")

    fig = plt.figure(figsize=(13, 8.2))
    gs = GridSpec(2, 2, figure=fig, hspace=0.42, wspace=0.24,
                  left=0.07, right=0.97, top=0.88, bottom=0.09)

    # ---- Panel A: grouped bar, ECE by condition ----
    axA = fig.add_subplot(gs[0, 0]); style(axA)
    conds = ["E0_none", "E1_smote", "E1_ros", "E1_rus", "E2_cw",
             "E3_smote_platt", "E3_smote_iso"]
    labs = ["Base", "SMOTE", "ROS", "RUS", "CW", "+Platt", "+Iso"]
    ece = main_df.groupby("condition").ece.mean().reindex(conds).values
    cols = [C_BASE, C_SMOTE, C_SMOTE, C_RUS, C_BASE, C_FIX, C_FIX]
    axA.bar(range(len(conds)), ece, color=cols, width=0.68, zorder=3)
    axA.axhline(ece[0], color=MUTED, ls="--", lw=1, zorder=2)
    axA.set_xticks(range(len(conds))); axA.set_xticklabels(labs, fontsize=9)
    axA.set_ylabel("Expected Calibration Error")
    axA.set_title("A  Resampling inflates ECE; recalibration repairs it", loc="left")

    # ---- Panel B: line + spread, ECE vs rho ----
    axB = fig.add_subplot(gs[0, 1]); style(axB)
    for name, g in rho_df.groupby("dataset"):
        gg = g.groupby("rho").ece.mean()
        axB.plot(gg.index, gg.values, "-", lw=1.2, alpha=0.5, color=MUTED)
    agg = rho_df.groupby("rho").ece.mean()
    axB.plot(agg.index, agg.values, "o-", lw=2.6, color=C_SMOTE,
             ms=7, mec="white", mew=1.5, zorder=5, label="mean")
    axB.set_xlabel(r"Oversampling ratio $\rho$"); axB.set_ylabel("ECE")
    axB.legend(frameon=False, loc="upper left")
    axB.set_title("B  Calibration cost grows with oversampling", loc="left")

    # ---- Panel C: log-scatter, ECE inflation vs imbalance ratio ----
    axC = fig.add_subplot(gs[1, 0]); style(axC)
    base = main_df[main_df.condition == "E0_none"].groupby(["dataset", "ir"]).ece.mean()
    rus = main_df[main_df.condition == "E1_rus"].groupby(["dataset", "ir"]).ece.mean()
    smo = main_df[main_df.condition == "E1_smote"].groupby(["dataset", "ir"]).ece.mean()
    irs = [k[1] for k in base.index]
    axC.scatter(irs, (rus - base).values, s=130, color=C_RUS, ec="white",
                lw=1.5, zorder=4, label="Undersampling")
    axC.scatter(irs, (smo - base).values, s=130, color=C_SMOTE, ec="white",
                lw=1.5, zorder=4, label="SMOTE")
    axC.set_xscale("log")
    axC.set_xlabel("Imbalance ratio (log scale)")
    axC.set_ylabel("ECE inflation over baseline")
    axC.legend(frameon=False)
    axC.set_title("C  Undersampling damage explodes at high imbalance", loc="left")

    # ---- Panel D: heatmap, per-condition x per-dataset ECE ----
    axD = fig.add_subplot(gs[1, 1]); style(axD)
    _heatmap(axD, main_df)
    axD.set_title("D  ECE across every condition and dataset", loc="left")

    fig.suptitle("Resampling silently degrades probability calibration in tree ensembles",
                 fontsize=15, fontweight="bold", color=INK, x=0.07, ha="left", y=0.96)
    fig.text(0.07, 0.915, "Five OpenML datasets · two ensembles · seven conditions · "
             "ten seeds · paired statistics — every number from real runs",
             fontsize=10, color=MUTED, ha="left")
    fig.savefig(FIG / "showcase.png", facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("[OK] showcase.png")


main()

