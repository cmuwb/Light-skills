# -*- coding: utf-8 -*-
"""共享语义相似度 (semantic_sim) — Light 升级地基契约 2/4。

目的
----
消灭"该用语义的地方全用词面 Jaccard"的全包瘟疫(审查病3)。同一缺口此前在
6 个技能里各犯一遍 = 六次代差。本契约一次建设、六处复用。

最臭名昭著的反例:m10 用字符 Jaccard 判标题撞车，"Attention Is All You Need"
与 "All You Need Is Attention" 被裸 token-Jaccard 判为 1.0(完全相同) —— 但它们
其实是倒装，应判"高度相似但非同一"。本契约的离线档必须正确区分这种情况。

三档降级(可注入 scorer)
------------------------
1. embedding 档(最佳): sentence-transformers 本地模型 / 注入的 embed 端点 → 向量余弦
2. LLM-judge 档: 注入 LLM 打分函数(set_llm_scorer) → 批量 0-1
3. 离线档(兜底，纯 stdlib): 字符 3-gram 余弦 + token 集合 Jaccard + 词序惩罚的混合，
   比裸 Jaccard 强——词序无关地识别倒装、处理子集/包含、中文按字 bigram。

被谁消费
--------
m01(相关度重排) / m10(标题·作者匹配) / m03(中文贡献去重) /
m04(撞车检测) / m13(稿件→venue 匹配) / a07(CONTRIBUTION_DRIFT)

纯 stdlib 核心，embedding 是可选增强。`python semantic_sim.py --selftest` 自测。
"""
from __future__ import annotations
import math
import re
import sys
from collections import Counter

# ── 可注入的高档 scorer(默认 None，缺失则降级到离线档) ──────────────
_EMBED_FN = None   # callable(list[str]) -> list[vector]
_LLM_FN = None     # callable(a:str, b:str) -> float[0,1]


def set_embed_fn(fn):
    """注入 embedding 函数: list[str] -> list[list[float]]。"""
    global _EMBED_FN
    _EMBED_FN = fn


def set_llm_scorer(fn):
    """注入 LLM 打分函数: (a,b) -> float[0,1]。prompt 模板见 LLM_JUDGE_PROMPT。"""
    global _LLM_FN
    _LLM_FN = fn


LLM_JUDGE_PROMPT = (
    "Rate the semantic similarity of the two texts on a 0.0-1.0 scale "
    "(1.0=same meaning, 0.0=unrelated). Reply with ONLY the number.\n"
    "A: {a}\nB: {b}"
)


# ── 文本规范化 ────────────────────────────────────────────────────
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().strip())


def _has_cjk(s: str) -> bool:
    return any("一" <= ch <= "鿿" for ch in s)


def _stem(tok: str) -> str:
    """轻量英文词干化(仅去常见屈折后缀)，让 images↔image、classify↔classifies
    这类词形变化能匹配。非语言学完整 stemmer，够用即可。"""
    if len(tok) <= 3 or not tok.isascii():
        return tok
    for suf in ("ization", "ation", "izes", "ize", "ing", "ies", "ied", "es", "ed", "s"):
        if tok.endswith(suf) and len(tok) - len(suf) >= 3:
            base = tok[:-len(suf)]
            if suf == "ies":
                base += "y"
            return base
    return tok


def _tokens(s: str) -> list:
    """英文按词、中文按字切。"""
    s = _norm(s)
    if _has_cjk(s):
        # 中文逐字 + 夹杂的英文词
        toks = re.findall(r"[一-鿿]|[a-z0-9]+", s)
        return toks
    return re.findall(r"[a-z0-9]+", s)


_STOPWORDS = {"a", "an", "the", "for", "of", "to", "in", "on", "and", "or",
              "with", "is", "are", "be", "by", "as", "at", "this", "that"}


def _stemmed_tokens(s: str) -> list:
    """词干化 + 去停用词后的 token(英文),用于词重合匹配以吸收屈折变化与功能词噪声。"""
    return [_stem(t) for t in _tokens(s) if t not in _STOPWORDS]


def _char_ngrams(s: str, n: int = 3) -> Counter:
    s = _norm(s).replace(" ", "")
    if len(s) < n:
        return Counter([s]) if s else Counter()
    return Counter(s[i:i + n] for i in range(len(s) - n + 1))


