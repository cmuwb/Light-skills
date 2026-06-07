#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scaffold.py — 一条命令生成规范科研项目骨架。

用法:
    python scaffold.py <目标目录> [--name 名称] [--module 包名] [--dvc] [--poetry] [--force]

行为:
    1. 创建标准科研目录树 (data 四分层 / src / experiments / ... 见 DIRS)。
    2. 从本脚本同目录拷贝 5 个模板, 去掉 .template 后缀落到项目根:
       README / CHANGELOG / PROJECT_PLAN / .gitignore / .editorconfig。
    3. --poetry: 额外写 pyproject.toml (Poetry + Ruff 配置, 离线可用)。
    4. --dvc:    写 dvc.yaml 占位管线; 若本机有 dvc 则顺带 dvc init。
    5. 空目录放 .gitkeep, 便于 git 跟踪空树。

模板缺失或目标已存在(无 --force)时报错退出, 不静默覆盖。
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台默认 GBK, 防中文乱码
sys.stderr.reconfigure(encoding="utf-8")

import argparse  # noqa: E402  (stdout/stderr reconfigure 必须先于其余 import)
import shutil  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
TEMPLATE_DIR = HERE.parent / "templates"  # scaffold.py lives in scripts/, templates are siblings

# 标准科研目录树 (与 PROJECT_STRUCTURE.md 一致)
DIRS = [
    "data/raw", "data/interim", "data/processed", "data/external",
    "src", "models", "experiments", "results", "figures",
    "notebooks/exploratory", "notebooks/reports",
    "configs", "logs", "references", "docs",
    "paper", "ppt", "patent", "software-copyright", "assets", "tests",
]

# 模板 -> 项目根目标文件名 (去 .template 后缀; gitignore/editorconfig 特殊改名)
TEMPLATE_MAP = {
    "README.template.md": "README.md",
    "CHANGELOG.template.md": "CHANGELOG.md",
    "PROJECT_PLAN.template.md": "PROJECT_PLAN.md",
    "python-research.gitignore": ".gitignore",
    "editorconfig.template": ".editorconfig",
}

PYPROJECT_TOML = '''[project]
name = "{name}"
version = "0.1.0"
description = "{name} research project"
requires-python = ">=3.10"
dependencies = []

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.poetry]
packages = [{{ include = "{module}", from = "src" }}]

[tool.poetry.group.dev.dependencies]
pytest = "*"
ruff = "*"

[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "B"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"
'''

DVC_YAML = '''# DVC 管线占位; 用 `dvc repro` 运行, 只重跑变更阶段。
# 真正使用时把 cmd/deps/outs 改成项目实际命令与产物。
stages:
  prepare:
    cmd: python -m {module}.dataset
    deps:
      - data/raw
    outs:
      - data/processed
'''


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def copy_templates(root: Path) -> list[str]:
    """拷贝 5 个模板到项目根, 去后缀。返回已落地文件名列表。"""
    done = []
    for src_name, dst_name in TEMPLATE_MAP.items():
        src = TEMPLATE_DIR / src_name
        if not src.exists():
            raise FileNotFoundError(f"缺模板: {src}")
        write_text(root / dst_name, src.read_text(encoding="utf-8"))
        done.append(dst_name)
    return done


def make_tree(root: Path) -> None:
    for d in DIRS:
        p = root / d
        p.mkdir(parents=True, exist_ok=True)
        (p / ".gitkeep").write_text("", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="生成规范科研项目骨架")
    ap.add_argument("target", help="目标目录")
    ap.add_argument("--name", help="项目名称 (默认取目标目录名)")
    ap.add_argument("--module", help="源码包名 (默认由 name 推断, 连字符转下划线)")
    ap.add_argument("--dvc", action="store_true", help="写 dvc.yaml 并尝试 dvc init")
    ap.add_argument("--poetry", action="store_true", help="写 pyproject.toml (Poetry+Ruff)")
    ap.add_argument("--force", action="store_true", help="目标非空时仍继续")
    args = ap.parse_args(argv)

    root = Path(args.target).resolve()
    name = args.name or root.name
    module = args.module or name.replace("-", "_").replace(" ", "_")

    if root.exists() and any(root.iterdir()) and not args.force:
        print(f"错误: 目标非空: {root} (加 --force 覆盖)", file=sys.stderr)
        return 2

    root.mkdir(parents=True, exist_ok=True)
    make_tree(root)
    (root / "src" / module).mkdir(parents=True, exist_ok=True)
    write_text(root / "src" / module / "__init__.py", '"""%s package."""\n' % module)

    copied = copy_templates(root)

    extras = []
    if args.poetry:
        write_text(root / "pyproject.toml", PYPROJECT_TOML.format(name=name, module=module))
        extras.append("pyproject.toml")
    if args.dvc:
        write_text(root / "dvc.yaml", DVC_YAML.format(module=module))
        extras.append("dvc.yaml")
        if shutil.which("dvc"):
            try:
                subprocess.run(["dvc", "init", "--no-scm", "-q"], cwd=root, check=True)
                extras.append(".dvc/ (dvc init)")
            except subprocess.CalledProcessError as e:
                print(f"警告: dvc init 失败 ({e}); 仅写了 dvc.yaml", file=sys.stderr)
        else:
            print("提示: 未找到 dvc 命令, 仅写了 dvc.yaml (装 dvc 后跑 `dvc init`)")

    print(f"已生成项目: {root}")
    print(f"  名称={name}  模块=src/{module}/")
    print(f"  目录 {len(DIRS)} 个 (含 data 四分层 + notebooks 探索/报告分流)")
    print(f"  模板落地: {', '.join(copied)}")
    if extras:
        print(f"  附加: {', '.join(extras)}")
    print("下一步: 填 README/CHANGELOG/PROJECT_PLAN 的 {{占位}}, git init, 写第一个测试。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
