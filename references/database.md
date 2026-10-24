# 原文数据库与检索

目录：来源与结构；查询；数据口径；质量边界；重建；动态资料。

## 来源与结构

固定版本：2026年3月《中华人民共和国国民经济和社会发展第十五个五年规划纲要》，2026—2030年。

本库以用户上传PDF为内容依据。官方检索确认同名文件位于国家发展改革委域名，标题、文件名及网络读取返回的字节大小一致；尚未远程下载并比较哈希，不声称字节级同一性。网址与本地SHA256见 `assets/data/manifest.json`。原始文件为 `assets/source/plan-2026-2030.pdf`，未修改。

|资源|用途|
|---|---|
|plan.sqlite|结构化检索，Python标准库sqlite3只读访问|
|pages.jsonl|140页原始提取文本、去页码正文、每行文字/字体/坐标、图像数|
|chunks.jsonl|360个正文连续行片段，保留原文和篇章节/专栏定位|
|structure.json|274个标题节点：18篇+62章+171节+23专栏|
|indicators.json|20项主要指标及第10项两个子指标、原始列值、年份及脚注|
|topics.json|18个模型编写的检索主题词组，不属于原文分类|
|chapter_analysis.json|62章分析，关联原文章节/页码/片段，非官方解读|
|boxes.json|23专栏：20项指标和122条项目内容，含跨页范围与原文词语提示|
|figures.json / heritage.json|3张地图图例和限制、60个遗产主编号视觉配对|
|sector_analysis.json|16类行业任务、进入条件、待查证据与低成本验证，均为分析|
|manifest.json|来源哈希、版本、质量范围、结构与页数统计|

SQLite表：`metadata(key,value)`、`pages(pdf_page,printed_page,kind,text,raw_text,embedded_images)`、`nodes(id,kind,number,label,title,parent,pdf_page,printed_page,line_start)`、`chunks(id,document_id,pdf_page,printed_page,line_start,line_end,path,part,chapter,section,box,text,search_text,needs_visual_check)`、`indicators(id,name,data_json)`；可用时另建 `chunk_fts` FTS5 trigram索引。另有 `chapter_analysis`、`boxes`、`figures`、`heritage`、`sector_analysis` 五张表，均使用 `(id,data_json)`。动态现实证据不在这些表里。

ID在当前PDF/解析器版本中稳定；修改源PDF或分块算法后不可保证旧片段ID沿用，应同时保留文档ID、SHA256、页码和原句。不要只引用一个技术ID。

## 查询

从skill根目录运行：

```bash
python3 scripts/query.py --query '对外投资 海外' --limit 5
python3 scripts/query.py --query '人工智能 就业' --all --json
python3 scripts/query.py --topic '新能源'
python3 scripts/query.py --chapter 22
python3 scripts/query.py --page 62
python3 scripts/query.py --printed-page 57
python3 scripts/query.py --chunk p0101-c03
python3 scripts/query.py --indicators --json
python3 scripts/query.py --stats
```

`--all`在同一片段或其标题路径中要求全部关键词。跨页/跨片段关键词可能被漏掉，可加 `--search-scope chapter`，或改成单词搜索、同义词和整章阅读。章节共现不代表因果关系。默认任一匹配；按正文匹配数、有限词频和标题匹配加权排序。检索得分只用于找文本，不反映行业前景、政策强度或置信度。

中文不依赖空格分词；对正文移除排版空白、拉丁字母小写后做子串匹配。命中的`text`仍保留提取换行。主题词仅扩展查询，不改原文。读取某片段后，跨页句子或表格须补读前后页，不能将半句当完整条款。

若运行环境不支持SQLite，可读取JSONL或用`rg -n '人工智能|就业' references/fulltext.md`后读取附近内容。没有Python/文件工具时说明环境限制，不假装执行命令。

## 数据口径

正文印刷页1对应PDF第6页；PDF第1页为封面，第2—5页为目录。第87页是印刷82页的横版世界遗产表，页码为图像，已视觉确认；不要用“页首第一项”猜页码。

主要指标结构化表保留字符串以保护“＞”“＜”“左右”“〔〕”“*”“—”。空缺不是0；2024脚注不能误称2025；五年累计不是年增长；百分点不是百分比。第10项医护人员分执业医师和注册护士，不能相加成原文未给出的指标。原表的年均/累计为一个合并栏，不擅自把城镇调查失业率等变成2030时点目标。

## 质量边界与视觉核验

已检查全部正文文本行都被连续分块覆盖、章节编号1—62完整、结构计数一致、数据库完整性与PDF哈希。所有页保留原始提取文本；这不等于全部图表信息已识别。

主要指标表（PDF第15页）已逐项视觉核对。PDF第27、86、87、119页含嵌入图像，文字数据库不能完整表达地图与空间关系。全部专栏片段标记`needs_visual_check`；全部23专栏已逐项视觉复核；专业项目和数字可用 `--box` 读取结构化原文。图1、图3已解除错误专栏归属。PDF87页多栏原始文本只保留作追溯，关键词检索改用60个主编号配对；原始页/片段读取显示阅读顺序警告。系列遗产子条目仍需看原图。不要在未查看图像时给地图地理细节或根据多栏抽取的顺序做关联。

需要核查某页时，用PDF技能渲染原始页，或PyMuPDF：

```python
import fitz
pdf=fitz.open('assets/source/plan-2026-2030.pdf')
pdf[14].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save('/tmp/plan-page-15.png')
```

查看生成图像后再转述数字或空间关系。该例的14是零起始索引，用户看到的是PDF第15页。

## 重建与校验

查询只需要Python标准库。重建需要PyMuPDF；原环境已可用，不需联网嵌入服务。

```bash
python3 scripts/build_database.py
python3 scripts/validate_database.py
python3 scripts/validate_knowledge.py
```

`build_database.py` 会自动调用 `compile_knowledge.py` 编译分析、专栏、图表与SQLite扩展表。仅修改分析卡时可单独运行编译脚本。任一步失败不得发布。

先保持原PDF不变。构建脚本针对本文件字体识别标题；结构与页数不符合时停止，不适用于任意PDF。重建数据库读取现有indicators.json，不自动猜测或改写人工核对的指标值。更新PDF或标题样式时新建来源版本，先适配解析并核查，再更换。

## 后续动态资料

按 `references/evidence-updates.md` 与 `scripts/evidence.py` 的任务记录结构执行。单独记录主张、证据类别、来源、日期、地域、关联章节、核查状态与局限。保存原始快照时遵守访问与引用要求。不要把新闻发布日期当统计期，不把全国纲要与地方细则混为一份。若链接失效仍要保留旧证据出处，不能将“无法打开”理解为政策废止。
