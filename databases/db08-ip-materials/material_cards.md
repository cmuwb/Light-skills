# db08 材料模板卡（seed）

> 软著/专利材料不得虚构或夸大；专利最终文本须由专业代理人审核(final_review_needed)。联动 a10。

## 卡片模板
```yaml
- material_type:
  required_sections:
  official_requirement:
  writing_style:
  common_mistakes:
  checklist:
  sample_structure:
  legal_risk:
  reuse_scope:
  final_review_needed:
```

## 种子卡片

```yaml
- material_type: 软件著作权申请
  required_sections: [软件名称, 功能说明, 操作说明书, 源代码(前30+后30页), 申请表, 权属证明]
  official_requirement: 中国版权保护中心; 源代码连续带页眉(软件名+版本); 文档配界面截图
  writing_style: 客观描述功能与操作, 不夸大
  common_mistakes: [代码页不连续, 含敏感信息/密钥, 版本号不一致, 功能与代码不符, 截图与说明不符]
  checklist: ["名称规范(全称+简称+版本)", "60页代码带页眉", "操作手册配截图", "开发完成/首次发表日期", "权属清晰", "功能模块说明完整"]
  legal_risk: 软件须真实存在, 材料不实将影响登记效力
  reuse_scope: 功能说明可与系统设计(a04)/论文系统描述复用
  final_review_needed: false(建议自查, 高校可咨询科技处)

- material_type: 发明专利
  required_sections: [技术领域, 背景技术, 发明内容, 附图说明, 具体实施方式, 权利要求书]
  official_requirement: CNIPA; 权利要求得到说明书支持; 附图符合制图规范
  writing_style: 独立权利要求求最大保护范围, 从属权利要求逐层限定; 说明书充分公开
  common_mistakes: [权利要求过宽/过窄, 缺实施例, 创新点表述不清, 检索不足导致新颖性问题, 公开不充分]
  checklist: ["可专利性初判(新颖/创造/实用)", "现有技术检索(Google Patents/CNIPA/Espacenet/Lens)", "至少一个实施例", "附图与说明书一致", "权利要求层次清晰"]
  legal_risk: 权属(职务发明)、保护范围理解错误风险高
  reuse_scope: 技术方案可与 m05 方案/a03 实现/论文方法复用
  final_review_needed: true(必须专业代理人/法律审核)

- material_type: 竞赛/项目申报书(大创/挑战杯/互联网+)
  required_sections: [项目摘要, 背景意义, 研究内容, 技术路线, 创新点, 可行性分析, 研究基础, 预期成果, 进度安排, 经费预算, 团队分工]
  official_requirement: 按各校/各赛事官方通知模板
  writing_style: 突出创新与价值, 逻辑闭环, 数据支撑真实
  common_mistakes: [创新点空泛, 可行性论证不足, 预算不合理, 市场数据臆造, 团队分工与内容不匹配]
  checklist: ["创新点可量化", "技术路线与研究内容对应", "预算分类合理", "市场数据可核查(创业类)", "预期成果具体"]
  sample_structure: 各赛事高分结构骨架见 case_skeletons.md(互联网+创业/创意组、挑战杯大挑三类、大创申报书、数模CUMCM/MCM); 经费预算与创业财务预测模板见 budget_template.md
  legal_risk: 商业数据不得臆造
  reuse_scope: 与论文(m07)/PPT(m16)/软著专利(m15)联动
  final_review_needed: false(建议导师/指导老师审阅)
```

## 配套资产
- [budget_template.md](budget_template.md) — 经费预算表模板：科研经费支出预算表(大创/大挑)+已填示例+创业财务预测表(互联网+创业组,含假设登记表)+自审清单。
- [case_skeletons.md](case_skeletons.md) — 各赛事高分材料结构骨架+评审维度+高分特征/常见出局点(互联网+、挑战杯大挑、大创、数模)。

## 待补充
后续可按用户具体参赛类型补充更细的官方模板差异(以当届官方压缩包为准, 不缓存受版权原文)。
