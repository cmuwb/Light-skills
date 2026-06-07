#!/usr/bin/env python3
"""校验每个技能的 SKILL.md frontmatter:必须有 name 与 description。
常驻技能(标了 user-invocable: false)单独统计。CI 用。"""
import io
import pathlib
import sys

# 强制 UTF-8 输出,避免 Windows GBK 控制台编不了 ✓/✗
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILLS = ROOT / "skills"

errors = []
manual = resident = 0

for skill_dir in sorted(SKILLS.glob("light-*")):
    md = skill_dir / "SKILL.md"
    if not md.exists():
        errors.append(f"{skill_dir.name}: 缺 SKILL.md")
        continue
    text = md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        errors.append(f"{skill_dir.name}: 缺 frontmatter")
        continue
    fm = text.split("---", 2)[1]
    has_name = any(l.strip().startswith("name:") for l in fm.splitlines())
    has_desc = any(l.strip().startswith("description:") for l in fm.splitlines())
    if not has_name:
        errors.append(f"{skill_dir.name}: frontmatter 缺 name")
    if not has_desc:
        errors.append(f"{skill_dir.name}: frontmatter 缺 description")
    if any("user-invocable: false" in l for l in fm.splitlines()):
        resident += 1
    else:
        manual += 1

print(f"技能总数: {manual + resident}  (手动 {manual} / 常驻 {resident})")
if errors:
    print("\n校验失败:")
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)
print("✓ 所有技能 frontmatter 合规")
