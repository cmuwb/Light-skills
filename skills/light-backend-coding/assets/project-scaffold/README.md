# example-project

`light-backend-coding` 的可运行项目骨架。复制本目录改名即用。

## 安装

```bash
uv sync --extra dev      # 按 pyproject 解析并装运行+dev 依赖
uv run pre-commit install   # 启用提交钩子（可选）
```

无 uv 时可退回：

```bash
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## 运行测试

```bash
uv run pytest                                   # 全测试，首失败即停
uv run pytest --cov=src --cov-report=term-missing   # 看覆盖率
```

## 质量门

```bash
uv run ruff check .          # linter
uv run ruff format --check . # formatter（与 linter 是两个命令）
uv run pre-commit run --all-files
```

## 复现

- Python 版本锁在 `pyproject.toml` 的 `requires-python`；CI matrix 跑 3.11/3.12/3.13。
- 提交 `uv.lock`（首次 `uv lock` 生成），CI 用 `uv sync` 还原确定性环境。
- 固定随机种子、记录环境（`uv pip freeze` 或 lock 文件）。

## 结构

```
pyproject.toml            # 元数据 + 依赖 + ruff/pytest 配置
.pre-commit-config.yaml   # ruff + 基础钩子，rev 锁版本
.github/workflows/ci.yml  # checkout -> setup-python -> uv sync -> ruff -> pytest
src/example/stats.py      # 示例模块（单一职责 + 输入校验）
tests/test_stats.py       # parametrize + 异常断言
tests/conftest.py         # 共享路径设置
```
