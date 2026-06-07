---
name: light-ip-application
description: 辅助软件著作权与专利申请。当用户需要做软著或专利材料时使用。软著：软件名称、功能说明、操作说明书、源代码整理、文档撰写、材料清单、流程、界面截图、功能模块说明、版本与完成日期。专利：判断是否可申发明/实用新型/外观，梳理技术问题、技术方案、有益效果、创新点、实施例、权利要求书与说明书草案、附图说明。最终文本须由专业代理人审核。
---

# 软著与专利申请辅助

## 重要声明（每次开头都提醒）
本技能产出为**草稿与辅助梳理**，不构成法律意见。软著/专利最终文本须由专业代理人或法律人员审核；材料不得虚构或夸大（联动 a10）。

## 软件著作权（登记机关：中国版权保护中心 CPCC，ccopyright.com）
软著只做**形式登记**，不审查代码质量/新颖性，确认权属与完成时间。
1. **软件命名**：全称+简称+版本号，规范可注册、体现功能；登记后不便更改，定稿前确认。
2. **功能说明**：软件用途、主要功能模块、运行环境、技术特点。
3. **操作说明书**：安装、配置、各功能操作步骤，配界面截图、功能模块说明。
4. **源代码整理**：提交**前 30 页 + 后 30 页**(连续、每页约 50 行；不足 60 页则全交)；页眉含软件全称+版本号；去除注释中个人/敏感信息。
5. **文档**：用户手册或设计说明书，前 30 页+后 30 页规则同源码。
6. **材料清单核对**：登记申请表(系统生成)、源程序、文档、身份/营业执照、权属证明(合作/委托/职务开发需对应证明)。
7. **关键信息**：开发完成日期、首次发表日期(未发表可注明)、版本号、开发方式(独立/合作/委托/职务)、权利归属。
8. **流程与周期**：在线登记系统填报→提交→受理→审查(法定约 30 个工作日，可付费加急)→下发《计算机软件著作权登记证书》。
材料须真实对应、不得拼凑虚构。模板与审查重点见 db08。

## 专利
1. **可专利性初判**：是否属发明/实用新型/外观；新颖性、创造性、实用性初步判断；做查新检索（见下）。
2. **技术交底梳理**：要解决的技术问题 → 现有技术缺陷 → 本发明技术方案 → 有益效果 → 创新点。
3. **权利要求书草案**：
   - 独立权利要求记载解决问题的**全部必要技术特征**，构成最大保护范围；推荐"两部分撰写法"：前序部分(主题名称+与现有技术共有特征) + "其特征在于"引出的特征部分(区别技术特征)。
   - 从属权利要求用"根据权利要求 N 所述的…，其特征在于…"逐层附加限定；引用多项用"或"，不得引用编号更大的项。
   - 软件类常用组合布局：方法 + 装置/系统 + 计算机可读存储介质。
   - 须**以说明书为依据**；避免功能性/含糊措辞("约""左右")；术语前后一致；多项独立权利要求须属同一总发明构思(单一性)。
4. **说明书草案**(须**充分公开**，使本领域技术人员可实现)，按审查指南顺序：技术领域 → 背景技术(现状+对比文件+客观缺陷) → 发明内容(技术问题/技术方案/有益效果，效果尽量可量化或给机理) → 附图说明(逐图+标记清单) → 具体实施方式(≥1 个实施例，软件类给流程/模块交互/伪代码级描述使方案可重现)。每个权利要求特征都要在说明书找到支持。
5. **附图**：流程图/结构图/示意图，按专利制图规范(交 m11 绘制)。

