#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 读取与结构操作工具集（light-file-reading）。

依赖：pypdf（结构操作/内嵌文本），pdfplumber（版面文本+表格），pandas（表格→DataFrame）。
扫描件 OCR 不在此处——见 references/PDF-REF.md（pytesseract+pdf2image）。

所有函数可独立调用。

CLI（处理真实文件）：
    python pdf_ops.py meta        f.pdf
    python pdf_ops.py extract-text f.pdf [--pages 1-3,5] [--no-layout]
    python pdf_ops.py extract-tables f.pdf
    python pdf_ops.py merge a.pdf b.pdf --out merged.pdf
    python pdf_ops.py split      f.pdf --out-dir parts/
    python pdf_ops.py rotate     f.pdf --out r.pdf [--degrees 90] [--pages 1,2]
自检（reportlab 合成、离线、自清理）：
    python pdf_ops.py --selftest
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台默认 GBK，强制 UTF-8 防乱码


def _imp(mod, pip_name=None):
    """惰性导入，缺失时给 pip 提示而非裸 ImportError。"""
    import importlib
    try:
        return importlib.import_module(mod)
    except ImportError as e:  # pragma: no cover - 仅依赖缺失时触发
        raise SystemExit(f"缺少 {mod}，请先安装：pip install {pip_name or mod}") from e


def read_meta(path):
    """读取页数与元数据（标题/作者/主题等），返回 dict。"""
    pypdf = _imp("pypdf")
    r = pypdf.PdfReader(path)
    m = r.metadata or {}
    return {
        "pages": len(r.pages),
        "title": m.get("/Title"),
        "author": m.get("/Author"),
        "subject": m.get("/Subject"),
        "creator": m.get("/Creator"),
    }


def extract_text(path, layout=True, pages=None):
    """逐页抽文本。layout=True 用 pdfplumber 保留版面（推荐论文/多栏）。
    pages 为 0 起页索引可迭代对象（None=全部），返回 [(page_no, text), ...]
    （page_no 从 1 起，对应原文档真实页号）。"""
    pdfplumber = _imp("pdfplumber")
    want = set(pages) if pages is not None else None
    out = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            if want is not None and i not in want:
                continue
            txt = page.extract_text(layout=layout) or ""
            out.append((i + 1, txt))
    return out


def extract_tables(path):
    """抽所有表格 → [DataFrame]。首行作表头。空表跳过。

    诚实警示：这是最朴素的 first-row-header，对合并单元格/跨行表头/错位会静默出错。
    抽表后务必跑 verify_tables() 看每表 confidence，低分表别直接喂下游。"""
    pdfplumber = _imp("pdfplumber")
    pd = _imp("pandas")
    dfs = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for tbl in page.extract_tables():
                if tbl and len(tbl) > 1:
                    dfs.append(pd.DataFrame(tbl[1:], columns=tbl[0]))
    return dfs


# ── 表格抽取自校验 + 置信度门控 ────────────────────────────────────────
# 竞品（MinerU/marker）的核心壁垒是表格结构识别；Light 的 extract_tables 是朴素
# first-row-header，对合并单元格/ragged row 静默出错、下游污染最重。这里给每个抽到
# 的表打 confidence 分并列具体缺陷，低于阈值时要求人工复核/换策略，杜绝静默出错。

_TABLE_CONF_THRESHOLD = 0.6   # 低于此分判为「存疑，需人工复核」


def _norm_cell(c):
    """单元格规范化为字符串（None→空串），去首尾空白。"""
    return "" if c is None else str(c).strip()


