#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scaffold.py — 一条命令生成规范科研项目骨架。

用法:
    python scaffold.py <目标目录> [--name 名称] [--module 包名] [--dvc] [--uv|--poetry] [--force]

行为:
    1. 创建标准科研目录树 (data 四分层 / src / experiments / ... 见 DIRS)。
    2. 从本脚本同目录拷贝 7 个模板, 去掉 .template 后缀落到项目根:
       README / CHANGELOG / PROJECT_PLAN / PROJECT_STRUCTURE / .gitignore /
       .editorconfig / .pre-commit-config.yaml。.pre-commit-config.yaml 在
       `pre-commit install` 前完全惰性, 故与 .editorconfig 一样默认始终落地。
    3. pyproject.toml 始终落地; 依赖管理后端默认 uv (--uv, 与 a03 推荐一致),
       --poetry 切到 Poetry 备选。两者互斥。
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
    ".light", ".light/handoff",  # 编排器台账 passport.yaml + 会话衔接卡 (CONVENTIONS §9)
]

# 模板 -> 项目根目标文件名 (去 .template 后缀; gitignore/editorconfig 特殊改名)
TEMPLATE_MAP = {
    "README.template.md": "README.md",
    "CHANGELOG.template.md": "CHANGELOG.md",
    "PROJECT_PLAN.template.md": "PROJECT_PLAN.md",
    "PROJECT_STRUCTURE.md": "PROJECT_STRUCTURE.md",
    "python-research.gitignore": ".gitignore",
    "editorconfig.template": ".editorconfig",
    "pre-commit-config.template.yaml": ".pre-commit-config.yaml",
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

# 默认后端: uv (PEP 621 标准表 + hatchling, 与 a03 backend-coding 推荐一致)。
# dev 依赖走 [dependency-groups] (uv/PEP 735); src 布局用 [tool.hatch] 指定包路径。
PYPROJECT_TOML_UV = '''[project]
name = "{name}"
version = "0.1.0"
description = "{name} research project"
requires-python = ">=3.10"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/{module}"]

[dependency-groups]
dev = ["pytest", "ruff"]

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
      - src/{module}/dataset.py
    outs:
      - data/processed
'''

# --dvc 生成的最小可跑桩, 让 `dvc repro` 首跑不报 "module not found"。
# 真正使用时把 main() 换成实际的 raw->processed 转换逻辑。
DATASET_PY = '''"""{module}.dataset — DVC prepare 阶段占位脚本。

读 data/raw, 写 data/processed。当前仅占位, 把 raw 下文件名清单
落到 processed/manifest.txt, 保证 `dvc repro` 首跑能产出 outs。
真正使用时替换 main() 为实际的数据转换逻辑。
"""
from pathlib import Path

RAW = Path("data/raw")
PROCESSED = Path("data/processed")


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    names = sorted(p.name for p in RAW.glob("*") if p.is_file())
    (PROCESSED / "manifest.txt").write_text(
        "\\n".join(names) + "\\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
'''


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def copy_templates(root: Path) -> list[str]:
    """拷贝模板到项目根, 去后缀。返回已落地文件名列表。"""
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



# ---------------------------------------------------------------- 审计模式
# 应被 .gitignore 挡住、不该进 Git 的可重算/大体积产物目录 (DAG 铁律: 能重算的不入库)
_NON_TRACK_DIRS = ["data/raw", "data/interim", "data/processed", "data/external",
                   "models", "results", "logs"]
# 命名违规: 空格 / 中文 / 其它非 ASCII (DAG 铁律: 命名规范)
_BAD_NAME = __import__("re").compile(r"[\s一-鿿]|[^\x00-\x7f]")
# 期望存在的根工件
_EXPECT_FILES = ["README.md", "CHANGELOG.md"]
_EXPECT_DIRS_ROOT = ["data", "src"]


def _git_tracked(root: Path):
    """返回 git 已跟踪文件的相对路径集合; 无 git 或不在仓库内返回 None (无法判定)。"""
    if not shutil.which("git"):
        return None
    try:
        out = subprocess.run(["git", "ls-files"], cwd=root, check=True,
                             capture_output=True, text=True, encoding="utf-8")
    except (subprocess.CalledProcessError, OSError):
        return None
    return set(out.stdout.replace("\\", "/").split("\n")) - {""}


def audit(root: Path) -> dict:
    """扫描已有项目, 报结构合规。返回 {verified, violations} —— 把 SKILL 的三条
    DAG 铁律(raw 不可变/能重算的不入库/命名规范)从口头方法论变成可执行校验。

    violations 每条: {rule, severity, loc, detail, fix}。
    severity: critical(产物入库/raw 被跟踪) / important(缺关键工件) / minor(命名)。
    """
    violations, verified = [], []
    tracked = _git_tracked(root)  # None=无法判定(无 git)

    # ① 可重算/大体积产物是否被 Git 跟踪 (能重算的不入库)
    if tracked is None:
        verified.append("git 不可用或非仓库: 跳过'产物入库'检查(无法判定, 未静默通过)")
    else:
        for d in _NON_TRACK_DIRS:
            bad = sorted(f for f in tracked
                         if (f == d or f.startswith(d + "/")) and not f.endswith("/.gitkeep"))
            if bad:
                sev = "critical" if d == "data/raw" else "important"
                rule = "raw_immutable_tracked" if d == "data/raw" else "derived_artifact_tracked"
                violations.append({
                    "rule": rule, "severity": sev, "loc": d,
                    "detail": f"{d}/ 下有 {len(bad)} 个文件被 Git 跟踪(应可重算/不入库): {bad[:3]}",
                    "fix": f"git rm -r --cached {d} && 在 .gitignore 补 `{d}/`(保留 .gitkeep)"})
            else:
                verified.append(f"{d}/ 未被 Git 跟踪 ✓(符合'能重算的不入库')")

    # ② 命名违规: 目录/文件含空格或中文 (只扫项目自有树, 跳过 .git/.venv/node_modules 等)
    skip = {".git", ".venv", "venv", "node_modules", "__pycache__", ".dvc", ".light"}
    name_bad = []
    for p in root.rglob("*"):
        if any(part in skip for part in p.relative_to(root).parts):
            continue
        if _BAD_NAME.search(p.name):
            name_bad.append(str(p.relative_to(root)).replace("\\", "/"))
    if name_bad:
        violations.append({
            "rule": "bad_naming", "severity": "minor", "loc": ", ".join(name_bad[:5]),
            "detail": f"{len(name_bad)} 个路径含空格/中文/非 ASCII(违反命名规范)",
            "fix": "重命名为小写+连字符/下划线, 不用空格与中文"})
    else:
        verified.append("命名规范 ✓(无空格/中文/非 ASCII 路径)")

    # ③ 关键工件缺失
    for f in _EXPECT_FILES:
        if not (root / f).exists():
            violations.append({"rule": "missing_artifact", "severity": "important",
                               "loc": f, "detail": f"缺 {f}",
                               "fix": f"补 {f}(可用 scaffold.py 模板)"})
        else:
            verified.append(f"{f} 存在 ✓")
    for d in _EXPECT_DIRS_ROOT:
        if not (root / d).is_dir():
            violations.append({"rule": "missing_dir", "severity": "important",
                               "loc": d + "/", "detail": f"缺标准目录 {d}/",
                               "fix": f"mkdir {d}(参照 PROJECT_STRUCTURE.md)"})
    # .light/passport 联动 (SKILL 宣称'跨阶段真相源')
    if not (root / ".light").is_dir():
        violations.append({"rule": "missing_light_ledger", "severity": "minor",
                           "loc": ".light/", "detail": "缺 .light/ 编排台账目录",
                           "fix": "mkdir .light(放 passport.yaml / handoff 衔接卡)"})
    else:
        verified.append(".light/ 编排台账存在 ✓")

    return {"root": str(root), "verified": verified, "violations": violations,
            "n_violations": len(violations),
            "n_critical": sum(1 for v in violations if v["severity"] == "critical")}


def _print_audit(rep: dict) -> None:
    print(f"== 结构审计: {rep['root']} ==")
    print(f"通过 {len(rep['verified'])} 项 / 违规 {rep['n_violations']} 项"
          f"(critical {rep['n_critical']})")
    for v in rep["verified"]:
        print(f"  ✓ {v}")
    for v in rep["violations"]:
        print(f"  ✖ [{v['severity']}] {v['rule']} @ {v['loc']}")
        print(f"      {v['detail']}")
        print(f"      修复: {v['fix']}")


def _selftest() -> int:
    import tempfile
    try:
        import tomllib  # py3.11+
    except ModuleNotFoundError:
        tomllib = None
    with tempfile.TemporaryDirectory(prefix="light_scaffold_") as tmp:
        # 路径一: 默认 (uv) 后端
        target = Path(tmp) / "demo-project"
        rc = main([str(target), "--name", "demo-project", "--module", "demo_project"])
        assert rc == 0, rc
        required = [target / "README.md", target / "CHANGELOG.md", target / "PROJECT_PLAN.md",
                    target / "PROJECT_STRUCTURE.md",
                    target / ".pre-commit-config.yaml", target / "src" / "demo_project" / "__init__.py",
                    target / "pyproject.toml", target / "data" / "raw" / ".gitkeep",
                    target / ".light" / ".gitkeep", target / ".light" / "handoff" / ".gitkeep"]
        missing = [str(p) for p in required if not p.exists()]
        assert not missing, missing
        uv_toml = (target / "pyproject.toml").read_text(encoding="utf-8")
        assert "[dependency-groups]" in uv_toml and "hatchling" in uv_toml, "uv 默认后端未写入"
        if tomllib:
            assert tomllib.loads(uv_toml)["project"]["name"] == "demo-project"
        rc2 = main([str(target)])  # 非空守卫
        assert rc2 == 2, rc2
        # 路径二: --poetry 备选后端
        target2 = Path(tmp) / "demo-poetry"
        rc3 = main([str(target2), "--name", "demo-poetry", "--module", "demo_poetry", "--poetry"])
        assert rc3 == 0, rc3
        poetry_toml = (target2 / "pyproject.toml").read_text(encoding="utf-8")
        assert "[tool.poetry]" in poetry_toml and "poetry-core" in poetry_toml, "Poetry 备选后端未写入"
        if tomllib:
            assert tomllib.loads(poetry_toml)["project"]["name"] == "demo-poetry"
        # 路径三: --dvc 写 dvc.yaml + prepare 桩 (不依赖本机 dvc/git 二进制)
        target3 = Path(tmp) / "demo-dvc"
        rc4 = main([str(target3), "--name", "demo-dvc", "--module", "demo_dvc", "--dvc"])
        assert rc4 == 0, rc4
        assert (target3 / "dvc.yaml").exists(), "dvc.yaml 未落地"
        stub = target3 / "src" / "demo_dvc" / "dataset.py"
        assert stub.exists(), "prepare 桩 dataset.py 未生成"
        assert "def main" in stub.read_text(encoding="utf-8"), "dataset.py 桩缺 main()"
        dvc_yaml = (target3 / "dvc.yaml").read_text(encoding="utf-8")
        assert "demo_dvc.dataset" in dvc_yaml, "dvc.yaml cmd 未指向桩模块"
        # 路径四: audit() 在脏项目上抓违规 (无 git 时跳过入库检查, 仍查命名/缺件)
        dirty = Path(tmp) / "dirty-proj"
        (dirty / "src").mkdir(parents=True)
        (dirty / "data" / "raw").mkdir(parents=True)
        (dirty / "我的 实验").mkdir()  # 命名违规: 空格 + 中文
        rep = audit(dirty)
        rules = {v["rule"] for v in rep["violations"]}
        assert "bad_naming" in rules, "未抓出命名违规"
        assert "missing_artifact" in rules, "未抓出缺 README/CHANGELOG"
        assert "missing_light_ledger" in rules, "未抓出缺 .light"
        assert rep["n_violations"] >= 3, rep["n_violations"]
        # 干净项目(scaffold 刚建的)审计应近乎全过 (无 git 时入库检查跳过)
        clean_rep = audit(target)
        assert not any(v["rule"] == "bad_naming" for v in clean_rep["violations"]), \
            "scaffold 自建项目不应有命名违规"
        assert any("命名规范" in v for v in clean_rep["verified"]), "干净项目应记命名通过"
        print("[selftest] PASS scaffold (uv 默认 + poetry 备选 + dvc + audit 四路径)")
        return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="生成规范科研项目骨架")
    ap.add_argument("target", nargs="?", help="目标目录")
    ap.add_argument("--name", help="项目名称 (默认取目标目录名)")
    ap.add_argument("--module", help="源码包名 (默认由 name 推断, 连字符转下划线)")
    ap.add_argument("--dvc", action="store_true", help="写 dvc.yaml 并尝试 dvc init")
    backend = ap.add_mutually_exclusive_group()
    backend.add_argument("--uv", action="store_true", help="pyproject.toml 用 uv 后端 (默认)")
    backend.add_argument("--poetry", action="store_true", help="pyproject.toml 改用 Poetry 后端 (备选)")
    ap.add_argument("--force", action="store_true", help="目标非空时仍继续")
    ap.add_argument("--check", metavar="DIR", help="审计已有项目结构合规(不建树), 报违规+修复建议")
    ap.add_argument("--json", action="store_true", help="配合 --check: 输出 JSON")
    ap.add_argument("--selftest", action="store_true", help="run offline scaffold self-test")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest()
    if args.check:
        croot = Path(args.check).resolve()
        if not croot.is_dir():
            print(f"错误: 待审计目录不存在: {croot}", file=sys.stderr)
            return 2
        rep = audit(croot)
        if args.json:
            import json as _json
            print(_json.dumps(rep, ensure_ascii=False, indent=2))
        else:
            _print_audit(rep)
        # critical 违规 -> exit 1 (可被 CI / pre-commit 阻断); 仅 minor/important 不阻断
        return 1 if rep["n_critical"] else 0
    if not args.target:
        ap.error("需要提供目标目录（或使用 --selftest）")

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
    # pyproject.toml 始终落地; 默认 uv 后端, --poetry 切备选。
    if args.poetry:
        write_text(root / "pyproject.toml", PYPROJECT_TOML.format(name=name, module=module))
        extras.append("pyproject.toml (Poetry)")
    else:
        write_text(root / "pyproject.toml", PYPROJECT_TOML_UV.format(name=name, module=module))
        extras.append("pyproject.toml (uv)")
    if args.dvc:
        write_text(root / "dvc.yaml", DVC_YAML.format(module=module))
        extras.append("dvc.yaml")
        write_text(root / "src" / module / "dataset.py", DATASET_PY.format(module=module))
        extras.append(f"src/{module}/dataset.py (prepare 桩)")
        if shutil.which("dvc"):
            # dvc init 默认要求处于 git 仓库内 (与 SKILL.md 的 git init→dvc init 一致)。
            # 无 .git 时先 git init, 让 dvc 接管 git 而非 --no-scm 脱离版本控制。
            if not (root / ".git").exists() and shutil.which("git"):
                try:
                    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
                    extras.append(".git/ (git init)")
                except subprocess.CalledProcessError as e:
                    print(f"警告: git init 失败 ({e}); 跳过 dvc init", file=sys.stderr)
            try:
                subprocess.run(["dvc", "init", "-q"], cwd=root, check=True)
                extras.append(".dvc/ (dvc init)")
            except subprocess.CalledProcessError as e:
                print(f"警告: dvc init 失败 ({e}); 仅写了 dvc.yaml", file=sys.stderr)
        else:
            print("提示: 未找到 dvc 命令, 仅写了 dvc.yaml (装 dvc 后跑 `git init && dvc init`)")

    print(f"已生成项目: {root}")
    print(f"  名称={name}  模块=src/{module}/")
    print(f"  目录 {len(DIRS)} 个 (含 data 四分层 + notebooks 探索/报告分流)")
    print(f"  模板落地: {', '.join(copied)}")
    if extras:
        print(f"  附加: {', '.join(extras)}")
    print("下一步:")
    print("  1. 填 README/CHANGELOG/PROJECT_PLAN 的 {{占位}}。")
    print("  2. git init  (无 git 仓库时 .pre-commit-config.yaml 不生效)。")
    if args.poetry:
        print("  3. poetry install  (装依赖并建虚拟环境)。")
    else:
        print("  3. uv sync  (装依赖并建 .venv; 未装 uv 见 https://docs.astral.sh/uv/)。")
    print("  4. pre-commit install  (把钩子挂进 .git/hooks/, 否则有配置也没门)。")
    print("  5. pre-commit run --all-files  (首次全量跑一遍)。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
