"""imagegen.py — imggen-enhanced 流水线的三后端统一生图封装。

支持后端（自动探测环境变量，--backend 可指定）：
    openai    GPT Image（gpt-image-1/1.5/2）   key=OPENAI_API_KEY  唯一有显式透明背景
    gemini    Nano Banana（gemini-*-image）    key=GEMINI_API_KEY  原生 16:9，无透明开关
    seedream  火山方舟 Seedream（豆包）         key=ARK_API_KEY     默认水印已关，无透明开关
    mock      离线占位（PIL 现画，无需 key/网络）——--selftest 与无 key 装配链专用

端点/参数/尺寸/透明支持的实测真相源：仓库根 _verification_log/R6-imggen-api.md。
改端点同步那里 + skills/light-slides/references.md + 本文件 ENDPOINTS/常量。

用法：
    python imagegen.py --check                          # 探测可用后端
    python imagegen.py --prompt "上升箭头图标" --type icon --transparent -o icon.png
    python imagegen.py --prompt "..." --backend mock --bbox 0.1,0.2,0.4,0.5 -o ph.png
    python imagegen.py --selftest                       # 完全离线全链路自测

无任何真实 key 且未显式 --backend mock 时：明确报"imggen 后端不可用"并提示退回
programmatic mode，绝不静默假成功（与 to_pdf.py 同纪律）。
"""
from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")
import os
import json
import base64
import argparse
import tempfile
import urllib.error
import urllib.request

# ---- 后端端点与默认模型（真相源见 _verification_log/R6-imggen-api.md，2026-06-12 核实）----
ENDPOINTS = {
    "openai": "https://api.openai.com/v1/images/generations",
    "gemini": "https://generativelanguage.googleapis.com/v1/models/{model}:generateContent",
    "seedream": "https://ark.cn-beijing.volces.com/api/v3/images/generations",
}
DEFAULT_MODELS = {
    "openai": "gpt-image-1",
    "gemini": "gemini-3.1-flash-image",          # Nano Banana 2
    "seedream": "doubao-seedream-3-0-t2i-250415",  # 随版本变，用前查方舟控制台 endpoint id
}
ENV_KEYS = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY", "seedream": "ARK_API_KEY"}

# 中转/自定义网关覆盖（很多用户经 OpenAI 兼容中转站访问，必须吃这些环境变量）：
#   OPENAI_IMAGE_BASE_URL > OPENAI_BASE_URL（形如 https://host/v1，自动拼 /images/generations）
#   OPENAI_IMAGE_MODEL / LIGHT_IMAGEGEN_MODEL 覆盖默认模型 id（如 gpt-image-2）
#   OPENAI_IMAGE_API_KEY 优先于 OPENAI_API_KEY