def _assess_table(rows):
    """对一个原始表格（list[list]，pdfplumber.extract_tables 的单表）做结构体检。

    纯函数、不碰文件，便于单测。返回:
      {n_header_cols, n_rows, confidence(0-1), issues:[...], ragged_rows, recommend}
    检测：空表头单元、ragged row（列数与表头不符）、重复表头名、空列、
    行内疑似合并单元格（非边缘的空洞）。confidence 从 1.0 起按缺陷扣分。
    """
    issues = []
    if not rows:
        return {"n_header_cols": 0, "n_rows": 0, "confidence": 0.0,
                "issues": [{"type": "empty_table", "detail": "无任何行"}],
                "ragged_rows": 0, "recommend": "空表，跳过或换抽取策略"}

    header = [_norm_cell(c) for c in rows[0]]
    n_cols = len(header)
    body = rows[1:]
    conf = 1.0

    # 1) 空表头单元
    empty_hdr = [i for i, h in enumerate(header) if h == ""]
    if empty_hdr:
        issues.append({"type": "empty_header",
                       "detail": f"表头有 {len(empty_hdr)} 个空单元(列号 {empty_hdr})",
                       "suggestion": "可能跨行表头被切断；试 lines_strict 或合并表头两行"})
        conf -= 0.3

    # 2) 重复表头名（DataFrame 列名冲突，下游按名取列会取错）
    seen, dup = set(), set()
    for h in header:
        if h and h in seen:
            dup.add(h)
        seen.add(h)
    if dup:
        issues.append({"type": "duplicate_header",
                       "detail": f"表头重复名: {sorted(dup)}",
                       "suggestion": "按列名取数会拿错列；重命名或按列号定位"})
        conf -= 0.2

    # 3) ragged row：每行有效列数与表头列数不符
    ragged = 0
    for ri, r in enumerate(body):
        if len(r) != n_cols:
            ragged += 1
    if ragged:
        frac = ragged / max(len(body), 1)
        issues.append({"type": "ragged_rows",
                       "detail": f"{ragged}/{len(body)} 行列数与表头({n_cols})不符",
                       "suggestion": "错位/漏框线；用 debug-tablefinder 看框线，或换 text 策略"})
        conf -= min(0.5, frac * 0.5 + 0.1)

    # 4) 行内疑似合并单元格：非边缘位置出现空洞（左右都有内容、中间空）
    merged_like = 0
    for r in body:
        cells = [_norm_cell(c) for c in r]
        for k in range(1, len(cells) - 1):
            if cells[k] == "" and cells[k - 1] != "" and cells[k + 1] != "":
                merged_like += 1
                break
    if merged_like:
        issues.append({"type": "interior_blank",
                       "detail": f"{merged_like} 行存在行内空洞(疑似合并单元格)",
                       "suggestion": "合并单元格会被拆成 None；核对原表是否有跨列合并"})
        conf -= min(0.2, merged_like / max(len(body), 1) * 0.2)

    # 5) 整列为空
    blank_cols = []
    for ci in range(n_cols):
        col_vals = [_norm_cell(r[ci]) for r in body if ci < len(r)]
        if col_vals and all(v == "" for v in col_vals):
            blank_cols.append(ci)
    if blank_cols:
        issues.append({"type": "blank_column",
                       "detail": f"整列为空: 列号 {blank_cols}",
                       "suggestion": "多余切分线产生空列；调 snap_tolerance"})
        conf -= 0.1

    conf = max(0.0, round(conf, 3))
    recommend = ("表格抽取存疑，建议人工复核或换 lines_strict/text 策略后重抽"
                 if conf < _TABLE_CONF_THRESHOLD else "结构可信，可喂下游")
    return {"n_header_cols": n_cols, "n_rows": len(body), "confidence": conf,
            "issues": issues, "ragged_rows": ragged, "recommend": recommend}


def verify_tables(path, debug_png_dir=None):
    """抽所有表格并逐表打 confidence 分 + 列缺陷，可选导出 debug PNG 供肉眼复核。

    debug_png_dir 非空时，对含可疑表的页用 pdfplumber page.to_image(resolution=150)
    .debug_tablefinder() 落 PNG（看完即删，勿留库内）。返回:
      [{page, index, ...(_assess_table 的字段), debug_png?}]
    """
    pdfplumber = _imp("pdfplumber")
    out = []
    with pdfplumber.open(path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            tbls = page.extract_tables()
            page_has_suspect = False
            for ti, tbl in enumerate(tbls):
                if not tbl:
                    continue
                a = _assess_table(tbl)
                a["page"] = pno
                a["index"] = ti
                if a["confidence"] < _TABLE_CONF_THRESHOLD:
                    page_has_suspect = True
                out.append(a)
            if debug_png_dir and page_has_suspect:
                try:
                    import os
                    os.makedirs(debug_png_dir, exist_ok=True)
                    im = page.to_image(resolution=150)
                    im.debug_tablefinder()
                    png = os.path.join(debug_png_dir, f"debug_p{pno}.png")
                    im.save(png)
                    for a in out:
                        if a.get("page") == pno:
                            a["debug_png"] = png
                except Exception as e:  # 渲染器/依赖缺失不致命，如实标注
                    for a in out:
                        if a.get("page") == pno:
                            a["debug_png_error"] = str(e)
    return out


# ── 版面几何体检（挂接 _shared/visual_qa 契约）────────────────────────
# 灭病5：把页面元素的 AABB 喂回共享 visual_qa 几何检测器，发现表/图重叠、溢出页面
# 等版面问题（reading-order hazard 的确定性代理）。像素级回看需把页渲染成 PNG 再喂
# 多模态 Opus（render_then_review 协议，见 visual_qa.visual_qa_rubric）。
def _load_visual_qa():
    """脚本模式导入 _shared/visual_qa（参考 _shared/README 方式 B）。"""
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "_shared"))
    import visual_qa
    return visual_qa


