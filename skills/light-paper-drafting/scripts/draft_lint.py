#!/usr/bin/env python3
"""draft_lint.py — 论文草稿诚信门机检器（人判优先，机检兜底）。

检查项：
  1. 残留缺口标记：[MATERIAL GAP] / [RESULT GAP] / TODO（终稿门必须为 0）。
  2. 必备声明小节缺失：Data Availability / Ethics / CRediT / Conflicts / Funding / AI Use。
  3. 高危结果句无显著性：含 SOTA/outperform/最优 等措辞却无 p 值/CI/±std 提示。
  4. 引用台账：抽取 DOI/arXiv，输出待 curl 核查清单（不联网，只列动作）。

用法：
  python draft_lint.py <draft.md> [--final]   # --final 时残留 GAP 视为失败
  python draft_lint.py --selftest             # 合成数据自测，无需外部文件

退出码：0 通过；1 发现需返工项；2 用法错误。
"""
import re
import sys

GAP_PAT = re.compile(r"\[(?:MATERIAL GAP|RESULT GAP)\b[^\]]*\]|(?<![\w/])TODO\b")
DOI_PAT = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
ARXIV_PAT = re.compile(r"arXiv:\d{4}\.\d{4,5}", re.IGNORECASE)
HYPE_PAT = re.compile(r"\b(?:state[- ]of[- ]the[- ]art|SOTA|outperform\w*|best[- ]ever|超越|最优|优于)\b", re.IGNORECASE)
SIG_PAT = re.compile(r"p\s*[<=>]\s*0?\.\d+|95%\s*CI|±\s*\d|std", re.IGNORECASE)

REQUIRED_SECTIONS = {
    "Data Availability": r"data\s+availability",
    "Ethics": r"ethics",
    "CRediT": r"credit|author\s+contribution",
    "Conflicts of Interest": r"conflict|competing\s+interest",
    "Funding": r"funding",
    "AI Use Disclosure": r"ai\s+use|generative\s+ai|llm",
}


def lint(text, final=False):
    findings = []
    lines = text.splitlines()

    # 1. 残留缺口标记
    gaps = [(i + 1, m.group(0)) for i, ln in enumerate(lines) for m in GAP_PAT.finditer(ln)]
    if gaps:
        sev = "FAIL" if final else "WARN"
        findings.append((sev, f"残留缺口标记 {len(gaps)} 处" + (" — 终稿门要求清零" if final else " — 初稿可暂留")))
        for ln_no, tok in gaps[:20]:
            findings.append(("  ", f"L{ln_no}: {tok}"))

    # 2. 必备声明
    low = text.lower()
    missing = [name for name, pat in REQUIRED_SECTIONS.items() if not re.search(pat, low)]
    if missing:
        findings.append(("WARN", "缺必备声明小节: " + ", ".join(missing)))

    # 3. 高危结果句缺显著性
    for i, ln in enumerate(lines):
        if HYPE_PAT.search(ln) and not SIG_PAT.search(ln):
            findings.append(("WARN", f"L{i+1}: 含夸大/SOTA 措辞但无显著性(p/CI/±std): {ln.strip()[:70]}"))

    # 4. 引用台账
    dois = sorted(set(DOI_PAT.findall(text)))
    arxivs = sorted(set(ARXIV_PAT.findall(text)))
    if dois or arxivs:
        findings.append(("INFO", f"引用待核: {len(dois)} DOI + {len(arxivs)} arXiv（需 curl 实测记 HTTP 码）"))
        for d in dois[:20]:
            findings.append(("  ", f'curl -sI -H "Accept: application/vnd.citationstyles.csl+json" https://doi.org/{d}'))
        for a in arxivs[:20]:
            aid = a.split(":", 1)[1]
            findings.append(("  ", f"curl -sI https://arxiv.org/abs/{aid}"))

    failed = any(sev == "FAIL" for sev, _ in findings)
    return findings, failed


def _selftest():
    bad = """# Title
We achieve state-of-the-art results, outperforming all baselines.
Tail accuracy improves by [RESULT GAP: 待实验].
Prior work [MATERIAL GAP: 需引用] showed something.
See doi 10.1109/CVPR.2016.90 and arXiv:1512.03385 for ResNet.
TODO: add ablation.
"""
    good = """# Title
We improve tail accuracy by 4.2 points (p<0.001, ±0.3 std) over the baseline.
## Data Availability
Synthetic data; code at anonymous repo.
## Ethics Statement
No human or animal subjects.
## CRediT Author Contributions
A.B.: all.
## Conflicts of Interest
None.
## Funding
No specific grant.
## AI Use Disclosure
LLM used for language editing; authors verified all content.
"""
    print("=== selftest: BAD draft (初稿门) ===")
    f1, fail1 = lint(bad, final=False)
    for sev, msg in f1:
        print(f"[{sev}] {msg}")
    print(f"final-mode fail? {lint(bad, final=True)[1]}")

    print("\n=== selftest: GOOD draft (终稿门) ===")
    f2, fail2 = lint(good, final=True)
    for sev, msg in f2:
        print(f"[{sev}] {msg}")

    # 断言：bad 在终稿门必失败；good 在终稿门不因 GAP 失败且无缺失声明
    assert lint(bad, final=True)[1] is True, "BAD 应在终稿门 FAIL"
    assert fail2 is False, "GOOD 不应有 FAIL 级问题"
    assert not any("缺必备声明" in m for _, m in f2), "GOOD 不应缺声明"
    assert any("引用待核" in m for _, m in f1), "BAD 应抽出引用待核"
    assert any("无显著性" in m for _, m in f1), "BAD 应标出无显著性的 SOTA 句"
    print("\nALL SELFTEST ASSERTIONS PASSED")


def main(argv):
    if len(argv) == 2 and argv[1] == "--selftest":
        _selftest()
        return 0
    if len(argv) < 2:
        print(__doc__)
        return 2
    final = "--final" in argv
    path = [a for a in argv[1:] if not a.startswith("--")][0]
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    findings, failed = lint(text, final=final)
    for sev, msg in findings:
        print(f"[{sev}] {msg}")
    print("\n==> " + ("FAIL: 有需返工项" if failed else "PASS: 无 FAIL 级问题（WARN 仍需人判）"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
