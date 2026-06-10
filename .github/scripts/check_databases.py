#!/usr/bin/env python3
"""Validate Light database markdown files.

CI scope:
- strict modern card files must have parseable fenced ```yaml blocks;
- legacy YAML-like card files are reported as warnings, not failed immediately;
- every local .md link in a database README must point to an existing file.

Some early database cards were authored as YAML-looking Markdown prose rather
than strict YAML (for example, unquoted colons inside natural-language fields).
Failing CI on the entire legacy backlog would block unrelated database work, so
this script fails strictly on new standardized card files and on README links,
while printing legacy parse problems for future cleanup.
"""
from __future__ import annotations

import io
import pathlib
import re
import sys
from collections import Counter

import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATABASES = ROOT / "databases"

errors: list[str] = []
warnings: list[str] = []
yaml_blocks = 0
strict_yaml_blocks = 0
readme_links = 0
strict_seen: dict[str, int] = {}

STRICT_YAML_FILES = {
    # db03/db04 领域扩充（2026-06-10）
    "databases/db03-methods/cards_biomedical.md",
    "databases/db03-methods/cards_nlp_speech.md",
    "databases/db03-methods/cards_physical_sciences.md",
    "databases/db03-methods/cards_stats_econ_finance.md",
    "databases/db04-datasets/cards_biomedical.md",
    "databases/db04-datasets/cards_nlp_speech.md",
    "databases/db04-datasets/cards_physical_sciences.md",
    "databases/db04-datasets/cards_stats_econ_finance.md",
    # db05-db08 场景扩充（2026-06-10）
    "databases/db05-frontend-styles/design_system_cards.md",
    "databases/db06-ppt-styles/slide_pattern_cards.md",
    "databases/db07-figures/figure_advanced_cards.md",
    "databases/db08-ip-materials/material_extended_cards.md",
}

if not DATABASES.exists():
    errors.append("databases/: missing directory")
else:
    for rel in sorted(STRICT_YAML_FILES):
        path = ROOT / rel
        if not path.exists():
            errors.append(f"{rel}: strict YAML file is missing")
            continue
        strict_seen[rel] = 0

    for md in sorted(DATABASES.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        rel = md.relative_to(ROOT)
        rel_posix = rel.as_posix()
        for idx, block in enumerate(re.findall(r"```yaml\n(.*?)\n```", text, flags=re.S), start=1):
            yaml_blocks += 1
            strict = rel_posix in STRICT_YAML_FILES
            if strict:
                strict_yaml_blocks += 1
                strict_seen[rel_posix] = strict_seen.get(rel_posix, 0) + 1
            try:
                yaml.safe_load(block)
            except Exception as exc:  # noqa: BLE001 - report parser detail in CI
                msg = f"{rel}: yaml block #{idx} does not parse: {exc}"
                if strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)

    for readme in sorted(DATABASES.glob("db*/README.md")):
        text = readme.read_text(encoding="utf-8")
        base = readme.parent
        rel_readme = readme.relative_to(ROOT)
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if re.match(r"^[a-z]+://", target):
                continue
            if target.startswith("#"):
                continue
            clean = target.split("#", 1)[0].split("?", 1)[0]
            if not clean.endswith(".md"):
                continue
            readme_links += 1
            path = (base / clean).resolve()
            try:
                path.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(f"{rel_readme}: link escapes repo: {target}")
                continue
            if not path.exists():
                errors.append(f"{rel_readme}: missing linked file {target}")

    for rel, count in sorted(strict_seen.items()):
        if count == 0:
            errors.append(f"{rel}: strict YAML file has no fenced ```yaml block")

print(
    "数据库 Markdown: "
    f"yaml_blocks={yaml_blocks}, strict_yaml_blocks={strict_yaml_blocks}, "
    f"legacy_yaml_warnings={len(warnings)}, readme_md_links={readme_links}"
)
if warnings:
    print("\n历史 YAML 风格卡片警告（暂不阻断 CI）:")
    by_file = Counter(warn.split(": yaml block", 1)[0] for warn in warnings)
    for filename, count in sorted(by_file.items()):
        print(f"  ! {filename}: {count} legacy YAML-style block(s)")
    print("  ! 这些旧卡保留为未来清理债务；严格校验只作用于新标准卡文件。")
if errors:
    print("\n数据库校验失败:")
    for err in errors:
        print(f"  ✗ {err}")
    sys.exit(1)
print("✓ 数据库 YAML 与 README 链接合规")