def _page_shapes(page):
    """把一页的表格框 + 图片框收成 visual_qa 的 AABB 元素列表。
    坐标用 pdf 点(pt)，原点左上(与 visual_qa 一致)。"""
    shapes = []
    try:
        for ti, t in enumerate(page.find_tables()):
            x0, top, x1, bottom = t.bbox
            shapes.append({"id": f"table{ti}", "kind": "table",
                           "x": float(x0), "y": float(top),
                           "w": float(x1 - x0), "h": float(bottom - top)})
    except Exception:
        pass
    for ii, im in enumerate(page.images or []):
        shapes.append({"id": f"image{ii}", "kind": "image",
                       "x": float(im["x0"]), "y": float(im["top"]),
                       "w": float(im["x1"] - im["x0"]),
                       "h": float(im["bottom"] - im["top"])})
    return shapes


def page_layout_qa(path, pages=None):
    """逐页做版面几何体检（挂接 _shared/visual_qa）。检测表/图重叠、溢出页面边界。

    返回 [{page, shapes_checked, qa: <visual_qa.qa_report>}]。qa_report 中
    pixel_review_done=False，明确标注「未做像素级回看」——要做视觉品味/对比度核对
    需按 visual_qa_rubric() 把页面渲染成 PNG 喂回多模态 Opus。"""
    pdfplumber = _imp("pdfplumber")
    vq = _load_visual_qa()
    want = set(pages) if pages is not None else None
    out = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            if want is not None and i not in want:
                continue
            shapes = _page_shapes(page)
            issues = vq.detect_geometry_issues(
                shapes, (float(page.width), float(page.height)))
            out.append({"page": i + 1, "shapes_checked": len(shapes),
                        "qa": vq.qa_report(issues, vlm_findings=None)})
    return out


def merge(paths, out_path):
    """合并多个 PDF 为一个，返回输出页数。"""
    pypdf = _imp("pypdf")
    w = pypdf.PdfWriter()
    for p in paths:
        for page in pypdf.PdfReader(p).pages:
            w.add_page(page)
    with open(out_path, "wb") as f:
        w.write(f)
    return len(w.pages)


def split(path, out_dir):
    """每页拆成单独 PDF，返回生成的文件路径列表。"""
    import os
    pypdf = _imp("pypdf")
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, page in enumerate(pypdf.PdfReader(path).pages, 1):
        w = pypdf.PdfWriter()
        w.add_page(page)
        op = os.path.join(out_dir, f"page_{i}.pdf")
        with open(op, "wb") as f:
            w.write(f)
        paths.append(op)
    return paths


def rotate(path, out_path, degrees=90, pages=None):
    """旋转指定页（pages 为 0 起索引列表，None=全部），degrees 顺时针。"""
    pypdf = _imp("pypdf")
    r = pypdf.PdfReader(path)
    w = pypdf.PdfWriter()
    for i, page in enumerate(r.pages):
        if pages is None or i in pages:
            page.rotate(degrees)
        w.add_page(page)
    with open(out_path, "wb") as f:
        w.write(f)
    return out_path


