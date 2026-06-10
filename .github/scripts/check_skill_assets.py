#!/usr/bin/env python3
"""Validate Light skill script assets.

CI scope:
- every skills/light-*/scripts/*.py is documented exactly once in the
  WHATS_INCLUDED.md "可运行脚本" table as (skill, script);
- every documented executable script table row points to an existing script;
- every script compiles with py_compile;
- every script has a real ``if __name__ == "__main__"`` guard;
- selftest coverage is reported as WARN, not a hard failure yet.
"""
from __future__ import annotations

import ast
import io
import pathlib
import py_compile
import re
import sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILLS = ROOT / "skills"
WHATS_INCLUDED = ROOT / "WHATS_INCLUDED.md"

errors: list[str] = []
warnings: list[str] = []


def extract_section(markdown: str, heading: str) -> str:
    """Return the content under a level-2 heading until the next level-2 heading."""
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(markdown)
    if not match:
        errors.append(f"WHATS_INCLUDED.md: missing section ## {heading}")
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", markdown[start:], flags=re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(markdown)
    return markdown[start:end]


def parse_executable_script_table(markdown: str) -> list[tuple[str, str]]:
    """Parse rows from the 可运行脚本 table as (skill_slug, script_name)."""
    section = extract_section(markdown, "可运行脚本")
    rows: list[tuple[str, str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "`scripts/" not in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 3:
            errors.append(f"WHATS_INCLUDED.md: malformed executable script row: {line}")
            continue
        skill = cells[0]
        script_match = re.fullmatch(r"`scripts/([^`]+\.py)`", cells[1])
        if not script_match:
            errors.append(f"WHATS_INCLUDED.md: malformed script cell in row: {line}")
            continue
        if not skill:
            errors.append(f"WHATS_INCLUDED.md: empty skill in row: {line}")
            continue
        rows.append((skill, script_match.group(1)))
    return rows


def is_name_main_compare(node: ast.AST) -> bool:
    """Return True for __name__ == "__main__" or the reversed comparison."""
    if not isinstance(node, ast.Compare) or len(node.ops) != 1 or not isinstance(node.ops[0], ast.Eq):
        return False
    if len(node.comparators) != 1:
        return False

    def is_dunder_name(value: ast.AST) -> bool:
        return isinstance(value, ast.Name) and value.id == "__name__"

    def is_main_literal(value: ast.AST) -> bool:
        return isinstance(value, ast.Constant) and value.value == "__main__"

    left = node.left
    right = node.comparators[0]
    return (is_dunder_name(left) and is_main_literal(right)) or (
        is_main_literal(left) and is_dunder_name(right)
    )


def has_main_guard(tree: ast.AST) -> bool:
    """Detect a real if __name__ == "__main__" guard in parsed Python AST."""
    return any(isinstance(node, ast.If) and is_name_main_compare(node.test) for node in ast.walk(tree))


if not WHATS_INCLUDED.exists():
    errors.append("WHATS_INCLUDED.md: missing file")
    whats_text = ""
else:
    whats_text = WHATS_INCLUDED.read_text(encoding="utf-8")

script_paths = sorted(SKILLS.glob("light-*/scripts/*.py"))
actual_keys = [
    (path.parts[-3].removeprefix("light-"), path.name)
    for path in script_paths
]
actual_key_set = set(actual_keys)

documented_keys = parse_executable_script_table(whats_text)
documented_counter = Counter(documented_keys)
documented_key_set = set(documented_keys)

for key, count in sorted(documented_counter.items()):
    if count > 1:
        skill, script_name = key
        errors.append(
            f"WHATS_INCLUDED.md: duplicate executable script row for {skill}/scripts/{script_name}"
        )

for skill, script_name in actual_keys:
    if (skill, script_name) not in documented_key_set:
        errors.append(
            f"WHATS_INCLUDED.md: missing executable script row for {skill}/scripts/{script_name}"
        )

for skill, script_name in sorted(documented_key_set):
    if (skill, script_name) not in actual_key_set:
        errors.append(
            f"WHATS_INCLUDED.md: documented executable script does not exist: "
            f"{skill}/scripts/{script_name}"
        )

for script in script_paths:
    rel = script.relative_to(ROOT).as_posix()
    text = script.read_text(encoding="utf-8", errors="ignore")
    try:
        py_compile.compile(str(script), doraise=True)
        tree = ast.parse(text, filename=rel)
    except Exception as exc:  # noqa: BLE001 - report compile detail in CI
        errors.append(f"{rel}: Python parse/compile failed: {exc}")
        continue
    if not has_main_guard(tree):
        errors.append(f"{rel}: missing real if __name__ == \"__main__\" guard")
    if "--selftest" not in text and "selftest" not in text.lower():
        warnings.append(f"{rel}: no selftest marker yet")

print(
    "技能脚本资产: "
    f"scripts={len(script_paths)}, executable_table_rows={len(documented_keys)}, "
    f"with_selftest={len(script_paths) - len(warnings)}, missing_selftest={len(warnings)}"
)

if warnings:
    print("\n资产校验警告（当前不阻断 CI，后续逐步补 selftest）:")
    for warning in warnings:
        print(f"  ! {warning}")

if errors:
    print("\n脚本资产校验失败:")
    for error in errors:
        print(f"  ✗ {error}")
    sys.exit(1)

print("✓ 技能脚本均已在可运行脚本表登记、可编译且具备真实 __main__ 入口")
