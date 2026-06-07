# db05 — 前端设计风格库

搜集主流热门前端风格，训练 a05(前端设计) 的审美、布局、配色、组件能力。**学版式逻辑，不抄袭**。

## design_card schema
`project_type, style_tag, layout_type, color_palette, font_style, component_pattern, interaction_pattern, animation_type, screenshot_reference, implementation_notes, suitable_project_scene`

## 数据来源
Mobbin、Awwwards、Dribbble、Behance、Lapa Ninja、Land-book、Godly、Siteinspire、CSS Design Awards、Pinterest、Figma Community、shadcn/ui、Tailwind UI、Vercel templates、GitHub frontend-design 类技能。

## 使用方式（重要）
不存图片本身，存**为什么好看 + 适合什么场景 + 可迁移到什么项目 + 实现需要哪些组件**。

## 风格速查

| style_tag | 特征 | 适用场景 | 实现要点 |
|---|---|---|---|
| 极简(minimalist) | 大留白、克制配色、强排版 | 学术主页、作品集 | 栅格 + 字体层次 |
| 科技感(tech) | 深色、霓虹强调色、网格/光效 | 产品落地页、答辩 | 深色主题 + 渐变 + 微动效 |
| 玻璃拟态(glassmorphism) | 半透明模糊、层叠 | 仪表盘、卡片 | backdrop-blur + 边框高光 |
| 卡片式(card) | 模块化卡片、清晰分区 | 管理系统、内容站 | 卡片组件 + 阴影层次 |
| 大屏可视化(data-screen) | 深色、高信息密度、实时图表 | 数据中台、监控大屏 | ECharts/D3 + 16:9 栅格 |
| 农业智慧化(agri-tech) | 绿色系、自然质感、数据+地图 | 智慧农业项目 | 绿色调色板 + 地图组件 |
| 医疗科技(medical) | 蓝白、干净、信任感 | 医疗平台 | 蓝色系 + 高可读性 |
| 移动端(mobile) | 拇指可达、底部导航 | App 演示 | 移动栅格 + 手势 |

## 设计 token 化
每个项目沉淀一套 tokens(色/字/间距/圆角)，由 a07 跨材料统一(链 Style Dictionary/Design Tokens)。

种子卡片见 [design_cards.md](design_cards.md)。

## 真实资源文件
- [resources_real.md](resources_real.md) — 真实可用前端资源清单（shadcn/ui、Tailwind、ECharts、Awwwards、Mobbin 等，带链接与许可）+ 科研场景 design_card。
