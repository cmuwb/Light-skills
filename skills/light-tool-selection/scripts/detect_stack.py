#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""detect_stack.py — 读取项目清单文件，识别技术栈，给出工具/技能选型建议。

支持的清单：package.json / pyproject.toml(含 poetry 段) /
requirements.txt / environment.yml(.yaml) / Pipfile。

用法：
  python detect_stack.py <项目目录>      # 扫描真实项目
  python detect_stack.py --self-test     # 无数据时用合成清单自检
  python detect_stack.py <目录> --json   # 机器可读输出

设计：纯标准库（tomllib 3.11+）+ 可选 PyYAML（缺失则降级正则解析 yml）。
不臆造——只对“清单里真实出现的依赖”给建议，未命中标 'no signal'。
"""
import sys, os, json, re, argparse

sys.stdout.reconfigure(encoding="utf-8")

# 挂接 _shared 地基契约4(findings): 把检测出的冲突/异味/过时版本，
# 以机读的 light.findings.v1 交接给下游(a01 passport gate / db09 记忆)。
# 脚本模式 import(README 方式B)：把 ../../_shared 加进 sys.path。
_SHARED = os.path.join(os.path.dirname(__file__), "..", "..", "_shared")
sys.path.insert(0, os.path.abspath(_SHARED))
try:
    from findings_schema import Finding, GateResult, FindingsReport  # type: ignore
    from gate_runner import run_gates  # type: ignore
    _HAS_SHARED = True
except Exception:  # 契约缺失时降级：仍出本地报告，但不发 findings
    _HAS_SHARED = False

try:
    import tomllib  # py3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

# 依赖名(规整后精确匹配) -> (类别, 选型建议)。suggest() 按 dep==key
# 或 dep==key 的连字符转下划线 变体精确相等命中，不做子串匹配。
RULES = {
    # ---- Python 数据 ----
    "pandas": ("数据处理", "中小数据(<2GB)主力；超内存切 polars/dask"),
    "polars": ("数据处理", "已选高性能 DataFrame，适合 1-50GB 单机"),
    "dask": ("数据处理", "已选超内存/并行；确认是否真需要分布式"),
    "duckdb": ("数据处理", "out-of-core SQL 直查 parquet/csv；超内存分析首选之一"),
    "vaex": ("数据处理", "⚠ vaex 2023 后停维护(已淘汰)；迁 DuckDB / polars streaming"),
    "pyspark": ("数据处理", "集群级；单机数据 <50GB 时 polars 更省心"),
    # ---- Python 科学/ML ----
    "numpy": ("科学计算", "数值基座，向量化优先于 Python 循环"),
    "scipy": ("科学计算", "统计/优化/信号；配 statsmodels 做推断统计"),
    "statsmodels": ("统计推断", "回归/检验/时序，要 p 值/置信区间选它"),
    "scikit-learn": ("机器学习", "经典 ML 主力；深度学习转 torch"),
    "sklearn": ("机器学习", "⚠ PyPI 上 `sklearn` 是占位空壳包(已弃用)，应改装 `scikit-learn`"),
    "scikit-image": ("计算机视觉", "科学图像处理(导入名 skimage)；通用图像/视频用 opencv"),
    "xgboost": ("机器学习", "梯度提升树；表格数据强基线，调参看 early_stopping"),
    "lightgbm": ("机器学习", "高效 GBDT；大表格/类别特征比 xgboost 更省内存"),
    "torch": ("深度学习", "PyTorch；GPU 训练考虑 Modal 云算力"),
    "pytorch": ("深度学习", "PyTorch(conda 包名)；GPU 训练考虑 Modal 云算力"),
    "torchvision": ("深度学习", "PyTorch 视觉数据集/模型/变换，配 torch 用"),
    "tensorflow": ("深度学习", "TF；环境用 conda 协调 CUDA"),
    "transformers": ("深度学习", "HF 模型；大模型推理可上 Modal/serverless"),
    "opencv-python": ("计算机视觉", "图像/视频处理；导入名 cv2，重计算可上 GPU/云"),
    # ---- LLM/API ----
    "openai": ("大模型API", "OpenAI SDK；密钥走环境变量/Secrets，勿硬编码"),
    "anthropic": ("大模型API", "Anthropic Claude SDK；密钥走环境变量/Secrets，勿硬编码"),
    "langchain": ("大模型编排", "LLM 应用编排/RAG；注意版本拆分(langchain-core 等)"),
    "aiohttp": ("HTTP", "异步 HTTP 客户端/服务端；纯客户端 httpx 更省心"),
    # ---- 绘图 ----
    "matplotlib": ("绘图", "投稿矢量图(pdf/svg)；演示用 png"),
    "seaborn": ("绘图", "统计图速成，底层 matplotlib"),
    "plotly": ("绘图", "交互图/HTML 报告；静态投稿仍用 matplotlib"),
    # ---- Python Web/后端 ----
    "fastapi": ("后端", "异步 API 首选；OpenAPI 自动生成便于确定性调用"),
    "django": ("后端", "全功能框架；ORM/admin/auth 齐全"),
    "flask": ("后端", "轻量 API；规模上来考虑 FastAPI 异步"),
    "uvicorn": ("后端", "ASGI 服务器，配 FastAPI"),
    "sqlalchemy": ("数据库", "ORM；参数化查询防注入"),
    "psycopg": ("数据库", "Postgres 驱动"),
    "redis": ("数据库", "缓存/队列"),
    # ---- 演示/原型 ----
    "gradio": ("演示界面", "ML 模型快速 Web demo；分享/评测原型首选"),
    "streamlit": ("演示界面", "数据应用/看板原型；纯 Python 交互页面"),
    # ---- 文档/排版 ----
    "python-docx": ("文档", "程序化生成 Word"),
    "python-pptx": ("PPT", "程序化生成 PPT；模板化幻灯片"),
    "openpyxl": ("文档", "读写 Excel xlsx"),
    "pylatex": ("排版", "Python 驱动 LaTeX；复杂排版直接写 .tex + latexmk"),
    # ---- 实验/版本管理 ----
    "mlflow": ("实验管理", "实验追踪/模型注册"),
    "wandb": ("实验管理", "W&B 实验可视化"),
    "dvc": ("数据版本", "大数据/模型版本化，配 Git"),
    "hydra-core": ("配置管理", "分层配置/多组实验扫描"),
    "snakemake": ("流水线", "可复现工作流编排"),
    # ---- 浏览器/抓取 ----
    "browser-use": ("浏览器自动化", "LLM 驱动 Playwright；偏 CLI/CDP 选 agent-browser"),
    "playwright": ("浏览器自动化", "底层自动化；AI 任务封装看 browser-use"),
    "scrapy": ("抓取", "大规模爬虫框架"),
    "requests": ("HTTP", "同步请求；有 OpenAPI 描述按 schema 确定性调用"),
    "httpx": ("HTTP", "异步/同步 HTTP，支持 HTTP/2"),
    # ---- JS/前端 ----
    "next": ("前端", "Next.js/React 全栈；配 shadcn/ui + Tailwind"),
    "react": ("前端", "组件库 shadcn/ui，图表 ECharts/D3"),
    "vue": ("前端", "Vue 生态；图表同样 ECharts"),
    "tailwindcss": ("前端", "原子化 CSS"),
    "echarts": ("前端", "数据可视化图表库"),
    "d3": ("前端", "底层可视化，自定义图形"),
    "vite": ("前端构建", "快速 dev server/打包"),
    "typescript": ("前端", "类型安全 JS；新项目默认开启"),
    "express": ("后端", "Node 轻量 API"),
    "jest": ("测试", "JS 单测"),
    "vitest": ("测试", "Vite 原生单测，比 jest 快"),
    "playwright-test": ("测试", "E2E 测试"),
    "pytest": ("测试", "Python 单测主力；配 pytest-cov 看覆盖率"),
    "ruff": ("代码质量", "Rust 写的极速 lint+format，替代 flake8/isort/black"),
    "black": ("代码质量", "格式化；新项目可用 ruff format 统一"),
    "mypy": ("代码质量", "静态类型检查"),
    "pre-commit": ("代码质量", "提交前钩子统一跑 lint/format/检查"),
    "great-expectations": ("数据质量", "数据校验/期望套件"),
    "ydata-profiling": ("数据质量", "一键数据画像报告"),
}

# 锁文件/配置文件存在性 -> 环境工具结论
ENV_HINTS = {
    "uv.lock": "检测到 uv.lock：用 `uv sync` 确定性安装，`uv run` 执行",
    "poetry.lock": "检测到 poetry.lock：延续 `poetry install`，勿混 pip/conda",
    "Pipfile.lock": "检测到 Pipfile.lock：pipenv 项目",
    "environment.yml": "检测到 conda 环境：`conda env create -f`，提速用 mamba",
    "environment.yaml": "检测到 conda 环境：`conda env create -f`，提速用 mamba",
    "Dockerfile": "检测到 Dockerfile：钉 FROM 版本 tag，依赖层在前源码在后",
    "package-lock.json": "npm 锁文件：`npm ci` 复现安装",
    "pnpm-lock.yaml": "pnpm 锁文件：`pnpm install --frozen-lockfile`",
    "yarn.lock": "yarn 锁文件：`yarn install --frozen-lockfile`",
}

# 别名/规范化表：真实生态里常见的后缀/异名包 -> RULES 里的规范键。
# 解决 claim_vs_code_gaps：torch-geometric / langchain-core / opencv-contrib 等
# 过去会全落 no-signal。规范化后这些包能命中已有规则，覆盖面如实扩大。
# 仅收录“确凿同族/确凿别名”，不做模糊子串猜测(守 no-signal 纪律)。
ALIASES = {
    # PyTorch 生态
    "torch-geometric": "torch", "torchgeometric": "torch",
    "torch-scatter": "torch", "torch-sparse": "torch", "pytorch-lightning": "torch",
    "lightning": "torch", "torchaudio": "torchvision",
    # LangChain 生态(版本拆分后多个子包)
    "langchain-core": "langchain", "langchain-community": "langchain",
    "langchain-openai": "langchain", "langchain-anthropic": "langchain",
    "langgraph": "langchain", "langchain-text-splitters": "langchain",
    # OpenCV 变体
    "opencv-contrib-python": "opencv-python",
    "opencv-python-headless": "opencv-python",
    "cv2": "opencv-python",
    # 科学图像
    "skimage": "scikit-image",
    # HF 生态
    "huggingface-hub": "transformers", "tokenizers": "transformers",
    "accelerate": "transformers", "datasets": "transformers",
    # 前端别名
    "react-dom": "react", "next.js": "next", "nextjs": "next",
    "tailwind": "tailwindcss",
    # 其它常见别名
    "hydra": "hydra-core", "ydata_profiling": "ydata-profiling",
    "pandas-profiling": "ydata-profiling",  # 旧名，已更名 ydata-profiling
}

# 异味/冲突规则：把 SKILL 反复 preach 的铁律("不混 pip+conda""选维护活跃工具")
# 变成可执行的确定性核对。每条 = (id, predicate(ctx)->命中详情或None, 级别, 文案模板)。
# 级别: "critical"(冲突，必处理) / "warn"(异味，建议) / "info"(提示)。
# ctx 是 build_context() 给的字典，含 deps/conda_deps/pip_deps/manifests/license_signals 等。
_DEPRECATED = {
    "vaex": "vaex 2023 后停维护(已淘汰)；迁 DuckDB / polars streaming",
    "nose": "nose 已废弃多年(不兼容新 Python)；迁 pytest",
    "nose2": "nose 系列维护停滞；统一用 pytest",
    "distutils": "distutils 在 Python 3.12 已移除；改用 setuptools/packaging",
    "python-levenshtein": "旧名已弃用；改装 `Levenshtein`(python-Levenshtein 仅留兼容壳)",
    "sklearn": "PyPI `sklearn` 是占位空壳包(已弃用)；应改装 `scikit-learn`",
    "pandas-profiling": "pandas-profiling 已更名 `ydata-profiling`，旧名停更",
}


def _smell_pip_conda_mix(ctx):
    """同一 environment.yml 里 conda 段与 pip: 子列表声明了同一包 -> 求解冲突风险。"""
    overlap = sorted(set(ctx["conda_deps"]) & set(ctx["pip_deps"]))
    if overlap:
        return (f"environment.yml 同时用 conda 段与 pip: 子列表声明了 "
                f"{', '.join(overlap)} —— pip/conda 混装同一包易致依赖求解冲突，"
                f"二选一(优先 conda 段统一管理，或全交给 pip)")
    return None


def _smell_double_dl_framework(ctx):
    d = set(ctx["deps"])
    if "tensorflow" in d and ("torch" in d or "pytorch" in d):
        return ("同时依赖 tensorflow 与 torch —— 两大深度学习框架并存会膨胀环境/"
                "CUDA 协调复杂；确认是否真需双框架，否则收敛到其一")
    return None


def _smell_redundant_http(ctx):
    d = set(ctx["deps"])
    http_libs = [x for x in ("requests", "httpx", "aiohttp") if x in d]
    if len(http_libs) >= 3:
        return (f"同时依赖 {', '.join(http_libs)} 三个 HTTP 库 —— 多为历史叠加冗余；"
                f"新代码统一到 httpx(同步+异步+HTTP/2)可减少维护面")
    return None


def _smell_deprecated(ctx):
    hits = [(d, _DEPRECATED[d]) for d in sorted(set(ctx["deps"])) if d in _DEPRECATED]
    if hits:
        return "；".join(f"{d}: {msg}" for d, msg in hits)
    return None


def _smell_anaconda_channel(ctx):
    """检测到 anaconda defaults channel -> Anaconda 商业 license 合规提醒。"""
    if ctx.get("uses_defaults_channel"):
        return ("environment.yml 使用了 anaconda `defaults` channel —— "
                "Anaconda 默认源对中大型组织已转商业许可；学术/商用前确认 ToS，"
                "或改用全 `conda-forge`(社区免费) channel")
    return None


SMELLS = [
    ("pip_conda_mix", _smell_pip_conda_mix, "critical"),
    ("double_dl_framework", _smell_double_dl_framework, "warn"),
    ("redundant_http", _smell_redundant_http, "warn"),
    ("deprecated_dep", _smell_deprecated, "warn"),
    ("anaconda_license", _smell_anaconda_channel, "info"),
]

# environment.yml 解析时把 conda 段 / pip 子列表分别记到这里(供冲突检测)。
# 每次 scan() 开头 reset，避免跨调用串味。
_ENV_SPLIT = {"conda_deps": [], "pip_deps": [], "uses_defaults_channel": False}


def _reset_env_split():
    _ENV_SPLIT["conda_deps"] = []
    _ENV_SPLIT["pip_deps"] = []
    _ENV_SPLIT["uses_defaults_channel"] = False


def _norm(name):
    """规整依赖名：去版本/extras/空白，转小写。"""
    name = name.strip().lower()
    name = re.split(r"[<>=!~;\[\(@\s]", name, 1)[0]
    return name.strip()


def _canon(dep):
    """把别名/同族包规范到 RULES 的规范键(命不中别名则原样返回)。"""
    return ALIASES.get(dep, dep)


def _currency_path():
    return os.path.join(os.path.dirname(__file__), "..", "references", "tool_currency.json")


def load_currency():
    """加载工具时效元数据(最新大版本/EOL/弃用)。缺失/损坏则返回 None 并降级。"""
    p = _currency_path()
    if not os.path.isfile(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _parse_version_tuple(v):
    """'2.1.0' -> (2,1,0)；解析失败返回 None。只取前三段数字。"""
    if not v:
        return None
    nums = re.findall(r"\d+", str(v))
    if not nums:
        return None
    return tuple(int(x) for x in nums[:3])


def parse_lock_versions(project_dir):
    """解析锁文件里钉死的版本号(uv.lock / poetry.lock / package-lock.json)。

    返回 {规范包名: 版本字符串}。纯文本/JSON 解析，无第三方依赖。
    这是 claim_vs_code_gaps 的兑现点：过去只做 isfile 存在性判断、从不读版本。
    """
    versions = {}

    # ---- uv.lock / poetry.lock 都是 TOML，结构 [[package]] name=.. version=.. ----
    for lock in ("uv.lock", "poetry.lock"):
        p = os.path.join(project_dir, lock)
        if not os.path.isfile(p) or tomllib is None:
            continue
        try:
            with open(p, "rb") as f:
                d = tomllib.load(f)
        except Exception:
            continue
        for pkg in (d.get("package") or []):
            nm = _norm(str(pkg.get("name", "")))
            ver = pkg.get("version")
            if nm and ver:
                versions.setdefault(_canon(nm), str(ver))

    # ---- package-lock.json (npm v2/v3: packages{} 或 v1: dependencies{}) ----
    p = os.path.join(project_dir, "package-lock.json")
    if os.path.isfile(p):
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            d = {}
        pkgs = d.get("packages") or {}
        for path, meta in pkgs.items():
            if not path.startswith("node_modules/"):
                continue
            nm = _norm(path.split("node_modules/")[-1])
            ver = (meta or {}).get("version")
            if nm and ver:
                versions.setdefault(_canon(nm), str(ver))
        for nm, meta in (d.get("dependencies") or {}).items():  # v1 兜底
            ver = (meta or {}).get("version")
            if ver:
                versions.setdefault(_canon(_norm(nm)), str(ver))
    return versions


def check_version_currency(lock_versions, currency):
    """据锁文件版本 + 时效元数据，标记落后大版本/已 EOL/弃用。

    返回 version_flags 列表，每项 {package, installed, latest_major, level, msg}。
    currency 缺失时返回 [] 并不臆造(降级，由调用方标注)。
    """
    flags = []
    if not currency:
        return flags
    tools = currency.get("tools", {})
    for pkg, ver in sorted(lock_versions.items()):
        meta = tools.get(pkg)
        if not meta:
            continue
        installed = _parse_version_tuple(ver)
        if meta.get("deprecated"):
            flags.append({"package": pkg, "installed": ver,
                          "level": "warn",
                          "msg": f"{pkg} {ver}: {meta.get('note', '已弃用')}"})
            continue
        latest_major = meta.get("latest_major")
        if installed and isinstance(latest_major, int):
            behind = latest_major - installed[0]
            if behind >= 2:
                flags.append({"package": pkg, "installed": ver,
                              "latest_major": latest_major, "level": "warn",
                              "msg": (f"{pkg} {ver} 落后 {behind} 个大版本"
                                      f"(最新主版本 {latest_major}，"
                                      f"last_checked {meta.get('last_checked', '?')})；"
                                      f"评估升级")})
            elif behind == 1:
                flags.append({"package": pkg, "installed": ver,
                              "latest_major": latest_major, "level": "info",
                              "msg": (f"{pkg} {ver} 落后 1 个大版本"
                                      f"(最新 {latest_major})；非紧急但留意")})
    return flags


def parse_package_json(path):
    deps = []
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:
        return deps, [f"package.json 解析失败: {e}"]
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        for k in (d.get(key) or {}):
            deps.append(_norm(k))
    return deps, []


def parse_pyproject(path):
    deps, notes = [], []
    if tomllib is None:
        return deps, ["tomllib 不可用(需 Python 3.11+)，跳过 pyproject.toml"]
    try:
        with open(path, "rb") as f:
            d = tomllib.load(f)
    except Exception as e:
        return deps, [f"pyproject.toml 解析失败: {e}"]
    # PEP 621
    for item in (d.get("project", {}).get("dependencies") or []):
        deps.append(_norm(item))
    og = d.get("project", {}).get("optional-dependencies", {})
    for grp in og.values():
        for item in grp:
            deps.append(_norm(item))
    # Poetry
    poetry = d.get("tool", {}).get("poetry", {})
    for k in (poetry.get("dependencies") or {}):
        if k.lower() != "python":
            deps.append(_norm(k))
    return deps, notes


def parse_requirements(path):
    deps = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(("#", "-")):
                    continue
                deps.append(_norm(line))
    except Exception as e:
        return deps, [f"requirements 解析失败: {e}"]
    return deps, []


def parse_environment_yml(path):
    """conda environment.yml：优先 PyYAML，缺失则正则降级。

    返回 (deps, notes)。同时把 conda 段 / pip 子列表分别记录到模块级
    _ENV_SPLIT(供冲突检测用)，并标记是否用了 defaults channel。
    """
    deps, notes = [], []
    conda_deps, pip_deps = [], []
    uses_defaults = False
    try:
        text = open(path, encoding="utf-8").read()
    except Exception as e:
        return deps, [f"environment.yml 读取失败: {e}"]
    try:
        import yaml
        d = yaml.safe_load(text) or {}
        for ch in (d.get("channels") or []):
            if str(ch).strip() in ("defaults", "anaconda"):
                uses_defaults = True
        for item in (d.get("dependencies") or []):
            if isinstance(item, str):
                nm = _norm(item)
                deps.append(nm)
                conda_deps.append(nm)
            elif isinstance(item, dict):  # pip: 子列表
                for sub in item.get("pip", []) or []:
                    nm = _norm(sub)
                    deps.append(nm)
                    pip_deps.append(nm)
    except ModuleNotFoundError:
        notes.append("PyYAML 缺失，environment.yml 用正则降级解析(pip/conda 分段近似)")
        in_pip = False
        in_channels = False
        for line in text.splitlines():
            stripped = line.strip()
            if re.match(r"channels\s*:", line):
                in_channels = True
                continue
            if re.match(r"dependencies\s*:", line):
                in_channels = False
            if in_channels and re.search(r"-\s*(defaults|anaconda)\b", stripped):
                uses_defaults = True
            if re.match(r"\s*-?\s*pip\s*:", line):
                in_pip = True
                continue
            m = re.match(r"(\s*)-\s*([A-Za-z0-9_.\-]+)", line)
            if m and not in_channels:
                indent = len(m.group(1))
                nm = _norm(m.group(2))
                if nm in ("pip", "defaults", "anaconda", "conda-forge"):
                    continue
                deps.append(nm)
                # 缩进更深的视为 pip 子列表项(降级近似)
                (pip_deps if (in_pip and indent >= 6) else conda_deps).append(nm)
    _ENV_SPLIT["conda_deps"].extend(conda_deps)
    _ENV_SPLIT["pip_deps"].extend(pip_deps)
    if uses_defaults:
        _ENV_SPLIT["uses_defaults_channel"] = True
    return deps, notes


def parse_pipfile(path):
    """Pipfile 本质是 TOML，读 [packages] 与 [dev-packages] 的键名。"""
    deps, notes = [], []
    if tomllib is None:
        return deps, ["tomllib 不可用(需 Python 3.11+)，跳过 Pipfile"]
    try:
        with open(path, "rb") as f:
            d = tomllib.load(f)
    except Exception as e:
        return deps, [f"Pipfile 解析失败: {e}"]
    for section in ("packages", "dev-packages"):
        for k in (d.get(section) or {}):
            if k.lower() != "python":
                deps.append(_norm(k))
    return deps, notes


MANIFESTS = {
    "package.json": parse_package_json,
    "pyproject.toml": parse_pyproject,
    "requirements.txt": parse_requirements,
    "environment.yml": parse_environment_yml,
    "environment.yaml": parse_environment_yml,
    "Pipfile": parse_pipfile,
}


def _detect_ci(project_dir):
    """探测 .github/workflows/*.yml(.yaml) 是否存在 → CI 已配置提示。"""
    wf_dir = os.path.join(project_dir, ".github", "workflows")
    if not os.path.isdir(wf_dir):
        return None
    try:
        wfs = [f for f in os.listdir(wf_dir)
               if f.endswith((".yml", ".yaml"))]
    except OSError:
        return None
    if not wfs:
        return None
    return (f"检测到 GitHub Actions({len(wfs)} 个 workflow: "
            f"{', '.join(sorted(wfs)[:5])}{' ...' if len(wfs) > 5 else ''})："
            "CI 已配置；事件触发/定时/matrix 复现走 Actions，本地数据依赖编排仍用 Snakemake/Make")


def _detect_lang_stacks(project_dir):
    """探测 SKILL 宣称但无依赖清单的科研语言栈：R/MATLAB/LaTeX/Jupyter。

    靠特征文件存在性 + 顶层扩展名扫描判断（与 MANIFESTS 一致的浅层扫描，
    确定性、不臆造）。返回结论字符串列表。
    """
    hits = []
    try:
        entries = os.listdir(project_dir)
    except OSError:
        entries = []
    names = set(entries)

    def _has_ext(ext):
        return any(e.lower().endswith(ext) for e in entries)

    # ---- R ----
    r_signals = []
    if "DESCRIPTION" in names:
        r_signals.append("DESCRIPTION")
    if "renv.lock" in names:
        r_signals.append("renv.lock")
    if _has_ext(".rproj"):
        r_signals.append(".Rproj")
    if r_signals:
        hits.append(f"检测到 R 项目({', '.join(r_signals)})："
                    "高级统计/混合模型/ggplot2 出图用 R；"
                    "依赖复现用 renv(`renv::restore()`)")
    # ---- MATLAB ----
    if _has_ext(".m"):
        hits.append("检测到 MATLAB 源码(.m)："
                    "信号/控制/数值/Simulink 场景用 MATLAB；"
                    "可复现脚本化运行、跨语言可经 conda 协调")
    # ---- LaTeX ----
    tex_signals = []
    if _has_ext(".tex"):
        tex_signals.append(".tex")
    if "latexmkrc" in names or ".latexmkrc" in names:
        tex_signals.append("latexmkrc")
    if tex_signals:
        hits.append(f"检测到 LaTeX 排版({', '.join(tex_signals)})："
                    "用 latexmk 一键编译(TinyTeX/TeX Live)，矢量 PDF 投稿")
    # ---- Jupyter ----
    if _has_ext(".ipynb"):
        hits.append("检测到 Jupyter Notebook(.ipynb)："
                    "探索/演示用；投稿/复现把稳定逻辑抽进 .py 脚本，配 nbconvert")
    return hits


def scan(project_dir):
    """扫描目录，返回 (deps集合, 命中清单文件, env提示, 解析备注)。"""
    _reset_env_split()
    deps, found_manifests, env_hits, notes = [], [], [], []
    for fname, parser in MANIFESTS.items():
        p = os.path.join(project_dir, fname)
        if os.path.isfile(p):
            d, n = parser(p)
            deps.extend(d)
            notes.extend(n)
            found_manifests.append(fname)
    for fname, hint in ENV_HINTS.items():
        if os.path.isfile(os.path.join(project_dir, fname)):
            env_hits.append(hint)
    ci = _detect_ci(project_dir)
    if ci:
        env_hits.append(ci)
    env_hits.extend(_detect_lang_stacks(project_dir))
    return sorted(set(deps)), found_manifests, env_hits, notes


def suggest(deps):
    """对命中规则的依赖给建议，按类别聚合。

    匹配顺序：精确键 -> 连字符/下划线变体 -> ALIASES 规范化(同族/别名)。
    命中别名时如实记录映射(matched 记原始 dep，advice 注明规范到哪个键)。"""
    by_cat = {}
    matched = []
    for dep in deps:
        canon = _canon(dep)
        hit_key = None
        for key in (dep, dep.replace("-", "_"), canon, canon.replace("-", "_")):
            if key in RULES:
                hit_key = key
                break
        if hit_key:
            cat, advice = RULES[hit_key]
            if canon != dep and hit_key in (canon, canon.replace("-", "_")):
                advice = f"(经别名规范到 {canon}) {advice}"
            by_cat.setdefault(cat, []).append((dep, advice))
            matched.append(dep)
    return by_cat, matched


def build_context(project_dir):
    """汇总一次扫描的全部上下文(供 smells/version/tooling-plan 共用)。"""
    deps, manifests, env_hits, notes = scan(project_dir)
    return {
        "project_dir": project_dir,
        "deps": deps,
        "manifests": manifests,
        "env_hits": env_hits,
        "notes": notes,
        "conda_deps": list(_ENV_SPLIT["conda_deps"]),
        "pip_deps": list(_ENV_SPLIT["pip_deps"]),
        "uses_defaults_channel": _ENV_SPLIT["uses_defaults_channel"],
    }


def check_smells(ctx):
    """跑所有 SMELLS 规则，返回命中列表 [{id, level, detail}]。"""
    out = []
    for sid, pred, level in SMELLS:
        detail = pred(ctx)
        if detail:
            out.append({"id": sid, "level": level, "detail": detail})
    return out


def build_tooling_plan(rep):
    """把检测结论凝成机读 tooling_plan：每条 = 任务环节→选定工具→理由→数据格式。

    供下游技能(m02 数据工程/a03 后端/m09 图/m07 写作)直接消费选型，不各自重判栈。
    只据已命中规则生成(no-signal 不进 plan)，守不臆造纪律。"""
    # 类别 -> 推荐数据流转格式(多工具协同时的交接格式)
    fmt_by_cat = {
        "数据处理": "parquet/csv", "数据质量": "html/json 报告",
        "绘图": "矢量 pdf/svg(投稿)·png(演示)", "前端": "json/REST",
        "后端": "json/REST", "排版": "pdf", "文档": "docx/xlsx",
        "PPT": "pptx", "深度学习": "checkpoint/onnx", "机器学习": "pkl/onnx",
        "实验管理": "run logs/metrics", "数据库": "sql/连接串",
    }
    steps = []
    for cat, items in sorted(rep["suggestions_by_category"].items()):
        tools = [it["dep"] for it in items]
        rationale = items[0]["advice"]
        steps.append({
            "stage": cat,
            "selected_tools": tools,
            "rationale": rationale,
            "data_format": fmt_by_cat.get(cat, "按下游约定"),
        })
    return {
        "schema": "light.tooling_plan.v1",
        "producer": "a09",
        "project_dir": rep["project_dir"],
        "steps": steps,
        "env": rep["env_recommendations"],
        "version_flags": rep["version_flags"],
        "smells": rep["smells"],
        "no_signal": rep["unmatched_no_signal"],
    }


def build_report(project_dir):
    ctx = build_context(project_dir)
    deps, manifests, env_hits, notes = (
        ctx["deps"], ctx["manifests"], ctx["env_hits"], ctx["notes"])
    by_cat, matched = suggest(deps)
    unmatched = [d for d in deps if d not in matched]
    smells = check_smells(ctx)
    currency = load_currency()
    lock_versions = parse_lock_versions(project_dir)
    if currency:
        version_flags = check_version_currency(lock_versions, currency)
    else:
        version_flags = []
        if lock_versions:
            notes.append("tool_currency.json 缺失/损坏：已解析锁文件版本但跳过时效判定"
                         "(降级，不臆造落后/EOL)")
    rep = {
        "project_dir": os.path.abspath(project_dir),
        "manifests_found": manifests,
        "total_deps": len(deps),
        "matched": matched,
        "unmatched_no_signal": unmatched,
        "suggestions_by_category": {
            c: [{"dep": d, "advice": a} for d, a in v] for c, v in by_cat.items()
        },
        "env_recommendations": env_hits,
        "smells": smells,
        "lock_versions": lock_versions,
        "version_flags": version_flags,
        "parse_notes": notes,
    }
    rep["tooling_plan"] = build_tooling_plan(rep)
    return rep


def print_report(rep):
    print("=" * 60)
    print(f"技术栈检测报告  目录: {rep['project_dir']}")
    print("=" * 60)
    if not rep["manifests_found"]:
        if rep["env_recommendations"]:
            print("未发现依赖清单文件，但检测到以下语言栈/环境信号：")
            for h in rep["env_recommendations"]:
                print(f"  - {h}")
            return
        print("未发现任何清单文件 (package.json/pyproject.toml/requirements.txt/"
              "environment.yml/Pipfile)。无信号，无法建议。")
        return
    print(f"清单文件: {', '.join(rep['manifests_found'])}")
    print(f"依赖总数: {rep['total_deps']}  命中规则: {len(rep['matched'])}")
    print()
    # 冲突/异味优先打印(这是 SKILL 铁律的可执行兑现)
    if rep["smells"]:
        print("[冲突/异味]")
        _lab = {"critical": "冲突", "warn": "异味", "info": "提示"}
        for s in rep["smells"]:
            print(f"  - [{_lab.get(s['level'], s['level'])}] {s['detail']}")
        print()
    if rep["version_flags"]:
        print("[版本时效]")
        for vf in rep["version_flags"]:
            print(f"  - {vf['msg']}")
        print()
    if rep["env_recommendations"]:
        print("[环境/复现]")
        for h in rep["env_recommendations"]:
            print(f"  - {h}")
        print()
    if rep["suggestions_by_category"]:
        print("[工具选型建议]")
        for cat, items in sorted(rep["suggestions_by_category"].items()):
            print(f"  {cat}:")
            for it in items:
                print(f"    - {it['dep']}: {it['advice']}")
        print()
    if rep["unmatched_no_signal"]:
        u = rep["unmatched_no_signal"]
        print(f"[no signal] {len(u)} 个依赖无内置规则(不臆造建议): "
              f"{', '.join(u[:12])}{' ...' if len(u) > 12 else ''}")
        print()
    if rep["parse_notes"]:
        print("[解析备注]")
        for n in rep["parse_notes"]:
            print(f"  - {n}")


# ---------------------------------------------------------------- findings 契约
def _smell_gate(rep):
    """把冲突/异味凝成一个 gate。critical 级冲突 -> 阻断。"""
    findings = []
    for s in rep["smells"]:
        findings.append(Finding(
            loc=f"stack:{s['id']}", issue=s["detail"],
            fix="见 SKILL 选型铁律(不混 pip+conda / 收敛冗余框架 / 迁出弃用包)",
            rule=f"detect_stack.smell.{s['id']}"))
    has_crit = any(s["level"] == "critical" for s in rep["smells"])
    status = "fail" if findings else "pass"
    sev = "critical" if has_crit else ("major" if findings else "info")
    return GateResult("dependency_smells", status, sev, findings,
                      note="冲突/异味确定性核对(兑现 SKILL 铁律)")


def _currency_gate(rep):
    """把版本时效旗标凝成一个 gate(落后大版本/EOL/弃用)。"""
    findings = [Finding(loc=f"version:{vf['package']}", issue=vf["msg"],
                        fix="评估升级到受支持的大版本",
                        rule="detect_stack.version_currency")
                for vf in rep["version_flags"]]
    status = "warn" if findings else "pass"
    sev = "major" if findings else "info"
    note = ("据 tool_currency.json + 锁文件版本判定"
            if rep["lock_versions"] or findings
            else "无锁文件版本或 currency 元数据缺失，跳过(降级)")
    return GateResult("version_currency", status, sev, findings, note=note)


def emit_findings(rep):
    """据检测报告产出 light.findings.v1(挂接 _shared/gate_runner)。

    producer=a09，target=tooling-plan(本技能的产出工件)。供 a01 passport 接线、
    db09 记忆消费。fresh_evidence=True 因为本轮现扫现判。"""
    if not _HAS_SHARED:
        return {"error": "_shared findings 契约不可用(降级)，未产出 findings",
                "schema": None}
    report = run_gates(
        [_smell_gate, _currency_gate], rep,
        producer="a09", target="tooling-plan",
        summary=(f"{rep['total_deps']} deps, {len(rep['matched'])} matched, "
                 f"{len(rep['smells'])} smells, {len(rep['version_flags'])} version flags"),
        fresh_evidence=True)
    return json.loads(report.to_json())


def self_test():
    """无数据时：在临时目录写合成清单，跑全流程并断言。"""
    import tempfile, shutil
    tmp = tempfile.mkdtemp(prefix="detect_stack_")
    try:
        # 合成一个 Python 数据科学 + conda 项目
        # 故意埋入异味：tensorflow+torch 双框架、requests+httpx+aiohttp 三 HTTP、
        # 弃用包 vaex；以及别名包 torch-geometric / langchain-core / skimage。
        with open(os.path.join(tmp, "requirements.txt"), "w", encoding="utf-8") as f:
            f.write("pandas>=2.0\nscikit-learn==1.4.0\nmatplotlib\n"
                    "fastapi\nxgboost\nopencv-python\ngradio\n"
                    "tensorflow\ntorch\nrequests\nhttpx\naiohttp\nvaex\n"
                    "torch-geometric\nlangchain-core\nscikit-image\n"
                    "some-private-internal-lib==9.9\n# comment\n")
        # environment.yml 故意 conda 段与 pip 子列表都声明 numpy -> pip/conda 混装冲突
        # 且用 defaults channel -> Anaconda license 提示
        with open(os.path.join(tmp, "environment.yml"), "w", encoding="utf-8") as f:
            f.write("name: demo\nchannels:\n  - defaults\n  - conda-forge\n"
                    "dependencies:\n  - numpy\n  - pytorch\n  - pip:\n"
                    "      - wandb\n      - numpy\n")
        # 合成一个 JS 前端清单(含别名 react-dom / next.js)
        with open(os.path.join(tmp, "package.json"), "w", encoding="utf-8") as f:
            json.dump({"dependencies": {"next": "15", "react": "19",
                       "react-dom": "19", "tailwindcss": "4"},
                       "devDependencies": {"vitest": "3"}}, f)
        # uv.lock 含一个落后大版本的包(pydantic 1.x，最新主版本 2) -> 版本时效旗标
        with open(os.path.join(tmp, "uv.lock"), "w", encoding="utf-8") as f:
            f.write('[[package]]\nname = "pydantic"\nversion = "1.10.2"\n\n'
                    '[[package]]\nname = "fastapi"\nversion = "0.110.0"\n')

        # 合成 GitHub Actions workflow
        wf_dir = os.path.join(tmp, ".github", "workflows")
        os.makedirs(wf_dir, exist_ok=True)
        with open(os.path.join(wf_dir, "ci.yml"), "w", encoding="utf-8") as f:
            f.write("name: ci\non: [push]\njobs:\n  test:\n"
                    "    runs-on: ubuntu-latest\n    steps:\n"
                    "      - uses: actions/checkout@v6\n")

        # 合成 SKILL 宣称的科研语言栈特征文件：R/MATLAB/LaTeX/Jupyter
        open(os.path.join(tmp, "DESCRIPTION"), "w").close()
        open(os.path.join(tmp, "renv.lock"), "w").close()
        open(os.path.join(tmp, "analysis.m"), "w").close()
        open(os.path.join(tmp, "paper.tex"), "w").close()
        open(os.path.join(tmp, "explore.ipynb"), "w").close()

        rep = build_report(tmp)
        print_report(rep)
        findings = emit_findings(rep)
        print("\n[findings 契约(light.findings.v1)]")
        print(json.dumps(findings, ensure_ascii=False, indent=2)[:600], "...")
        print("\n--- 自检断言 ---")

        smell_ids = {s["id"] for s in rep["smells"]}
        vf_pkgs = {vf["package"] for vf in rep["version_flags"]}
        checks = {
            "命中 pandas": "pandas" in rep["matched"],
            "命中 fastapi": "fastapi" in rep["matched"],
            "命中 next(JS)": "next" in rep["matched"],
            "命中 wandb(conda pip 子列表)": "wandb" in rep["matched"],
            "命中 xgboost(新增别名)": "xgboost" in rep["matched"],
            "命中 opencv-python(新增别名)": "opencv-python" in rep["matched"],
            "命中 gradio(新增别名)": "gradio" in rep["matched"],
            "别名命中 torch-geometric->torch": "torch-geometric" in rep["matched"],
            "别名命中 langchain-core->langchain": "langchain-core" in rep["matched"],
            "别名命中 scikit-image": "scikit-image" in rep["matched"],
            "别名命中 react-dom->react": "react-dom" in rep["matched"],
            "私有库归入 no-signal": "some-private-internal-lib"
                in rep["unmatched_no_signal"],
            "冲突: pip/conda 混装 numpy": "pip_conda_mix" in smell_ids,
            "异味: tf+torch 双框架": "double_dl_framework" in smell_ids,
            "异味: requests/httpx/aiohttp 三 HTTP 冗余": "redundant_http" in smell_ids,
            "异味: 弃用包 vaex": "deprecated_dep" in smell_ids,
            "提示: anaconda defaults channel 许可": "anaconda_license" in smell_ids,
            "锁文件版本被解析(pydantic)": "pydantic" in rep["lock_versions"],
            "版本时效旗标命中 pydantic 落后大版本": "pydantic" in vf_pkgs,
            "tooling_plan 已生成且含 steps":
                bool(rep["tooling_plan"]["steps"]) and
                rep["tooling_plan"]["schema"] == "light.tooling_plan.v1",
            "findings 契约可用且 producer=a09":
                _HAS_SHARED and findings.get("producer") == "a09",
            "findings verdict=fail(critical 冲突应阻断)":
                findings.get("verdict") == "fail",
            "识别 uv.lock 环境": any("uv.lock" in h
                for h in rep["env_recommendations"]),
            "识别 conda 环境": any("conda" in h
                for h in rep["env_recommendations"]),
            "识别 GitHub Actions CI": any("GitHub Actions" in h
                for h in rep["env_recommendations"]),
            "识别 R 项目(DESCRIPTION/renv.lock)": any("R 项目" in h
                for h in rep["env_recommendations"]),
            "识别 MATLAB(.m)": any("MATLAB" in h
                for h in rep["env_recommendations"]),
            "识别 LaTeX(.tex)": any("LaTeX" in h
                for h in rep["env_recommendations"]),
            "识别 Jupyter(.ipynb)": any("Jupyter" in h
                for h in rep["env_recommendations"]),
            "三个清单都解析到": set(rep["manifests_found"]) >=
                {"package.json", "requirements.txt", "environment.yml"},
        }
        ok = True
        for name, passed in checks.items():
            print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
            ok = ok and passed
        print(f"\n自检结果: {'全部通过' if ok else '存在失败'}")
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="检测项目技术栈并建议工具选型")
    ap.add_argument("project_dir", nargs="?", help="项目目录")
    ap.add_argument("--self-test", "--selftest", dest="self_test", action="store_true", help="合成清单自检")
    ap.add_argument("--json", action="store_true", help="输出完整 JSON 报告(含 tooling_plan)")
    ap.add_argument("--findings", action="store_true",
                    help="输出 light.findings.v1(冲突/版本时效门，供 a01/db09 消费)")
    args = ap.parse_args()

    if args.self_test or not args.project_dir:
        if not args.project_dir:
            print("[未提供目录，运行自检 --self-test]\n")
        return self_test()

    if not os.path.isdir(args.project_dir):
        print(f"错误：目录不存在 {args.project_dir}", file=sys.stderr)
        return 2
    rep = build_report(args.project_dir)
    if args.findings:
        print(json.dumps(emit_findings(rep), ensure_ascii=False, indent=2))
    elif args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print_report(rep)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