def _openai_url() -> str:
    base = os.environ.get("OPENAI_IMAGE_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
    if base:
        return base.rstrip("/") + "/images/generations"
    return ENDPOINTS["openai"]


def _env_model(backend: str) -> str | None:
    if backend == "openai":
        return os.environ.get("OPENAI_IMAGE_MODEL") or os.environ.get("LIGHT_IMAGEGEN_MODEL")
    return None


def _env_key(backend: str) -> str:
    if backend == "openai":
        return os.environ.get("OPENAI_IMAGE_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    return os.environ.get(ENV_KEYS[backend], "")

# OpenAI gpt-image 仅接受固定档；16:9 用 1536x1024 近似（见实测日志）
_OPENAI_SIZES = {"16:9": "1536x1024", "9:16": "1024x1536", "1:1": "1024x1024", "auto": "auto"}


def detect_backends() -> list[str]:
    """返回当前环境探测到 key 的后端（按 openai/gemini/seedream 顺序）。"""
    return [b for b in ("openai", "gemini", "seedream") if _env_key(b)]


def _norm_size(backend: str, size: str) -> str:
    """把统一 size（16:9/9:16/1:1 或像素 WxH）映射到各后端可接受形式。"""
    if backend == "openai":
        return _OPENAI_SIZES.get(size, "1536x1024" if "x" not in size else size)
    return size  # gemini 走 aspectRatio（见 build_request）；seedream 直接吃像素/2K/3K


def build_request(backend: str, prompt: str, *, model: str | None = None,
                  size: str = "16:9", transparent: bool = False) -> dict:
    """构造一次生图请求（url/headers/body/解析提示），**不发送**。

    这是离线可验证的核心：selftest 断言三后端请求结构正确，无需网络。
    返回 dict：{url, headers, body, resp_kind}（resp_kind 标明响应取图方式）。
    """
    if backend not in ENDPOINTS:
        raise ValueError(f"未知后端 {backend!r}，可选 {list(ENDPOINTS)}")
    model = model or _env_model(backend) or DEFAULT_MODELS[backend]
    key = _env_key(backend)

    if backend == "openai":
        body = {"model": model, "prompt": prompt, "size": _norm_size("openai", size),
                "output_format": "png", "n": 1}
        if transparent:
            body["background"] = "transparent"  # 唯一支持显式透明的后端
        return {"url": _openai_url(),
                "headers": {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                "body": body, "resp_kind": "openai_b64"}

    if backend == "gemini":
        ar = size if ":" in size else "16:9"
        body = {"contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseModalities": ["TEXT", "IMAGE"],
                                     "responseFormat": {"image": {"aspectRatio": ar, "imageSize": "2K"}}}}
        # 无透明开关：transparent 仅记录，去底交 PIL（Stage C 说明）
        return {"url": ENDPOINTS["gemini"].format(model=model),
                "headers": {"x-goog-api-key": key, "Content-Type": "application/json"},
                "body": body, "resp_kind": "gemini_inline"}

    # seedream
    body = {"model": model, "prompt": prompt,
            "size": _norm_size("seedream", size) if "x" in size else "2K",
            "response_format": "b64_json", "output_format": "png",
            "watermark": False}  # 默认 true 会加"AI 生成"水印，PPT 元素必须关
    return {"url": ENDPOINTS["seedream"],
            "headers": {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            "body": body, "resp_kind": "seedream_b64"}


# ---- mock 后端：离线占位 PNG（PIL 现画，无 key/网络）----
def render_placeholder(out_path: str, *, kind: str = "icon", prompt: str = "",
                       bbox: tuple[float, float, float, float] | None = None,
                       transparent: bool = False, size_px: tuple[int, int] | None = None) -> str:
    """用 PIL 画一张占位 PNG，示意元素位置/类型。装配链无 key 时的真实产物。

    icon/illustration：默认透明底 + 居中虚框 + 类型标签；
    decor/background：低对比全幅底；
    visual_draft：按 bbox（若给）画灰块版式示意图。
    """
    from PIL import Image, ImageDraw

    if size_px is None:
        size_px = (1536, 864) if kind in ("decor", "background", "visual_draft") else (256, 256)
    w, h = size_px
    bg = (0, 0, 0, 0) if (transparent or kind in ("icon", "illustration")) else (235, 238, 244, 255)
    img = Image.new("RGBA", (w, h), bg)
    d = ImageDraw.Draw(img)

    if kind == "visual_draft" and bbox:
        # 单元素灰块示意（assemble 预览用）
        d.rectangle([2, 2, w - 3, h - 3], outline=(150, 160, 175, 255), width=2)
        d.rectangle([int(w * 0.1), int(h * 0.1), int(w * 0.9), int(h * 0.9)],
                    fill=(205, 210, 220, 255))
    elif kind in ("decor", "background"):
        d.rectangle([0, 0, int(w * 0.18), h], fill=(220, 224, 232, 255))  # 边缘装饰带
    else:  # icon / illustration：居中虚框 + 对角线，标明"占位"
        m = int(min(w, h) * 0.12)
        d.rectangle([m, m, w - m, h - m], outline=(120, 130, 150, 255), width=3)
        d.line([m, m, w - m, h - m], fill=(120, 130, 150, 200), width=2)
        d.line([w - m, m, m, h - m], fill=(120, 130, 150, 200), width=2)
    label = f"[{kind}] placeholder"
    d.text((8, 6), label, fill=(90, 100, 120, 255))
    if prompt:
        d.text((8, h - 16), prompt[:40], fill=(110, 120, 140, 255))

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    img.save(out_path, "PNG")
    return out_path


# 中转 CDN 二次下载也得带浏览器 UA（裸 urlopen 会被 CDN/WAF 403，zzshu 实测）。
_DL_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def _download(url: str, timeout: int = 180) -> bytes:
    """下载一个 CDN 图片 url，带 UA + 三次退避重试（中转网关侧偶发 403/断连）。"""
    last_err: Exception | None = None
    for attempt in range(3):
        if attempt:
            import time
            time.sleep(2 * attempt)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _DL_UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except (urllib.error.HTTPError, urllib.error.URLError, ConnectionError, OSError) as e:
            last_err = e
    raise RuntimeError(f"CDN 图片下载三次均失败：{last_err}") from last_err


def _parse_response(resp_kind: str, payload: dict) -> bytes:
    """从各后端响应 JSON 取出图片字节（真实调用路径，selftest 用构造样例覆盖）。

    openai 兼容口径两种都认：官方 b64_json；中转网关常给 url（需二次下载）。
    """
    if resp_kind in ("openai_b64", "seedream_b64"):
        item = payload["data"][0]
        if item.get("b64_json"):
            return base64.b64decode(item["b64_json"])
        if item.get("url"):  # 中转站实测（zzshu 2026-06-12）：只回 CDN url
            return _download(item["url"])
        raise ValueError(f"响应 data[0] 无 b64_json/url，键={list(item)}")
    if resp_kind == "gemini_inline":
        for part in payload["candidates"][0]["content"]["parts"]:
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])
        raise ValueError("gemini 响应无 inlineData 图片块")
    raise ValueError(f"未知 resp_kind {resp_kind!r}")


def generate(prompt: str, out_path: str, *, backend: str | None = None, kind: str = "icon",
             model: str | None = None, size: str = "16:9", transparent: bool = False,
             bbox=None, timeout: int = 120) -> dict:
    """生成一张图并落盘。返回 manifest 记录（含 backend/prompt/参数/产物路径）。

    backend=None 时自动探测：有 key 取第一个，无 key 抛错（不静默假成功）。
    backend='mock' 强制走离线占位。
    """
    if backend == "mock":
        render_placeholder(out_path, kind=kind, prompt=prompt, bbox=bbox, transparent=transparent)
        return {"backend": "mock", "model": "pil-placeholder", "prompt": prompt,
                "kind": kind, "size": size, "transparent": transparent, "out": out_path}

    if backend is None:
        avail = detect_backends()
        if not avail:
            raise RuntimeError(
                "imggen 后端不可用：未探测到 OPENAI_API_KEY / GEMINI_API_KEY / ARK_API_KEY。\n"
                "  配置任一生图 key 后重试，或退回 programmatic mode（python-pptx 程序化路线，"
                "见 build_deck.py/patterns.md），或用 --backend mock 走离线占位装配链。")
        backend = avail[0]

    req = build_request(backend, prompt, model=model, size=size, transparent=transparent)
    data = json.dumps(req["body"]).encode("utf-8")
    # 中转网关传输层兼容（zzshu 2026-06-12 实测）：①缺 User-Agent 直接 RemoteDisconnected，
    # 且自报家门式 UA 仍偶发 403/断连，浏览器 UA 成功率最高（官方端点不挑 UA）；
    # ②同一请求偶发 403/RemoteDisconnected 属网关侧抖动，重试即过——故带退避重试。
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                             "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
               **req["headers"]}
    last_err: Exception | None = None
    for attempt in range(3):
        if attempt:
            import time
            time.sleep(2 * attempt)  # 2s/4s 退避
        httpreq = urllib.request.Request(req["url"], data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(httpreq, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            break
        except (urllib.error.HTTPError, urllib.error.URLError, ConnectionError, OSError) as e:
            # 4xx 中只有 403 值得重试（网关 WAF 抖动）；其余参数/鉴权错误重试无意义
            code = getattr(e, "code", None)
            if code is not None and code != 403 and 400 <= code < 500:
                raise
            last_err = e
    else:
        raise RuntimeError(f"生图请求三次均失败（网关抖动或不可用）：{last_err}") from last_err
    img_bytes = _parse_response(req["resp_kind"], payload)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(img_bytes)
    return {"backend": backend, "model": model or _env_model(backend) or DEFAULT_MODELS[backend],
            "prompt": prompt, "kind": kind, "size": size, "transparent": transparent,
            "out": out_path}


def append_manifest(manifest_path: str, record: dict) -> None:
    """把一条生成记录追加进 manifest.json（可复现、可单独重生成）。"""
    recs = []
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            recs = json.load(f)
    recs.append(record)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=2)


def _selftest() -> int:
    """完全离线：断言三后端请求结构 + 响应解析 + mock 落盘/清理，绝不打网络。"""
    # 1) 三后端请求结构（无 key 也能构造）
    r_openai = build_request("openai", "icon", size="16:9", transparent=True)
    assert r_openai["url"].endswith("/v1/images/generations"), r_openai["url"]
    assert r_openai["body"]["size"] == "1536x1024", r_openai["body"]
    assert r_openai["body"]["background"] == "transparent", "openai 透明开关缺失"
    assert r_openai["body"].get("output_format") == "png"

    r_gem = build_request("gemini", "full slide", size="16:9")
    assert ":generateContent" in r_gem["url"] and "gemini-3.1-flash-image" in r_gem["url"], r_gem["url"]
    assert r_gem["body"]["generationConfig"]["responseFormat"]["image"]["aspectRatio"] == "16:9"
    assert "x-goog-api-key" in r_gem["headers"]

    r_sd = build_request("seedream", "decor", size="16:9")
    assert r_sd["url"].endswith("/api/v3/images/generations"), r_sd["url"]
    assert r_sd["body"]["watermark"] is False, "seedream 水印未关（PPT 元素会带 AI 水印）"
    assert r_sd["headers"]["Authorization"].startswith("Bearer ")

    try:
        build_request("nope", "x")
        assert False, "未知后端应抛错"
    except ValueError:
        pass

    # 1.5) 中转/网关 env 覆盖（OPENAI_IMAGE_BASE_URL / OPENAI_IMAGE_MODEL / OPENAI_IMAGE_API_KEY）
    _saved = {k: os.environ.get(k) for k in
              ("OPENAI_IMAGE_BASE_URL", "OPENAI_BASE_URL", "OPENAI_IMAGE_MODEL",
               "LIGHT_IMAGEGEN_MODEL", "OPENAI_IMAGE_API_KEY", "OPENAI_API_KEY")}
    try:
        os.environ["OPENAI_IMAGE_BASE_URL"] = "https://relay.example.com/v1/"
        os.environ["OPENAI_IMAGE_MODEL"] = "gpt-image-2"
        os.environ["OPENAI_IMAGE_API_KEY"] = "sk-relay-test"
        r_relay = build_request("openai", "icon")
        assert r_relay["url"] == "https://relay.example.com/v1/images/generations", r_relay["url"]
        assert r_relay["body"]["model"] == "gpt-image-2", r_relay["body"]["model"]
        assert r_relay["headers"]["Authorization"] == "Bearer sk-relay-test"
        assert "openai" in detect_backends(), "OPENAI_IMAGE_API_KEY 应被识别为可用后端"
        # 显式 --model 参数优先级高于 env
        r_cli = build_request("openai", "icon", model="gpt-image-1.5")
        assert r_cli["body"]["model"] == "gpt-image-1.5"
    finally:
        for k, v in _saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    # 2) 响应解析（构造样例 b64，不发网络）
    px = base64.b64encode(b"\x89PNG\r\n\x1a\n").decode()
    assert _parse_response("openai_b64", {"data": [{"b64_json": px}]}) == b"\x89PNG\r\n\x1a\n"
    assert _parse_response("seedream_b64", {"data": [{"b64_json": px}]}) == b"\x89PNG\r\n\x1a\n"
    gem_payload = {"candidates": [{"content": {"parts": [{"text": "x"}, {"inlineData": {"data": px}}]}}]}
    assert _parse_response("gemini_inline", gem_payload) == b"\x89PNG\r\n\x1a\n"

    # 3) 无 key 自动探测应抛"后端不可用"（除非真机器配了 key——那就跳过此断言）
    if not detect_backends():
        try:
            generate("x", os.devnull, backend=None)
            assert False, "无 key 应抛 RuntimeError，不可静默假成功"
        except RuntimeError as e:
            assert "不可用" in str(e)

    # 4) mock 落盘 + 透明底 + 清理
    with tempfile.TemporaryDirectory() as td:
        from PIL import Image
        for kind, tr in (("icon", True), ("decor", False), ("visual_draft", False)):
            out = os.path.join(td, f"{kind}.png")
            rec = generate("占位测试 prompt", out, backend="mock", kind=kind,
                           bbox=(0.1, 0.2, 0.4, 0.5))
            assert os.path.exists(out) and rec["backend"] == "mock"
            with Image.open(out) as im:
                im.load()  # 立即读入像素，释放文件句柄（Windows 下否则锁文件、清理失败）
                assert im.mode == "RGBA", im.mode
                if kind == "icon":
                    assert im.getpixel((0, 0))[3] == 0, "icon 应透明底（四角全透明）"
        # manifest 追加
        mf = os.path.join(td, "manifest.json")
        append_manifest(mf, {"out": "a.png"})
        append_manifest(mf, {"out": "b.png"})
        with open(mf, encoding="utf-8") as f:
            assert len(json.load(f)) == 2
    print("[selftest] PASS imagegen（3 后端请求结构 + 响应解析 + mock 落盘/透明/manifest 全离线）")
    return 0


def main():
    ap = argparse.ArgumentParser(description="imggen-enhanced 三后端统一生图封装")
    ap.add_argument("--prompt", help="生图描述")
    ap.add_argument("-o", "--out", help="输出 PNG 路径")
    ap.add_argument("--backend", choices=["openai", "gemini", "seedream", "mock"],
                    help="指定后端（默认自动探测）")
    ap.add_argument("--type", dest="kind", default="icon",
                    choices=["icon", "illustration", "decor", "background", "visual_draft"])
    ap.add_argument("--model", help="覆盖默认模型 id")
    ap.add_argument("--size", default="16:9", help="16:9/9:16/1:1 或像素 WxH")
    ap.add_argument("--transparent", action="store_true", help="透明背景（仅 openai 原生支持）")
    ap.add_argument("--bbox", help="visual_draft 占位用 x,y,w,h（相对 0-1）")
    ap.add_argument("--manifest", help="把本次记录追加进该 manifest.json")
    ap.add_argument("--timeout", type=int, default=180,
                    help="单次请求超时秒数（gpt-image 出图慢，默认 180）")
    ap.add_argument("--check", action="store_true", help="只探测可用后端")
    ap.add_argument("--selftest", action="store_true", help="完全离线自测")
    args = ap.parse_args()

    if args.selftest:
        raise SystemExit(_selftest())

    if args.check:
        avail = detect_backends()
        print(f"可用生图后端：{avail if avail else '无（配置 key 或用 --backend mock）'}")
        print("  mock 后端始终可用（离线占位）")
        sys.exit(0)

    if not args.prompt or not args.out:
        ap.error("生成图片需要 --prompt 与 -o/--out（或用 --check / --selftest）")
    bbox = tuple(float(x) for x in args.bbox.split(",")) if args.bbox else None
    try:
        rec = generate(args.prompt, args.out, backend=args.backend, kind=args.kind,
                       model=args.model, size=args.size, transparent=args.transparent,
                       bbox=bbox, timeout=args.timeout)
    except RuntimeError as e:
        print(f"[unavailable] {e}")
        sys.exit(2)
    if args.manifest:
        append_manifest(args.manifest, rec)
    print(f"[ok] {rec['backend']} -> {rec['out']}")


if __name__ == "__main__":
    main()
