#!/usr/bin/env python3
"""figure_export.py — 投稿级图像导出工具 (Light / light-figure-drawing)

提供:
  - save_publication_figure(fig, basename, formats, dpi, ...)  多格式 + DPI 导出
  - save_for_journal(fig, basename, journal, column, ...)      按刊规格设尺寸并导出
  - check_figure_size(fig, max_width_mm, ...)                  校验栏宽(mm)是否合规
  - JOURNAL_SPECS                                              逐刊硬规格表(mm/DPI/字号)

设计:无外部数据;matplotlib Agg 后端;__main__ 产 demo 图并自检。
依据规格见 SKILL.md 逐刊表;付费墙未实测项以 verified=False 标注。
"""
from __future__ import annotations
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

MM_PER_INCH = 25.4

# 逐刊规格: width_mm 为 (单栏, 双栏/整版) 可选键; min_dpi 按线条图; min_font_pt 最终字号下限
JOURNAL_SPECS = {
    "nature": {
        "single_mm": 89.0, "double_mm": 183.0,
        "min_dpi_line": 600, "min_dpi_halftone": 300, "min_dpi_combo": 600,
        "min_font_pt": 5.0, "preferred_formats": ("pdf", "tiff", "eps"),
        "font_family": "sans-serif", "verified": True,
        "note": "实测 nature.com/nature/for-authors/final-submission (HTTP200): "
                "89mm单栏/183mm双栏; 面板标 8pt粗体 a,b,c; 正文最大7pt 最小5pt; "
                "Helvetica/Arial; 照片300-600dpi; 文字勿转曲",
    },
    "science": {
        "single_mm": 55.0, "double_mm": 121.0, "full_mm": 183.0,
        "min_dpi_line": 600, "min_dpi_halftone": 300, "min_dpi_combo": 500,
        "min_font_pt": 5.0, "preferred_formats": ("eps", "pdf", "ai", "tiff"),
        "font_family": "sans-serif", "verified": False,
        "note": "Science/AAAS 作图规格;单栏约 55mm,整版 183mm;细则未逐项实测",
    },
    "cell": {
        "single_mm": 85.0, "double_mm": 174.0,
        "min_dpi_line": 1000, "min_dpi_halftone": 300, "min_dpi_combo": 500,
        "min_font_pt": 5.0, "preferred_formats": ("pdf", "ai", "eps", "tiff"),
        "font_family": "sans-serif", "verified": False,
        "note": "Cell Press 数字艺术规格;线条图常要求 1000dpi;未逐项实测",
    },
    "plos": {
        "single_mm": 83.0, "onehalf_mm": 140.0, "double_mm": 190.0,
        "min_dpi_line": 600, "min_dpi_halftone": 300, "min_dpi_combo": 600,
        "min_font_pt": 8.0, "preferred_formats": ("tiff", "eps"),
        "font_family": "sans-serif", "verified": True,
        "note": "实测 journals.plos.org/plosone/s/figures (HTTP200): "
                "仅收 TIFF/EPS; 宽 789-2250px@300dpi (6.68-19.05cm); "
                "高<=2625px; 分辨率300-600dpi; 文字 Arial/Times/Symbol 8-12pt; <10MB",
    },
    "ieee": {
        "single_mm": 88.9, "double_mm": 181.0,
        "min_dpi_line": 600, "min_dpi_halftone": 300, "min_dpi_combo": 600,
        "min_font_pt": 8.0, "preferred_formats": ("pdf", "eps", "tiff"),
        "font_family": "sans-serif", "verified": False,
        "note": "IEEE 双栏模板栏宽约 3.5in/7.16in;Graphics Checker 建议 >=300dpi",
    },
    "elsevier": {
        "single_mm": 90.0, "double_mm": 190.0, "onehalf_mm": 140.0,
        "min_dpi_line": 1000, "min_dpi_halftone": 300, "min_dpi_combo": 500,
        "min_font_pt": 7.0, "preferred_formats": ("pdf", "eps", "tiff"),
        "font_family": "sans-serif", "verified": False,
        "note": "Elsevier 艺术指南:线条 1000dpi, 灰/彩 300dpi, 组合 500dpi;未逐项实测",
    },
}

