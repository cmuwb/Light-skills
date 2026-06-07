# db05 前端设计卡（seed）

> 存"为什么好看 + 适合场景 + 可迁移项目 + 实现组件"，不存图片本身。学版式不抄袭(CONVENTIONS §5)。

## 卡片模板
```yaml
- project_type:
  style_tag:
  layout_type:
  color_palette:        # 主/辅/强调/中性
  font_style:
  component_pattern:
  interaction_pattern:
  animation_type:
  screenshot_reference: # 来源链接(仅元数据)
  implementation_notes:
  suitable_project_scene:
```

## 种子卡片

```yaml
- project_type: 数据可视化大屏
  style_tag: 科技感/深色
  layout_type: 16:9 三栏网格 + 中央主图
  color_palette: 深蓝底 #0A1A2F / 青强调 #2EE6D6 / 橙警示 #FF8A3D / 浅灰文字
  font_style: 无衬线(数字用等宽), 大号指标
  component_pattern: 指标卡 + 实时折线 + 地图热力 + 排行榜
  interaction_pattern: 自动轮播 + 悬停明细
  animation_type: 数字滚动 + 渐入
  implementation_notes: ECharts/D3 + CSS Grid; 注意投影对比度
  suitable_project_scene: 智慧农业/监控/竞赛答辩大屏

- project_type: 学术个人/项目主页
  style_tag: 极简/浅色
  layout_type: 单列居中 + 充足留白
  color_palette: 白底 + 单一强调色 + 深灰文字
  font_style: 衬线标题 + 无衬线正文, 强字号层次
  component_pattern: 论文列表卡 + 顶部导航 + 锚点
  interaction_pattern: 平滑滚动 + 锚点高亮
  animation_type: 克制(淡入)
  implementation_notes: Next.js + Tailwind; 可用 shadcn 卡片
  suitable_project_scene: 论文项目展示/作品集

- project_type: 管理/分析系统
  style_tag: 卡片式/玻璃拟态可选
  layout_type: 侧边栏 + 顶栏 + 内容区卡片网格
  color_palette: 浅灰底 + 品牌主色 + 状态色(成功/警告/危险)
  font_style: 无衬线, 表格密排
  component_pattern: 侧导航 + 数据表 + 筛选器 + 图表卡 + 模态框
  interaction_pattern: 分页/筛选/排序 + 表单校验反馈
  implementation_notes: shadcn/ui + Tailwind + ECharts; token 化主题
  suitable_project_scene: 科研数据平台/软著系统作品
```

## 待补充
按用户项目主题补充风格卡，沉淀可复用的设计 token。
