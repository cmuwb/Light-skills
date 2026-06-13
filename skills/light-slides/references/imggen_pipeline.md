# imggen-enhanced 五阶段生图流水线（m16 light-slides 核心资产）

本文件是 m16 `imggen-enhanced` mode 的完整规程。SKILL.md 正文只放两 mode 分流与触发，细节全在此（常驻瘦身纪律）。
配套脚本：`scripts/imagegen.py`（三后端封装）、`scripts/assemble_from_spec.py`（重组装配）；契约模板 `templates/deck_spec.yaml`。
API 端点/参数实测真相源：仓库根 `_verification_log/R6-imggen-api.md`（改端点同步那里 + references.md + imagegen.py 常量）。

## 0. 这条管线解决什么 / 不碰什么

**核心思路**：先出每页详细大纲（每要素的位置与风格）→ 生图模型逐页生成**整页视觉稿**（仅作设计参考，不进成品）→ 把版式**超细拆解为独立元素**，按类型分流（图标/插画用生图模型**单独重生成**为透明 PNG，数据图走 m11 真数据，文本/表格走 python-pptx 原生）→ **重新排版**装回，产出**可编辑** pptx。

**与「贴图假 PPT」的本质区别**：整页视觉稿**绝不被贴进成品**；它只用来审版式美感。成品里每个元素都是独立可编辑对象。

### 三条硬边界（与 m11 figure_integrity、a10 research-ethics 互引，红线）
1. **数据图永不生图**——折线/柱状/混淆矩阵/显微/凝胶等一律由 m11/m06 matplotlib 真数据出图。生图模型会编造数据，违反诚实底线。
2. **论文图链路（m09/m11）严禁生图**——Nature/Science/Elsevier 三家头部出版商明令禁止 AI 生成论文图像（m11 `references/figure_integrity.md`「AI 生成图像政策」节为真相源）。本管线产物**只服务 PPT/路演/前端**。
3. **文本永不烤进图**——所有文字以 python-pptx 原生文本框落地，字体/字号/颜色受 spec 控制；否则"可编辑"是假的。生图模型渲染文字必出乱码，更不能让它写字。

> 三处互引锚点（可 grep）：m16 此文件 + references.md ↔ m11 figure_integrity「与 R6 生图流水线的边界」节 ↔ a10 SKILL.md 署名/AI 政策段。

## 1. 五阶段总览

```
Stage A 大纲卡(deck_spec.yaml)   ── 契约，先过大纲审
   ↓
Stage B 整页视觉稿(visual_draft/) ── 仅设计参考，不进成品
   ↓
Stage C 元素化拆解(assets_gen/)   ── 按 type 分流，逐元素独立生成
   ↓
Stage D 重组装配(assemble_from_spec.py) ── 产出可编辑 pptx
   ↓
Stage E QA 循环                   ── 文本未栅格化检查 + 风格一致性人审
```
无生图 key 时：Stage B/C 的生图元素降级为占位 PNG（imagegen.py mock 后端 PIL 现画），A/D/E 全程可离线走通——这是 R6.6「无 key 也必须过」的装配链。

## Stage A | 大纲卡（deck_spec.yaml）——整条流水线的契约

每页一张结构卡。模板见 `templates/deck_spec.yaml`，字段语义：

- `deck`：`title` / `aspect`(16:9) / `theme`(取 assets/themes.py 十主题之一) / `palette`(8 字段色板 hex，缺省继承 theme) / `font_pair`{title,body} / `style_anchor`（风格锚段落，所有生图 prompt 复用，见 R6.4 模板五——**全 deck 唯一真相源**）。
- `pages[]`：每页 `page_id` / `page_type`(cover/agenda/transition/content/result/compare/timeline/team/conclusion) / `action_title`（行动式标题，沿用 m16 既有纪律）/ `key_message` / `elements[]` / `notes`(speaker notes)。
- `elements[]`：`id` / `type` / `bbox:[x,y,w,h]`（相对 0-1 坐标）/ 按 type 带 `text`/`bullets`/`source`/`data_ref`/`desc`/`font_size`/`color`/`style`。
  - `type ∈ {title, body, table, chart, icon, illustration, decor, background}`。

