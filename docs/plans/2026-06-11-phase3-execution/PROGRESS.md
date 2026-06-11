# 第三期执行进度台账（PROGRESS）

> 每轮收尾时由执行模型更新本文件（总纲 §5 第 6 步）。新对话接手时**先读本文件**再读对应轮次文件。
> 状态取值：`未开始 / 进行中 / 已完成 / 部分完成（见偏差）`。

## 轮次状态

| 轮 | 名称 | 状态 | 开始 | 完成 | commit 区间 | CI |
|---|---|---|---|---|---|---|
| R1 | P0 与卫生修复 | 已完成 | 2026-06-11 | 2026-06-11 | `1520d93..056165c`（8 commit） | 本地 7 门禁全绿；待推送确认 CI |
| R2 | 会话衔接协议 | 已完成 | 2026-06-11 | 2026-06-11 | `dd00835..7b60de3`（5 commit） | 绿（run 27341424084 三任务全 success） |
| R3 | 中文链路专项 | 已完成 | 2026-06-11 | 2026-06-11 | `89627e2..74a1bb0`（4 commit） | 绿（run 27346343103 三任务全 success） |
| R4 | 合规与生态吸收 | 未开始 | | | | |
| R5 | 资产补全 | 未开始 | | | | |
| R6 | PPT 生图流水线 | 未开始 | | | | |
| R7 | 横切机制与瘦身 | 未开始 | | | | |
| R8 | CI 门禁扩建 | 未开始 | | | | |
| R9 | 数据库规模化（批1/批2/批3） | 未开始 | | | | |
| R11 | 行为评测与自动化闭环 | 未开始 | | | | |
| R12 | 安全、领域与微缺口增补 | 未开始 | | | | |
| R10 | 门面工程与发布（收官） | 未开始 | | | | |

## 基线度量（首次用到时填，后续轮引用）

- 常驻 11 技能 SKILL.md 总行数基线（R7 开工时 `wc -l` 量取并记录在此）：＿＿＿
- db05/db06/db07 真实卡数基线：约 1-2 / 1-2 / 2（审计 2026-06-11 口径）
- ROUTER_EXAMPLES 必覆盖基线：7/28

## 偏差日志（只追加，不删改）

> 格式：`- [日期] R几.第几项 — 计划说什么 / 现实是什么 / 怎么处理的（自行修正|降级|跳过待用户）`

