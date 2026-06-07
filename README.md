<div align="center">

<img src="assets/logo.svg" width="150" alt="Light logo"/>

# Light

**全流程科研技能包 · 让 AI 陪你把一篇论文从想法做到投稿**

从找文献到投稿返修,科研每一步都有专门技能接管 · 适配 Claude Code 与 Codex

<br/>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/Light0305/Light/actions/workflows/ci.yml/badge.svg)](https://github.com/Light0305/Light/actions/workflows/ci.yml)
[![Skills](https://img.shields.io/badge/skills-27-5B6FE0.svg)](#-技能总览)
[![Knowledge bases](https://img.shields.io/badge/knowledge%20bases-9-3DDC84.svg)](#-知识库)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-ready-8AA0FF.svg)](#-安装)
[![Codex](https://img.shields.io/badge/Codex-ready-FFA63D.svg)](#-安装)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**简体中文** · [English](README.en.md)

</div>

---

## 目录

- [Light 是什么](#light-是什么)
- [为什么用它](#为什么用它)
- [快速上手](#-安装)
- [技能总览](#-技能总览)
- [一个项目的完整链路](#一个项目的完整链路)
- [知识库](#-知识库)
- [设计理念](#-设计理念)
- [目录结构](#-目录结构)
- [常见问题](#-常见问题)
- [参与贡献](#-参与贡献)
- [支持与反馈](#-支持与鼓励)
- [许可](#-许可)

---

## Light 是什么

Light 把科研全流程拆成 **27 个互相衔接的 AI 技能**,装进你的 Claude Code 和 Codex。从找文献、理数据、想创新点,到写论文、画图、排版、投稿、返修,再到软著专利、答辩 PPT、竞赛申报——每一步都有专门的技能接手,背后还垫着 9 个**可溯源**的知识库。

它不是一堆提示词。每个技能都带**能跑的脚本、能套的模板、真实的范例**:对外接口经过实测,统计代码与 `scipy`/`sklearn` 逐位对齐。**不编文献、不造数据、不臆想出处和数据来源**——这是不可逾越的底线。

> 一句话:把一位真正懂科研工具的资深伙伴,装进你的编辑器。

## 为什么用它

市面上的"科研 AI"大多止于聊天问答。Light 不一样,它有三个硬核区别:

| | 普通提示词 / 助手 | **Light** |
|---|---|---|
| **产出** | 一段文字建议 | 能跑的脚本 + 能套的模板 + 真实范例 |
| **可信** | 可能编造文献、数据、DOI | 写进规约的硬底线:不编造,核不实标"待核查" |
| **协同** | 单点回答,前后脱节 | 27 个技能沿一条主线衔接,9 个知识库共享术语与方法 |
| **质量** | 一次成型 | 对抗式自检:独立"挑刺" + 权威库交叉验证 |
| **记忆** | 关掉就忘 | 跨会话项目记忆,记住做到哪一步 |

适合:**要把项目真正做成论文/软著/专利/竞赛成果**的本科生、研究生、独立研究者,尤其是导师资源有限、需要一个靠谱搭子全程兜底的人。

## 🚀 安装

> 前置:已安装 [Claude Code](https://claude.ai/code) 或 Codex,本机有 `git`。

27 个技能共用根目录下的 9 个知识库与 `code_assets/`(靠相对路径引用),所以**整个仓库必须放在一起**——安装脚本会把技能和共享库一起链接到客户端的技能目录。

**1. 克隆仓库**(放哪都行):

```bash
git clone https://github.com/Light0305/Light.git
cd Light
```

**2. 运行安装脚本:**

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File install.ps1            # 两端都装
powershell -ExecutionPolicy Bypass -File install.ps1 -Client claude   # 只装 Claude Code

# macOS / Linux
./install.sh           # 两端都装
./install.sh claude    # 只装某一端
```

脚本幂等、可重跑,把技能链接进 Claude Code 的 `~/.claude/skills/` 与 Codex 的 `~/.agents/skills/`。

**3. 重启客户端,开说:**

```
帮我把这个方向做一遍文献调研
这篇论文该投哪个期刊?
帮我把实验结果做显著性检验,出一张出版级的图
```

相关技能会**自动触发**(根据你的需求智能匹配,无需记命令);也可以用 `/` 点名调用 17 个手动技能。Codex 端还需一步小配置,详见 [.codex/INSTALL.md](.codex/INSTALL.md)。

**卸载**:删掉客户端技能目录下对应的链接即可,不影响源仓库。

## 🧭 技能总览

27 个技能分两类:**17 个手动技能**可直接用 `/` 点名调用,也会在相关任务里自动触发;**10 个常驻技能**只在后台自动生效(不出现在 `/` 菜单,但照常工作)。

### 手动技能 · 按科研主线(17)

| 阶段 | 技能 | 做什么 |
|------|------|--------|
| 📚 资料调研 | `light-literature-search` | 多源检索、去重、可信度判断、重要性分级、综述骨架 |
| 🧹 数据处理 | `light-data-engineering` | 数据体检、防泄漏划分、质量门校验、自建数据集规划 |
| 💡 创新提案 | `light-idea-generation` ⇄ `light-idea-critique` | 提创新点 ↔ 审稿人级对抗挑刺,成对循环到站得住 |
| 🗺️ 方案设计 | `light-research-plan` | 技术路线、实验矩阵、可行性、可复现规划 |
| 📊 结果分析 | `light-result-analysis` | EDA、显著性检验、效应量、异常溯因、规律发现 |
| ✍️ 论文写作 | `light-paper-drafting` ⇄ `light-paper-polishing` | 分模块成稿 / 逻辑·结构·语言润色,审稿人视角打磨 |
| 📈 图表 | `light-figure-planning` ⇄ `light-figure-drawing` | 图表规划(做什么图、放哪) / 逐刊规格出版级绘图 |
| 🔖 引用排版 | `light-citation` · `light-typesetting` | DOI 核验、多格式参考文献 / LaTeX·Word 排版导出 PDF |
| 📮 投稿返修 | `light-venue-matching` · `light-review-rebuttal` | 投稿定位分层(冲刺/稳妥/保底) / 模拟审稿 + 逐条返修 |
| 🏆 成果转化 | `light-ip-application` · `light-slides` · `light-competition` | 软著专利 / 答辩路演 PPT / 竞赛申报材料 |

### 常驻技能 · 后台自动(10)

无需调用,在相关任务中自动生效,贯穿全程保障质量:

| 技能 | 职责 |
|------|------|
| `light-file-reading` | 读 PDF/Word/PPT/Excel/CSV/图片/代码/压缩包,理解结构而非只提字 |
| `light-memory-pm` | 跨会话项目记忆、阶段拆解、里程碑与版本记录 |
| `light-backend-coding` | 实验/模型/数据/可视化/后端代码,TDD 与系统化调试 |
| `light-system-design` | 系统架构、数据库、接口、权限、部署设计 |
| `light-frontend-design` | 前端界面与可视化大屏,审美统一、可演示 |
| `light-project-structure` | 规范项目目录与命名,便于复现与成果整理 |
| `light-consistency` | 术语/指标/创新点跨论文·PPT·软著一致 |
| `light-self-review` | 逻辑/事实/格式/夸大自审,产出前先迭代 |
| `light-tool-selection` | 按任务选最合适的工具与方法 |
| `light-research-ethics` | 学术伦理、合规、防造假与过度包装的底线 |

## 一个项目的完整链路

技能不是孤立工具,而是沿一条科研主线相互交接:

```
立项 → literature-search 找方向与 gap → data-engineering 数据体检与防泄漏划分
     → idea-generation ⇄ idea-critique 提创新点、对抗挑刺,循环到站得住
     → research-plan 定技术路线与实验矩阵 → backend-coding 落地实验(TDD)
     → result-analysis 显著性检验 + 效应量 + 出版级图
     → paper-drafting ⇄ paper-polishing 成稿与润色
     → citation / figure-drawing / typesetting 引用核验、出图、排版
     → venue-matching 选刊投稿 → review-rebuttal 返修回复
     → ip-application 软著专利 · slides 答辩 PPT · competition 竞赛申报
```

全程 10 个常驻技能在后台兜底:`file-reading` 吃进任意材料,`memory-pm` 记住做到哪一步,`consistency` 盯跨材料一致,`self-review` 每次产出前自审,`research-ethics` 守住诚信底线。

## 📚 知识库

技能背后垫着 9 个共享知识库(`databases/`),内容均经核查、可溯源:

| 库 | 内容 |
|----|------|
| `db01` 期刊会议 | 期刊/会议元数据、审稿周期、代表作、分层(含真实 ISSN 与替代指标) |
| `db02` 模板 | 各阶段产出的可套用模板 |
| `db03` 方法 | 方法卡:任务/输入输出/优劣/基线/评测/代表作与实现仓库 |
| `db04` 数据集 | 数据集卡:规模/许可/已知问题/下载方式 |
| `db05` 设计系统 | 前端/可视化设计规范 |
| `db06` 幻灯主题 | PPT 主题与配色 |
| `db07` 科研图表 | 顶刊顶会图表案例:审美/布局/配色/组图逻辑 |
| `db08` 知识产权与竞赛 | 软著专利、竞赛申报材料骨架与评审维度 |
| `db09` 项目状态 | 跨会话项目记忆:项目卡/术语表/决策日志 |

另有 `code_assets/` 收录经对抗验证的统计与指标代码(一致性 κ/QWK 对照 `sklearn`,Welch t/BH-FDR/Wilson 对照 `scipy`,MOTA/IDF1、CORAL 序数损失、长尾重采样),数值与权威库逐位对齐,并由 CI 持续校验。

## 🎯 设计理念

- **诚实优先** — 不编造文献、数据、出处、数据来源;核不实的明确标注"待核查",并区分"已验证"与"推测";受版权材料只保留元数据与链接。
- **能跑,不空谈** — 技能内置真实可运行的脚本、可套用的模板、完整的范例,而非一段段抽象指令。
- **对抗式自检** — 关键产出都经过独立"挑刺"和权威工具的交叉验证(统计结果对照 `scipy`/`sklearn`,对外接口逐一实测)。
- **全流程协同** — 27 个技能围绕一条科研主线衔接,共享 9 个知识库的术语、方法与投稿信息。

## 🗂️ 目录结构

```
Light/
├── skills/             # 27 个技能,每个含 SKILL.md + references + scripts/templates/examples
├── databases/          # 9 个知识库(db01–db09)
├── code_assets/        # 经对抗验证、CI 持续校验的统计与指标代码
├── assets/             # LOGO、图片
├── install.ps1 / .sh   # 一键安装脚本(幂等可重跑)
├── CONVENTIONS.md      # 全局规约(诚实底线、产出规范)
├── ROUTER.md           # 技能路由逻辑
├── AGENTS.snippet.md   # Codex 路由片段
├── CONTRIBUTING.md     # 贡献指南
├── CHANGELOG.md        # 更新日志
├── .github/            # issue/PR 模板、CI、赞助配置
└── .codex/INSTALL.md   # Codex 安装说明
```

## ❓ 常见问题

**Q:它和直接用 ChatGPT/Claude 聊有什么区别?**
A:Light 给的是能跑的脚本、能套的模板和真实范例,且有"不编造"的硬底线和对抗式自检;还能跨会话记住你的项目进度。不是一次性问答。

**Q:常驻技能为什么在 `/` 里看不到?**
A:这 10 个技能设计为后台自动生效,无需手动唤起,所以不占用 `/` 菜单。17 个手动技能则照常用 `/` 调用。

**Q:必须两端都装吗?**
A:不必。`install.ps1 -Client claude` 或 `install.sh claude` 只装一端。

**Q:会把我的数据上传到第三方吗?**
A:不会,除非任务本身需要(如检索文献会访问公开学术 API)。涉及上传的操作会提示。详见 [SECURITY.md](SECURITY.md)。

**Q:Light 会替我写论文/造数据吗?**
A:不会。它辅助你做研究、组织表达,但严守学术伦理(见 `light-research-ethics`):不造数据、不编文献、不过度包装。

## 🤝 参与贡献

欢迎修 bug、加技能、扩知识库、改文档。请先读 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [CONVENTIONS.md](CONVENTIONS.md)(尤其是诚实底线),并遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。安全问题请按 [SECURITY.md](SECURITY.md) 私下报告。

## ❤️ 支持与鼓励

Light 由一个人利用业余时间打磨。如果它帮你省下了时间、让科研更顺手,欢迎请作者喝杯咖啡——你的支持是持续更新的最大动力。

<div align="center">
<img src="assets/wechat-donation.jpg" width="220" alt="微信收款码"/>

*微信扫码,金额随意,心意已收到 🙏*
</div>

## 💬 反馈与建议

- **问题反馈 / 功能建议**:在本仓库提 [Issue](https://github.com/Light0305/Light/issues)(有 bug / 功能模板)
- **使用交流**:欢迎到 [Discussions](https://github.com/Light0305/Light/discussions)
- **改进贡献**:Fork 后提 Pull Request
- **邮件联系**:1833058953@qq.com

## 📌 引用

如果 Light 对你的研究有帮助,可按 [CITATION.cff](CITATION.cff) 引用,或在 GitHub 仓库页点击 "Cite this repository"。

## 📄 许可

[MIT License](LICENSE) © 2026 Light

---

<div align="center">
<sub>用 Light 把想法照进论文 · Made with care for researchers</sub>
</div>
