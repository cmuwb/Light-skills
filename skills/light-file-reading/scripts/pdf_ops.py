#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 读取与结构操作工具集（light-file-reading）。

依赖：pypdf（结构操作/内嵌文本），pdfplumber（版面文本+表格），pandas（表格→DataFrame）。
扫描件 OCR 不在此处——见 references/PDF-REF.md（pytesseract+pdf2image）。

所有函数可独立调用；本文件直接运行会用 reportlab 合成一个测试 PDF 跑全流程自检
（reportlab 仅自检需要，主功能不依赖它）。
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台默认 GBK，强制 UTF-8 防乱码


def read_meta(path):
    """读取页数与元数据（标题/作者/主题等），返回 dict。"""
    from pypdf import PdfReader
    r = PdfReader(path)
    m = r.metadata or {}
    return {
        "pages": len(r.pages),
        "title": m.get("/Title"),
        "author": m.get("/Author"),
        "subject": m.get("/Subject"),
        "creator": m.get("/Creator"),
    }


def extract_text(path, layout=True):
    """逐页抽文本。layout=True 用 pdfplumber 保留版面（推荐论文/多栏），
    返回 [(page_no, text), ...]（page_no 从 1 起）。"""
    import pdfplumber
    out = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            txt = page.extract_text(layout=layout) or ""
            out.append((i, txt))
    return out


def extract_tables(path):
    """抽所有表格 → [DataFrame]。首行作表头。空表跳过。"""
    import pdfplumber
    import pandas as pd
    dfs = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for tbl in page.extract_tables():
                if tbl and len(tbl) > 1:
                    dfs.append(pd.DataFrame(tbl[1:], columns=tbl[0]))
    return dfs


def merge(paths, out_path):
    """合并多个 PDF 为一个，返回输出页数。"""
    from pypdf import PdfReader, PdfWriter
    w = PdfWriter()
    for p in paths:
        for page in PdfReader(p).pages:
            w.add_page(page)
    with open(out_path, "wb") as f:
        w.write(f)
    return len(w.pages)


def split(path, out_dir):
    """每页拆成单独 PDF，返回生成的文件路径列表。"""
    import os
    from pypdf import PdfReader, PdfWriter
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, page in enumerate(PdfReader(path).pages, 1):
        w = PdfWriter()
        w.add_page(page)
        op = os.path.join(out_dir, f"page_{i}.pdf")
        with open(op, "wb") as f:
            w.write(f)
        paths.append(op)
    return paths


def rotate(path, out_path, degrees=90, pages=None):
    """旋转指定页（pages 为 0 起索引列表，None=全部），degrees 顺时针。"""
    from pypdf import PdfReader, PdfWriter
    r = PdfReader(path)
    w = PdfWriter()
    for i, page in enumerate(r.pages):
        if pages is None or i in pages:
            page.rotate(degrees)
        w.add_page(page)
    with open(out_path, "wb") as f:
        w.write(f)
    return out_path


def _selftest():
    """合成测试 PDF（reportlab）跑全流程，断言每步结果，结束清理临时文件。"""
    import os
    import tempfile
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors

    tmp = tempfile.mkdtemp(prefix="pdfops_")
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

    tables = extract_tables(src)
    assert tables and list(tables[0].columns) == ["Metric", "Value"], tables

    merged = os.path.join(tmp, "merged.pdf")
    assert merge([src, src], merged) == 4

    parts = split(src, os.path.join(tmp, "parts"))
    assert len(parts) == 2

    rot = rotate(src, os.path.join(tmp, "rot.pdf"), 90, pages=[0])
    assert read_meta(rot)["pages"] == 2

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print("pdf_ops self-test OK: meta/text/tables/merge/split/rotate all passed")


if __name__ == "__main__":
    if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] != "--selftest"):
        raise SystemExit(f"usage: python {sys.argv[0]} [--selftest]")
    _selftest()
