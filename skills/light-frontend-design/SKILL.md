---
name: light-frontend-design
description: 独特吸睛、审美好、有特色、美观全面的前端设计。当任务涉及前端界面、项目展示页、系统演示、大屏可视化、可视化平台、微信小程序 UI、移动端界面、设计系统、Tailwind v4、shadcn/ui、Next.js、React、Vite、可访问性、动效、重设计审计时使用。不只是能用，而是好看、统一、清晰、有亮点、有视觉记忆点，适合展示/答辩/演示/落地。按主题选风格：科技感、学术感、农业智慧化、数据可视化、极简、玻璃拟态、卡片式、大屏、管理系统、移动端、小程序等。
user-invocable: false
---

# 有审美的前端设计

## 先定设计方向（写码前必答四问，来自 frontend-design skill）
1. **Purpose**：解决什么问题、谁在用、什么场景(答辩/大屏/后台)。
2. **Tone**：从基调谱系选一个并押注到底——科技/学术/农业智慧化/医疗/极简/玻璃拟态/卡片/大屏/管理系统/移动端，或 editorial/brutalist/luxury/organic。先 web 搜索核实涉及的具名产品/品牌(10 秒搜索胜过 1-2 小时返工)。
3. **Constraints**：框架、性能、可访问性、信息密度。
4. **Differentiation**：一个会被记住的唯一视觉/交互记忆点(不是堆特效)。
据此定 **设计语言**：调色板(主/辅/强调/中性) + 字体系统 + 间距栅格 + 圆角阴影 + 图标风格，落到 Design Tokens，登记 db05。设计长在已有语境(品牌/代码库/UI kit/真实截图)上而非凭空造。简报太空(如"做个好看的")时进 Advisor 模式：从风格库提 3 个差异化方向让用户选，再押注其一(canvas-design)。涉及品牌则先按 Core Asset Protocol 收集 logo/产品图/UI 截图/品牌色字，写入 brand-spec.md 当一等公民。
设计系统持久化：用一个全局真相源(如 MASTER.md/design tokens)+ 页级覆盖文件(页文件覆盖全局，无页文件则用全局)，避免跨页风格漂移(ui-ux-pro-max)。

## 设计原则（可量化）
- 视觉层次清晰，留白充足，对齐严格；"主色 + 锐利强调色" 优于均匀分布的怯懦调色板。
- 字体：避开 Inter/Roboto/Arial/系统字体，展示字配精炼正文字，pair 出个性。
- 一致性：组件复用、token 化、风格统一(a07)；用 CSS 变量承载主题。
- 可访问性(WCAG 2.1 AA)：正文对比 ≥4.5:1、大字 ≥3:1、UI 组件 ≥3:1；键盘可达 + 焦点态可见；颜色不作唯一信息载体；图片有意义 alt；尊重 prefers-reduced-motion。
- 克制动效：HTML 优先纯 CSS、React 用 Motion/GSAP；一次编排良好的页面载入 + 错峰揭示(animation-delay) > 散落微交互；hover/交互过渡 150-300ms。
- **反 AI-slop 禁令**：紫/粉渐变配白底、emoji 当图标(用 SVG: Lucide/Heroicons)、rounded-card-左边框、gradient-orb 代表 AI、CSS 剪影冒充产品图、千篇一律模板布局。
- 可调三旋钮(taste-skill)：VARIANCE(布局实验度)/MOTION(动效深度)/DENSITY(每屏信息量)，按场景拨——大屏调高 DENSITY，落地页调高 VARIANCE，后台调低两者。

