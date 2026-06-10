#!/usr/bin/env python3
"""Validate Light database markdown files.

CI scope:
- every fenced ```yaml block under databases/ must parse as YAML;
- every local .md link in a database README must point to an existing file.

This gate prevents broken database cards and stale README indexes from landing.
It does not yet require every historical card to fill every schema field; schema
completeness can be tightened later per-db once the full legacy corpus is
normalized.
"""
from __future__ import annotations

import io
import pathlib
import re
import sys

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATABASES = ROOT / "databases"

errors: list[str] = []
yaml_blocks = 0
readme_links = 0


class UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader variant that rejects duplicate keys instead of overwriting."""


def construct_unique_mapping(loader: UniqueKeyLoader, node: MappingNode, deep: bool = False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_unique_mapping,
)


YAML_FENCE_RE = re.compile(
    r"^[ \t]{0,3}```[ \t]*(?:ya?ml)(?:[ \t].*)?[ \t]*\n(.*?)\n^[ \t]{0,3}```[ \t]*$",
    flags=re.S | re.I | re.M,
)


def is_card_file(path: pathlib.Path) -> bool:
    name = path.name.lower()
    return name.startswith("cards") or name.endswith("_cards.md")

if not DATABASES.exists():
    errors.append("databases/: missing directory")
else:
    for md in sorted(DATABASES.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        rel = md.relative_to(ROOT)
        blocks = list(YAML_FENCE_RE.finditer(text))
        if is_card_file(md) and not blocks:
            errors.append(f"{rel}: card file has no fenced YAML blocks")
        for idx, match in enumerate(blocks, start=1):
            block = match.group(1)
            yaml_blocks += 1
            try:
                data = yaml.load(block, Loader=UniqueKeyLoader)
            except Exception as exc:  # noqa: BLE001 - report parser detail in CI
                errors.append(f"{rel}: yaml block #{idx} does not parse: {exc}")
                continue
            if is_card_file(md):
                if not isinstance(data, list) or not data:
                    errors.append(f"{rel}: yaml block #{idx} must be a non-empty list")
                elif not all(isinstance(item, dict) for item in data):
                    errors.append(f"{rel}: yaml block #{idx} must contain only mappings")

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

print(f"数据库 Markdown: yaml_blocks={yaml_blocks}, readme_md_links={readme_links}")
if errors:
    print("\n数据库校验失败:")
    for err in errors:
        print(f"  ✗ {err}")
    sys.exit(1)
print("✓ 数据库 YAML 与 README 链接合规")
