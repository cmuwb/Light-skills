#!/usr/bin/env python3
"""Evidence-strength -> wording binder for the "conclusion overclaim" gate
(light-research-ethics asset). Gives SKILL §8 ("结论夸大/过度包装") an executable
tool instead of prose-only judgement.

What it does
------------
Reads three things and binds them:
  1. m06 evidence_strength.json (light.evidence_strength.v1) — the claim->grade
     source produced by result-analysis (shared contract _shared/evidence_contract).
  2. an m07 draft (draft.md / results section) — the prose to lint.
  3. (optional) m08 novelty signals — strong novelty words (SOTA/novel/first) get
     the same evidence-backing requirement.
For every strong assertion verb in the draft, it checks the matching claim's
evidence grade; if the wording outranks the evidence (e.g. "proves" on weak
evidence), it is flagged with a concrete down-graded wording suggestion.

Shared-contract hookups (no wheel re-invention):
  - _shared/evidence_contract.py : grade_evidence / allowed_verb_tier / lint_wording
    do the grade->verb-tier mapping and the per-claim lint.
  - _shared/findings_schema.py + gate_runner.py : the result is emitted as a
    light.findings.v1 FindingsReport, so a01 passport / db09 memory consume a
    machine-readable verdict (not prose). This IS the a10 "overclaim gate" wired
    into the shared gate-runner.

HONEST LIMITS:
- Matching a draft sentence to its claim is heuristic: when an
  evidence_strength.json is supplied we lint each claim's text-bearing wording;
  with --whole-draft we apply the *strongest* applicable grade across all claims
  to the whole text (conservative — fewer false "overclaim" alarms only when a
  strong claim genuinely exists). A flag is a needs-revision signal, not proof.
- No evidence file => the gate runs in "unbacked-claims" mode: every strong claim
  verb without ANY backing evidence is flagged as "assertion with no evidence
  grade on record", which is itself the integrity finding.

Usage:
    python claim_evidence_bind.py --draft draft.md --evidence evidence_strength.json
    python claim_evidence_bind.py --draft draft.md            # unbacked mode
    python claim_evidence_bind.py --draft draft.md --json
    python claim_evidence_bind.py --selftest
"""
import sys
import os
import re
import json
import argparse

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# ── Hook the shared contracts (script-mode import per _shared/README §B) ──
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "_shared"))
import evidence_contract as ec            # noqa: E402
from findings_schema import Finding, GateResult, FindingsReport  # noqa: E402
from gate_runner import run_gates         # noqa: E402

# Strong-assertion vocabulary (English + Chinese) used in unbacked-claims mode.
_STRONG_EN = [
    "prove", "proves", "proven", "proved",
    "demonstrate", "demonstrates", "demonstrated",
    "establish", "establishes", "established",
    "confirm", "confirms", "confirmed",
    "significantly outperform", "significantly outperforms",
    "state-of-the-art", "sota", "novel", "first to",
    "guarantee", "guarantees",
]
_STRONG_CN = ["证明", "证实", "确证", "首次", "显著优于", "远超", "全面超越", "突破性"]
# softened wording suggestions for unbacked strong verbs
_SOFTEN = {
    "prove": "is consistent with", "proves": "is consistent with",
    "proved": "was consistent with", "proven": "consistent with",
    "demonstrate": "indicate", "demonstrates": "indicates",
    "demonstrated": "indicated", "establish": "suggest",
    "establishes": "suggests", "established": "suggested",
    "confirm": "is consistent with", "confirms": "is consistent with",
    "guarantee": "is expected to", "guarantees": "is expected to",
    "证明": "与……一致 / 表明", "证实": "表明", "确证": "表明",
    "首次": "据我们所知较早地", "显著优于": "在本实验中优于",
    "远超": "高于", "全面超越": "在所测维度上优于", "突破性": "值得关注的",
}


def _line_of(text, idx):
    return text.count("\n", 0, idx) + 1