**大纲生成纪律**（沿用 m16 既有）：叙事骨架（SCR/漏斗+答案/答案先行）+ 幽灵 deck 测试（只读标题连起来要能讲完论证）+ 一页一观点。**先过大纲审再进 Stage B**——不满意改 spec，别等出图再返工。

`bbox` 约定：`x,y` 为左上角相对坐标，`w,h` 为相对宽高，均 ∈[0,1]。装配时 `left = x × 13.333in`、`top = y × 7.5in`（16:9 宽屏 EMU）。

## Stage B | 整页视觉稿（设计稿，**不进成品**）

- 逐页用**模板一**生成 16:9 整页图（≥1920×1080），存 `visual_draft/p03.png`。
- 用途：**仅作设计参考**——确认版式美感、配色落地效果、留白节奏。**它不会被贴进 PPT**（这是与"贴图假 PPT"的本质区别）。
- 关键技巧：让所有文字用**无意义灰色块占位**（不渲染可读文字）——生图模型渲染文字必乱码，版式审稿只需看块面关系。
- 审稿：用户/agent 对照 deck_spec 审——版式是否符合 bbox 规划、风格是否统一。不满意改 spec 或 prompt 重生成本页，**不进 Stage C**。
- 无 key：imagegen.py mock 后端按 bbox 画灰块示意图占位，版式审稿照常（只是没有真实美感参考）。

## Stage C | 元素化拆解（核心，逐元素处理）

对每页按 `elements` 清单逐项落地，**按 type 分流**：

| type | 处理方式 | 绝不 |
|---|---|---|
| `title`/`body` | python-pptx 原生文本框（字体/字号/颜色从 spec/theme） | 不进图 |
| `table` | `add_table` 原生表格（主题描边/斑马纹，patterns.md 已有函数） | 不生图 |
| `chart` | m11/m06 matplotlib 真数据出图后 `add_picture` | **不让生图模型画数据** |
| `icon` | 生图模型**单独生成**：单元素、透明背景 PNG（模板二） | 不从整页稿裁切 |
| `illustration` | 生图模型单独生成（模板三），透明或纯色可去底 | 不裁切 |
| `decor`/`background` | 生图模型单独生成全幅低对比底图（模板四） | 不喧宾夺主 |

- 每个生图元素**一次独立 API 调用**，prompt = 元素描述 + **style_anchor（模板五）复用**，保证全套风格一致。
- 产物命名 `assets_gen/p03_e4_icon.png`（页_元素_类型）；imagegen.py 写 `manifest.json` 记录每张图的 prompt 与参数（可复现、可单独重生成）。
- 透明背景注意（见 _verification_log/R6-imggen-api.md）：**仅 OpenAI gpt-image 有显式 `background:transparent`**；Gemini/Seedream 无透明开关，做透明图标优先选 OpenAI 后端，否则生成后 PIL 去底（有毛刺风险，Stage E 把关）。
- Seedream 注意：`watermark` 默认 true，封装层已默认置 false，勿让元素带"AI 生成"水印。

## Stage D | 重组装配（assemble_from_spec.py）

- 读 `deck_spec.yaml` + `assets_gen/` + `figures/` → python-pptx 产出**可编辑 pptx**。
- 坐标换算：`left = bbox.x × slide_width`（EMU），`top/width/height` 同理；slide 尺寸 16:9（13.333×7.5 英寸）。
- 文本框：margin=0、左对齐（仅标题可居中）、中文字体缺失回退链（退 Microsoft YaHei 并 warn）。
- speaker notes 从 `spec.notes` 写入。
- 复用既有 `fill_bg`/`add_text`/`rect`（patterns.md），**勿重写**。
- `--selftest`：内置最小 spec + PIL 占位 PNG，离线产出 2 页 pptx 到临时目录并断言元素数，**不留产物**。