def mm_to_inch(mm: float) -> float:
    return mm / MM_PER_INCH


def inch_to_mm(inch: float) -> float:
    return inch * MM_PER_INCH


def save_publication_figure(fig, basename, formats=("pdf", "png", "svg"),
                            dpi=600, transparent=False, pad_inches=0.02,
                            close=False):
    """多格式 + DPI 导出。返回写出的文件路径列表。

    - basename 可含目录, 不含扩展名。
    - 矢量格式(pdf/svg/eps)忽略 dpi(对线条无意义), 但保留以便位图。
    - 自动确保 pdf/ps fonttype=42、svg 文字不转曲, 文字可二次编辑。
    """
    os.makedirs(os.path.dirname(os.path.abspath(basename)), exist_ok=True)
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["ps.fonttype"] = 42
    plt.rcParams["svg.fonttype"] = "none"
    written = []
    for fmt in formats:
        path = f"{basename}.{fmt}"
        fig.savefig(path, format=fmt, dpi=dpi, transparent=transparent,
                    bbox_inches="tight", pad_inches=pad_inches)
        written.append(path)
    if close:
        plt.close(fig)
    return written


def save_for_journal(fig, basename, journal="nature", column="single",
                     height_mm=None, formats=None, dpi=None, **kwargs):
    """按目标刊规格设置物理尺寸并导出。

    - journal: JOURNAL_SPECS 的键。
    - column: 'single' / 'double' / 'full' / 'onehalf' (依该刊有的键)。
    - height_mm: 不给则保持当前宽高比缩放到目标宽度。
    返回 (written_paths, info_dict)。
    """
    j = journal.lower()
    if j not in JOURNAL_SPECS:
        raise ValueError(f"未知期刊 '{journal}', 可选: {list(JOURNAL_SPECS)}")
    spec = JOURNAL_SPECS[j]
    key = f"{column}_mm"
    if key not in spec:
        avail = [k.replace("_mm", "") for k in spec if k.endswith("_mm")]
        raise ValueError(f"{journal} 无 '{column}' 栏宽, 可选: {avail}")
    width_mm = spec[key]
    width_in = mm_to_inch(width_mm)
    cur_w, cur_h = fig.get_size_inches()
    if height_mm is None:
        height_in = width_in * (cur_h / cur_w)
    else:
        height_in = mm_to_inch(height_mm)
    fig.set_size_inches(width_in, height_in)
    if formats is None:
        formats = spec["preferred_formats"][:2]
    if dpi is None:
        dpi = spec["min_dpi_line"]
    written = save_publication_figure(fig, basename, formats=formats, dpi=dpi, **kwargs)
    info = {"journal": j, "column": column, "width_mm": width_mm,
            "height_mm": round(inch_to_mm(height_in), 1), "dpi": dpi,
            "formats": list(formats), "min_font_pt": spec["min_font_pt"],
            "verified": spec["verified"], "note": spec["note"]}
    return written, info


