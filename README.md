# 十五五规划解读与决策

**把国家规划转化为可查证、能讨论、可行动的决策参考。**

基于《中华人民共和国国民经济和社会发展第十五个五年规划纲要（2026—2030年）》的中文 AI skill，包含原文数据库、逐章解读、行业分析路径和决策流程。适用于了解国家发展方向，以及商业、求职、行业研究、技能学习、地区选择和海外发展等问题。

它会先找规划依据，再解释可能的影响，结合现实证据和个人条件提出下一步。**政策支持不等于企业盈利、岗位增加或个人高薪。**

本项目为非官方整理与辅助分析，内置解读不是官方释义。

## 可以用它做什么

|需求|如何帮助|
|---|---|
|读懂规划|找到原文所在章、节、专栏和页码，解释目标与政策措施|
|判断行业方向|分析政策如何影响需求、产业链任务、进入门槛和竞争|
|比较职业选择|区分行业前景、具体雇主、岗位要求与个人匹配|
|评估商业想法|识别付款方、真实需求、准入、现金流和需要补查的证据|
|规划技能学习|从具体任务选择技能与作品，设计低成本验证|
|研究地区或海外机会|串联国家方向、地方落实、企业需求和个人适用条件|
|核对政策说法|检查数字、时间、统计口径和引用，避免把目标当事实|

## 内容与覆盖

当前版本：**2.0**。内容核对日期：**2026-10-23**。原文版本：**2026年3月**。

|内容|覆盖|
|---|---:|
|原始PDF|140页，正文印刷页1—135|
|原文章节结构|18篇、62章、171节|
|可追溯原文片段|360个|
|逐章解读|62章|
|已视觉复核专栏|23个|
|主要指标|20项，第10项含2个子指标|
|专栏项目内容|122条|
|地图说明|3张地图的图名、图例和使用限制|
|世界遗产名录|本版规划所附60个主编号的视觉配对|
|行业决策路径|16类|

行业路径包括：人工智能与数据服务、制造升级、能源、低空经济、跨境贸易、专业服务、农业、养老、健康、文化文旅、城市更新、绿色转型、教育技能、未来产业、物流供应链、海洋产业。

逐章解读和行业路径均标注为分析，包含成立条件、反向证据、观察指标或低成本验证，不是行业推荐排名。

## 快速开始

### 作为 AI skill 使用

先将仓库下载到本地（私有仓库需要先登录拥有访问权限的 GitHub 账号）：

```bash
git clone https://github.com/MurrayTsai/interpret-15th-plan.git
cd interpret-15th-plan
python3 scripts/validate_database.py
python3 scripts/validate_knowledge.py
```

将完整仓库放入支持 `SKILL.md` 的 AI 助手可访问的位置，让助手先读取根目录的 [SKILL.md](SKILL.md)，再按任务调用脚本或读取对应参考资料。目录必须整体保留；只复制 `SKILL.md` 不会包含数据库和原文。

支持技能目录的客户端可将整个目录命名为 `interpret-15th-plan` 并放入其技能目录。具体安装位置和启用方式按所用客户端说明操作。仅把仓库上传到 GitHub，不会自动给其他客户端安装 skill。

示例请求：

> 使用 interpret-15th-plan，解释十五五对普通求职者意味着什么。区分规划方向、现实证据和分析判断，给出原文页码。

> 我有销售经验，正在比较制造业销售和低空经济培训创业。结合十五五分析进入门槛、主要风险及一个低成本验证方案。

> 帮我核对“2030年GDP增速目标是5%、入托率目标6%、每年碳排放减少17%”这三个说法。

> 分析一个城市的养老服务机会：先找国家规划依据，再查当地支付能力、实施政策与实际需求。没有核实的地方请明确说明。

没有脚本运行能力时，仍可按 [章节导航](references/structure.md)、[整体阅读图](references/reading-map.md) 和 [行业路径](references/industry-pathways.md) 阅读。原文数据库及相关资源须能被客户端实际访问；不要把无法读取说成已检索。

### 作为本地资料库使用

查询使用 Python 标准库，无需 API key、付费嵌入或外部向量服务。在仓库根目录执行：

```bash
# 查看数据版本与覆盖
python3 scripts/query.py --stats

# 原文关键词：默认任一匹配；--all 要求全部匹配
python3 scripts/query.py --query '人工智能 就业' --all

# 跨片段整章匹配，然后读取原文
python3 scripts/query.py --query '人工智能 就业' --all --search-scope chapter
python3 scripts/query.py --chapter 41

# 读取分析卡，不将其当作原文
python3 scripts/query.py --interpret 41
python3 scripts/query.py --sectors
python3 scripts/query.py --sector trade

# 专栏、指标、图表
python3 scripts/query.py --box 5
python3 scripts/query.py --indicators
python3 scripts/query.py --figures
python3 scripts/query.py --heritage

# 按页或片段回溯
python3 scripts/query.py --printed-page 96
python3 scripts/query.py --page 101
python3 scripts/query.py --context p0101-c03
```

加 `--json` 可获得结构化输出；关键词或主题检索可用 `--limit 1..100` 控制结果数。更多说明见 [数据库文档](references/database.md)。