### 查新检索（在先技术）实操
- **中国专利权威源 CNIPA**："专利检索及分析"系统 pss-system.cponline.cnipa.gov.cn（需登录、免费）；用高级检索字段(名称/摘要/IPC/申请人/申请日)+法律状态筛选，避免引用已失效/未授权文献。无公开 API。
- **全球免费界面 Google Patents**：patents.google.com，URL 参数式检索(`q=`、`country=`、`before:/after:` 配 `priority/filing/publication`、CPC 码)；大规模程序化检索走 BigQuery 公开数据集 `patents-public-data.patents.publications`(字段 publication_number/abstract_localized/cpc/assignee_harmonized/citation 等)。机器翻译与法律状态非权威。
- **PCT 与跨语言 WIPO PATENTSCOPE**：patentscope.wipo.int；字段码 `EN_TI/EN_AB/EN_CL/IC/PA`，邻近 `NEAR5`、同段 `P`、截词 `*`；CLIR 跨语言扩展适合用中文查外文在先技术。
- **欧洲官方机读 EPO OPS API**：base `https://ops.epo.org/3.2/rest-services`；OAuth2 client_credentials(POST `/auth/accesstoken` 拿 Bearer token，约 20 分钟过期需缓存)；检索 `/published-data/search?q=<CQL>`(CQL 字段 `ti= ab= ta= pa= cpc= pd=`，分页用 `Range: X-Y` 头、每页≤100)；同族 `/family/...`。节流看响应头 `X-Throttling-Control`(系统态 idle/busy/overloaded + search/retrieval/inpadoc/images/other 五类各自 green/yellow/black，1 分钟滚动窗口自适应降速)；另有每周 GB 配额与每小时请求上限，超限 403/429。
- **专利学术一体 The Lens API**：`POST https://api.lens.org/patent/search` 与 `/scholarly/search`，头 `Authorization: Bearer <token>`(学术可免费授权)；ES 风格 DSL(`query/size/from/sort/include`)；全量导出用 `scroll`(返回 `scroll_id` 续传，过期 404)。限流看响应头 `x-rate-limit-remaining-request-per-minute/-per-month`、`x-rate-limit-remaining-record-per-month`，超限 429。适合做专利↔论文关联。
- **美国数据 USPTO**：人机检索 PPUBS(ppubs.uspto.gov，字段语法如 `词.ti.`/`.pn.`，邻近 `ADJ3 NEAR WITH SAME`，截词 `$ ? !`)；程序化用 **PatentSearch API**(原 PatentsView)，三参数 `q/f/o/s`(运算符 `_and _gte _text_phrase`，分页 `o={"size":1000,"after":...}` 游标)、头 `X-Api-Key`。⚠️ 端点迁移已完成：旧 `api.patentsview.org` 301 弃用、过渡域 `search.patentsview.org` 本机无法解析(受网络策略限制，未实测其在线状态)，程序化访问**统一走 USPTO Open Data Portal(data.uspto.gov)**，调用前到 ODP 注册 key 并核对当前 base URL 与端点路径(实测见 references)。仅美国数据。
- **非专利文献(NPL)在先技术 OpenAlex**：`https://api.openalex.org/works?filter=...&search=...`。免费匿名即可用(无 key 无 mailto 实测 HTTP 200)，建议带 `?mailto=you@x.com` 进 polite pool 更稳；`api_key` 可选(不传也能用，传错 key 反而 401)。过滤逗号即 AND，`per_page`**上限 200**(API 错误信息明确"between 1 and 200")，`page` 方式最多到第 10000 条、更深翻用 `cursor=*`，`group_by=` 直接出计数分布。用于补充论文型在先技术与作者机构关联。
- 检索证据(命中文献号/日期/相关段落)随交底书留档；FTO/无效结论须代理师/律师定，本技能不下法律结论。

## 可运行资产（scripts/ 与 templates/，均已 python 跑通/curl 实测）
- `scripts/patent_search.py`：在先技术检索。OpenAlex `/works` 做 NPL 检索（免 key，curl 实测 HTTP 200，`per_page` 上限 200），并为 The Lens / EPO OPS / USPTO ODP 构造请求体（这三者需自带凭证，实测均 401=需鉴权）。
  - `python scripts/patent_search.py "关键词" --from-year 2015 --per-page 10 --mailto you@x.com`
  - `python scripts/patent_search.py --print-adapters`（打印专利库请求模板）
  - `python scripts/patent_search.py --selftest`（离线自测，不联网）
- `scripts/copyright_source_prep.py`：软著源码材料整理。按"50 行/页、≤60 页全交否则前 30+后 30 页、页眉含全称+版本、注释脱敏"规则生成提交文本。
  - `python scripts/copyright_source_prep.py --src <代码目录> --name "全称" --version V1.0 --out submit_source.txt`
  - `python scripts/copyright_source_prep.py --selftest`
- `templates/disclosure_template.md`：技术交底书模板。
- `templates/claims_template.md`：权利要求书草案（方法+装置+介质组合布局）。
- `templates/specification_template.md`：说明书草案（按审查指南顺序）。
- `templates/copyright_checklist.md`：软著材料清单核对表。

## 产出
软著：全套草稿材料（套 `templates/copyright_checklist.md`）+ 源码整理（`copyright_source_prep.py`）+ 截图整理建议。
专利：可专利性分析 + 交底书（`disclosure_template.md`）+ 权利要求草案（`claims_template.md`）+ 说明书草案（`specification_template.md`）+ 检索证据（`patent_search.py`）+ 附图清单 + "需代理人审核"标注。

## 衔接
技术内容取自 m05/a03/a04；附图交 m11；与论文/系统保持一致(a07)；材料入 db09。检索与权属风险上报 a10。

---
检索工具真实端点/参数、撰写规范要点与已知坑详见 references.md。