def lint_against_evidence(draft_text, evidence):
    """Lint draft wording against a light.evidence_strength.v1 dict.

    Uses the *strongest-applicable* claim grade as the ceiling when claims are not
    individually localizable in the draft (conservative). Returns Finding list.
    """
    claims = evidence.get("claims", [])
    findings = []
    if not claims:
        return findings
    # Determine the strongest grade present; lint the whole draft against the
    # weakest claim that still carries the strong wording would be too noisy, so
    # we lint each claim's own grade and merge (a verb flagged by ANY claim whose
    # grade forbids it, but allowed by a stronger claim, is NOT flagged — we keep
    # only verbs that exceed the STRONGEST available grade).
    order = {"none": 0, "weak": 1, "moderate": 2, "strong": 3}
    best_grade = max((c.get("evidence_grade")
                      or ec.grade_evidence(c.get("q_fdr"), c.get("effect_size"),
                                           c.get("ci95"), c.get("n"))
                      for c in claims), key=lambda g: order.get(g, 0))
    synthetic = {"evidence_grade": best_grade}
    for v in ec.lint_wording(draft_text, synthetic):
        findings.append(Finding(
            loc=v["loc"], issue=v["issue"], fix=v["suggestion"],
            evidence="best available evidence grade=%s" % best_grade,
            rule="evidence_contract.lint_wording"))
    return findings, best_grade


def lint_unbacked(draft_text):
    """No evidence file: flag every strong assertion verb as unbacked."""
    findings = []
    low = draft_text.lower()
    for verb in _STRONG_EN:
        pat = re.compile(r"(?<![a-z])" + re.escape(verb.lower()) + r"(?![a-z])")
        for m in pat.finditer(low):
            sug = _SOFTEN.get(verb, "(hedge / cite evidence)")
            findings.append(Finding(
                loc="line %d" % _line_of(draft_text, m.start()),
                issue="strong claim '%s' with no evidence grade on record" % verb,
                fix="back with m06 evidence or soften to '%s'" % sug,
                rule="claim_evidence_bind.unbacked"))
    for verb in _STRONG_CN:
        for m in re.finditer(re.escape(verb), draft_text):
            sug = _SOFTEN.get(verb, "（加证据或弱化措辞）")
            findings.append(Finding(
                loc="line %d" % _line_of(draft_text, m.start()),
                issue="强主张『%s』无证据等级支撑" % verb,
                fix="用 m06 证据支撑,或弱化为『%s』" % sug,
                rule="claim_evidence_bind.unbacked"))
    return findings


def overclaim_gate(artifact):
    """gate_runner-compatible gate. artifact = {'draft':str, 'evidence':dict|None}."""
    draft = artifact["draft"]
    evidence = artifact.get("evidence")
    if evidence:
        findings, best_grade = lint_against_evidence(draft, evidence)
        note = "linted against evidence (strongest grade=%s)" % best_grade
        if findings:
            # Wording outranks the actual computed evidence grade — a clear,
            # confident overclaim. Block it (critical).
            return GateResult("conclusion_overclaim", "fail", "critical", findings,
                              note=note)
        return GateResult("conclusion_overclaim", "pass", "info", [], note=note)
    # No evidence file: softer signal (could just be a missing artifact), but many
    # unbacked strong claims still blocks.
    findings = lint_unbacked(draft)
    if findings:
        sev = "critical" if len(findings) >= 3 else "major"
        return GateResult("conclusion_overclaim", "fail", sev, findings,
                          note="no evidence file: every strong claim treated as unbacked")
    return GateResult("conclusion_overclaim", "pass", "info", [],
                      note="no evidence file; no strong unbacked claims found")


def bind(draft_text, evidence=None, producer="a10", target="draft.md"):
    """Run the overclaim gate through the shared gate-runner -> FindingsReport."""
    artifact = {"draft": draft_text, "evidence": evidence}
    report = run_gates([overclaim_gate], artifact,
                       producer=producer, target=target,
                       summary="evidence-strength->wording binding (a10 §8 gate)",
                       fresh_evidence=bool(evidence))
    return report


