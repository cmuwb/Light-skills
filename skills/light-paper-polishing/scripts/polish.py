#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""polish.py — LanguageTool-backed grammar/style polish for academic text.

Pipeline:
  1. Read text (--text / --file / stdin).
  2. Chunk on sentence/paragraph boundaries so each chunk stays under the
     anonymous LanguageTool size cap (default 18000 chars, cap is ~20000).
  3. POST each chunk to https://api.languagetool.org/v2/check (level=picky).
  4. Map every match back to an absolute line/column in the ORIGINAL text and
     emit structured findings {line, col, rule, issue, suggestion, context}.
  5. If the endpoint is unreachable / non-200, degrade gracefully to a small
     set of local regex rules so the script still produces findings offline.

Honesty: the endpoint is curl-tested in SKILL.md / references.md (HTTP 200,
2026-06-06). This script reuses that exact endpoint and records the HTTP code
it actually receives at runtime in the JSON output under "_meta".

Usage:
  python polish.py --text "This sentence have a error."
  python polish.py --file paper.txt --language en-US --level picky
  echo "..." | python polish.py --json
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import argparse
import json
import re
import urllib.parse
import urllib.request
import urllib.error

LT_ENDPOINT = "https://api.languagetool.org/v2/check"
MAX_CHUNK = 18000          # stay safely under anonymous ~20k char cap
TIMEOUT = 30


def split_chunks(text, max_chunk=MAX_CHUNK):
    """Split text into <=max_chunk pieces on paragraph/sentence boundaries.

    Returns list of (offset_in_original, chunk_text) so matches can be mapped
    back to absolute positions.
    """
    if len(text) <= max_chunk:
        return [(0, text)]
    chunks = []
    # prefer paragraph boundaries, fall back to sentence, then hard cut
    pieces = re.split(r"(\n\s*\n)", text)
    buf, buf_start, cursor = "", 0, 0
    for piece in pieces:
        if len(buf) + len(piece) > max_chunk and buf:
            chunks.append((buf_start, buf))
            buf, buf_start = "", cursor
        buf += piece
        cursor += len(piece)
    if buf:
        chunks.append((buf_start, buf))
    # any chunk still too big -> hard split
    final = []
    for off, ch in chunks:
        while len(ch) > max_chunk:
            final.append((off, ch[:max_chunk]))
            ch = ch[max_chunk:]
            off += max_chunk
        if ch:
            final.append((off, ch))
    return final


def offset_to_linecol(text, offset):
    prefix = text[:offset]
    line = prefix.count("\n") + 1
    col = offset - (prefix.rfind("\n") + 1) + 1
    return line, col


def check_chunk(chunk, language, level, mother_tongue):
    """POST one chunk to LanguageTool. Returns (http_code, matches_list)."""
    data = {"text": chunk, "language": language, "level": level}
    if mother_tongue:
        data["motherTongue"] = mother_tongue
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        LT_ENDPOINT, data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "Accept": "application/json",
                 "User-Agent": "light-paper-polishing/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            code = resp.getcode()
            payload = json.loads(resp.read().decode("utf-8"))
            return code, payload.get("matches", [])
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:  # network down, DNS, timeout, SSL...
        return None, None


# ---- offline fallback rules (no network) ----
LOCAL_RULES = [
    (r"\b(\w+)\s+\1\b", "DUP_WORD", "Repeated word.", None),
    (r"\bthis\s+(results|datas|analyses)\b", "AGREEMENT", "Possible number disagreement.", None),
    (r"\ba\s+([aeiouAEIOU]\w+)", "A_VS_AN", "Use 'an' before a vowel sound.", "an \\1"),
    (r"\s+([,.;:])", "SPACE_BEFORE_PUNCT", "No space before punctuation.", "\\1"),
    (r"\b(dont|cant|wont|isnt|arent|doesnt)\b", "MISSING_APOSTROPHE", "Missing apostrophe.", None),
    (r"  +", "DOUBLE_SPACE", "Multiple consecutive spaces.", " "),
]


def local_check(text):
    findings = []
    for pat, rid, msg, repl in LOCAL_RULES:
        for m in re.finditer(pat, text):
            line, col = offset_to_linecol(text, m.start())
            suggestion = None
            if repl is not None:
                try:
                    suggestion = re.sub(pat, repl, m.group(0))
                except re.error:
                    suggestion = None
            findings.append({
                "line": line, "col": col, "rule": rid,
                "issue": msg, "suggestion": suggestion,
                "context": text[max(0, m.start() - 25):m.end() + 25].replace("\n", " "),
                "source": "local",
            })
    return findings


def run(text, language, level, mother_tongue):
    chunks = split_chunks(text)
    findings = []
    http_codes = []
    online_ok = True
    for off, chunk in chunks:
        code, matches = check_chunk(chunk, language, level, mother_tongue)
        http_codes.append(code)
        if code != 200 or matches is None:
            online_ok = False
            break
        for m in matches:
            abs_off = off + m["offset"]
            line, col = offset_to_linecol(text, abs_off)
            reps = [r["value"] for r in m.get("replacements", [])][:3]
            findings.append({
                "line": line, "col": col,
                "rule": m.get("rule", {}).get("id", ""),
                "issue": m.get("message", ""),
                "suggestion": "; ".join(reps) if reps else None,
                "context": m.get("context", {}).get("text", ""),
                "source": "languagetool",
            })
    if not online_ok:
        findings = local_check(text)
    return {
        "_meta": {
            "endpoint": LT_ENDPOINT,
            "http_codes": http_codes,
            "mode": "languagetool" if online_ok else "local-fallback",
            "n_chunks": len(chunks),
            "n_findings": len(findings),
        },
        "findings": findings,
    }


def main():
    ap = argparse.ArgumentParser(description="LanguageTool-backed academic polish.")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--text")
    g.add_argument("--file")
    ap.add_argument("--language", default="en-US")
    ap.add_argument("--level", default="picky", choices=["default", "picky"])
    ap.add_argument("--mother-tongue", default="zh-CN")
    ap.add_argument("--json", action="store_true", help="emit raw JSON")
    args = ap.parse_args()

    if args.text is not None:
        text = args.text
    elif args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read()
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        # self-test when no input (so the script always runs)
        text = ("This sentence have a error.  In conclusion, the results "
                "is significant and a unique approach was used used.")
        print("[self-test: no input given, using built-in sample]\n", file=sys.stderr)

    result = run(text, args.language, args.level, args.mother_tongue)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    meta = result["_meta"]
    print(f"mode={meta['mode']}  http={meta['http_codes']}  "
          f"chunks={meta['n_chunks']}  findings={meta['n_findings']}")
    for f in result["findings"]:
        sug = f["suggestion"] or "—"
        print(f"  L{f['line']}:C{f['col']} [{f['rule']}] {f['issue']}")
        print(f"      → {sug}   ({f['source']})")


if __name__ == "__main__":
    main()
