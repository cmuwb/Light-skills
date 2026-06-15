#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compile_driver.py — LaTeX 真实编译驱动器（引擎自动探测 + 多轮收敛 + 报错翻译）。

为什么有这个脚本（补 m12『编译能力基本是口头描述而非工具』）
----------------------------------------------------------
SKILL 反复讲『latexmk 自动收敛多轮编译/缺包 tlmgr install』给人有编译能力的印象，但此前
**全技能没有任何编译驱动脚本**——真正的『编译』靠模型手敲 latexmk。竞品 latex-document-skill
的 compile_latex.sh 才是真编译器（引擎自动探测 + 多轮 + auto-fix + 报错翻译成大白话）。本脚本
补上这一层：从 .tex 内容自动选引擎、用 latexmk/tectonic 真编译、把 cryptic 报错翻译成可执行提示。

能力
----
  · detect_engine：扫 .tex 的 fontspec/xeCJK/ctex→xelatex、luacode→lualatex，否则 pdflatex
  · find_tool：优先 latexmk（多轮收敛 + bibtex/biber 自动），回退 tectonic（自带宏包、更自包含）
  · compile：真调编译器（latexmk -pdfxe/-pdf 或 tectonic），多轮由 latexmk 自动收敛
  · translate_log：把 "Undefined control sequence""Missing $ inserted" 等翻成大白话 + 修复方向
  · auto_fix_hints：扫日志给可执行修复建议（float [h]→[htbp]、缺 microtype、缺宏包 tlmgr install）

⚠ 诚实降级：**无 latexmk/tectonic 时不假装编译成功**——返回 tool_missing 并明确标注，让用户装工具。
  本脚本不替你改 .tex（auto_fix 只给建议不自动改，避免误伤）；真实编译须本地有 TeX 发行版。

用法：
  python compile_driver.py --compile paper.tex [--engine auto|xelatex|pdflatex] [--outdir build]
  python compile_driver.py --detect paper.tex      # 只报引擎选择
  python compile_driver.py --selftest              # 离线逻辑自测（不跑真编译）