- [2026-06-11] 总纲§5 — 计划写校验器在 `tools/`；现实在 `.github/scripts/`（check_*.py + run_skill_selftests.py）。自行修正：全程用 `.github/scripts/` 路径，后续轮同。
- [2026-06-11] 总纲§5 — selftest 在 Windows 默认 GBK 控制台打印 `✓` 抛 UnicodeEncodeError（退出码1，非测试失败，45 脚本全 PASS）。处理：全程用 `PYTHONUTF8=1` 跑门禁；本身是真实可移植性隐患，但修 runner 编码属 R8 CI 范畴，本轮未改 runner，仅记录。
- [2026-06-11] R1.1 — 计划点名限流口径在 m04/m13/m10/a09；现实具体数字在 m01(literature-search)、m03(idea-generation)、venue-matching、citation、ip-application。按现实处理：m01 设真相源，其余全部指向并删数字。另发现 ip-application 有 2026-06-06 curl 实测"匿名仍 200"与官网"需 key"冲突——联网核实官网现行需 key+$1/天，保留实测为诚实存档并判定为过渡期现象。附带修正：OpenAlex 文档域名已迁 docs.openalex.org→developers.openalex.org，相关链接同步。
- [2026-06-11] R1.2 — 计划说 MDPI 栏宽"以 m09 SKILL.md 已核实表格为准"；现实 m09 表无 MDPI 行，真实来源是 m11(figure-planning) references.md「出版商图宽核查表」MDPI 行(170mm,⚠️付费墙未实测通行值)。按现实处理：figure_export.py mdpi 键 note 注明来源为 m11，verified=False。
- [2026-06-11] R1.3 — 联网核实 Science 三档为 5.5/12/18.3cm，即双栏 120mm，121mm 系换算误差。额外发现 science.mplstyle 把 121mm 写死进默认 figsize(真实出图偏差)，一并订正为 120mm(4.724in)。science.org 仍 403，数值经 WebSearch 多源一致核实。
- [2026-06-11] R1.4 — m05 模板实际文件名是连字符 experiment-matrix.md，与 orchestrator 下划线契约不符；按计划统一为下划线(git mv + 3 处引用)。仓库内 m 编号与计划标签偶有错位(如 figure-planning 内部自称 m11 指执行器)，按文件路径作业，不按编号。
- [2026-06-11] R1.5 — 计划假设 11 个 SKILL.md 有 `../../docs/design`/CONVENTIONS 硬路径会断；现实只有 orchestrator:121 一处 `../../docs/design` 硬链接(已改弱引用)，其余 16 处 CONVENTIONS 均为纯文字提及(不算断链)。仍按计划把 4 文档随装链接(sh symlink / ps1 hardlink)并加校验，使纯文字引用装后可达。已在临时/真实 ~/.claude 实测链接生成成功、内容可读。
- [2026-06-11] R1.5 — install.ps1 原为纯 ASCII；首次加中文注释触发 PowerShell 5.1 GBK 解析错误(真实 Windows 用户会中招)。修正：install.ps1 注释保持 ASCII-only。
- [2026-06-11] R1.6 — 计划假设 README:9 写"三端(Claude/Codex/Hermes)"与 install 两端冲突；现实 README 已是"Claude Code 与 Codex"两端表述，无三端硬冲突。曾按方案 B 在中英 README 补 Hermes 说明，**后经用户确认对外只支持两端，已删除该 Hermes 段**（见用户决策项，此项关闭，install 不加第三目标）。
- [2026-06-11] R1.8 — 计划说 a03 已实测 v6；现实 a03(backend-coding)确已全 v6 且有 GitHub API 实测记录。真正残留 v4/v5 在 system-design(a04 模板+references)与 tool-selection(references+detect_stack.py fixture)，已升 v6 并指向 a03 真相源。
- [2026-06-11] R1.10 — 计划说无参 selftest 落 5 PNG 到技能根；现实 `--selftest` 路径已用 tempfile(不污染)，真正污染是"无参无 JSON 的 demo 路径"(tag=selftest 落 CWD)。修正该 demo 路径改临时目录，并把 tag 由 selftest 改 demo。
- [2026-06-11] R1.12 — .gitignore 已含 __pycache__//*.py[cod]，无 tracked 缓存；out_multipanel 由 examples/example_matplotlib_multipanel.py 落 HERE 造成。改为默认临时目录(--outdir 可选)，删残留 PNG/PDF，清本地缓存目录。
- [2026-06-11] R2 全程 — 计划要求 a02 新模板放 templates/、细则下沉 references/；orchestrator §5 引用这些跨技能文件时，check_skill_links.py 会把裸 `templates/x.md` / `references/x.md` 反引号路径当成 orchestrator 自身内部路径校验而报缺失。处理：orchestrator 内一律写全 `light-memory-pm/templates/...`、`light-memory-pm/references/...` 前缀，链接门转绿。后续轮跨技能引用模板/参考时同此写法。
- [2026-06-11] R2.4-4 — 计划只说 a06 scaffold 纳入 `.light/`；执行中明确 `.light/`（passport + handoff 卡）是跨会话续跑真相源，应**纳入版本控制而非忽略**，故在 python-research.gitignore 末尾加注释显式声明不忽略 .light/，并在 scaffold selftest 断言两目录生成。
- [2026-06-11] R2.5 演练 — 示例项目 dairygoat 演练前无 `.light/`（轻项目靠 db09 卡承载）。按协议新建 .light/handoff 并落 S01/S02 两张真实卡作为工作示例；B 会话恢复用 `pytest tests/test_infer_track.py`(2 passed)实证 S01"已完成"声明无损，非口头比对。
- [2026-06-11] R3.5 — 计划说把实测栏宽写入 db01"新增字段/列"；现实 venues.csv 为固定 19 列 schema，check_databases.py 按列校验，新增列会破坏既有 332 卡。按现实处理：栏宽实测值追加进末列 catch-all `risk_note`（带来源+日期+方法），不改 schema，与 README"新增条目追加"惯例一致。
- [2026-06-11] R3.5 — 农业机械学报(j-csam.org)版心栏宽未取得：站点 PDF 入口返回反爬 JS 守卫页(`_guard/html.js`，59 字节)而非 PDF，三次重试均被拦。按诚信纪律标 GAP、db01 该刊栏宽留"待核查"，不从记忆/英文刊类比硬填。其余三刊(农业工程学报/中国农业科学/作物学报)均从发表 PDF 实测成功。
- [2026-06-11] R3.2 — 可选项 lint_gbt7714.py(GB/T 7714 中文条目 lint 脚本)本轮未实现：核验兜底以"人工浏览器比对检索结果页"为主路径(CNKI 执行环境直连不通，见验证日志§4)，脚本化 lint 价值有限且会新增 selftest 负担，判定为非必需，降级跳过。如后续要做，归 R8 CI 门禁范畴。

