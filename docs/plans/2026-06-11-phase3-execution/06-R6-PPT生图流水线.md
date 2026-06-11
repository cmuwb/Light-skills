# R6 | PPT 生图流水线（旗舰功能，预计 1-2 天）

- 前置：R1；建议 R4.2（AI 图像政策）已完成以便边界互引。
- 需求来源：用户钦定。核心思路——先出**每页详细大纲**（每个要素的排版位置与审美风格）→ 生图模型**逐页生成整页视觉稿** → 把视觉稿**超细拆解为可放进 PPT 的独立元素**（用生图模型重新生成，**不是截图抠图**；图标须单张透明 PNG，文本须独立文本框且字体颜色受控，表格须原生表格）→ **重新排版**装回 PPT，产出**可编辑**的 pptx。用户特别强调：**这条流水线的提示词本身是核心资产**。
- 落点：m16 light-slides 新增显式 mode（不新增技能，技能数保持 28）。

## R6.0 定位与边界（先写进文档，再写代码）

m16 从此有两条显式 mode（登记 MODE_REGISTRY，"仅 3 个技能有 mode"句子改为 4 个）：

| mode | 路线 | 适用 |
|---|---|---|
| `programmatic`（默认） | 现有 python-pptx 程序化路线（themes.py/patterns.md/build_deck.py） | 无生图 key、数据密集、批量出页 |
| `imggen-enhanced` | 本轮新增五阶段生图流水线 | 配置了生图模型、要高审美路演/答辩/发布会质感 |

**三条硬边界**（与 R4.2 互引）：
1. **数据图永不生图**——折线/柱状/混淆矩阵等一律由 m11/m06 matplotlib 真数据出图（生图模型会编数据，违反诚实底线）；
2. **论文图链路（m09/m11）严禁生图**——出版商明令禁止（R4.2 政策节）；
3. **文本永不烤进图**——所有文字以原生文本框落地，否则"可编辑"是假的。

## R6.1 生图模型配置层

- 推荐模型（README/R10 同步）：**GPT Image 2、Nanobanana 2、Seedream 5.0**（任配一个即可）。
- 新增 `skills/light-slides/scripts/imagegen.py`：统一封装三后端。
  - key 来源：环境变量 `OPENAI_API_KEY` / `GEMINI_API_KEY` / `ARK_API_KEY`（火山方舟），自动探测可用后端，`--backend` 可指定；
  - 端点与参数：**执行时联网核实三家当前 API 的真实端点/参数/尺寸与透明背景支持**，逐条写入 m16 references（带实测日期）；无网/无 key 则接口层代码照写、references 标 `GAP：待实测`；
  - `--selftest`：**完全离线**——mock 后端返回占位 PNG（PIL 现画），跑通"请求构造→落盘→清理"全链路，不打网络；
  - 无任何 key 时：明确报"imggen 后端不可用"并提示退回 `programmatic` mode（**不静默假成功**，与 to_pdf.py 同纪律）。
- README"关于 API key"节同步（R10 落地，本轮先改 m16 文档）：核心功能仍免 key；`imggen-enhanced` 模式需自备生图 key，强烈建议配置。SECURITY.md 口径核对（key 只走环境变量）。

## R6.2 五阶段管线（写入新文件 `skills/light-slides/references/imggen_pipeline.md`）

### Stage A | 大纲卡（deck_spec.yaml）
每页一张结构卡，**这是整条流水线的契约**。新建 `templates/deck_spec.yaml`：

