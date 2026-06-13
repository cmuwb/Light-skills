# imggen-enhanced 有 key 端到端实跑留痕（关闭 R6.6#4 GAP）

- 日期：2026-06-12
- 目的：关闭 PROGRESS「R6.6#4 — 有 key 端到端实跑」长期 GAP。此前只有无 key 装配链
  （mock 占位）实测过，真实生图请求因计费 + 需用户授权未触发；本次用户显式授权后实跑。
- 后端：OpenAI gpt-image-2，经 OpenAI 兼容中转（`OPENAI_IMAGE_BASE_URL`=zzshu，
  `OPENAI_IMAGE_API_KEY`）。
- 封装：`skills/light-slides/scripts/imagegen.py`（生图）+ `assemble_from_spec.py`（装配）。
- 契约：`skills/light-slides/examples/deck_spec.dairygoat.yaml`（5 页智慧农业答辩）。

## 五阶段产物齐全（imggen-enhanced 全链路）

| Stage | 动作 | 产物 | 实测 |
|---|---|---|---|
| A 大纲 | deck_spec 5 页结构卡 | `examples/deck_spec.dairygoat.yaml` | ✅ 行动式标题 + key_message + elements/bbox |
| B 生图 | 5 个生图元素逐个出图 | assets_gen/ 5 PNG | ✅ 2 背景(16:9)+2 插画(1:1)+1 图标(1:1)，全真实出图 |
| C 真数据图 | m11 出图 | figures/metrics_bar.png | ✅ 召回柱状图(color_palettes+figure_export)，**非生图模型画** |
| D 装配 | 按 bbox 装回 pptx | dairygoat_deck.pptx | ✅ 5 页 / 16 元素 / **0 warning** |
| E QA | 可编辑性 + 边界检查 | — | ✅ 10 原生文本框(非栅格化) + 6 图片；数据图未生图 |

## 关键实测发现（已回灌 imagegen.py，附 selftest 覆盖）

1. **中转两跳协议**：`POST /v1/images/generations` 成功后，响应 `data[0]` 只回
   `url`（CDN 地址）不回 `b64_json`，须二次 GET 下载图片字节。
2. **CDN 下载也要浏览器 UA**：裸 `urlopen(cdn_url)` 被 CDN/WAF 403。这是 logo 与 deck
   首轮反复 403 的真因——POST 其实成功了，失败在第二跳下载。修复：`_download()` 带
   Chrome UA + 3 次退避重试。
3. **UA 选择**：自报家门式 UA 偶发 403/RemoteDisconnected，Chrome UA 成功率最高；
   官方 `api.openai.com` 不挑 UA，统一用 Chrome UA 无副作用。
4. **出图慢**：gpt-image 单图常 60–120s+，原默认 120s 超时不够 → `--timeout` 默认提到
   180，deck/logo 出图显式用 300。
5. **manifest model 字段**：原 `model or DEFAULT_MODELS[backend]` 漏了 env 覆盖，误记
   `gpt-image-1`；改为 `model or _env_model(backend) or DEFAULT_MODELS[backend]`，
   如实记录实发的 `gpt-image-2`。

## 守边界确认

- **数据图绝不生图**：p04 召回柱状图走 m11 真数据 add_picture，生图模型只画
  背景/插画/图标。
- **文本不烤进图**：10 个标题/正文是原生 PowerPoint TextFrame，可直接在 PPT 里改字。
- **离线纪律不破**：imagegen.py `--selftest` 全程 mock、不打真网络；本次真实请求是
  用户显式授权的一次性实跑，不写进任何 selftest。

## 可复现命令

```bash
# 1) 5 个生图元素（每个带 style_anchor，串行，中转一次一张）
python skills/light-slides/scripts/imagegen.py --backend openai --size 16:9 \
  --type background --timeout 300 --manifest deck/manifest.json \
  -o deck/assets_gen/p01_e1_background.png --prompt "<desc>。<style_anchor>"
# ...（p02 插画 / p03 图标+插画 / p05 背景 同理，见 deck_spec elements）

# 2) 真数据图（m11 流水线，非生图）
#    color_palettes + figure_export 出 deck/figures/metrics_bar.png

# 3) 装配为可编辑 pptx
python skills/light-slides/scripts/assemble_from_spec.py \
  skills/light-slides/examples/deck_spec.dairygoat.yaml \
  -o deck/dairygoat_deck.pptx --assets deck/assets_gen --figures deck/figures
# -> [ok] 5 页 / 16 元素，0 warning
```

注：gpt-image seed 不稳，逐次重生构图会变；本留痕证明链路通、五阶段齐、守边界，
而非精确像素复现。生成的 deck 产物体积大（含 5 张 AI 图），不入仓，prompt 与
spec 已入仓可复现。