def check_figure_size(fig, max_width_mm=None, journal=None, column="single",
                      tol_mm=0.5, verbose=True):
    """校验图形物理宽度(mm)是否符合栏宽。返回 dict 报告。

    给 journal 则用该刊该栏宽作为上限; 否则用 max_width_mm。
    同时检查可见文字字号是否 >= 该刊下限(若给 journal)。
    """
    w_in, h_in = fig.get_size_inches()
    w_mm, h_mm = inch_to_mm(w_in), inch_to_mm(h_in)
    report = {"width_mm": round(w_mm, 2), "height_mm": round(h_mm, 2),
              "ok": True, "problems": []}
    limit = max_width_mm
    min_font = None
    if journal is not None:
        spec = JOURNAL_SPECS[journal.lower()]
        limit = spec.get(f"{column}_mm", limit)
        min_font = spec["min_font_pt"]
        report["journal"] = journal.lower()
        report["column"] = column
    if limit is not None:
        report["max_width_mm"] = limit
        if w_mm > limit + tol_mm:
            report["ok"] = False
            report["problems"].append(
                f"宽度 {w_mm:.1f}mm 超过上限 {limit}mm")
    if min_font is not None:
        tiny = _collect_small_fonts(fig, min_font)
        report["min_font_pt"] = min_font
        if tiny:
            report["ok"] = False
            report["problems"].append(
                f"{len(tiny)} 处文字字号 < {min_font}pt: 最小 {min(tiny):.1f}pt")
    if verbose:
        status = "OK" if report["ok"] else "FAIL"
        print(f"[check_figure_size] {status}  {report}")
    return report


def _collect_small_fonts(fig, min_font_pt):
    """收集小于下限的可见文字字号(pt)。"""
    small = []
    for txt in fig.findobj(plt.Text):
        try:
            s = txt.get_text()
        except Exception:
            continue
        if not s or not s.strip():
            continue
        if not txt.get_visible():
            continue
        fs = txt.get_fontsize()
        if fs < min_font_pt - 1e-6:
            small.append(fs)
    return small


def _demo_and_selfcheck():
    """产 demo 图, 跑三个函数, 断言关键不变量。"""
    import numpy as np
    here = os.path.dirname(os.path.abspath(__file__))
    style = os.path.join(here, "..", "assets", "publication.mplstyle")
    if os.path.exists(style):
        plt.style.use(style)
    rng = np.random.default_rng(0)
    x = np.linspace(0, 2 * np.pi, 100)
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    ax.plot(x, np.sin(x), label="sin")
    ax.plot(x, np.cos(x), label="cos", linestyle="--")
    ax.fill_between(x, np.sin(x) - 0.1, np.sin(x) + 0.1, alpha=0.2)
    ax.set_xlabel("phase (rad)")
    ax.set_ylabel("amplitude (a.u.)")
    ax.set_title("a", loc="left")
    ax.legend()

    outdir = os.path.join(here, "..", "examples", "_export_demo")
    base = os.path.join(outdir, "demo_export")
    written = save_publication_figure(fig, base, formats=("pdf", "png", "svg"))
    assert all(os.path.exists(p) and os.path.getsize(p) > 0 for p in written), written
    print("[demo] save_publication_figure ->", [os.path.basename(p) for p in written])

    # 按 Nature 单栏导出并校验
    fig2, ax2 = plt.subplots(figsize=(5.0, 4.0))
    ax2.bar(["A", "B", "C"], [3, 5, 2])
    ax2.set_ylabel("count")
    w2, info = save_for_journal(fig2, os.path.join(outdir, "demo_nature"),
                                journal="nature", column="single")
    assert abs(info["width_mm"] - 89.0) < 0.6, info
    print("[demo] save_for_journal nature/single ->", info["width_mm"], "mm",
          [os.path.basename(p) for p in w2])

    rep_ok = check_figure_size(fig2, journal="nature", column="single", verbose=False)
    assert rep_ok["ok"], rep_ok
    # 故意造一个超宽图, 应 FAIL
    fig3, ax3 = plt.subplots(figsize=(10, 4))
    ax3.plot([0, 1], [0, 1])
    rep_bad = check_figure_size(fig3, journal="nature", column="single", verbose=False)
    assert not rep_bad["ok"], rep_bad
    print("[demo] check_figure_size: 合规图 OK, 超宽图正确判 FAIL")

    plt.close("all")
    print("[selfcheck] ALL PASS, 输出目录:", os.path.abspath(outdir))


if __name__ == "__main__":
    _demo_and_selfcheck()
