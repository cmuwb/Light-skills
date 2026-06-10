# db04 数据集卡（seed）

> 每条必须记录 license 与隐私/再分发/商用限制（联动 a10）。受版权数据仅存元数据与链接。

## 卡片模板
```yaml
- dataset_name:
  domain:
  task:
  data_type:
  size:
  format:
  license:            # 含 商用?/再分发?/需授权?
  download_url:
  paper_url:
  citation:
  leaderboard_url:
  known_issues:
  bias_risk:
  privacy_risk:
  preprocessing_steps:
  recommended_splits:
```

## 种子卡片

```yaml
- dataset_name: ImageNet (ILSVRC)
  domain: 计算机视觉
  task: 图像分类
  data_type: 图像
  size: ~1.28M 训练图, 1000 类
  format: JPEG + 标注
  license: 仅限非商业研究, 需注册同意条款; 再分发受限
  download_url: https://image-net.org
  paper_url: https://doi.org/10.1109/CVPR.2009.5206848
  citation: "Deng et al. (2009). ImageNet: A Large-Scale Hierarchical Image Database. CVPR."
  leaderboard_url: https://paperswithcode.com/sota/image-classification-on-imagenet
  known_issues: 标签噪声、部分类别不均衡
  bias_risk: 地域/文化偏差、部分类别敏感
  privacy_risk: 含人物图像, 隐私争议
  preprocessing_steps: resize/center-crop/归一化
  recommended_splits: train/val(官方)

- dataset_name: MNIST
  domain: 计算机视觉
  task: 手写数字分类
  data_type: 灰度图像 28x28
  size: 70k(60k/10k)
  format: IDX/常见库内置
  license: 公开(CC/自由使用)
  download_url: http://yann.lecun.com/exdb/mnist/
  paper_url: https://doi.org/10.1109/5.726791
  citation: LeCun et al. (1998). Gradient-based learning applied to document recognition. Proceedings of the IEEE.
  leaderboard_url: 无官方榜; 教学基准已高度饱和
  known_issues: 过于简单, 已饱和, 仅适合教学/快速验证
  bias_risk: 低
  privacy_risk: 无
  preprocessing_steps: 归一化到 [0,1] 或标准化; 通常无需复杂增强
  recommended_splits: 官方 60k/10k

- dataset_name: GLUE
  domain: NLP
  task: 自然语言理解(多任务基准)
  data_type: 文本
  size: 多子任务
  format: TSV/JSON
  license: 各子任务许可不一, 多为研究用途
  download_url: https://gluebenchmark.com
  paper_url: https://doi.org/10.18653/v1/W18-5446
  citation: "Wang et al. (2018). GLUE: A Multi-Task Benchmark and Analysis Platform for Natural Language Understanding. EMNLP BlackboxNLP."
  leaderboard_url: https://gluebenchmark.com/leaderboard
  known_issues: 已被 SuperGLUE 接棒, 部分任务饱和
  bias_risk: 子任务来源与标注 artifact 带来偏差; WNLI 等任务有已知陷阱
  privacy_risk: 低-中; 含公开文本/问答/影评等来源, 逐子任务复核
  preprocessing_steps: 按子任务格式化句/句对; 分词截断; test 需在线提交
  recommended_splits: 各任务官方 train/dev/test

- dataset_name: UCI Adult (Census Income)
  domain: 表格/社会数据
  task: 收入二分类
  data_type: 结构化
  size: ~48k
  format: CSV
  license: 公开
  download_url: https://archive.ics.uci.edu/dataset/2/adult
  paper_url: https://doi.org/10.24432/C5XW20
  citation: Becker & Kohavi (1996). Adult. UCI Machine Learning Repository.
  leaderboard_url: 无统一官方榜; 常见于公平性/表格学习论文对比
  known_issues: 含敏感属性
  bias_risk: 性别/种族偏差(公平性研究常用反例)
  privacy_risk: 普查衍生, 已脱敏
  preprocessing_steps: 处理缺失值; 类别编码/one-hot; 数值标准化; 敏感属性单独登记
  recommended_splits: 官方 train/test
```

## 待补充
按用户领域补充数据集卡，重点核实 license 与隐私限制。
