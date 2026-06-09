# 产物台账（Passport）

一份贯穿整个 pipeline 的记录，回答三个问题：**做到哪了、每步产出了什么、过了哪些关**。中断后据此续跑。写入 a02 memory-pm 的项目记忆。

## 为什么需要

跨阶段任务常被打断（换天、等实验、等审稿）。没有台账，重启时只能靠翻聊天记录猜进度，容易重做或跳步。台账让"做到哪了"有单一真相源。

## 字段

每个已完成阶段记一条：

```yaml
project: <项目名/slug>
pipeline: A   # 走的哪条链
created: 2026-06-08T09:00   # 首次启动时间，固定不变
updated: 2026-06-08T14:30   # 台账最后更新时间，续跑时判断新旧（记到分钟）
current_stage: 8  # 当前到第几阶段
stages:
  - stage: 1
    skill: m01
    input: "用户提供的信用卡欺诈数据集 + 研究目标"
    output: "文献清单 12 篇，方向=校准+不平衡，gap=缺少树模型系统对照"
    artifacts: [docs/lit-review.md]
    gate: {type: confirm, result: PASS, notes: "来源均可核"}
  - stage: 4
    round: 2   # m03⇄m04 回环的第几轮，首轮可省略
    skill: m04
    input: "m03 第 2 轮提出的 idea"
    output: "idea 八维 72 分，新颖性存疑"
    gate: {type: decision, choice: "微调放行（缩小到树模型）", by: user}
  - stage: 8
    skill: m07
    input: "m05 方案 + a03 实验结果 + m06 分析"
    output: "初稿 6 节"
    gate: {type: confirm, result: FAIL→PASS, notes: "首轮 2 处幻觉引用(M2)，已删/替换后过"}
    gaps: ["讨论节 1 处 [RESULT GAP] 待补敏感性分析"]
known_limitations:
  - "E5 先验校正为负结果，如实写入，未强行修正"
```

字段说明：
- `input`：本阶段从上游接收了什么——续跑和回溯时靠它还原阶段间交接。
- `round`：m03⇄m04 这类回环阶段记第几轮；线性阶段省略。
- `created`：首次启动 pipeline 的时间，建后不改。
- `updated`：每次写台账都刷新（记到分钟），续跑时一眼看出进度多旧、项目跨了多久。

## 存哪 / 叫什么（续跑的前提）

台账存为项目记忆里的固定文件：**`.light/passport.yaml`**（项目根目录下）。这是 orchestrator 和 a02 memory-pm 约定的单一位置。

- 启动 pipeline 时：先查 `.light/passport.yaml` 是否存在——存在则是续跑（读 current_stage 接着走），不存在则新建。
- 每过一阶段：更新该文件并刷新 `updated`。
- a02 memory-pm 负责把它纳入项目长期记忆、跨会话恢复；orchestrator 只负责按上述路径读写内容。

## 维护规则

- 每过一个阶段就追加一条，**当场写**，别攒到最后补。
- 决策点记录用户**选了什么**（choice + by:user），不只记"已确认"。
- 确认点记录闸门结果；FAIL→PASS 要记原因（什么不达标、怎么修的）。
- GAP 和 known_limitations 必须如实留痕——这是诚实底线，不是可选项。
- 续跑时：读台账 → 定位 current_stage → 从下一阶段继续，已过阶段不重跑（除非用户要求）。

## 与 memory-pm 的关系

台账是 pipeline 维度的进度记录，memory-pm 是项目维度的长期记忆。台账写入 memory-pm 作为项目卡的一部分；memory-pm 负责持久化和跨会话恢复。编排器只管在 pipeline 运行时维护台账内容。