```yaml
deck:
  title: "XX 项目答辩"
  aspect: "16:9"
  theme: tech            # 取 assets/themes.py 十主题之一
  palette:               # 8 字段色板，hex；缺省继承 theme
    primary: "#1F4E79"
  font_pair: {title: "思源黑体 Bold", body: "思源黑体 Regular"}
  style_anchor: |        # 风格锚段落，所有生图 prompt 复用（见 R6.4 模板五）
    现代科技感，深蓝主色#1F4E79，几何渐变，克制留白，扁平插画风，无拟物阴影
pages:
  - page_id: p03
    page_type: content   # cover/agenda/transition/content/result/compare/timeline/team/conclusion
    action_title: "三个队列的处理效应均显著"   # 行动式标题（沿用 m16 既有纪律）
    key_message: "一句话核心信息"
    elements:
      - {id: e1, type: title,  bbox: [0.06, 0.06, 0.88, 0.12], text: "...", font_size: 36, color: text}
      - {id: e2, type: body,   bbox: [0.06, 0.22, 0.40, 0.55], bullets: ["..."], font_size: 16}
      - {id: e3, type: chart,  bbox: [0.50, 0.22, 0.44, 0.55], source: "figures/fig3.png"}  # m11 真数据图
      - {id: e4, type: icon,   bbox: [0.06, 0.82, 0.06, 0.10], desc: "上升趋势箭头", style: flat}
      - {id: e5, type: table,  bbox: [0.50, 0.80, 0.44, 0.14], data_ref: "tables/t1.csv"}
      - {id: e6, type: decor,  bbox: [0.00, 0.00, 1.00, 1.00], desc: "右上角几何装饰，低对比"}
    notes: "speaker notes..."
```
- `bbox = [x, y, w, h]`，相对 0-1 坐标；`type ∈ {title, body, table, chart, icon, illustration, decor, background}`。
- 大纲生成纪律：沿用 m16 既有的叙事骨架/幽灵 deck 测试/一页一观点，**先过大纲审再进 Stage B**。

### Stage B | 整页视觉稿（设计稿，不进成品）
- 逐页用"模板一"生成 16:9 整页图（≥1920×1080），存 `visual_draft/p03.png`；
- 用途：**仅作设计参考**——确认版式美感、配色落地效果；它不会被贴进 PPT（这是与"贴图假 PPT"的本质区别，写进文档加粗）；
- 用户/agent 对照 deck_spec 审稿：版式是否符合 bbox 规划、风格是否统一；不满意改 spec 或 prompt 重生成本页。

### Stage C | 元素化拆解（核心，逐元素处理）
对每页按 elements 清单逐项落地，**按 type 分流**：

| type | 处理方式 | 绝不 |
|---|---|---|
| title/body | python-pptx 原生文本框（字体/字号/颜色从 spec/theme） | 不进图 |
| table | `add_table` 原生表格（主题描边/斑马纹，patterns.md 已有工具函数） | 不生图 |
| chart | m11/m06 matplotlib 真数据出图后 `add_picture` | **不让生图模型画数据** |
| icon | 生图模型**单独生成**：单元素、透明背景 PNG（模板二） | 不从整页稿裁切 |
| illustration | 生图模型单独生成（模板三），透明或纯色可去底 | 不裁切 |
| decor/background | 生图模型单独生成全幅低对比底图（模板四） | 不喧宾夺主 |

- 每个生图元素一次独立 API 调用，prompt = 元素描述 + **style_anchor（模板五）**复用，保证全套风格一致；
- 产物落 `assets_gen/p03_e4_icon.png` 命名规则（页_元素_类型），manifest 记录每张图的 prompt 与参数（可复现、可重生成）。

### Stage D | 重组装配
- 新增 `skills/light-slides/scripts/assemble_from_spec.py`：读 deck_spec.yaml + assets_gen/ + figures/ → python-pptx 产出**可编辑 pptx**；
  - 坐标换算：`left = bbox.x × slide_width`（EMU），余同；slide 尺寸 16:9（13.333×7.5 英寸）；
  - 文本框 margin=0、左对齐、字体回退链（中文字体缺失时退 Microsoft YaHei 并 warn）；
  - speaker notes 从 spec.notes 写入；
  - `--selftest`：用内置最小 spec + PIL 占位 PNG 离线产出 2 页 pptx 到临时目录并断言元素数，**不留产物**。
- 复用既有 `fill_bg`/`add_text`/`rect`（patterns.md），勿重写。

### Stage E | QA 循环（升级既有 QA 节）
- 既有：thumbnail.py 网格视觉扫 + markitdown 内容查。新增两条本路线专属：
  1. **文本未栅格化检查**：`python -m markitdown out.pptx` 提取的文本条数 ≥ spec 中 title/body 元素数（证明文字真的是文本框）；
  2. **风格一致性人审**：图标是否同一风格族/透明底是否干净（无白边毛刺）/装饰是否压字。
- 不合格元素：改该元素 prompt **单独重生成**（manifest 有记录），不重跑整页。

## R6.3 风格一致性策略（写进 references）