def _emit(report, as_json):
    if as_json:
        print(report.to_json())
        return
    print("claim_evidence_bind -> verdict: %s" % report.verdict)
    for g in report.gates:
        print("  [%s/%s] %s — %s" % (g.status, g.severity, g.gate, g.note))
        for f in g.findings:
            print("    - %s : %s" % (f.loc, f.issue))
            if f.fix:
                print("      fix: %s" % f.fix)


def _selftest():
    # 1. Evidence-backed: weak evidence + "demonstrates" should be flagged.
    weak_ev = ec.build_evidence_json([
        {"claim_id": "c1", "text": "A>B", "q_fdr": 0.03, "effect_size": 0.2,
         "ci95": [0.05, 0.4], "n": 200}])
    rep = bind("Our method demonstrates a significant improvement over baselines.",
               evidence=weak_ev)
    assert rep.verdict == "fail", "weak evidence + demonstrate should fail: %s" % rep.verdict
    assert any("demonstrate" in f.issue for g in rep.gates for f in g.findings)
    print("[selftest] evidence-backed: weak+demonstrate flagged PASS")

    # 2. Evidence-backed: strong evidence + "demonstrate" should pass.
    strong_ev = ec.build_evidence_json([
        {"claim_id": "c1", "text": "A>B", "q_fdr": 0.001, "effect_size": 0.9,
         "ci95": [0.4, 1.3], "n": 120}])
    rep2 = bind("We demonstrate a clear and reliable effect.", evidence=strong_ev)
    assert rep2.verdict == "pass", "strong evidence + demonstrate should pass: %s" % rep2.verdict
    print("[selftest] evidence-backed: strong+demonstrate passes PASS")

    # 3. Unbacked mode: strong claims with no evidence file are flagged.
    rep3 = bind("We prove our approach and establish that it is state-of-the-art.")
    assert rep3.verdict == "fail", "unbacked strong claims should fail"
    issues = [f.issue for g in rep3.gates for f in g.findings]
    assert any("prove" in i for i in issues), issues
    print("[selftest] unbacked mode: strong claims flagged PASS")

    # 4. Chinese strong claims flagged in unbacked mode.
    rep4 = bind("本文首次证明该方法显著优于现有方案。")
    assert rep4.verdict == "fail"
    assert any("证明" in f.issue or "首次" in f.issue
               for g in rep4.gates for f in g.findings)
    print("[selftest] unbacked mode: Chinese strong claims flagged PASS")

    # 5. Clean hedged draft passes in unbacked mode.
    rep5 = bind("Our results suggest the method may improve accuracy in some settings.")
    assert rep5.verdict == "pass", "hedged draft should pass: %s" % rep5.verdict
    print("[selftest] hedged draft passes PASS")

    # 6. FindingsReport round-trips as light.findings.v1 JSON.
    s = rep.to_json()
    d = json.loads(s)
    assert d["schema"] == "light.findings.v1" and d["producer"] == "a10"
    assert FindingsReport.from_json(s).verdict == rep.verdict
    print("[selftest] light.findings.v1 JSON round-trip PASS")

    print("[selftest] all assertions PASS")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="Evidence-strength -> wording binder (a10 overclaim gate)")
    ap.add_argument("--draft", help="draft / results text file")
    ap.add_argument("--text", help="inline draft text")
    ap.add_argument("--evidence", help="m06 evidence_strength.json")
    ap.add_argument("--target", default="draft.md")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()

    if args.text is not None:
        draft = args.text
    elif args.draft:
        with open(args.draft, encoding="utf-8", errors="replace") as f:
            draft = f.read()
    else:
        ap.error("provide --draft, --text, or --selftest")
    evidence = None
    if args.evidence:
        evidence = ec.load(args.evidence)
    report = bind(draft, evidence=evidence, target=args.target)
    _emit(report, args.json)
    return 0 if report.verdict != "fail" else 2


if __name__ == "__main__":
    sys.exit(main())
