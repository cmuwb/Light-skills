# db08 — 软著、专利与项目材料模板库

不只存模板，还总结**写作逻辑、常见错误、审查重点、高质量结构、材料间如何互相支撑、可复用范围**。服务 m15(软著专利)、m17(竞赛申报)。

## material_card schema
`material_type, required_sections, official_requirement, writing_style, common_mistakes, checklist, sample_structure, legal_risk, reuse_scope, final_review_needed`

## 数据来源
中国版权保护中心公开材料、CNIPA、WIPO、USPTO、EPO、Google Patents、The Lens、各高校创新创业/大创/挑战杯/互联网+官方通知、优秀申报书样例、学校教务处/创新创业学院模板、专利代理机构公开案例。

## ⚠ 合规（联动 a10）
- 软著/专利材料不得夸大或虚构。
- 专利最终文本应由专业代理人或法律人员审查（`final_review_needed: true`）。
- 仅学习公开模板结构，不违规收集受版权材料。

## 材料类型库

### 软件著作权
required_sections: 软件名称(全称+简称+版本) / 功能说明 / 操作说明书 / 源代码(前后30页) / 申请表 / 权属证明。
common_mistakes: 源代码页不连续、含敏感信息、版本号不一致、功能与代码不符。
checklist: □ 名称规范 □ 60页代码带页眉 □ 文档配截图 □ 完成/发表日期 □ 权属清晰。

### 发明专利
required_sections: 技术领域 / 背景技术 / 发明内容 / 附图说明 / 具体实施方式 / 权利要求书。
writing_style: 权利要求独立项求最大范围、从属项逐层限定；说明书支持权利要求。
common_mistakes: 权利要求过窄/过宽、缺实施例、创新点不清、检索不足。

### 竞赛/项目申报书
required_sections: 项目摘要 / 背景意义 / 研究内容 / 技术路线 / 创新点 / 可行性 / 研究基础 / 预期成果 / 进度 / 经费预算 / 团队分工。
common_mistakes: 创新点空泛、可行性不足、预算不合理、市场数据臆造。

种子模板见 [material_cards.md](material_cards.md)。

## 竞赛申报配套资产（服务 m17 / light-competition）
- [budget_template.md](budget_template.md) — **经费预算表模板**：科研经费支出预算表（大创/大挑，含科目+测算依据列）、已填示例、创业财务预测表（互联网+创业组，含假设登记表+三年损益+现金流转正点）、提交前自审清单。
- [case_skeletons.md](case_skeletons.md) — **优秀案例结构骨架**：互联网+创业组/创意组、挑战杯大挑三类作品、大创申报书、数模 CUMCM/MCM-ICM 的高分结构 + 评审维度 + 高分特征/常见出局点 + 评委视角自审。

## 真实资源文件
- [resources_real.md](resources_real.md) — 真实专利检索入口（Google Patents/CNIPA/Espacenet/PATENTSCOPE/PatentsView/The Lens，含 API 现状与可达性实测）、软著申请要点（中国版权保护中心流程、源代码 60 页规则）、专利文书结构与常见驳回理由、竞赛申报官方入口。
- [material_extended_cards.md](material_extended_cards.md) — 软著/专利/竞赛材料细分卡（技术交底、权利要求、专利附图、在先技术检索报告、软著说明书/源码材料、挑战杯申报书、创新大赛商业计划书等 8 卡，官方入口 HTTP 200 核验）。