1. 所有 prompt 共用 style_anchor 段（唯一真相源在 deck_spec）；
2. 后端支持 seed 则全 deck 固定 seed；
3. 首页定稿后，支持图生图/参考图的后端把首页视觉稿作风格参照传入；
4. 同类元素（如一组 4 个图标）**一次会话连续生成**并在 prompt 里声明"与前一张同风格族"；
5. 风格漂移自查：把全部生成元素拼一张 contact sheet（thumbnail.py 思路）人审。

## R6.4 Prompt 模板（核心资产，全文写入 imggen_pipeline.md）

> 以下五个模板为初稿，执行时实跑回填"实测记录"（哪个后端、什么参数、效果如何）；无 key 则标 GAP。变量槽用 `{…}`。

**模板一 · 整页视觉稿**
```text
为一页 16:9 演示幻灯片生成完整视觉设计稿。
主题风格：{style_anchor}
版式要求：{按 elements 逐条描述，如"标题区位于顶部 6%-18% 高度，左对齐；左侧 40% 宽为要点列表区；右侧 44% 宽为图表占位区（画抽象占位框即可，不要画具体数据）；左下角一枚扁平图标"}
配色：主色 {primary}，辅色 {secondary}，强调色 {accent}，背景 {bg}。
文字一律用无意义灰色块占位（不要渲染可读文字，不要伪文字乱码）。
负面清单：无水印、无签名、无照片级人脸、无凌乱细节、无超出画面的元素。
```
（要点：让文字用灰块占位是关键技巧——生图模型渲染文字必乱码，版式审稿只需要看块面关系。）

**模板二 · 单个图标（透明）**
```text
生成一枚单独的扁平风格图标：{desc，如"上升趋势箭头与坐标轴"}。
要求：透明背景 PNG；居中；单一主体不带任何文字；线条与配色遵循：{style_anchor}，主色 {primary}；
形状简洁可在 96×96 px 下仍清晰；边缘干净无白边无阴影。
负面清单：无背景色块、无文字、无水印、无渐变噪点。
```

**模板三 · 插画/示意元素（透明）**
```text
生成一幅单独的扁平插画元素：{desc，如"奶山羊侧面剪影与传感器示意"}。
透明背景；构图独立完整（将被单独摆放进幻灯片）；风格：{style_anchor}；
主体占画面 80% 以上；不含任何文字与数字。
负面清单：无背景、无文字、无照片写实风、无多余小物件。
```

**模板四 · 页面背景/装饰**
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
```

## R6.5 知识库与下游联动

- **db06 沉淀钩子**：每次实跑 imggen-enhanced 出一套 deck，把 style_anchor+生效 prompt+缩略图记成一张 db06 风格卡（R9 的 db06 上量与此联动——实跑沉卡是真实卡的主要来源）；
- m17 路演 PPT、a05 视觉灵感声明可复用本管线（各加一行指针，**双向**）；
- a07 一致性：生成元素配色须与项目 palette 对齐（R9 palette.json 落地后接上，本轮先留一行前向指针）。

## R6.6 验收

- [ ] MODE_REGISTRY 登记 m16 两 mode；SKILL.md 路线分流清晰（正文增量 ≤15 行，细节全在 imggen_pipeline.md——常驻瘦身纪律）。
- [ ] `imagegen.py --selftest`、`assemble_from_spec.py --selftest` 离线全绿、不留产物；WHATS_INCLUDED 登记。
- [ ] 用示例 deck_spec（3 页：封面/内容/结果）+ 占位 PNG 走通 D 阶段，产出 pptx 在 PowerPoint/WPS 打开可编辑（文本可改、表格原生）——此项**无 key 也必须过**。
- [ ] 有 key：端到端实跑一套 ≥5 页 deck，五阶段产物齐全，QA 两项新检查过，db06 沉一张风格卡，全程记录落 `_verification_log/`；无 key：上述标 `GAP：待实测`并在 PROGRESS 登记。
- [ ] 三条硬边界在 m16/m11/a10 三处互引可 grep。

## 提交切分建议

- `幻灯片技能:imggen-enhanced模式与五阶段生图流水线文档`
- `幻灯片技能:生图后端统一封装与离线自测`
- `幻灯片技能:deck_spec契约与重组装配脚本`
- `模式注册表与边界:登记新模式并声明生图三边界`

## 收尾

总纲 §5 八步；PROGRESS 更新；打印 R7 启动提示词。