def parse_page_range(spec):
    """把 '1-3,5' 这类 1 起的页范围字符串解析为排序去重的 0 起索引列表。
    None 或空串返回 None（表示全部）。"""
    if not spec:
        return None
    idx = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            lo, hi = int(a), int(b)
            if lo > hi:
                lo, hi = hi, lo
            for n in range(lo, hi + 1):
                idx.add(n - 1)
        else:
            idx.add(int(part) - 1)
    bad = [i for i in idx if i < 0]
    if bad:
        raise SystemExit(f"页范围非法（页号从 1 起）：{spec}")
    return sorted(idx)


def _selftest():
    """合成测试 PDF（reportlab）跑全流程，断言每步结果，结束清理临时文件。"""
    import os
    import tempfile
    _imp("reportlab")
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors

    # 先验证纯函数 parse_page_range（无需文件）
    assert parse_page_range("1-3,5") == [0, 1, 2, 4], parse_page_range("1-3,5")
    assert parse_page_range(None) is None
    assert parse_page_range("2") == [1]

    # 纯函数 _assess_table（无需文件）：分别造干净/空表头/ragged/重复名/合并洞表
    clean = [["Metric", "Value"], ["Acc", "0.91"], ["F1", "0.88"]]
    a_clean = _assess_table(clean)
    assert a_clean["confidence"] >= _TABLE_CONF_THRESHOLD and not a_clean["issues"], a_clean

    a_emptyhdr = _assess_table([["Metric", ""], ["Acc", "0.91"]])
    assert any(i["type"] == "empty_header" for i in a_emptyhdr["issues"]), a_emptyhdr

    a_ragged = _assess_table([["a", "b", "c"], ["1", "2"], ["3", "4", "5"]])
    assert a_ragged["ragged_rows"] == 1 and any(
        i["type"] == "ragged_rows" for i in a_ragged["issues"]), a_ragged

    a_dup = _assess_table([["x", "x"], ["1", "2"]])
    assert any(i["type"] == "duplicate_header" for i in a_dup["issues"]), a_dup
    # 严重缺陷叠加应跌破阈值
    a_bad = _assess_table([["x", "", "x"], ["1", "2"], ["3", "4", "5", "6"]])
    assert a_bad["confidence"] < _TABLE_CONF_THRESHOLD, a_bad

    tmp = tempfile.mkdtemp(prefix="pdfops_")
    try:
        src = os.path.join(tmp, "sample.pdf")
        styles = getSampleStyleSheet()
        tbl = Table([["Metric", "Value"], ["Accuracy", "0.91"], ["F1", "0.88"]])
        tbl.setStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)])
        story = [
            Paragraph("Light File Reading Self Test", styles["Title"]),
            Paragraph("This is page one body text for extraction.", styles["Normal"]),
            tbl,
            PageBreak(),
            Paragraph("Second page content.", styles["Normal"]),
        ]
        SimpleDocTemplate(src, pagesize=letter).build(story)

        meta = read_meta(src)
        assert meta["pages"] == 2, meta

        text = extract_text(src)
        assert len(text) == 2 and "page one" in text[0][1], text[0][1][:80]

        # 页范围：只取第 2 页，page_no 仍是真实页号 2
        only2 = extract_text(src, pages=[1])
        assert len(only2) == 1 and only2[0][0] == 2, only2

        tables = extract_tables(src)
        assert tables and list(tables[0].columns) == ["Metric", "Value"], tables

        # verify_tables：真 PDF 上跑通，干净表 confidence 应达标
        vt = verify_tables(src)
        assert vt and all("confidence" in t for t in vt), vt
        assert vt[0]["confidence"] >= _TABLE_CONF_THRESHOLD, vt[0]

        # page_layout_qa：挂接 _shared/visual_qa，返回 qa_report 结构且标注未做像素回看
        plq = page_layout_qa(src)
        assert plq and plq[0]["qa"]["schema"] == "light.visual_qa.v1", plq
        assert plq[0]["qa"]["pixel_review_done"] is False, plq[0]
        # 直接调几何检测器验证 import 真能跑（造一对重叠框）
        vq = _load_visual_qa()
        ov = vq.detect_geometry_issues(
            [{"id": "t0", "x": 0, "y": 0, "w": 50, "h": 50},
             {"id": "t1", "x": 20, "y": 20, "w": 50, "h": 50}], (100, 100))
        assert any(i["type"] == "overlap" for i in ov), ov

        merged = os.path.join(tmp, "merged.pdf")
        assert merge([src, src], merged) == 4

        parts = split(src, os.path.join(tmp, "parts"))
        assert len(parts) == 2

        rot = rotate(src, os.path.join(tmp, "rot.pdf"), 90, pages=[0])
        assert read_meta(rot)["pages"] == 2
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    print("pdf_ops self-test OK: "
          "meta/text/pagerange/tables/verify_tables/layout_qa/merge/split/rotate "
          "+ _assess_table(5 形态) all passed")


