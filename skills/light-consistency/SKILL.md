---
name: light-consistency
description: 统一风格与一致性维护。在论文、PPT、图表、代码、项目文档之间保持术语一致、视觉风格一致、逻辑线索一致、创新点表述一致（常驻，所有任务后台生效）。避免同一项目在不同材料中出现说法不一致、指标名称不统一、图表风格混乱、创新点前后矛盾、方法名称变化、数据集名称不统一、论文与 PPT 逻辑不一致、软著与系统功能不一致。
user-invocable: false
---

# 跨材料一致性维护

## 工作方式（常驻）
在任何产出材料的任务中后台运行：每生成或修改一份材料，比对项目库 db09 的"统一定义"，发现偏差即纠正或提示。

## 单一事实源：项目术语与定义表（存 db09）
借鉴 content-strategy 的"先定义后生产"：所有材料从一份定义文件派生，禁止下游各写各的。

**事实源的两种形态（同一份真相，机读 ⊃ 人读）：**
- **人读真相（每个项目必有）**：`databases/db09-projects/projects/<项目>/terminology.md`——Markdown 术语表（类别/标准叫法/缩写/英文/备注），由 a02 memory-pm 维护，是 db09 项目卡的固定组成。审计脚本可直接读它做**覆盖缺口**检测。
- **机读增强（需严格校验时再生成）**：下面三份 YAML schema 模板（`assets/`），比 Markdown 多出 `forbidden`/`confusable`/权威数值列，支撑**受控术语替换**与**指标数值冲突**检测。把项目的 terminology.md 扩写成这三份即可启用全部四类检测，仍存回该项目的 db09 目录（与 terminology.md 并列），保持 db09 是唯一物理位置。
  - **`db09_glossary.yaml`** 受控术语表：`canonical`/`aliases`/`forbidden`/`case_lock`/中英对照。
  - **`db09_method_lock.yaml`** 方法名锁定清单：`abbr`/`full`/`forbidden`/`first_use_rule`。
  - **`db09_metric_registry.yaml`** 指标登记表：`canonical`/`aliases`/`confusable`/`unit`/`decimals`/`records`(权威值)。

> `assets/` 下的三份是**空白模板/示例**；真实项目的事实源永远落在 `databases/db09-projects/projects/<项目>/`，避免"db09 指两个地方"的歧义。

维护要点：
- **方法名称**：模型/算法的统一叫法(含缩写)，列入"禁改清单"——润色/翻译不得替换。
- **数据集名称**：统一全称+简称。
- **指标名称**：统一符号与单位(如 F1 vs F-score)，连同定义与单位一并锁定。
- **创新点表述**：3 条贡献的标准措辞，论文/PPT/软著/竞赛一字对齐。
- **关键术语**：中英对照、专有名词译法、大小写与连字符(如 fine-tune 不写 finetune)。
- **视觉规范**：建议落成 DTCG/Style Dictionary 风格的命名 token——主色/语义色、字族字重、模块化字号、间距阶梯(4/8pt)、圆角阴影；论文图/PPT/前端/海报全部取同一 token 源(链 db05/db06/db07)。
- **变更广播**：定义一旦修改，立即触发对所有已产出材料的回扫，避免下游过期。

## 审计脚本：consistency_audit.py
`scripts/consistency_audit.py` 读取上述 db09 三件套，扫描一组材料文本，自动检测并**定位到 `材料:行号`** 的四类不一致，按 ERROR/WARN 分级，每条带"现状→问题→建议"，报告末尾做"条数自检"。

四类检测：
- `SUBSTITUTION` 受控术语/方法名被同义改写或写错(大小写/连字符/近义词)。
- `METRIC_NAME` 同一指标被换名(如把 F1 写成"准确率")。
- `METRIC_VALUE` 同一指标(同方法×数据集)跨材料数值不一致，或与 db09 权威值不符；位置感知，一行并列多指标/多方法也能就近配对，不串位。
- `COVERAGE_GAP` 规范术语/指标只在部分材料出现，应出现处缺席。

用法：
```bash
# 在本技能目录（skills/light-consistency/）下运行
# 真实审计
python scripts/consistency_audit.py --db09 assets \
    --materials examples/materials_paper.txt examples/materials_ppt.txt [--json out.json]
# 无参数 -> 内置合成材料自测(四类检测全触发)
python scripts/consistency_audit.py
```
退出码：发现 ERROR 返回 1(可接 CI)，否则 0。端到端实例见 `examples/worked_example.md`。
相比基准的 mermaid-syntax 单文件正则校验脚本，本脚本跨多材料做语义级一致性比对(术语/指标名/数值/覆盖)并给修正建议，能力维度更高。