"""
from __future__ import annotations
import argparse
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # 复用 precheck_log 的日志扫描
try:
    import precheck_log  # noqa: E402
    _HAS_PRECHECK = True
except Exception:
    _HAS_PRECHECK = False

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# 需要 unicode-engine 的宏包/类
_XE_TRIGGER = re.compile(r"\\usepackage(\[[^\]]*\])?\{[^}]*(fontspec|xeCJK|ctex|unicode-math|polyglossia)[^}]*\}"
                         r"|\\documentclass(\[[^\]]*\])?\{ctex", re.I)
_LUA_TRIGGER = re.compile(r"\\usepackage(\[[^\]]*\])?\{[^}]*(luacode|luatextra|lua-ul)[^}]*\}"
                          r"|\\directlua", re.I)

# cryptic 报错 → 大白话 + 修复方向
_LOG_TRANSLATIONS = [
    (re.compile(r"Undefined control sequence", re.I),
     "用了未定义的命令（命令拼写错，或缺加载对应宏包）——核对命令拼写 / \\usepackage 对应包。"),
    (re.compile(r"Missing \$ inserted", re.I),
     "数学符号（_ ^ \\alpha 等）写在了正文里——把它放进 $...$ 数学模式。"),
    (re.compile(r"Runaway argument|Paragraph ended before", re.I),
     "括号/环境没闭合（漏了 } 或 \\end{...}）——检查最近的 { 与 \\begin 是否配对。"),
    (re.compile(r"File [`']?([^'\s]+)'? not found", re.I),
     "缺文件/宏包——若是 .sty 用 tlmgr install <包名>（MiKTeX 会提示自动装），若是图/bib 核对路径。"),
    (re.compile(r"Citation [`']([^']+)'.*undefined", re.I),
     "引用键未定义——\\cite 的 key 不在 .bib 或没跑 bibtex/biber（latexmk 会自动跑，单引擎要手动多轮）。"),
    (re.compile(r"Reference [`']([^']+)'.*undefined", re.I),
     "交叉引用未定义——\\ref 的 label 不存在或需再编译一轮收敛（latexmk 自动处理）。"),
    (re.compile(r"Overfull \\hbox \(([\d.]+)pt", re.I),
     "行溢出版心（文字超出右边距）——改写句子 / 加连字符 / 调 \\sloppy，超 ~5pt 才需处理。"),
    (re.compile(r"Font .*not (?:loadable|found)|Font shape.*undefined", re.I),
     "字体缺失/回退——装该字体或换发行版自带字体；中文字体回退会变默认字形。"),
]

# auto-fix 建议（不自动改，只给可执行方向）
_AUTOFIX_HINTS = [
    (re.compile(r"Overfull \\hbox", re.I),
     "若多处 overfull：加 \\usepackage{microtype}（字符级微调常消除大部分溢出）。"),
    (re.compile(r"float specifier .*changed|Float too large|h' float specifier", re.I),
     "图表用了 [h]：改 [htbp] 给 LaTeX 更多放置自由度，避免浮动体卡死。"),
    (re.compile(r"Underfull \\hbox", re.I),
     "underfull 多为良性（行内空白拉伸）——一般可忽略，除非视觉明显。"),
]


def detect_engine(tex_text: str) -> dict:
    """从 .tex 内容选引擎。返回 {engine, reason}。"""
    if _XE_TRIGGER.search(tex_text):
        return {"engine": "xelatex", "reason": "检测到 fontspec/xeCJK/ctex/polyglossia → 需 Unicode 引擎"}
    if _LUA_TRIGGER.search(tex_text):
        return {"engine": "lualatex", "reason": "检测到 luacode/\\directlua → 用 lualatex"}
    return {"engine": "pdflatex", "reason": "无 Unicode/lua 触发器 → 默认 pdflatex"}


def find_tool() -> tuple:
    """优先 latexmk，回退 tectonic。返回 (tool, path) 或 (None, None)。"""
    for tool in ("latexmk", "tectonic"):
        p = shutil.which(tool)
        if p:
            return tool, p
    return None, None


def build_command(tool: str, engine: str, texfile: str, outdir: str) -> list:
    """构造编译命令。latexmk 走引擎专属 flag + 多轮收敛；tectonic 自带多轮。"""
    if tool == "latexmk":
        eng_flag = {"xelatex": "-pdfxe", "lualatex": "-pdflua", "pdflatex": "-pdf"}[engine]
        return ["latexmk", eng_flag, "-interaction=nonstopmode", "-halt-on-error",
                f"-output-directory={outdir}", texfile]
    # tectonic：引擎固定（自身处理多轮 + bib），不需 engine flag
    return ["tectonic", "--keep-logs", "--outdir", outdir, texfile]


def translate_log(log_text: str) -> list:
    """把 cryptic 编译日志翻译成大白话诊断（去重，保序）。"""
    out, seen = [], set()
    for pat, msg in _LOG_TRANSLATIONS:
        if pat.search(log_text) and msg not in seen:
            seen.add(msg)
            out.append(msg)
    return out


def auto_fix_hints(log_text: str) -> list:
    out, seen = [], set()
    for pat, msg in _AUTOFIX_HINTS:
        if pat.search(log_text) and msg not in seen:
            seen.add(msg)
            out.append(msg)
    return out


def compile_tex(texfile: str, engine: str = "auto", outdir: str = "build",
                timeout: int = 300) -> dict:
    """真编译。无工具/无文件时诚实降级，不假装成功。返回结构化结果。"""
    if not os.path.exists(texfile):
        return {"ok": False, "status": "no_file", "msg": f"找不到 {texfile}"}
    with open(texfile, encoding="utf-8", errors="replace") as f:
        tex = f.read()
    if engine == "auto":
        det = detect_engine(tex)
        engine = det["engine"]
        engine_reason = det["reason"]
    else:
        engine_reason = "用户指定"
    tool, path = find_tool()
    if not tool:
        return {"ok": False, "status": "tool_missing", "engine": engine,
                "msg": "未找到 latexmk / tectonic——装 TeX 发行版（MiKTeX/TeX Live）或 tectonic 后重试。"
                       "本脚本不假装编译成功。"}
    os.makedirs(outdir, exist_ok=True)
    cmd = build_command(tool, engine, texfile, outdir)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                              encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return {"ok": False, "status": "timeout", "engine": engine, "tool": tool,
                "msg": f"编译超时（>{timeout}s）——可能在等缺包交互或死循环。"}
    # 读 .log（latexmk/tectonic 都落 <base>.log 到 outdir）
    base = os.path.splitext(os.path.basename(texfile))[0]
    log_path = os.path.join(outdir, base + ".log")
    log_text = ""
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8", errors="replace") as f:
            log_text = f.read()
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "") + "\n" + log_text
    pdf = os.path.join(outdir, base + ".pdf")
    ok = proc.returncode == 0 and os.path.exists(pdf)
    result = {"ok": ok, "status": "compiled" if ok else "compile_error",
              "engine": engine, "engine_reason": engine_reason, "tool": tool,
              "returncode": proc.returncode, "pdf": pdf if os.path.exists(pdf) else None,
              "diagnostics": translate_log(combined), "fix_hints": auto_fix_hints(combined)}
    # 复用 precheck_log 的 undefined ref/cite 扫描（交付门用）
    if _HAS_PRECHECK and log_text:
        result["precheck"] = precheck_log.scan(log_text)
    return result


def to_markdown(r: dict) -> str:
    if r["status"] in ("no_file", "tool_missing", "timeout"):
        return f"# 编译驱动 — {r['status']}\n\n{r['msg']}"
    head = "✓ 编译成功" if r["ok"] else "✗ 编译失败"
    lines = [f"# {head}（引擎 {r['engine']}｜工具 {r['tool']}｜退出码 {r['returncode']}）",
             f"> 引擎选择：{r.get('engine_reason','')}",
             f"> PDF：{r['pdf'] or '未产出'}"]
    if r["diagnostics"]:
        lines.append("\n## 报错翻译（大白话）")
        lines += [f"- {d}" for d in r["diagnostics"]]
    if r["fix_hints"]:
        lines.append("\n## auto-fix 建议（须人工确认，不自动改）")
        lines += [f"- {h}" for h in r["fix_hints"]]
    return "\n".join(lines)


def _selftest() -> int:
    print("### compile_driver 离线逻辑自测（不跑真编译）", file=sys.stderr)

    # 1. 引擎探测
    assert detect_engine(r"\documentclass{ctexart}")["engine"] == "xelatex"
    assert detect_engine(r"\usepackage{fontspec}")["engine"] == "xelatex"
    assert detect_engine(r"\usepackage{xeCJK}")["engine"] == "xelatex"
    assert detect_engine(r"\usepackage{luacode}")["engine"] == "lualatex"
    assert detect_engine(r"\documentclass{article}\usepackage{amsmath}")["engine"] == "pdflatex"
    print("[1] 引擎探测 ctex/fontspec→xelatex, lua→lualatex, 否则 pdflatex ... OK", file=sys.stderr)

    # 2. 报错翻译
    log = ("! Undefined control sequence.\n! Missing $ inserted.\n"
           "File `microtype.sty' not found.\n"
           "Citation `smith2020' on page 1 undefined.\n"
           "Overfull \\hbox (15.3pt too wide) in paragraph at lines 10--12\n")
    diags = translate_log(log)
    joined = " ".join(diags)
    assert "未定义的命令" in joined and "数学模式" in joined and "缺文件" in joined \
        and "引用键未定义" in joined and "行溢出" in joined, diags
    print(f"[2] 报错翻译 {len(diags)} 条大白话 ... OK", file=sys.stderr)

    # 3. auto-fix 建议
    hints = auto_fix_hints(log + "\nh' float specifier changed to ht'.")
    hj = " ".join(hints)
    assert "microtype" in hj and "htbp" in hj, hints
    print("[3] auto-fix 建议(microtype/htbp) ... OK", file=sys.stderr)

    # 4. 命令构造
    cmd_xe = build_command("latexmk", "xelatex", "p.tex", "build")
    assert "-pdfxe" in cmd_xe and "p.tex" in cmd_xe and any("output-directory" in c for c in cmd_xe), cmd_xe
    cmd_pdf = build_command("latexmk", "pdflatex", "p.tex", "build")
    assert "-pdf" in cmd_pdf, cmd_pdf
    cmd_tec = build_command("tectonic", "xelatex", "p.tex", "build")
    assert cmd_tec[0] == "tectonic" and "--outdir" in cmd_tec, cmd_tec
    print("[4] 命令构造 latexmk -pdfxe/-pdf / tectonic ... OK", file=sys.stderr)

    # 5. 诚实降级：找不到文件不假装成功
    r = compile_tex("/no/such/file.tex")
    assert r["ok"] is False and r["status"] == "no_file", r
    # find_tool 返回值合法（本机有则非 None，无则 None，都不崩）
    tool, _ = find_tool()
    assert tool in ("latexmk", "tectonic", None), tool
    print(f"[5] 诚实降级(no_file) + find_tool={tool} ... OK", file=sys.stderr)

    print("[selftest] PASS compile_driver offline（真编译由 --compile 运行时驱动）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="LaTeX 真实编译驱动器")
    ap.add_argument("--compile", dest="texfile", help="要编译的 .tex")
    ap.add_argument("--detect", help="只报引擎选择，不编译")
    ap.add_argument("--engine", default="auto", choices=["auto", "xelatex", "lualatex", "pdflatex"])
    ap.add_argument("--outdir", default="build")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest or (not args.texfile and not args.detect):
        return _selftest()
    if args.detect:
        with open(args.detect, encoding="utf-8", errors="replace") as f:
            det = detect_engine(f.read())
        print(f"引擎：{det['engine']}（{det['reason']}）")
        return 0
    r = compile_tex(args.texfile, engine=args.engine, outdir=args.outdir)
    print(to_markdown(r))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
