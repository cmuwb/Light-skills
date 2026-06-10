# db03 方法卡（seed）

> 每张卡注明 maturity（经典/主流/新兴/过时/不推荐），避免提出落后方案。受版权全文不收录，仅元数据与开源链接。

## 卡片模板
```yaml
- method_name:
  task_type:
  input_data:
  output_result:
  core_assumption:
  advantages:
  limitations:
  common_baselines:
  evaluation_metrics:
  suitable_datasets:
  implementation_repo:
  representative_papers:
  possible_innovation_points:
  maturity:        # 经典|主流|新兴|过时|不推荐
```

## 种子卡片

```yaml
- method_name: Transformer / 自注意力
  task_type: 序列建模(NLP/CV/多模态)
  input_data: token/patch 序列
  output_result: 上下文表示/预测
  core_assumption: 全局注意力捕获长程依赖
  advantages: 并行、长程依赖、可扩展、迁移强
  limitations: 计算/显存随长度平方、数据需求大
  common_baselines: RNN/LSTM、CNN
  evaluation_metrics: 任务相关(Acc/F1/BLEU/mAP)
  suitable_datasets: 大规模语料/图像
  implementation_repo: HuggingFace Transformers
  representative_papers: Attention Is All You Need
  possible_innovation_points: 高效注意力、稀疏化、长上下文、领域适配
  maturity: 主流

- method_name: 随机森林
  task_type: 表格分类/回归
  input_data: 结构化特征
  output_result: 类别/数值 + 特征重要性
  core_assumption: 多树集成降方差
  advantages: 稳健、少调参、可解释(特征重要性)、小数据友好
  limitations: 大规模高维稀疏弱于 GBDT/深度
  common_baselines: 逻辑回归、单决策树
  evaluation_metrics: Acc/F1/AUC/RMSE
  suitable_datasets: UCI/表格类
  implementation_repo: scikit-learn
  representative_papers: Random Forests (Breiman 2001)
  possible_innovation_points: 与深度特征融合、可解释性增强
  maturity: 经典

- method_name: 梯度提升树(XGBoost/LightGBM)
  task_type: 表格分类/回归/排序
  input_data: 结构化特征
  output_result: 类别/数值
  core_assumption: 残差逐步拟合
  advantages: 表格任务常 SOTA、效率高、竞赛常胜
  limitations: 调参较多、对噪声敏感
  common_baselines: 随机森林、线性模型
  evaluation_metrics: AUC/F1/RMSE/NDCG
  suitable_datasets: Kaggle 表格赛
  implementation_repo: xgboost / lightgbm
  representative_papers: XGBoost (Chen 2016)
  possible_innovation_points: 特征工程协同、与深度融合、可解释
  maturity: 主流

- method_name: 扩散模型(Diffusion)
  task_type: 生成(图像/音频/分子等)
  input_data: 噪声 + 条件
  output_result: 生成样本
  core_assumption: 逐步去噪可逆扩散过程
  advantages: 生成质量高、训练稳定、可控生成
  limitations: 采样慢、算力大
  common_baselines: GAN、VAE
  evaluation_metrics: FID/IS/CLIP-score
  suitable_datasets: ImageNet/LAION 等
  implementation_repo: diffusers
  representative_papers: DDPM、Latent Diffusion
  possible_innovation_points: 加速采样、条件控制、领域迁移
  maturity: 新兴/主流

- method_name: 普通 GAN(原始)
  task_type: 图像生成
  input_data: 噪声向量 + 可选条件标签/图像
  output_result: 生成图像样本
  core_assumption: 生成器判别器对抗
  advantages: 采样快
  limitations: 训练不稳定、模式崩塌；多数场景已被扩散超越
  common_baselines: VAE、扩散模型、Flow-based 生成模型
  evaluation_metrics: FID/IS、人工评估、多样性指标
  suitable_datasets: MNIST/CIFAR-10/CelebA 等教学或历史对比数据集
  implementation_repo: PyTorch/TensorFlow GAN 示例、torchvision/DCGAN tutorial
  representative_papers: "Generative Adversarial Nets (Goodfellow et al., 2014)"
  possible_innovation_points: 仅作历史基线或教学对照；新研究优先扩散/自回归/现代生成模型
  maturity: 过时(基线可用,新研究不推荐作为主方法)
```

## 待补充
按用户具体领域补充 method_card，并定期复核 maturity。
