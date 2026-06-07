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
  known_issues: 过于简单, 已饱和, 仅适合教学/快速验证
  bias_risk: 低
  privacy_risk: 无
  recommended_splits: 官方 60k/10k

- dataset_name: GLUE
  domain: NLP
  task: 自然语言理解(多任务基准)
  data_type: 文本
  size: 多子任务
  format: TSV/JSON
  license: 各子任务许可不一, 多为研究用途
  download_url: https://gluebenchmark.com
  leaderboard_url: https://gluebenchmark.com/leaderboard
  known_issues: 已被 SuperGLUE 接棒, 部分任务饱和
  recommended_splits: 各任务官方 train/dev/test

- dataset_name: UCI Adult (Census Income)
  domain: 表格/社会数据
  task: 收入二分类
  data_type: 结构化
  size: ~48k
  format: CSV
  license: 公开
  download_url: https://archive.ics.uci.edu/dataset/2/adult
  known_issues: 含敏感属性
  bias_risk: 性别/种族偏差(公平性研究常用反例)
  privacy_risk: 普查衍生, 已脱敏
  recommended_splits: 官方 train/test
```

## 待补充
按用户领域补充数据集卡，重点核实 license 与隐私限制。
