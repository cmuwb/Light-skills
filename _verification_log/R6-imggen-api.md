# R6 生图后端 API 实测核验（三家端点/参数/尺寸/透明背景）

- 核验日期：2026-06-12
- 方式：联网核实官方 API Reference / 官方 SDK 类型定义 / 官方文档（无生图 key，未发真实生成请求；端点可达性用无鉴权探测确认）
- 目的：R6.1 要求「执行时联网核实三家当前 API 的真实端点/参数/尺寸与透明背景支持」，逐条写入 m16 references 与本日志；无 key 部分按诚信纪律标 GAP。
- 真相源去向：本日志为单一真相源，`skills/light-slides/references.md`「生图后端」节与 `scripts/imagegen.py` 内常量均指向本文件，改端点/参数须同步三处。

## 端点可达性（无鉴权探测，2026-06-12）

```
405  https://api.openai.com/v1/images/generations          # 方法不允许=端点在（GET 探测）
403  https://generativelanguage.googleapis.com/v1beta/...   # 无 key 拒绝=主机在
401  https://ark.cn-beijing.volces.com/api/v3/images/generations  # 未鉴权=端点在
```
三主机均可达；返回码是「缺鉴权/方法不符」而非 DNS/连接失败，证明端点路径正确。

## 后端一 · OpenAI GPT Image（gpt-image-1 / 1.5 / 2 系列）

- 端点：`POST https://api.openai.com/v1/images/generations`
- 鉴权：`Authorization: Bearer $OPENAI_API_KEY`
- 模型 id：`gpt-image-1`（亦接受 `gpt-image-1-mini` / `gpt-image-1.5` / `gpt-image-2`，随发布演进；用前查模型页）
- 关键参数（核自 openai-python `image_generate_params.py` 与 API Reference）：
  | 参数 | 取值 | 备注 |
  |---|---|---|
  | `prompt` | ≤32000 字符 | 必填 |
  | `size` | `1024x1024` / `1536x1024` / `1024x1536` / `auto` | 无任意像素；16:9 近似用 1536x1024 |
  | `background` | `transparent` / `opaque` / `auto` | **唯一有显式透明开关的后端**；透明须配 png/webp |
  | `output_format` | `png` / `jpeg` / `webp` | 透明背景需 png/webp |
  | `quality` | `low` / `medium` / `high` / `auto` | |
  | `n` | 1–10 | |
  | `moderation` | `low` / `auto` | |
- 返回：GPT image 系列**恒返回 `b64_json`**（不支持 `response_format:url`，与 DALL·E 2/3 不同）。
- seed：**官方参数表未列 seed** → 风格复现靠 prompt+background 固定，不能靠 seed 锁。标注：seed 复现能力 GAP（待官方补充或换支持 seed 的后端）。
- 透明背景：**支持**（`background:transparent`+png）——图标/插画元素首选此后端。
- 来源：https://developers.openai.com/api/reference/resources/images/methods/generate/ ；https://github.com/openai/openai-python/blob/5e8f09c2/src/openai/types/image_generate_params.py ；模型页 https://developers.openai.com/api/docs/models/gpt-image-1

## 后端二 · Google Gemini「Nano Banana」系列

- 端点：`POST https://generativelanguage.googleapis.com/v1/models/{model}:generateContent`（图像走通用 `generateContent`，**无独立 images 端点**——常见报错就是误调 `predict`/独立图像端点）
- 鉴权：HTTP 头 `x-goog-api-key: $GEMINI_API_KEY`
- 模型 id：`gemini-3.1-flash-image`（Nano Banana 2，速度向）/ `gemini-3-pro-image`（Nano Banana Pro，专业资产向）/ `gemini-2.5-flash-image`（初代 Nano Banana）
- 请求体：
  ```json
  {"contents":[{"parts":[{"text":"<prompt>"}]}],
   "generationConfig":{"responseModalities":["TEXT","IMAGE"],
     "responseFormat":{"image":{"aspectRatio":"16:9","imageSize":"2K"}}}}
  ```
