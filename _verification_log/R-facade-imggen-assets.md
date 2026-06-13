# 门面视觉资产生图留痕（logo / 社交预览背景）

- 日期：2026-06-12
- 后端：OpenAI gpt-image（经 OpenAI 兼容中转 zzshu，`OPENAI_IMAGE_MODEL=gpt-image-2`）
- 封装：`skills/light-slides/scripts/imagegen.py`（imggen-enhanced 流水线同一封装）
- 用途：仓库门面（README 头部 logo、GitHub 社交预览图背景）——**非论文图链路**，符合
  「生图只服务 PPT/前端视觉，严禁进论文图」边界。

## 实测确认的中转网关行为（已回灌进 imagegen.py）

1. **两跳协议**：中转 `POST /v1/images/generations` 成功后，响应 `data[0]` 只回 `url`
   （CDN 图片地址），不回 `b64_json`，须二次 GET 下载。
2. **CDN 下载也要浏览器 UA**：裸 `urlopen(cdn_url)` 被 CDN/WAF 403；带
   Chrome UA 后通过。这是 logo 首轮反复 403 的真因（POST 成功、第二跳下载失败）。
3. **UA 选择**：自报家门式 UA（`Light-imggen/1.0`）偶发 403/RemoteDisconnected；
   Chrome UA 成功率最高。官方 `api.openai.com` 端点不挑 UA，故统一用 Chrome UA 无副作用。
4. **出图慢**：gpt-image 单图常 60–120s+，默认 120s 超时不够 → `--timeout` 默认提到 180、
   logo/背景用 300。
5. **偶发抖动**：同一请求偶发 403/断连，重试即过 → POST 与 CDN 下载各加 3 次退避重试。

## 生成清单

| 产物 | 尺寸 | 落地 | prompt 摘要 |
|---|---|---|---|
| logo（B 版，主） | 1024² → 512² | `assets/logo.png` | 靛蓝渐变底+立体玻璃棱镜+鲜明彩虹光束，扁平矢量 app 图标，无文字 |
| logo（A 版，备） | 1024² → 512² | `assets/logo-alt.png` | 深空蓝黑底+冷峻光谱，电影感沉稳版 |
| 社交预览背景 | 1536×1024（16:9 近似） | `assets/social_bg.png` | 抽象 hero：左侧发光棱镜将光束折射成彩虹扫向右侧，深空留白供叠字 |

完整 prompt 见 `assets/` 旁的 manifest（生成时 `--manifest` 落盘，未入仓，prompt 同时
抄录于本文件下方与各生成脚本头注）。用户决策：主 logo 选 B 版（明亮清爽），A 版留备用。

## 可复现命令

```bash
# logo（B 版）
python skills/light-slides/scripts/imagegen.py --backend openai --size 1:1 \
  --type illustration --timeout 300 -o assets/logo_raw.png \
  --prompt "Minimalist flat vector app icon on a deep indigo-to-navy gradient rounded square: a clean geometric glass prism refracting a thin white beam into a smooth rainbow spectrum fan (red orange yellow green cyan blue violet), elegant modern tech-brand style, crisp edges, soft glow, generous margins, centered, simple and iconic. No text, no letters, no words, no watermark."
# 再用 PIL 缩到 512² 存 assets/logo.png

# 社交预览背景
python skills/light-slides/scripts/imagegen.py --backend openai --size 16:9 \
  --type background --timeout 300 -o assets/social_bg.png \
  --prompt "An elegant abstract hero background for a science software banner. Deep navy and indigo gradient, a softly glowing crystalline prism on the left refracting a beam of light into a delicate rainbow spectrum that sweeps across to the right, fading into clean dark space. Subtle particles and light rays, lots of smooth empty negative space in the lower and right areas for text overlay. Premium, modern, minimal, cinematic lighting. No text, no letters, no words, no watermark, no logos."

# 社交预览图（AI 背景 + 程序化文字叠加）
python assets/make_social_preview_hybrid.py
```

注：gpt-image seed 不稳，逐次重生构图会变；本批产物已入仓，重生用于迭代而非精确复现。

## 第二轮（2026-06-13）：social-preview 与 pipeline 改纯 AI 生图

用户要求这两张不再用"AI 背景 + 程序化文字"混合，改**纯生图模型**出图。
实测：gpt-image-2 渲染**短英文品牌词**（"Light"）稳定、无乱码；故 social 让模型直接出带
"Light" 字样的 banner，pipeline 不含任何文字（用图标+流向表达阶段）。中文标语/精确技能
标签**不进生图**（中文渲染易乱），改由 README 周边文字与下方技能总览表承载。

- `assets/social-preview.png`（1280×640）：纯 AI banner，含 "Light" 品牌词 + 棱镜光谱。
  生成 16:9（1536×1024）后 PIL 居中裁成 2:1 再缩 1280×640（保住左上 Light 与棱镜）。
- `assets/pipeline.png`（1280×853）：纯 AI 抽象流程图——9 个发光光谱节点串联，节点内
  极简图标（书/数据条/灯泡/齿轮/图表/文档/图片/纸飞机/奖杯）示意"文献→成果"，无文字。
  **诚实说明**：纯 AI 版丢了旧 svg 的"17 手动+11 常驻/28 技能"精确标签，但 README 链路节
  下方的纯文本版链路 + 技能总览表仍列全 28 技能，信息不丢；alt-text 同步改为不含具体计数。
- 旧资产保留：程序化 `make_pipeline_svg.py` / `make_social_preview.py` /
  `make_social_preview_hybrid.py` 与 `assets/pipeline.svg` / `assets/social_bg.png` 仍在仓库，
  作为无 key 降级路线与可复现脚本（README 已不引用 svg）。

```bash
# social-preview（纯 AI，含品牌词）
python skills/light-slides/scripts/imagegen.py --backend openai --size 16:9 \
  --type background --timeout 300 -o social_ai.png \
  --prompt "A polished GitHub social banner ... the single large word \"Light\" ... Only the word \"Light\", no other text ..."
# PIL 居中裁 2:1 -> 1280x640 -> assets/social-preview.png

# pipeline（纯 AI，无文字）
python skills/light-slides/scripts/imagegen.py --backend openai --size 16:9 \
  --type illustration --timeout 300 -o pipeline_ai.png \
  --prompt "A premium horizontal infographic ... flowing path of connected glowing nodes ... minimalist icons inside nodes ... No text, no letters, no words, no numbers, no watermark."
# PIL 缩 1280 宽 -> assets/pipeline.png
```
