# db03 — 研究方法与技术路线知识库

按领域建立 method_card，帮 m03(提 idea)、m04(审 idea)、m05(方案)、m01(调研) 快速判断该用什么方法、什么过时、什么可做创新基础、什么适合做对比。

## method_card schema
`method_name, task_type, input_data, output_result, core_assumption, advantages, limitations, common_baselines, evaluation_metrics, suitable_datasets, implementation_repo, representative_papers, possible_innovation_points, maturity`

- `maturity`: 经典 | 主流 | 新兴 | 过时 | 不推荐

## 数据来源
Papers With Code、Hugging Face Models/Papers、GitHub Trending、Awesome 系列、OpenReview、arXiv、Semantic Scholar、领域综述、各会议 tutorial、官方 benchmark leaderboard。

## 更新方式
每个方法标注成熟度(经典/主流/新兴/过时/不推荐)，避免 Light 提出已落后的方案。新兴方法定期升降级。

## 使用方式
- m03 提 idea 前：查目标任务的主流/新兴方法 + possible_innovation_points。
- m04 审 idea：用 maturity 判断是否"做烂了"或"已过时"。
- m05 方案：从 common_baselines / evaluation_metrics / suitable_datasets 直接取对比设置。

## 维护说明
方法卡按领域归档。每张卡注明代表论文与开源实现链接（受版权全文不收录，仅元数据/链接）。代表作的被引/DOI 均由 OpenAlex API 实拉，可核查。

## 卡片文件
- [cards_ml_stats.md](cards_ml_stats.md) — 机器学习/统计学习（随机森林/GBDT/SVM/聚类/降维等，12+ 卡，真实代表作）
- [cards_dl.md](cards_dl.md) — 深度学习/CV/NLP（ResNet/Transformer/Diffusion/GNN/RL/LoRA 等，14+ 卡）
- [cards_mining_other.md](cards_mining_other.md) — 数据挖掘/图/时序/推荐/优化（19+ 卡）
- [cards_frontier.md](cards_frontier.md) — 前沿/新兴方法（自监督/MAE/RAG/LLM Agent/Mamba/多模态大模型/NeRF/3DGS 等，22+ 卡，代表作 OpenAlex 实拉）
- [cards_detection_tracking.md](cards_detection_tracking.md) — 目标检测 + 多目标跟踪（Faster R-CNN/YOLO 系/DETR 系/SORT/ByteTrack/OC-SORT 等 25 卡，含奶山羊/家畜场景适配，代表作 OpenAlex 实拉）
- [cards_action_spatiotemporal.md](cards_action_spatiotemporal.md) — 行为识别 + 时空特征融合（Two-Stream/I3D/SlowFast/TimeSformer/VideoMAE/ST-GCN/PoseC3D 等 25 卡，含奶山羊行为细粒度/长时序适配）
- [cards_temporal_action.md](cards_temporal_action.md) — 时序动作检测(TAL) + 序数回归（ActionFormer/BMN/TriDet/CORAL/CORN/QWK 等 14 卡，专供发情爬跨瞬时事件定位与跛行有序评分，代表作 OpenAlex 实拉）
- [cards_nighttime_multimodal.md](cards_nighttime_multimodal.md) — 夜间红外/热成像检测 + RGB-IR 多模态融合 + 级联误差/端到端联合（Zero-DCE/CFT/ProbEn 等 18 卡，含昼夜预警与四级流水线误差传播适配）
- [method_cards.md](method_cards.md) — 早期种子卡 + 卡片模板（schema 参考）
- [cards_biomedical.md](cards_biomedical.md) — 生物医学方法（Cox/KM、U-Net/nnU-Net、GWAS、临床预测、AlphaFold、CheXNet 等 6 卡，OpenAlex 核验）
- [cards_physical_sciences.md](cards_physical_sciences.md) — 理工跨学科/物理化学材料（MPNN/SchNet/CGCNN、DFT、MLIP、EEGNet、Pangu/GraphCast、CALYPSO/USPEX 等 6 卡）
- [cards_stats_econ_finance.md](cards_stats_econ_finance.md) — 统计/经济金融/因果推断（DiD、IV/LATE、RDD、PSM/IPW、GARCH/VAR、分位数回归/因果森林等 6 卡）
- [cards_nlp_speech.md](cards_nlp_speech.md) — NLP/语音（Seq2Seq/Transformer、T5/GPT-3、RAG、CTC/Conformer、wav2vec2/HuBERT、Whisper 等 6 卡）
