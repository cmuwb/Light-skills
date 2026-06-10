# db06 PPT 设计卡（seed）

> 学版式、配色、视觉层次，最终原创化(CONVENTIONS §5)。

## 卡片模板
```yaml
- scenario:
  theme_style:
  page_type:
  layout_structure:
  color_palette:
  font_pairing:
  visual_hierarchy:
  chart_style:
  icon_style:
  transition_style:
  speaker_notes_style:
  reuse_template_notes:
```

## 种子卡片

```yaml
- scenario: 学术答辩
  theme_style: 学术风/浅色
  page_type: 封面/目录/内容/图表/结论/致谢
  layout_structure: 顶部标题条 + 左文右图 / 居中大图
  color_palette: 白底 + 学校主色 + 深灰文字
  font_pairing: 思源宋体标题 + 思源黑体正文
  visual_hierarchy: 页标题 > 小标题 > 要点; 一页一观点
  chart_style: 简洁折线/柱状, 复用论文图并放大字号
  icon_style: 线性图标统一
  transition_style: 淡入, 克制
  speaker_notes_style: 每页 1-2 句讲稿 + 时长
  reuse_template_notes: 封面/过渡可复用; 内容页按论文章节定制

- scenario: 互联网+/挑战杯路演
  theme_style: 竞赛路演风/科技感
  page_type: 封面/痛点/方案/技术/市场/团队/规划/结论
  layout_structure: 大字标题 + 视觉冲击主图 + 数据高亮
  color_palette: 品牌主色 + 强对比强调色
  font_pairing: 粗黑体标题 + 无衬线正文, 数字超大号
  visual_hierarchy: 核心数据/卖点最大, 弱化细节
  chart_style: 信息图/对比图/增长曲线
  icon_style: 填充式彩色图标
  transition_style: 动感但不过度
  speaker_notes_style: 路演节奏, 强调价值与市场
  reuse_template_notes: 强调叙事钩子(痛点→方案→价值)

- scenario: 数据分析汇报
  theme_style: 数据分析风/浅色高级
  page_type: 封面/概览/分析/洞察/结论
  layout_structure: 图表主导 + 关键结论批注
  color_palette: 中性底 + 一组协调数据色(色盲友好)
  font_pairing: 无衬线统一, 等宽显示数字
  visual_hierarchy: 图 > 结论批注 > 细节
  chart_style: 统一调色板, 突出关键序列
  icon_style: 简洁线性图标/状态符号, 不抢图表主视觉
  transition_style: 图表先出现, 关键结论批注淡入; 避免复杂飞入
  speaker_notes_style: 先讲一句结论, 再解释图中异常/趋势与下一步动作
  reuse_template_notes: 图表风格与论文/前端统一(a07)
```

## 待补充
按用户场景补充 PPT 风格卡，沉淀可复用页面版式。
