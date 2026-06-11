---
name: light-research-plan
description: 对已确认可行的 idea 制定极其详细的研究方案、实验设计与执行规划。当用户的 idea 已通过 m04 审查、需要把 idea 拆成可执行可复现的完整科研流程时使用。覆盖研究目标、技术路线、数据流程、实验/消融/敏感性/鲁棒性/显著性检验、时间安排、风险与备选，并保证全程可复现。
---

# 研究方案与实验执行规划

## 前置
仅对 m04 已放行的 idea 执行。开工前确认数据(m02)与方法(db03)就绪。

## 方案内容（逐项写实，不写空话）
1. **研究目标 & 核心问题**：可证伪的假设 H1/H2…。
2. **技术路线**：整体框架图（交 m09/m11），关键模块与数据流。
3. **数据**：来源、处理流程(引 m02 流水线)、划分方式、统计。
4. **模型/方法**：算法流程、公式、伪代码、复杂度。
5. **实验设计**：每个实验条目按 EXP-Bench 四要素写全 —— 研究问题(对应哪条假设)、设计(自/因/控变量+数据集+baseline+指标)、实现(代码+运行配置)、结论判定(用什么结果回答该假设)。"设计"和"结论"最易跑偏，重点核。
   - 主实验：任务、数据集（来自 db04：规模/划分/许可/已知问题）、baselines（来自 db03）、评价指标。
   - 消融实验：逐个移除创新组件，证明贡献来源。
   - 对比实验：与 SOTA 公平比较（同数据/同设置）。
   - 参数敏感性：关键超参网格 + 趋势分析。用 Hydra multirun（`-m lr=0.01,0.1 model=a,b` 笛卡尔积）或 W&B Sweeps（method=grid/random/bayes + metric goal + parameters）系统扫参。
   - 泛化测试：跨数据集/跨域/跨规模。
   - 鲁棒性：噪声/对抗/缺失/分布漂移。
   - 统计显著性：≥3~5 个随机种子；推断用 statsmodels（OLS/Logit，看 summary 的 p 值与 95% 置信区间，记得 `add_constant`）或 scipy（t-test/Wilcoxon）；需不确定性量化时上 PyMC（看 r_hat≈1、ESS 足够）。报均值±标准差 + 误差棒。
   - 防泄漏：所有依赖训练集统计量的预处理（标准化/填补/编码）必须封进 sklearn Pipeline + ColumnTransformer，再交给交叉验证，禁止对全量数据先 fit。
6. **可视化方案**：要出哪些图表（交 m09）。
7. **时间安排**：里程碑 + 甘特，对齐 deadline。
8. **风险点 & 备选方案**：每个风险配 plan B。
9. **预期成果**：论文层次/竞赛/专利/软著。

## 可复现规划（硬性）
逐项落实，给出具体配置而非工具名：
- **环境**：OS/驱动/CUDA 记录；依赖锁版本（requirements.txt 固定版本 / environment.yml / lockfile）。
- **目录脚手架**：按 Cookiecutter Data Science 布局——`data/{raw,interim,processed,external}`(raw 只读不改)、`src/`(可复用逻辑下沉，notebook 不放核心逻辑)、`models/`、`reports/figures/`、`Makefile`、`README`。
- **配置管理**：Hydra 分层配置（conf/ 下 model、dataset 分组 + defaults 列表组合），命令行可覆盖 `lr=0.1`，run 自动存最终合成配置。
- **数据/模型版本**：DVC——`dvc add` 跟踪大文件(git 只存 .dvc 指针)，`dvc.yaml` 定义 stages(cmd/deps/params/outs/metrics)，`dvc repro` 增量复现，`dvc.lock` 锁哈希；`dvc exp run/show` 对比实验。
- **流水线**：Snakemake rule(input/output/params/wildcards) 自动推 DAG + 增量重跑，每个 rule 用 `conda:`/`container:` 锁环境。
- **实验日志**：MLflow（`set_experiment`→`start_run`→`log_param/log_metric(step=)/log_artifact`，或 `autolog()`）或 W&B（`init(config=)`→`log()`，Artifacts 管血缘；敏感数据用 offline 模式避免外发）。
- **固定项**：随机种子、数据划分、超参、训练策略、结果文件命名规范、运行命令。

## 执行纪律（落地与验证，借鉴工程实践）
- **先计划后执行**：方案按 phase 分段，每段写明可验证的成功标准；执行时一次推进一个 phase，做完对照标准勾验再进下一段，偏离写回 decision_log。
- **关键代码 TDD**：数据处理、指标计算、统计检验等关键函数先写测试(给"已知输入→已知输出"金标准用例)、看它失败、再实现，警惕"测试全绿但实现错"。
- **系统化排错**：bug 按 复现→读完整报错→二分定位根因→验证假设→修复后回到复现确认 的顺序；同一思路失败两次即停下找根因换打法，不连续打补丁。
- **完成前验证**：声明"做完"前过 checklist——build 通过、相关测试通过、产出逐条对上成功标准、清理临时文件。

## 产出
1. 完整方案文档（上述全部）。**标准工件：`PROJECT_PLAN.md`**（交 a03/m06，工件契约见 CONVENTIONS §6.1）。
2. 实验矩阵表（实验 × 数据集 × 指标 × 状态）。**标准工件：`experiments/experiment_matrix.md`**（下划线命名，与契约一致）。
3. 复现清单 checklist。
4. 交 a03 落地代码、a06 建目录、a02 登记里程碑与里程碑到 db09。

现成模板见同目录 `templates/`（research-plan.md / experiment_matrix.md / reproducibility-checklist.md）。

## 衔接
方案交 a03 实现 → 实验跑完 → m06 result-analysis；方案变更回写 db09 decision_log。
**派生数据回边**：实验矩阵中鲁棒性/泛化/敏感性所需的派生评测集（加噪/缺失/跨域/扫参），作为派生数据规格回 m02（light-data-engineering）构建，产出数据集 + dataset_card 回填 db04。

---
工具细节（真实端点/参数/命令、已知坑）见同目录 `references.md`。