## Stage E | QA 循环（升级既有 QA 节）

既有：thumbnail.py 网格视觉扫 + markitdown 内容查。本路线**新增两条专属**：

1. **文本未栅格化检查**：`python -m markitdown out.pptx` 提取的文本条数 **≥ spec 中 title/body 元素数**——证明文字真是文本框，不是烤进图里（守边界三）。
2. **风格一致性人审**：图标是否同一风格族 / 透明底是否干净（无白边毛刺）/ 装饰是否压字。把全部生成元素拼一张 contact sheet（thumbnail.py 思路）人审最快。

- 不合格元素：改该元素 prompt **单独重生成**（manifest 有记录），**不重跑整页**——这是元素化拆解相对"整页贴图"的核心优势。
- 改完只重渲受影响页，循环到整轮无新问题才收。

## R6.3 风格一致性策略

三家后端 seed 都不稳定（见实测日志），**不依赖 seed**，靠下面五条：

1. 所有 prompt 共用 `style_anchor` 段（唯一真相源在 deck_spec，改风格只改这一段）。
2. 后端若支持 seed（Seedream 旧系列）则全 deck 固定 seed 作辅助，但不作为唯一保障。
3. 首页定稿后，支持图生图/参考图的后端把首页视觉稿作风格参照传入。
4. 同类元素（如一组 4 个图标）**一次会话连续生成**，prompt 里声明"与前一张同风格族"。
5. 风格漂移自查：把全部生成元素拼一张 contact sheet 人审（thumbnail.py 思路）。

## R6.4 Prompt 模板（核心资产，变量槽 `{…}`）

> 五个模板是流水线的核心资产。无 key 时为初稿；配 key 端到端实跑后，把"哪个后端/什么参数/效果如何"回填到「实测记录」小节（当前为 `GAP：待实测（2026-06-XX）`）。

**模板一 · 整页视觉稿**（Stage B，仅设计参考不进成品）
```text
为一页 16:9 演示幻灯片生成完整视觉设计稿。
主题风格：{style_anchor}
版式要求：{按 elements 逐条描述，如"标题区位于顶部 6%-18% 高度，左对齐；左侧 40% 宽为要点列表区；
右侧 44% 宽为图表占位区（画抽象占位框即可，不要画具体数据）；左下角一枚扁平图标"}
配色：主色 {primary}，辅色 {secondary}，强调色 {accent}，背景 {bg}。
文字一律用无意义灰色块占位（不要渲染可读文字，不要伪文字乱码）。
负面清单：无水印、无签名、无照片级人脸、无凌乱细节、无超出画面的元素。
```
要点：让文字用灰块占位是关键技巧——生图模型渲染文字必乱码，版式审稿只需看块面关系。

**模板二 · 单个图标（透明）**（Stage C，icon）
```text
生成一枚单独的扁平风格图标：{desc，如"上升趋势箭头与坐标轴"}。
要求：透明背景 PNG；居中；单一主体不带任何文字；线条与配色遵循：{style_anchor}，主色 {primary}；
形状简洁可在 96×96 px 下仍清晰；边缘干净无白边无阴影。
负面清单：无背景色块、无文字、无水印、无渐变噪点。
```
后端选择：透明背景仅 OpenAI gpt-image 有显式 `background:transparent`；用 Gemini/Seedream 则生成后 PIL 去底。

**模板三 · 插画/示意元素（透明）**（Stage C，illustration）
```text
生成一幅单独的扁平插画元素：{desc，如"奶山羊侧面剪影与传感器示意"}。
透明背景；构图独立完整（将被单独摆放进幻灯片）；风格：{style_anchor}；
主体占画面 80% 以上；不含任何文字与数字。
负面清单：无背景、无文字、无照片写实风、无多余小物件。
```

