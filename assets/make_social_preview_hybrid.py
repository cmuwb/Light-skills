#!/usr/bin/env python3
"""生成 GitHub 社交预览图 assets/social-preview.png(1280x640) —— AI 背景 + 程序化文字。

混合方案:背景用生图模型产的抽象 hero 图(assets/social_bg.png,棱镜光谱),
文字/数字卡/主线链用 matplotlib 程序化叠加(保证中文与数字清晰锐利、可改)。
背景缺失时自动退回纯渐变(与 make_social_preview.py 同口径),不依赖网络。

重生背景:python skills/light-slides/scripts/imagegen.py --backend openai --size 16:9 \
          --type background -o assets/social_bg.png --prompt "<见 README/manifest>"
重生本图:python assets/make_social_preview_hybrid.py
"""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.font_manager as fm

HERE = Path(__file__).resolve().parent
CJK = next((n for n in ["Microsoft YaHei", "SimHei", "SimSun",
                        "Noto Sans CJK SC", "Source Han Sans SC"]
            if n in {f.name for f in fm.fontManager.ttflist}), "DejaVu Sans")
plt.rcParams["font.sans-serif"] = [CJK, "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

WHITE = "#FFFFFF"
INK = "#0B1020"
GREEN = "#3DDC84"
SKY = "#7FB0FF"
GLASS = "#162038"


def _shadow(lw=3, fg="#0A0E1C", alpha=0.55):
    return [pe.withStroke(linewidth=lw, foreground=fg, alpha=alpha)]


def main(out=str(HERE / "social-preview.png"), bg=str(HERE / "social_bg.png")):
    W, H = 1280, 640
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

    bg_path = Path(bg)
    if bg_path.exists():
        img = mpimg.imread(bg)
        ax.imshow(img, extent=[0, W, 0, H], aspect="auto", zorder=0)
        # 左下→右压暗渐变蒙版,保证文字区对比度
        grad = [[(0, 0, 0, a)] for a in [0.0]]
        import numpy as np
        gx = np.linspace(0, 1, 256)
        mask = np.zeros((2, 256, 4))
        mask[..., :3] = 0.02
        # 底部更暗(文字在下半区)
        mask[0, :, 3] = 0.62          # 底
        mask[1, :, 3] = 0.10          # 顶
        ax.imshow(mask, extent=[0, W, 0, H], aspect="auto", zorder=1)
        # 左侧竖向暗带(给 Light 标题)
        lmask = np.zeros((2, 256, 4)); lmask[..., :3] = 0.02
        lcol = np.clip(0.6 - gx * 1.4, 0, 0.6)
        lmask[0, :, 3] = lcol; lmask[1, :, 3] = lcol
        ax.imshow(lmask, extent=[0, W, 0, H], aspect="auto", zorder=1,
                  origin="upper")
        dark = False
    else:  # 退回纯渐变
        ax.add_patch(plt.Rectangle((0, 0), W, H, color="#0B1020", zorder=0))
        dark = True
    ax.add_patch(plt.Rectangle((0, 0), W, 10, color=GREEN, zorder=5))
    ax.add_patch(plt.Rectangle((0, H - 10), W, 10, color=SKY, zorder=5))

    # 品牌名 + 标语(白字带暗描边,压在背景上清晰)
    ax.text(78, 502, "Light", fontsize=92, fontweight="bold", color=WHITE,
            ha="left", va="center", zorder=10, path_effects=_shadow(5))
    ax.text(84, 424, "全流程科研技能包", fontsize=37, fontweight="bold",
            color=WHITE, ha="left", va="center", zorder=10, path_effects=_shadow(4))
    ax.text(84, 378, "让 AI 陪你把一篇论文从想法做到投稿", fontsize=22,
            color="#D7E0F5", ha="left", va="center", zorder=10, path_effects=_shadow(3))

    # 数字卡片(半透明玻璃卡)
    stats = [("28", "技能"), ("9", "知识库"), ("51", "脚本"),
             ("40", "模板"), ("318", "知识卡")]
    cw, gap, x0, y0 = 198, 22, 80, 250
    for i, (num, lab) in enumerate(stats):
        x = x0 + i * (cw + gap)
        ax.add_patch(FancyBboxPatch((x, y0 - 56), cw, 112,
                     boxstyle="round,pad=2,rounding_size=14", linewidth=1.6,
                     edgecolor="#8FB4FF", facecolor=(0.08, 0.13, 0.26, 0.62),
                     zorder=8))
        ax.text(x + cw / 2, y0 + 16, num, fontsize=42, fontweight="bold",
                color=WHITE, ha="center", va="center", zorder=10,
                path_effects=_shadow(3))
        ax.text(x + cw / 2, y0 - 30, lab, fontsize=18, color="#BFD0F0",
                ha="center", va="center", zorder=10)

    # 主线链
    chain = ["文献", "数据", "创新", "实验", "分析", "写作", "图表", "投稿", "成果"]
    bx, by, bw2, bgap = 80, 118, 110, 18
    for i, c in enumerate(chain):
        x = bx + i * (bw2 + bgap)
        last = i == len(chain) - 1
        ax.add_patch(FancyBboxPatch((x, by - 26), bw2, 52,
                     boxstyle="round,pad=1,rounding_size=10", linewidth=1.6,
                     edgecolor=GREEN if last else "#8FB4FF",
                     facecolor=(0.10, 0.30, 0.18, 0.66) if last else (0.08, 0.13, 0.26, 0.62),
                     zorder=8))
        ax.text(x + bw2 / 2, by, c, fontsize=19, fontweight="bold", color=WHITE,
                ha="center", va="center", zorder=10, path_effects=_shadow(2.5))
        if not last:
            xa = x + bw2
            ax.add_patch(FancyArrowPatch((xa, by), (xa + bgap, by),
                         arrowstyle="-|>", mutation_scale=12, linewidth=1.8,
                         color="#8FB4FF", zorder=9))

    # 右上卖点
    ax.text(W - 70, 500, "Claude Code · Codex", fontsize=20, color=WHITE,
            ha="right", va="center", fontweight="bold", zorder=10,
            path_effects=_shadow(3))
    ax.text(W - 70, 466, "28 技能沿科研主线闭环 · 全程不编造", fontsize=16,
            color="#CBD8F2", ha="right", va="center", zorder=10,
            path_effects=_shadow(2.5))

    fig.savefig(out, format="png", dpi=100, facecolor="#0B1020")
    plt.close(fig)
    print(f"wrote {out} ({W}x{H}, bg={'AI' if bg_path.exists() else 'gradient'}, font={CJK})")


if __name__ == "__main__":
    main()