## 留给下一轮的话

> 每轮收尾写 1-3 行：下一轮要注意什么、有什么现场发现。

- R2 注意：orchestrator §5 已有 Handoff 格式、§0 断点恢复协议、§2 契约表(本轮已声明 CONVENTIONS §6.1 为真相源)；R2 收编 handoff 为单一口径时直接基于现有 §5，勿另起一套。
- R3 注意：会话衔接协议已就位——CONVENTIONS §9 全局纪律 + a02 两件套模板/细则 + orchestrator §5 收编 + a06 scaffold .light/ + 路由触发 + README FAQ + A/B 演练（_verification_log/session_handoff_drill.md）。后续任何轮长任务收尾都应主动留衔接卡 + 打印启动提示词（含执行本计划的轮间交接，11 号文件模板可与 handoff_prompt.md 互参）。
- R3 注意：跨技能引用别的技能的 templates//references/ 文件，反引号路径必须带 `light-<skill>/` 前缀，否则 check_skill_links.py 误判为本技能内部路径报缺失（R2 已踩，见偏差日志）。
- R3 注意：中文链路专项独立于 R2，无新增硬依赖；ROUTER_EXAMPLES 现 47 例(R2 +3 主动交接正例)，check_entry_docs 必覆盖集仍含 light-orchestrator。
- R4 注意：R3 未增减技能数(仍 28)、未加脚本、未动路由，故 WHATS_INCLUDED/MODE_REGISTRY/ROUTER_EXAMPLES 本轮无需同步(check_entry_docs 已绿)。R4 若收编外部生态技能会动技能数，记得四件套(README/ROUTER/MODE_REGISTRY/ROUTER_EXAMPLES)同步 + ROUTER_EXAMPLES 必覆盖集。
- R4 注意：db01 venues.csv 是 19 列固定 schema，任何"补字段"需求一律追加进 risk_note catch-all，勿加列(check_databases 按列校验 332 卡)。中文刊实测栏宽语义=版心栏宽(非官方图宽硬规格)，已在 db01 备注注明，引用时别当成出版商 author-guide 的 figure width。
- R4 注意：EI 收录权威源=Engineering Village 的 Compendex Source List(从产品页 View source list 现取当期 Excel，CDN 链接随版本变动，勿硬编码)；m13 已禁引第三方"EI 源刊"站。
- 全程门禁请带 `PYTHONUTF8=1`（Windows GBK 否则 selftest runner 打印 `✓` 报 UnicodeEncodeError，非测试失败）。校验器在 `.github/scripts/`，非 `tools/`。
- 安装链接已扩到 4 文档；R2 若动 CONVENTIONS/ROUTER 结构，记得 install 与 check_installation_assets.py 已对这些文件名有依赖。

## 用户决策项登记（出现一个登记一个，R10 统一找用户拍板）

- [ ] skills.sh 发布与否（审计 I-5）
- [ ] db08 脱敏高分申报书全文样例来源（用户提供或公开样例，R9）
- [x] Hermes 安装目标方案确认（2026-06-11 用户确认：对外只支持 Claude Code 与 Codex 两端，Hermes 不单独支持。已删除中英 README 的 Hermes 说明段；install 脚本不加第三目标。此项关闭。）
