<div align="center">

<img src="assets/logo.svg" width="150" alt="Light logo"/>

# Light

**A full-pipeline research skill pack — let AI walk a paper from idea to submission with you**

Every step of research, from literature search to rebuttal, has a dedicated skill · Works with Claude Code & Codex

<br/>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/Light0305/Light/actions/workflows/ci.yml/badge.svg)](https://github.com/Light0305/Light/actions/workflows/ci.yml)
[![Skills](https://img.shields.io/badge/skills-27-5B6FE0.svg)](#-skills-at-a-glance)
[![Knowledge bases](https://img.shields.io/badge/knowledge%20bases-9-3DDC84.svg)](#-knowledge-bases)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-ready-8AA0FF.svg)](#-install)
[![Codex](https://img.shields.io/badge/Codex-ready-FFA63D.svg)](#-install)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[简体中文](README.md) · **English**

</div>

---

## Contents

- [What is Light](#what-is-light)
- [Why use it](#why-use-it)
- [Quick start](#-install)
- [Skills at a glance](#-skills-at-a-glance)
- [A full project flow](#a-full-project-flow)
- [Knowledge bases](#-knowledge-bases)
- [Principles](#-principles)
- [Layout](#-layout)
- [FAQ](#-faq)
- [Contributing](#-contributing)
- [Support & feedback](#-support)
- [License](#-license)

---

## What is Light

Light breaks the full research pipeline into **27 interlocking AI skills**, installed into your Claude Code and Codex. From finding literature, wrangling data, and generating ideas, to drafting papers, making figures, typesetting, submitting, and rebutting — plus patents, defense decks, and competition materials — every step has a dedicated skill, backed by 9 **traceable** knowledge bases.

It is not a pile of prompts. Each skill ships **runnable scripts, reusable templates, and real worked examples**: external interfaces are tested for real, and statistics code is aligned with `scipy`/`sklearn` down to the last digit. **Never fabricating references, data, sources, or origins** is a line it won't cross.

> In one line: a senior research companion who genuinely knows the tools, installed into your editor.

## Why use it

Most "research AI" stops at chat. Light is different in three hard ways:

| | Ordinary prompt / assistant | **Light** |
|---|---|---|
| **Output** | A paragraph of advice | Runnable scripts + fillable templates + real examples |
| **Trust** | May fabricate refs, data, DOIs | Hard rule: never fabricate; the unverifiable is flagged |
| **Cohesion** | One-off answers, disjoint | 27 skills along one line, 9 shared knowledge bases |
| **Quality** | One pass | Adversarial self-check + authoritative cross-validation |
| **Memory** | Forgets on close | Cross-session project memory |

For: undergrads, grad students, and independent researchers who want to turn a project into a **real paper / copyright / patent / contest result** — especially anyone short on advisor support who needs a reliable companion across the whole pipeline.

## 🚀 Install

> Prereq: [Claude Code](https://claude.ai/code) or Codex installed, and `git` available.

The 27 skills share the 9 knowledge bases and `code_assets/` at the repo root (via relative paths), so **keep the whole repo together** — the installer links the skills plus shared libraries into your client's skills directory.

**1. Clone** (anywhere):

```bash
git clone https://github.com/Light0305/Light.git
cd Light
```

**2. Run the installer:**

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File install.ps1            # both clients
powershell -ExecutionPolicy Bypass -File install.ps1 -Client claude   # Claude Code only

# macOS / Linux
./install.sh           # both clients
./install.sh claude    # a single client
```

Idempotent and re-runnable; links into Claude Code's `~/.claude/skills/` and Codex's `~/.agents/skills/`.

**3. Restart your client and just ask:**

```
Do a literature review on this topic for me
Which venue should this paper go to?
Run significance tests on my results and make a publication-grade figure
```

Matching skills **trigger automatically** (matched to what you ask, no commands to memorize); or invoke any of the 17 manual skills by name with `/`. Codex needs one small extra step — see [.codex/INSTALL.md](.codex/INSTALL.md).

**Uninstall**: delete the links under your client's skills directory; the source repo is untouched.

## 🧭 Skills at a glance

The 27 skills split in two: **17 manual skills** you can invoke by name with `/`, which also trigger automatically on relevant tasks; and **10 always-on skills** that run in the background only (not in the `/` menu, but still working).

### Manual skills · along the research line (17)

| Stage | Skill | What it does |
|-------|-------|--------------|
| 📚 Literature | `light-literature-search` | Multi-source search, dedup, credibility & importance tiering, review skeleton |
| 🧹 Data | `light-data-engineering` | Health check, leakage-safe split, quality gate, dataset building |
| 💡 Ideation | `light-idea-generation` ⇄ `light-idea-critique` | Propose ideas ↔ reviewer-grade adversarial critique, paired loop |
| 🗺️ Planning | `light-research-plan` | Technical roadmap, experiment matrix, feasibility, reproducible plan |
| 📊 Analysis | `light-result-analysis` | EDA, significance tests, effect sizes, anomaly tracing |
| ✍️ Writing | `light-paper-drafting` ⇄ `light-paper-polishing` | Per-module drafting / logic-structure-language polish, reviewer lens |
| 📈 Figures | `light-figure-planning` ⇄ `light-figure-drawing` | Figure planning (what & where) / per-journal publication-grade drawing |
| 🔖 Cite & typeset | `light-citation` · `light-typesetting` | DOI verification, multi-format refs / LaTeX·Word typeset & export PDF |
| 📮 Submit & rebut | `light-venue-matching` · `light-review-rebuttal` | Venue targeting & tiering / mock review + point-by-point rebuttal |
| 🏆 Outputs | `light-ip-application` · `light-slides` · `light-competition` | Patents/copyright / defense & pitch decks / contest materials |

### Always-on skills · background (10)

No need to invoke — they kick in automatically on relevant tasks and guard quality throughout:

| Skill | Role |
|-------|------|
| `light-file-reading` | Read PDF/Word/PPT/Excel/CSV/image/code/archives — understand structure, not just text |
| `light-memory-pm` | Cross-session project memory, stage breakdown, milestones & versions |
| `light-backend-coding` | Experiment/model/data/viz/backend code, TDD & systematic debugging |
| `light-system-design` | Architecture, database, API, auth, deployment design |
| `light-frontend-design` | Frontend UI & visualization dashboards, polished and demo-ready |
| `light-project-structure` | Standard project layout & naming, reproducible and tidy |
| `light-consistency` | Terms/metrics/claims aligned across paper·slides·copyright |
| `light-self-review` | Logic/facts/format/overclaim self-check before output |
| `light-tool-selection` | Pick the most fitting tool & method per task |
| `light-research-ethics` | Academic ethics, compliance, anti-fabrication floor |

## A full project flow

Skills aren't isolated tools — they hand off along one research throughline:

```
kickoff → literature-search find direction & gaps → data-engineering health-check & leakage-safe split
        → idea-generation ⇄ idea-critique propose, adversarial critique, loop until solid
        → research-plan technical route & experiment matrix → backend-coding implement (TDD)
        → result-analysis significance + effect sizes + publication figures
        → paper-drafting ⇄ paper-polishing draft & polish
        → citation / figure-drawing / typesetting verify refs, render, typeset
        → venue-matching pick a venue → review-rebuttal rebuttal & revision
        → ip-application patents · slides defense deck · competition contest materials
```

Throughout, the 10 always-on skills backstop it: `file-reading` ingests any material, `memory-pm` remembers where you left off, `consistency` keeps materials aligned, `self-review` self-checks before every output, `research-ethics` holds the integrity floor.

## 📚 Knowledge bases

Behind the skills sit 9 shared knowledge bases (`databases/`), all verified and traceable:

| Base | Contents |
|------|----------|
| `db01` venues | Journal/conference metadata, review cycles, representative papers, tiers (real ISSNs + proxy metrics) |
| `db02` templates | Reusable templates for each pipeline stage |
| `db03` methods | Method cards: task/IO/pros-cons/baselines/metrics/papers & repos |
| `db04` datasets | Dataset cards: scale/license/known issues/download |
| `db05` design system | Frontend/visualization design specs |
| `db06` slide themes | PPT themes & palettes |
| `db07` figures | Top-venue figure cases: aesthetics/layout/palette/panel logic |
| `db08` IP & contests | Patents, contest material skeletons & rubric dimensions |
| `db09` project state | Cross-session project memory: project cards/glossary/decision log |

Plus `code_assets/` — adversarially-verified statistics and metrics code (Cohen's κ/QWK vs `sklearn`, Welch t/BH-FDR/Wilson vs `scipy`, MOTA/IDF1, CORAL ordinal loss, long-tail resampling), aligned to authoritative libraries down to the last digit and continuously checked by CI.

## 🎯 Principles

- **Honesty first** — never invent references, data, sources, or origins; the unverifiable is clearly flagged "to be checked", verified is kept separate from inferred, and copyrighted material is stored as metadata and links only.
- **Runnable, not hand-wavy** — skills carry scripts that actually run, fillable templates, and complete examples, not paragraphs of abstract advice.
- **Adversarial self-check** — key outputs pass an independent "refute it" pass and cross-validation against trusted tools (statistics checked against `scipy`/`sklearn`, external interfaces tested for real).
- **Pipeline cohesion** — 27 skills hand off along one research throughline, sharing 9 knowledge bases for terminology, methods, and venue data.

## 🗂️ Layout

```
Light/
├── skills/             # 27 skills, each with SKILL.md + references + scripts/templates/examples
├── databases/          # 9 knowledge bases (db01–db09)
├── code_assets/        # adversarially-verified stats & metrics code, CI-checked
├── assets/             # logo, images
├── install.ps1 / .sh   # one-command installer (idempotent)
├── CONVENTIONS.md      # global conventions (honesty floor, output norms)
├── ROUTER.md           # skill routing logic
├── AGENTS.snippet.md   # Codex routing block
├── CONTRIBUTING.md     # contribution guide
├── CHANGELOG.md        # changelog
├── .github/            # issue/PR templates, CI, funding config
└── .codex/INSTALL.md   # Codex install guide
```

## ❓ FAQ

**Q: How is this different from just chatting with ChatGPT/Claude?**
A: Light gives runnable scripts, fillable templates, and real examples, with a hard "no fabrication" rule and adversarial self-check — plus cross-session project memory. Not one-off Q&A.

**Q: Why don't the always-on skills show up under `/`?**
A: These 10 skills are designed to work in the background automatically, so they don't take up space in the `/` menu. The 17 manual skills work via `/` as usual.

**Q: Do I have to install both clients?**
A: No. `install.ps1 -Client claude` or `install.sh claude` installs just one.

**Q: Will it upload my data to third parties?**
A: No, unless the task requires it (e.g. searching public academic APIs). Operations that upload are surfaced. See [SECURITY.md](SECURITY.md).

**Q: Will Light write my paper or fabricate data for me?**
A: No. It assists your research and expression but enforces academic ethics (`light-research-ethics`): no fabricated data, no invented references, no overclaiming.

## 🤝 Contributing

Bug fixes, new skills, knowledge-base entries, and docs are all welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [CONVENTIONS.md](CONVENTIONS.md) (especially the honesty floor), and follow the [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report security issues privately per [SECURITY.md](SECURITY.md).

## ❤️ Support

Light is built and polished by one person in spare time. If it saves you time or makes research smoother, consider buying the author a coffee — your support is the biggest motivation for continued updates.

<div align="center">
<img src="assets/wechat-donation.jpg" width="220" alt="WeChat donation QR"/>

*Scan with WeChat — any amount, the thought is what counts 🙏*
</div>

## 💬 Feedback

- **Bugs / feature requests** — open an [Issue](https://github.com/Light0305/Light/issues) (bug / feature templates)
- **Usage & discussion** — head to [Discussions](https://github.com/Light0305/Light/discussions)
- **Contributions** — fork and send a Pull Request
- **Email** — 1833058953@qq.com

## 📌 Citation

If Light helps your research, cite it via [CITATION.cff](CITATION.cff), or click "Cite this repository" on the GitHub repo page.

## 📄 License

[MIT License](LICENSE) © 2026 Light

---

<div align="center">
<sub>Turn ideas into papers with Light · Made with care for researchers</sub>
</div>
