# 更新日志 / Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 与 [语义化版本](https://semver.org/lang/zh-CN/)。
All notable changes are documented here.

## [Unreleased]

### Added
- 仓库专业化:`.github/`(issue/PR 模板、CI、FUNDING)、`CONTRIBUTING.md`、`CODE_OF_CONDUCT.md`、`SECURITY.md`、`CITATION.cff`、本 `CHANGELOG.md`。
- CI 工作流:校验所有技能的 `SKILL.md` frontmatter、数据库 Markdown/YAML/README 链接,并编译校验 `code_assets/` 脚本。

### Changed
- 重写中英双语 README,按"17 手动 / 11 常驻"同步技能总览。
- 将 `light-orchestrator` 纳入常驻技能计数与 README 说明,并同步技能数量为 28。

## [1.0.0] - 2026-06

### Added
- 28 个技能,覆盖科研全流程:文献调研 → 数据 → 创新 → 方案 → 实验 → 分析 → 写作润色 → 图表 → 排版 → 投稿 → 返修 → 软著专利 → PPT → 竞赛。
  - **17 个手动技能**(`/` 可调用):literature-search、data-engineering、idea-generation、idea-critique、research-plan、result-analysis、paper-drafting、paper-polishing、figure-planning、figure-drawing、citation、typesetting、venue-matching、review-rebuttal、ip-application、slides、competition。
  - **11 个常驻技能**(后台自动):file-reading、memory-pm、orchestrator、backend-coding、system-design、frontend-design、project-structure、consistency、self-review、tool-selection、research-ethics。
- 9 个共享知识库(`databases/db01–db09`):期刊会议、模板、方法、数据集、设计系统、幻灯主题、科研图表、知识产权与竞赛、项目状态。
- `code_assets/`:经对抗验证的统计与指标代码(κ/QWK、Welch t/BH-FDR/Wilson、MOTA/IDF1、CORAL 序数损失、长尾重采样),与 `scipy`/`sklearn` 逐位对齐。
- 双端安装脚本 `install.ps1` / `install.sh`(Claude Code 与 Codex)。
- 全局规约 `CONVENTIONS.md` 与技能路由 `ROUTER.md`。

[Unreleased]: https://github.com/Light0305/Light/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Light0305/Light/releases/tag/v1.0.0