**模板四 · 页面背景/装饰**（Stage C，decor/background）
```text
生成一张 16:9 幻灯片背景图：{desc，如"右上角几何渐变装饰，整体极简"}。
约束：整体低对比、低饱和，中央 70% 区域接近纯色 {bg}（将覆盖正文文字，必须保证文字可读性）；
装饰元素只允许出现在边缘 15% 区域；风格：{style_anchor}。
负面清单：无文字、无强对比图案进入中央区、无水印。
```

**模板五 · style_anchor 写法规范**（不是 prompt，是写 anchor 的规则）
```text
一段 30-60 字中文：风格关键词（扁平/玻璃拟态/学术克制…）+ 主色 hex + 形状语言（几何/圆角/线性）+
质感（留白程度/渐变与否）+ 明确排除项。全 deck 唯一，所有模板引用，改风格只改这一段。
示例："现代科技感，深蓝主色#1F4E79，几何渐变，克制留白，扁平插画风，无拟物阴影、无照片写实、无文字"。
```

### 实测记录（有 key 端到端实跑，2026-06-12 关闭 R6.6#4 GAP）
- **实跑环境**：OpenAI gpt-image-2，经 OpenAI 兼容中转（`OPENAI_IMAGE_BASE_URL` + `OPENAI_IMAGE_API_KEY`）。spec=`examples/deck_spec.dairygoat.yaml`（5 页：封面/痛点/管线/结果/结论），留痕 `_verification_log/R-imggen-deck-e2e.md`。
- **生图元素**：5 个（2 背景 16:9 + 2 插画 1:1 + 1 图标 1:1），全部经 `imagegen.py` 真实出图，每图带 `style_anchor`（agriculture 叶绿暖橙）锁风格；manifest 记录每张 prompt/model/size。
- **装配结果**：`assemble_from_spec.py` 装回 5 页可编辑 pptx，**10 个原生文本框**（标题+正文，非栅格化）+ 6 张图片，**0 warning**；真数据图（p04 召回柱状图）走 m11 出图后 add_picture，未让生图模型画数据图（守边界一）。
- **实测踩坑（已回灌 imagegen.py）**：①中转 POST 成功后 `data[0]` 只回 CDN `url`，须二次 GET 下载，**且下载请求也要带浏览器 UA**否则 CDN/WAF 403（首轮反复 403 真因）；②gpt-image 单图 60–120s+，`--timeout` 默认提到 180、deck 出图用 300；③POST 与 CDN 下载各加 3 次退避重试应对网关抖动；④manifest 的 model 字段改吃 env 覆盖（原误记默认 `gpt-image-1`，实发 `gpt-image-2`）。
- **沉淀风格卡**：db06 `slide_pattern_cards.md` 新增「智慧农业项目答辩 — imggen 生图元素 + 真数据图混排（实跑沉淀）」卡，来源标注本次 imggen 实跑（兑现 R6.5"每套 deck 沉一卡"）。
- 各后端端点/参数/尺寸/透明支持已据官方文档核实，见 `_verification_log/R6-imggen-api.md`。

## R6.5 知识库与下游联动

- **db06 沉淀钩子**：每次实跑 imggen-enhanced 出一套 deck，把 `style_anchor` + 生效 prompt + 缩略图记成一张 db06 风格卡（R9 的 db06 上量与此联动——实跑沉卡是真实卡的主要来源）。imagegen.py 的 `manifest.json` 已留每张图的 prompt/参数，沉卡时直接取。
- **m17（light-competition）路演 PPT**：竞赛路演 deck 可走本管线出高审美元素；m17 与 m16 各留一行双向指针。
- **a05（light-frontend-design）视觉灵感**：前端 moodboard/灵感图可复用本管线的生图封装与 style_anchor 写法；双向指针。
- **a07（light-consistency）一致性**：生成元素配色须与项目 palette 对齐——R9 `palette.json` 落地后接上，本轮先留前向指针（生图元素的 primary/accent 应取自项目统一色板，不另起一套）。