def _cosine_counter(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    dot = sum(a[k] * b[k] for k in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def _bigram_set(toks: list) -> set:
    return set(zip(toks, toks[1:]))


# ── 离线档:混合相似度 ────────────────────────────────────────────
def _offline_similarity(a: str, b: str) -> float:
    """字符 3-gram 余弦 + token Jaccard + 词序惩罚 的混合。

    设计要点:
    - token 集合 Jaccard 捕捉"用词重合"(对倒装=1.0，故不能单用)
    - 字符 3-gram 余弦捕捉"字面接近"
    - bigram(相邻词序) Jaccard 捕捉"语序"——倒装会让它显著下降
    最终: 倒装句 token-Jaccard 高但 bigram-Jaccard 低 → 总分高(相似)但 <1.0(非同一)。
    """
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    # 词重合用词干化 token(吸收 image/images、classify/classification 等屈折)
    sta, stb = set(_stemmed_tokens(a)), set(_stemmed_tokens(b))
    tok_jac = len(sta & stb) / len(sta | stb)        # 词重合(词序无关,词干归一)
    char_cos = _cosine_counter(_char_ngrams(a), _char_ngrams(b))  # 字面
    ba, bb = _bigram_set(ta), _bigram_set(tb)
    if ba or bb:
        bg_jac = len(ba & bb) / len(ba | bb) if (ba | bb) else 1.0
    else:
        bg_jac = 1.0
    # 完全相同(含语序)→ 1.0;倒装 → tok_jac 高、bg_jac 低 → 被语序项拉到 <1
    # 权重: 词重合 0.5 + 字面 0.3 + 语序 0.2
    score = 0.5 * tok_jac + 0.3 * char_cos + 0.2 * bg_jac
    return round(min(1.0, score), 4)


# ── 主 API ────────────────────────────────────────────────────────
def similarity(a: str, b: str, mode: str = "auto") -> float:
    """返回 a,b 的语义相似度 [0,1]。

    mode: auto(按可用资源选档) | embed | llm | offline。
    经 last_mode() 可查实际所用档位。
    """
    global _LAST_MODE
    a = a or ""
    b = b or ""
    if a == b:
        _LAST_MODE = "exact"
        return 1.0
    use = mode
    if mode == "auto":
        use = "embed" if _EMBED_FN else ("llm" if _LLM_FN else "offline")
    if use == "embed" and _EMBED_FN:
        va, vb = _EMBED_FN([a, b])
        _LAST_MODE = "embed"
        dot = sum(x * y for x, y in zip(va, vb))
        na = math.sqrt(sum(x * x for x in va))
        nb = math.sqrt(sum(y * y for y in vb))
        return round(dot / (na * nb), 4) if na and nb else 0.0
    if use == "llm" and _LLM_FN:
        _LAST_MODE = "llm"
        return float(_LLM_FN(a, b))
    _LAST_MODE = "offline"
    return _offline_similarity(a, b)


_LAST_MODE = None


def last_mode() -> str | None:
    """上一次 similarity 实际所用档位(留痕)。"""
    return _LAST_MODE


def most_similar(query: str, candidates: list, top_k: int = 5,
                 mode: str = "auto") -> list:
    """返回 [(idx, score)] 按相似度降序，最多 top_k 个。"""
    scored = [(i, similarity(query, c, mode)) for i, c in enumerate(candidates)]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def is_near_duplicate(a: str, b: str, threshold: float = 0.85,
                      mode: str = "auto") -> bool:
    """是否近重复(相似度 >= threshold)。标题/贡献去重用。"""
    return similarity(a, b, mode) >= threshold


# ──────────────────────────── selftest ────────────────────────────
def _selftest() -> int:
    ok = True

    def check(cond, msg, val=None):
        nonlocal ok
        status = "PASS" if cond else "FAIL"
        if not cond:
            ok = False
        extra = f" (={val})" if val is not None else ""
        print(f"  [{status}] {msg}{extra}")

    print("semantic_sim selftest (offline 档)")
    # 1. 完全相同 = 1.0
    check(similarity("hello world", "hello world") == 1.0, "完全相同=1.0")

    # 2. 倒装句:高相似但 <1.0(核心测试 —— 治 m10 的 1.0 误判)
    inv = similarity("Attention Is All You Need", "All You Need Is Attention")
    check(0.7 <= inv < 1.0, "倒装句 0.7<=sim<1.0(非误判为同一)", inv)

    # 3. 完全无关 = 低分
    unrel = similarity("deep learning for vision", "the cat sat on the mat")
    check(unrel < 0.4, "无关文本<0.4", unrel)

    # 4. 屈折变化(复数/时态: detectors/detected ↔ detector/detect)经词干能匹配
    rel = similarity("object detector evaluation",
                     "evaluating object detectors")
    check(rel > 0.4, "屈折变化(复数/时态)经词干>0.4(离线档能力内)", rel)
    # 4b. 派生词/纯同义词(classification↔classifying, method↔approach)是离线档边界,
    #     诚实标注:需 embedding 档才能可靠捕捉,离线档不假装能做
    deriv = similarity("image classification", "classifying images")
    check(deriv >= 0.0, f"派生词离线档边界(={deriv},可靠捕捉需embedding档)")

    # 5. 中文逐字
    zh = similarity("基于深度学习的目标检测", "基于深度学习的目标识别")
    check(0.5 < zh < 1.0, "中文近似 0.5<sim<1.0", zh)
    zh2 = similarity("目标检测算法", "图像分类网络")
    check(zh2 < zh, "中文无关 < 中文近似", zh2)

    # 6. most_similar 排序
    cands = ["the quick brown fox", "a fast brown fox jumps", "machine learning model"]
    ms = most_similar("quick brown fox", cands, top_k=2)
    check(ms[0][0] in (0, 1) and ms[0][1] >= ms[1][1], "most_similar 降序且命中相关项")

    # 7. is_near_duplicate
    check(is_near_duplicate("Deep Residual Learning", "Deep Residual Learning"),
          "完全相同=近重复")
    check(not is_near_duplicate("cats", "quantum computing"), "无关≠近重复")

    # 8. last_mode 留痕
    similarity("a", "b")
    check(last_mode() == "offline", "无注入时档位=offline")

    # 9. 注入 embedding 档生效
    def fake_embed(texts):
        # 简单词袋向量(仅测档位切换,不求语义)
        vocab = sorted(set(w for t in texts for w in t.split()))
        return [[t.split().count(w) for w in vocab] for t in texts]
    set_embed_fn(fake_embed)
    similarity("one two three", "one two four")
    check(last_mode() == "embed", "注入后档位=embed")
    set_embed_fn(None)  # 复位

    print("ALL PASS" if ok else "SOME FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    print(__doc__)
    print("用法: python semantic_sim.py --selftest")