def _cli(argv):
    import argparse
    import json
    ap = argparse.ArgumentParser(prog="pdf_ops.py", description="PDF 读取与结构操作")
    ap.add_argument("--selftest", action="store_true",
                    help="reportlab 合成自检（离线、自清理），CI 用此标志")
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("meta", help="页数+元数据").add_argument("file")

    sp = sub.add_parser("extract-text", help="逐页抽文本")
    sp.add_argument("file")
    sp.add_argument("--pages", help="页范围 1 起，如 1-3,5（默认全部）")
    sp.add_argument("--no-layout", action="store_true", help="不保留版面")

    sub.add_parser("extract-tables", help="抽表格").add_argument("file")

    sp = sub.add_parser("verify-tables", help="抽表格并打 confidence 分+列缺陷")
    sp.add_argument("file")
    sp.add_argument("--debug-png-dir", help="可疑表落 debug PNG 的目录（看完即删）")

    sp = sub.add_parser("layout-qa", help="版面几何体检（挂接 _shared/visual_qa）")
    sp.add_argument("file")
    sp.add_argument("--pages", help="页范围 1 起（默认全部）")

    sp = sub.add_parser("merge", help="合并多个 PDF")
    sp.add_argument("files", nargs="+")
    sp.add_argument("--out", required=True)

    sp = sub.add_parser("split", help="逐页拆分")
    sp.add_argument("file")
    sp.add_argument("--out-dir", required=True)

    sp = sub.add_parser("rotate", help="旋转页面")
    sp.add_argument("file")
    sp.add_argument("--out", required=True)
    sp.add_argument("--degrees", type=int, default=90)
    sp.add_argument("--pages", help="页范围 1 起（默认全部）")

    args = ap.parse_args(argv)

    if args.selftest:
        _selftest()
        return
    if not args.cmd:
        ap.print_help()
        raise SystemExit(2)

    if args.cmd == "meta":
        print(json.dumps(read_meta(args.file), ensure_ascii=False, indent=2))
    elif args.cmd == "extract-text":
        for no, txt in extract_text(args.file, layout=not args.no_layout,
                                    pages=parse_page_range(args.pages)):
            print(f"===== page {no} =====")
            print(txt)
    elif args.cmd == "extract-tables":
        dfs = extract_tables(args.file)
        print(f"抽到 {len(dfs)} 个表格")
        for i, df in enumerate(dfs, 1):
            print(f"--- table {i} (shape={df.shape}) ---")
            print(df.to_csv(index=False))
    elif args.cmd == "verify-tables":
        rep = verify_tables(args.file, debug_png_dir=args.debug_png_dir)
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        suspect = [t for t in rep if t["confidence"] < _TABLE_CONF_THRESHOLD]
        if suspect:
            print(f"[warn] {len(suspect)}/{len(rep)} 个表 confidence "
                  f"< {_TABLE_CONF_THRESHOLD}，建议人工复核", file=sys.stderr)
    elif args.cmd == "layout-qa":
        rep = page_layout_qa(args.file, pages=parse_page_range(args.pages))
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    elif args.cmd == "merge":
        n = merge(args.files, args.out)
        print(f"合并 {len(args.files)} 个 PDF → {args.out}（{n} 页）")
    elif args.cmd == "split":
        parts = split(args.file, args.out_dir)
        print(f"拆出 {len(parts)} 页到 {args.out_dir}")
    elif args.cmd == "rotate":
        out = rotate(args.file, args.out, degrees=args.degrees,
                     pages=parse_page_range(args.pages))
        print(f"旋转完成 → {out}")


if __name__ == "__main__":
    _cli(sys.argv[1:])
