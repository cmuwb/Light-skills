# db04 — 数据集、Benchmark 与开源项目资源库

为各领域数据集/benchmark/开源项目建立 dataset_card，供 m02(数据)、m05(方案)、m03(idea) 使用。

## dataset_card schema
`dataset_name, domain, task, data_type, size, format, license, download_url, paper_url, citation, leaderboard_url, known_issues, bias_risk, privacy_risk, preprocessing_steps, recommended_splits`

## 数据来源
Hugging Face Datasets、Kaggle、OpenML、UCI ML Repository、Papers With Code Datasets、Google Dataset Search、Zenodo、Figshare、DataHub、Open Graph Benchmark、各领域官方数据集站、GitHub 论文复现仓库。

## ⚠ 许可协议（必记，联动 a10）
每条必须记录 `license`，并明确：
- 是否允许商用？
- 是否允许再分发？
- 是否涉及个人隐私(privacy_risk)？
- 是否需要申请授权？
不确定许可的数据集标红，使用前核实。

## 使用方式
- m02：从 known_issues / bias_risk / preprocessing_steps 预判数据坑。
- m05：从 recommended_splits / leaderboard_url 取标准设置与 SOTA。
- m03：从 data_type 判断创新机会。

## 维护说明
卡片归档。记录引用方式(citation)便于 m10 引用。每张卡的 license 必填、论文引用由 OpenAlex 实拉。

## 卡片文件
- [cards_cv_nlp.md](cards_cv_nlp.md) — CV/NLP 数据集（ImageNet/COCO/GLUE/SQuAD 等，含真实 paper_url/被引/license）
- [cards_tabular_other.md](cards_tabular_other.md) — 表格/图/时序/多模态/领域（UCI/OGB/MIMIC-III/遥感等，授权风险已标注）
- [cards_frontier.md](cards_frontier.md) — 前沿数据集（LAION-5B/The Pile/C4/nuScenes/QM9/CheXpert/PlantVillage 等，按大模型/多模态/3D/科学/语音/医疗/农业 七类，授权高风险已标注）
- [cards_animal_livestock.md](cards_animal_livestock.md) — 动物/家畜行为·姿态·检测（AP-10K/Animal Kingdom/Cows2021/CherryChèvre 等 15 卡；含奶山羊专用数据集现状评估与自建建议，缺口如实标注）
- [dataset_cards.md](dataset_cards.md) — 早期种子卡 + 卡片模板（schema 参考）
- [cards_physical_sciences.md](cards_physical_sciences.md) — 理工跨学科/科学计算数据集（Materials Project、QM9、OQMD、OC20、JARVIS、WeatherBench/ERA5、HCP 等 7 卡）
- [cards_biomedical.md](cards_biomedical.md) — 生物医学/临床/组学数据集（MIMIC-IV、eICU、UK Biobank、TCGA、MIMIC-CXR/CheXpert、ADNI、HAM10000/ISIC 等 7 卡）
- [cards_stats_econ_finance.md](cards_stats_econ_finance.md) — 统计/经济金融/社会科学数据集（FRED-MD/QD、PWT、WDI、Fama-French、CRSP/Compustat/WRDS、OECD 等 6 卡）
- [cards_nlp_speech.md](cards_nlp_speech.md) — NLP/语音/多语言评测数据集（MMLU、XTREME、LibriSpeech、Common Voice、VoxCeleb、FLEURS、VoxPopuli/AISHELL 等 7 卡）