## 技术实现（按需，见 a09）
- **框架 Next.js**：默认用 Server Components(零客户端 JS)，按需 `"use client"` 并检查边界位置避免膨胀 bundle；loading.tsx + Suspense 做流式、并行取数避免瀑布；next/font 防 layout shift、`<Image>` 防 CLS+WebP；Server Actions 内逐个鉴权、DB 访问放 server-only 层；request-time API(cookies/searchParams)会把路由打入动态渲染，需 Suspense 包裹。上线前 `next build` + Lighthouse + @next/bundle-analyzer。
- **组件 shadcn/ui**：`npx shadcn@latest init`(选 -t 框架 / -b radix / --css-variables)生成 components.json，`add [component]` 把源码拷进项目自行维护；主题走 CSS 变量。源码归你，升级需手动 diff。
- **样式 Tailwind v4**：CSS-first(`@import "tailwindcss"`)，@theme 暴露 token 为 CSS 变量；变体可叠(dark:/sm:/group-hover:/data-*:)，移动优先(sm=40rem)；复用用组件/循环而非滥抽 class；注意 class 顺序不决定优先级(样式表靠后者胜)。
- **组件 API 设计(vercel-composition-patterns)**：按优先级修——先架构(别用布尔属性定制行为，用组合 `architecture-avoid-boolean-props`；复杂组件用 compound + 共享 context `architecture-compound-components`)，再状态(状态上提到 Provider 供兄弟共享，只暴露 `{state, actions, meta}` 泛型接口隐藏实现)，最后实现细节(显式变体 PrimaryButton/GhostButton 优于 primary/secondary 布尔；children 优于 renderX props)。典型重构：Toggle 一堆布尔 → ToggleProvider + Toggle.On/Toggle.Off；Modal → Modal/ModalHeader/ModalBody + 共享 open/close context。React 19+ 才用 use() 替代 forwardRef/useContext。
- **移动端**：触控目标 iOS ≥44pt / Android ≥48dp；正文 ≥16；导航 iOS 底 tab(3-5)、Android bottom nav/FAB；交互元素带 accessibilityLabel/Role。
- **微信小程序 UI**：移动优先、`rpx`、安全区、首屏轻、tabBar 3-5 项；简单 tab 可用 text-only custom tabBar；组件库在 TDesign/Vant/WeUI/Ant Design Mini/NutUI Taro/custom 中选一条，不混搭。
- **可视化**：ECharts/D3/Plotly/大屏方案，色板统一、信息密度与可读性平衡。
- 参考实践见 references.md 与 `references/ecosystem-2026.md`：frontend-design、web-design-guidelines、ui-ux-pro-max、canvas-design、taste-skill、shadcn、Tailwind、Next.js 等。

## 灵感来源（学版式不抄袭）
- **热门 skill 雷达**：需要更新技能或选择外部设计能力时，先看 `references/ecosystem-2026.md`，优先吸收官方/高安装量/可验证的 workflow，而不是安装未知低信号包。
- **Mobbin**：真实生产 App(iOS/Android/web)的截图与用户流程——定信息架构/交互顺序前，先找 2-3 个同类真实 flow 对照。
- **Awwwards**：高水准网页创意，并直接借用其评审 rubric 自评(见下)。
- 其余：Dribbble、Behance、Land-book、Godly、Siteinspire、Figma Community、Tailwind UI、Vercel templates。总结"为什么好看、适合什么场景、需要哪些组件"，沉淀进 db05。
- **image-to-code 三段法(taste-skill)**：拿不准视觉方向时，先 Generate(出参考板/hero 图)→ Analyze(拆版式/字体/间距/动效线索)→ Implement(照参考帧出码)，比直接凭空写更稳。

## 可数 checklist（机械逐条判 Pass/Fail，见 scripts/audit_checklist.py）
不靠「看着不错」，靠数数。给页面 section/nav/hero/bento 加轻量 `data-*` 标注后跑脚本：
- **R1 eyebrow 实例 ≤ ceil(sectionCount/3)**：eyebrow 是稀缺强调，不是每段都配。
- **R2 连续 image+text split ≤ 2**：超过 2 段并排「图+文」就是布局偷懒。
- **R3 ≥8 sections 时 ≥4 个 layout family**（hero/split/bento/full/grid/stack…）：杜绝通篇一种版式。
- **R4 hero subtext ≤20 词且 ≤4 行**：首屏副文案克制。
- **R5 nav 单行且 ≤80px**：导航不臃肿。
- **R6 bento N 内容 = N 格**：不留空格、不溢出。
跑法：`cd skills/light-frontend-design && python scripts/audit_checklist.py`（自带 GOOD/BAD 合成自测）。