- 尺寸：`aspectRatio` ∈ {1:1,2:3,3:2,3:4,4:3,4:5,5:4,9:16,16:9,21:9,…，3.1 新增 1:4/4:1/1:8/8:1}；`imageSize` ∈ {512,1K,2K,4K}（**大写 K**；512 仅 3.1 Flash；默认 1K）。16:9 整页稿原生支持。
- 返回：base64 在 `candidates[0].content.parts[].inlineData.data`，`mime_type:image/png`。
- seed：官方文档**未列 seed** → 风格复现 GAP（靠 prompt + 图生图传参考图）。
- 透明背景：官方文档**无透明开关**（输出 png 容器支持透明但无 toggle）→ 透明背景 GAP；做透明图标建议改用 OpenAI 后端，或生成后用 PIL 去底（有毛刺风险，QA 把关）。
- 来源：https://ai.google.dev/gemini-api/docs/image-generation ；https://blog.google/innovation-and-ai/technology/developers-tools/build-with-nano-banana-2/

## 后端三 · 火山方舟 Seedream（豆包，国内）

- 端点：`POST https://ark.cn-beijing.volces.com/api/v3/images/generations`（OpenAI 兼容风格）
- 鉴权：`Authorization: Bearer $ARK_API_KEY`，`Content-Type: application/json`
- 模型 id：随版本变（如 `doubao-seedream-3-0-t2i-250415`；Seedream 4.0/4.5/5.0 各有 id，用前查方舟控制台「开通管理」取当前 endpoint id）
- 关键参数：
  | 参数 | 取值 | 备注 |
  |---|---|---|
  | `prompt` | 建议 ≤300 汉字/600 英文词 | |
  | `size` | `2K`/`3K` 关键字 或像素 `2048x2048`/`3072x3072` 等；总像素与宽高比有范围约束 | 5.0 lite 总像素约 3.69M–10.4M、宽高比 [1/16,16] |
  | `response_format` | `url`（下载链接）/ `b64_json` | url 链接有时效 |
  | `output_format` | `png` / `jpeg` | |
  | `seed` | 整数（旧系列有；5.0 系列官方参考未明列） | 5.0 seed 支持 GAP，旧 t2i 系列支持 |
  | `watermark` | bool，**默认 `true`**（加「AI 生成」水印） | **PPT 用务必显式置 `false`**，否则元素带水印 |
  | `guidance_scale` | 浮点 | 越大越贴 prompt |
- 透明背景：官方文档**无透明开关**→ 透明背景 GAP；透明图标建议改 OpenAI 后端。
- 注意：`watermark` 默认 true 是 PPT 元素的隐形坑——封装层必须默认传 `watermark:false`。
- 来源：https://www.volcengine.com/docs/82379/1541523 （Seedream 5.0 lite API 参考）；BytePlus 英文镜像 https://docs.byteplus.com/en/docs/ModelArk/1541523

## 三家横向结论（写入 references 的口径）

| 能力 | OpenAI gpt-image | Gemini Nano Banana | Seedream(Ark) |
|---|---|---|---|
| 显式透明背景 | ✅ `background:transparent` | ❌ GAP | ❌ GAP |
| seed 复现 | ❌ 未列 | ❌ 未列 | ⚠️旧系列有，5.0 GAP |
| 任意 16:9 整页 | ⚠️ 1536x1024 近似 | ✅ `aspectRatio:16:9` | ✅ 像素自定义 |
| 默认水印 | 无 | 无 | ⚠️**默认有**，须关 |
| 返回 | b64 恒定 | inlineData b64 | url 或 b64 |

- **选型建议**：透明图标/插画 → OpenAI（唯一原生透明）；整页视觉稿/16:9 背景 → Gemini 或 Seedream（原生 16:9 + 高分辨率）；国内网络 → Seedream（注意关水印）。
- **风格复现策略**（因三家 seed 都不稳）：不依赖 seed，改靠①唯一 style_anchor 段全 prompt 复用 ②支持图生图的后端传首页视觉稿作风格参照 ③同类元素一次会话连续生成（详见 imggen_pipeline.md R6.3）。

## GAP 台账（无 key 未实跑真实生成）

- `GAP：待实测（2026-06-XX）` — 三家**真实生成请求**（出图质量、透明底干净度、风格一致性实效、各档 size 真实像素）均未跑，因执行环境无 OPENAI/GEMINI/ARK key。端点/参数/尺寸/透明支持已据官方文档与 SDK 类型核实如上；待用户配 key 后按 R6.6 验收第 4 条端到端实跑回填，并把生效 prompt+缩略图沉一张 db06 风格卡。