## 一致性审计流程（inventory → tag → gap → fix）
借鉴内容审计(audit)四步法，对每次跨材料检查：
1. **盘点(inventory)**：逐份材料抽取关键主张（方法名、指标名+数值、创新点措辞、图表风格）成清单。
2. **打标(tag)**：每项标 一致/冲突/缺失，冲突项指向具体位置(章节/页/行)。
3. **差距(gap)**：量化覆盖率——哪些贡献点在 PPT 缺席、哪个指标只在论文出现。
4. **修正(fix)**：每条给"现状→问题→统一建议→修正后文本/配置"，不止于列问题。
**完整性强制**(借 full-output-enforcement)：逐条列全，不用省略号或"其余同理"代替；报告末尾自检"清单条数 = 实际处理条数"。

## 一致性检查维度
1. **术语一致**：同一概念全程同一叫法，跨论文/PPT/代码/文档。
2. **指标一致**：名称、定义、数值在各处相同(论文表 = PPT 图 = 摘要数字)。
3. **创新点一致**：摘要/引言/结论/PPT/申报书表述不矛盾。
4. **方法/数据集名称一致**：不中途改名。
5. **视觉一致**：论文图、PPT、前端、海报共用设计语言；逐项对照 token(主色/字体/字号/间距/圆角)而非凭感觉。
6. **逻辑线索一致**：论文叙事与 PPT 叙事、软著功能与系统实现对得上。

## 触发检查的场景
论文↔PPT、论文↔软著、系统↔软著功能说明、多版本图表、竞赛材料↔论文、代码命名↔论文符号。

## 产出
一致性检查报告（不一致清单 + 统一建议 + 修正后文本/配置）+ 更新后的术语表(db09)。

## 工具视角（具体用法）
内容层：
- **distill/polish** 改写时最易制造不一致——同义改写会把受控术语换近义词、把"F1"写成"准确率"。规则：把 db09 受控词表当"禁改清单"传入；distill/polish 视为零事实变更操作，改完必须过术语表回扫。
- **audit/critique** 提供"分维度+具体证据"评审模式：每条批评指向位置、给三段式(现状→问题→建议)，维度即上述五维。

风格层（视觉一致工程化）：
- **extract-design-system**：从现有论文图/PPT/前端反推设计语言(主色/语义色、字族字重、模块化字号、间距阶梯、圆角阴影)，归一成命名 token 写入规范。
- **Design Tokens(W3C DTCG)**：用 `$value`/`$type` 结构定义视觉 token，分组 `$type` 可继承，别名用花括号引用 `{color.brand.primary}`；复合类型 typography/shadow/border 直接描述完整样式。作为跨工具交换格式。
- **Style Dictionary(v4)**：单一 token 源经 `transformGroup`/`transforms` 输出到多平台(`css/variables`、`scss/variables`、`javascript/es6` 等)，实现"一处定义、多端一致"。注意 v4 为 ESM+异步。
- **Prettier**：统一代码格式(`.prettierrc`：printWidth/tabWidth/semi/singleQuote/trailingComma)，保证代码符号与论文符号、跨文件风格一致。
- **EditorConfig**：`.editorconfig`(root=true + glob 分节)统一缩进/换行/编码，消除 diff 噪声；其 indent 设定须与 Prettier 一致否则互相打架。
- **Mermaid**：图即代码，全项目统一方向(TD/LR)与主题；节点文字含括号/冒号/中文标点须用 `["..."]` 包裹，生成后走渲染校验。

## 衔接
服务 m07/m08/m09/m11/m15/m16/m17/a05；定义存 db09 并被所有技能读取。

## 文件清单
- `assets/db09_glossary.yaml` / `db09_method_lock.yaml` / `db09_metric_registry.yaml`：db09 单一事实源 schema 模板。
- `scripts/consistency_audit.py`：跨材料一致性审计器(四类检测+定位+修正建议+JSON 导出+自测)。
- `examples/worked_example.md`：论文 vs PPT 指标名/数值冲突的端到端实例(定位→统一→修正→回归)。
- `examples/materials_paper.txt` / `materials_ppt.txt`：配套可运行材料。

---
工具实现细节、真实配置项与端点见 `references.md`（逐工具核查笔记）。
