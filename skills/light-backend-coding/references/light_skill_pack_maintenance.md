# Light 技能包维护：断点恢复、质量门与入口防漂移

适用于维护 `D:/skill/Light` 这类多技能包仓库：用户经常在 Claude/Hermes 断流后说“继续 / 刚断了”，期望直接接手并完成真实验证、提交、推送、等待 CI。

## 断点恢复流程

1. **不要询问用户复述**：把“继续 / 刚断了 / 接手 Claude”视为恢复指令。
2. 立即读取活状态：
   - `git status --short --branch`
   - 最近提交：`git log --oneline -8`
   - 相关 CI：`gh run list --branch master --limit 5`
   - 当前 todo（若可用）
   - 当前任务相关文件 diff / 校验器输出
3. 若看到 CRLF/整文件换行污染，先转 LF 再继续；不要把换行污染和真实改动混在一起提交。
4. 只在真实 blocker（缺上下文且工具无法恢复、危险破坏性操作）时问用户。

## 提交前必须做到“真实跑过”

- 不能只写脚本或文档；要跑对应校验器和自测。
- Light 仓库当前核心 gates：
  - `python .github/scripts/check_skills.py`
  - `python .github/scripts/check_databases.py`
  - `python .github/scripts/check_skill_assets.py`
  - `python .github/scripts/check_entry_docs.py`
  - `/d/Anaconda/python.exe .github/scripts/run_skill_selftests.py --group all --timeout 120`
- 运行 `git diff --check` 和 added-line 静态扫描：secret、`shell=True`/`os.system`、`eval`/`exec`、`pickle.loads`、SQL 字符串拼接。
- 推送后用 `gh run watch <run_id> --exit-status` 等 CI 通过，再汇报。

## 技能脚本 `--selftest` 治理

- 资产校验不能只搜 `selftest` 字样；必须要求显式 `--selftest`。
- CI 不只检查 marker，还要实际执行 `python <script> --selftest`。
- 自测必须离线、合成数据/临时目录、真实断言，不依赖 DOI/Crossref/OpenAlex/S2、账号、LibreOffice 或网络。
- 旧脚本若保留无参自测，入口只能接受无参或唯一 `--selftest`：

```python
if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] != "--selftest"):
    raise SystemExit(f"usage: python {sys.argv[0]} [--selftest]")
_selftest()
```

## 入口文档防漂移

- `README.md` / `README.en.md` / `ROUTER.md` / `MODE_REGISTRY.md` / `CONVENTIONS.md` / `WHATS_INCLUDED.md` 是用户入口层，改动要一起审计。
- `ROUTER_EXAMPLES.md` 是路由样例回归集；新增/修改路由规则时同步样例。
- 重点锁定边界：
  - “继续 / 刚断了 / 接手 Claude” → `a02 memory-pm + light-orchestrator` 断点恢复。
  - “继续写 / 继续润色当前段落” → 单技能 `m07` / `m08`，不要启动 orchestrator。
  - 图表规划 `m09`、实际绘图/图表审查 `m11`、PPT/deck QA `m16`。
  - paper-drafting 的草稿 self-review 属 `m07`；正式模拟审稿/rebuttal 属 `m14`。
- 禁止重新引入非本包技能：`light-software`、`light-miniprogram`、`light-novel`。

## 提交习惯

- 按用途分组提交，中文 commit message 描述文件/模块目的，不写 Claude/AI co-author trailer。
- 推送前在提交后再跑一次完整 gate，避免 rebase/squash 后产生换行或校验漂移。