## 反 AI-tell 黑名单（机械可查，见 scripts/ai_tell_lint.py）
这些是「机器生成的破绽」，逐条用 linter 扫源码，命中即改：
- **T1 scroll cue**：禁 "scroll down/to explore"、hero 处弹跳 chevron/mouse 提示。
- **T2 section-numbering eyebrow**：禁把 "01 /"、"02."、"(03)" 当装饰性段落编号塞进 eyebrow。
- **T3 版本/Made-with 页脚**：禁 "v1.0.0"、"Made with love"、"Powered by <generic>" 填充式页脚。
- **T4 em-dash（—）**：禁用 em-dash 作正文标点（LLM 著名 tell），改用逗号/分句重写。
跑法：`python scripts/ai_tell_lint.py`（自带 DIRTY/CLEAN 自测）。

## 字体池与禁用清单（见 references/fonts-and-colors.md）
- **Sans display 默认池**：Geist / General Sans / Satoshi / Clash Display / Cabinet Grotesk（Space Grotesk 可用但已过度收敛，非必要不选）。
- **配对池**：display↔body 具名组合表（如 Clash Display + Geist、Cabinet Grotesk + Satoshi）。
- **Named banned serif**：禁 Fraunces、Instrument Serif（已成 AI-tell）。
- **禁用色族（连 hex）**：premium-consumer 套路「米色(#F5F0E8 族) + 黄铜(#B08D57 族) + 酱黑(#1A1714 族)」整族禁用；外加紫/粉渐变配白底。

## brief → 官方设计系统映射（见 references/design-systems-map.md）
按 brief 信号选**唯一一套**：Fluent(Office/Teams) / Carbon(数据后台) / Polaris(电商) / Atlaskit(协作) / Primer(devtool) / govuk-frontend(英政府) / USWDS(美政府) / Radix(自建底座)。
一仓一套、版本固定（表内 npm 包名与 latest 版本号均经 `curl registry.npmjs.org` 实测 HTTP 200）。

## redesign 审计协议（见 references/redesign-audit.md）
改造已有项目：detect(preserve vs overhaul) → audit 4 轴(Layout/Spacing/Hierarchy/Styling) → preservation rules(守住 IA/品牌/已达标无障碍) → modernisation levers(可放心拉动项) → 改造 vs 重做决策树。

## 可运行代码骨架（assets/，含 prefers-reduced-motion + cleanup）
直接拷进 Next.js client component 或 Vite+React 项目：
- `assets/gsap-sticky-stack.tsx` — GSAP ScrollTrigger 粘性堆叠卡片（gsap.context + ctx.revert 清理）。
- `assets/gsap-horizontal-pan.tsx` — 纵向滚动驱动横向 pan，pin+scrub，reduced-motion 回退原生 overflow。
- `assets/motion-scroll-reveal.tsx` — framer-motion 错峰滚动揭示，useReducedMotion 关动效，observer 自动清理。

## 自评 rubric（交付前必过）
- **Awwwards 维度**：Design 40% / Usability 30% / Creativity 20% / Content 10%，给自己打分，低于 6.5 重做(Awwwards 中 6.5+ 才得 Honorable Mention，开发奖需 >7)。
- **可执行 checklist**：不用 emoji 当图标；所有可点元素 cursor-pointer；hover 态平滑过渡 150-300ms；浅色文字对比 ≥4.5:1；键盘焦点态可见；尊重 prefers-reduced-motion；响应式断点 375/768/1024/1440px 全测；制品在真实浏览器干净加载。
- **机械门禁（必须全过）**：`python scripts/audit_checklist.py` 6/6 + `python scripts/ai_tell_lint.py` CLEAN。

## 场景适配
- **答辩/演示**：重展示力、首屏冲击、核心数据突出。
- **数据平台/大屏**：信息密度与可读性平衡、实时感、统一色板。
- **落地系统**：可用性 > 炫技，管理系统风规范化。

## 产出
可运行前端代码 + 设计说明(风格/色板/字体/组件清单) + 截图。设计系统登记 db05 与 db09。

## 衔接
数据接口对接 a04；与 PPT(m16)/论文图(m11) 视觉风格协调(a07)；无鉴权接口风险提示(security_awareness)。

---
逐工具核查笔记(真实端点/命令/参数/坑)见同目录 references.md。
热门技能/前端栈版本快照见 `references/ecosystem-2026.md`。
机械门禁脚本见 scripts/；可运行代码骨架见 assets/；字体色彩/设计系统/redesign 协议见 references/ 目录。
