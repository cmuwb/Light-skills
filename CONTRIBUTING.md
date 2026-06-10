# 贡献指南 / Contributing to Light

感谢你愿意让 Light 变得更好!无论是修 bug、加技能、扩知识库还是改文档,都欢迎。
Thanks for helping improve Light — bug fixes, new skills, knowledge-base entries, and docs are all welcome.

## 一条铁律:诚实优先 / The one hard rule: honesty first

Light 最核心的价值是**可核查**。任何贡献都必须遵守 [CONVENTIONS.md](CONVENTIONS.md):

- **不编造**文献、数据、DOI、API 端点、指标数值。无法核实的标注"待核查",区分"已验证"与"推测"。
- 写进技能的 **API 端点必须 `curl` 实测过**,并记录 HTTP 状态码。
- 统计/指标代码应与权威库(`scipy`/`sklearn` 等)对齐,并自带可运行的自测。
- 受版权材料只存元数据、链接、摘要,不做违规全文收集。

> Never fabricate references, data, DOIs, endpoints, or metric values. Mark the unverifiable as "to be checked", and keep verified separate from inferred.

## 仓库结构速记 / Repo layout

- `skills/light-*/` — 28 个技能,每个一个目录,含 `SKILL.md`(+ `references.md`、`scripts/`、`templates/`、`examples/`)
- `databases/db01–db09/` — 9 个共享知识库
- `code_assets/` — 经验证的统计/指标代码
- 技能通过相对路径引用 `databases/` 与 `code_assets/`,**所以整个仓库必须放在一起**

## 改技能 / Editing a skill

1. `SKILL.md` 的 frontmatter 只需 `name` 与 `description`;**常驻(后台自动)技能保留 `user-invocable: false`**,手动技能不加。
2. `description` 要写清触发场景——模型靠它自动调用。
3. 加脚本就放 `scripts/`,自带 `--selftest` 或 `__main__` 自测,跑完不要把产物(png/pdf/csv/__pycache__)留在目录里。
4. 本地校验:`python .github/scripts/check_skills.py`。

## 加知识库条目 / Adding knowledge-base entries

按对应库的 schema 填字段(见各 `dbXX/README.md`)。期刊/方法/数据集的元数据尽量来自 OpenAlex / Crossref / DOAJ 等可核查源,并注明 `last_checked_date`。

## 提交流程 / Workflow

1. Fork → 新建分支(如 `feat/xxx`、`fix/xxx`)。
2. 提交信息讲清"做了什么、为什么"。
3. 开 PR,按模板勾选自检项。
4. CI 会校验技能 frontmatter、数据库 Markdown/YAML/README 链接与 `code_assets/` 是否可编译。

## 行为准则 / Code of Conduct

参与即同意遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。

有任何疑问:开 [Issue](https://github.com/Light0305/Light-skills/issues) 或邮件 1833058953@qq.com。