检索采用中文关键词与人工主题扩展，不是语义搜索。完整问题宜先拆成2—5个关键词；无命中时换同义词或补读章节，不能据此断言原文没有涉及。章节共现也不证明因果联系。

## 怎样形成一个回答

1. 明确要做的决定、已有条件、期限与可接受损失。
2. 检索直接相关原文，同时寻找支持条件与限制条款。
3. 说明政策工具如何可能传导到需求、企业或岗位。
4. 涉及今天的招聘、工资、补贴、准入、项目进度时，另查最新证据。
5. 根据现实条件给出有条件的判断、低成本行动和改判标准。

回答区分四类内容：**规划原文、现实证据、分析判断、用户条件或待核实项**。

引用示例：

> 《十五五规划纲要》第四十一章第一节，印刷第96页（PDF第101页）。

印刷页码与PDF页码同时保留，便于复核。正文PDF页码＝印刷页码＋5。

## 现实证据与更新

项目不自带实时薪酬、全国地方政策、企业经营或补贴数据库，也不会在后台自动监测。涉及当前执行情况时，由使用该 skill 的助手借助可用联网能力核查；本地查询脚本本身不会联网抓取这些信息。

按 [现实证据流程](references/evidence-updates.md) 记录发布机关、来源、发布时间、数据所属期、地区、生效状态、核查日期与限制。任务资料应单独保存，不把个人合同、履历或财务信息加入通用资料库。

```bash
# 输出待填写的空白模板
python3 scripts/evidence.py --template

# 检查填好后的任务证据；日期应改为本次核查日期
python3 scripts/evidence.py --validate /absolute/path/evidence.json --as-of 2026-10-23
```

该工具只检查记录结构与日期，**不会验证来源内容是否真实，也不会认定法律适用性**。未联网或证据不足时，应明确保留“现实执行尚未核查”。

## 目录

|路径|内容|
|---|---|
|[SKILL.md](SKILL.md)|技能入口、解读流程、证据规则和资源导航|
|[agents/openai.yaml](agents/openai.yaml)|支持该格式的客户端所用技能展示元数据|
|[assets/source/](assets/source/)|未修改的原始PDF|
|[assets/data/](assets/data/)|SQLite、原文JSONL、章节/专栏/指标/图表与分析卡|
|[assets/quality/](assets/quality/)|核验记录、已修复问题与实际问答样例|
|[references/](references/)|章节解读、行业路径、决策框架、图表与维护说明|
|[scripts/](scripts/)|检索、编译、重建和验证脚本|

## 数据来源与可追溯性

- 原文：《中华人民共和国国民经济和社会发展第十五个五年规划纲要》，2026年3月版。
- [国家发展改革委同名PDF](https://www.ndrc.gov.cn/fggz/fzzlgh/gjfzgh/202603/U020260317369114704096.pdf)。
- 本项目以所提供的PDF为内容依据；官方来源核对包含标题、文件名与字节大小，未对远程文件进行哈希比对。
- 本地原文SHA256：`29b3c70720b1faff458a123cb29672ee2ee8874a53b6d4a91f402a73f6945027`。
- [manifest.json](assets/data/manifest.json) 记录来源、页数、结构、版本与质量边界。

原文与分析分开保存。项目中的行业映射、解读、主题扩展词和建议不能作为官方表述引用。

## 验证与重建

直接查询不需要额外安装第三方包。完整PDF重建使用 PyMuPDF；[requirements-rebuild.txt](requirements-rebuild.txt) 固定已验证的解析器版本。

```bash
# 验证现有数据，不重新解析PDF
python3 scripts/validate_database.py
python3 scripts/validate_knowledge.py

# 修改解读卡后重新编译
python3 scripts/compile_knowledge.py

# 完整重建：先在自己的Python环境安装解析依赖
python3 -m pip install -r requirements-rebuild.txt
python3 scripts/build_database.py
python3 scripts/validate_database.py
python3 scripts/validate_knowledge.py
```

`build_database.py` 针对此PDF的版式编写，并自动编译知识层；它不是适用于任意政策PDF的通用解析器。替换原文版本时，应重新适配、核验并记录版本，不能直接覆盖旧资料。

现有检查覆盖原文哈希、全文连续行、结构、指标口径、引用位置、专栏边界、名录配对、数据库一致性、检索和证据日期。另完成逐章核读、专栏视觉复核及两组独立实际问答验证；这些检查不保证所有未来回答都正确。

## 使用边界

- 规划目标不是今天的执行结果，也不是对个人收益的保证。
- 地图为示意，不支持精确选址、行政边界、路线长度或工程数量推断。
- PDF第87页为横版多栏名录，原始文本阅读顺序不安全；主编号使用已配对的结构化数据，系列子条目查看原PDF。
- 60个遗产主条目是本版规划快照，不能直接作为当前世界遗产总数。
- 涉及具体经营、职业或投资决定，应补查适用规则、现实需求和个人条件。

## 改进与贡献

欢迎提交可复现的检索问题、引文错误或结构化数据修正。请附原文章节与双重页码、复现命令、当前结果和建议修改；涉及新现实证据时附来源、日期、地区和适用范围。

修改后运行两项验证脚本。不要用未经核实的推测替换原文，不提交个人敏感材料、访问令牌或账号凭据。
