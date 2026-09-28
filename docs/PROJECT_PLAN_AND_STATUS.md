# 全球通史知识图谱 — 项目计划与进度

> 最后更新：2026-06-19  
> 仓库：本仓库根目录  
> 方法论参考：[zizhitongjian](https://github.com/JY0284/zizhitongjian)  
> 工程组织：**OpenSpec（需求契约）+ Superpowers（执行流程）**

---

## 一、项目目标

基于 **L. S. 斯塔夫里阿诺斯《全球通史：从史前史到 21 世纪》**（第 7 版，北大译本），构建：

1. **结构化文本库** — 8 编 44 章，机器可读
2. **LLM 知识抽取** — 人物、政权、地点、事件、关系
3. **实体消歧融合** — 跨段落合并别名，生成统一知识库
4. **交互可视化** — 全球年鉴式时间轴 / 关系网 / 地图检索

**时代分界**：1500 年（第 21 章末 → 第 22 章起为「1500 年后」）

---

## 二、总体路线图

```mermaid
flowchart LR
    A[EPUB 导入] --> B[年份索引]
    B --> C[LLM 抽取]
    C --> D[实体融合]
    D --> E[地理编码]
    E --> F[可视化前端]
    F --> G[全书扩面]
```

| 阶段 | 名称 | 状态 | 说明 |
|------|------|------|------|
| **0** | 工程初始化 | ✅ 完成 | 独立仓库、OpenSpec、文档、测试骨架 |
| **1** | 文本导入 | ✅ 完成 | EPUB → `adapted_book.json`，44 章 / 6417 段 |
| **2** | 年份索引 | ✅ 完成 | 44 章起止年；6417 段中 1457 段有显式年份 |
| **3** | LLM 抽取 | 🟡 试点完成 | 仅第 22 章跑通 |
| **4** | 实体融合 | 🟡 试点完成 | 仅第 22 章产出 unified KB |
| **5** | 地理编码 | 🟡 试点完成 | 第 22 章 102 地点，Nominatim + 手工 hints |
| **6** | 可视化前端 | 🟡 试点完成 | fork zizhitongjian，第 22 章可浏览（含地图） |
| **7** | 全书扩面 | ⏳ 未开始 | 44 章批量抽取 + 发布 |

**图例**：✅ 完成 · 🟡 部分完成 · ⏳ 未开始

---

## 三、当前做到什么程度（截至 2026-06-19）

### 3.1 已完成

#### 工程与契约
- [x] 独立仓库 `global-history`（与 zizhitongjian 分离，版权边界清晰）
- [x] OpenSpec change：`global-history-mvp`（proposal / design / specs / tasks）
- [x] `openspec validate global-history-mvp` 通过
- [x] Superpowers 设计文档：`docs/superpowers/specs/2026-06-19-global-history-design.md`
- [x] 实战手册：`docs/OpenSpec-Superpowers-实战指导手册.md`
- [x] 测试：`uv run pytest -q` → **8 passed**

#### 书籍元数据
- [x] `sources/book_structure.json` — 8 编 44 章目录（公开，无正文）
- [x] 1500 年时代分界校验（21 章前 / 22 章后）

#### 文本导入
- [x] 用户 EPUB 已导入：`sources/private/全球通史.epub`（40MB，gitignore）
- [x] `scripts/ingest_book.py` — 支持「第七章　中国文明」中文数字章标题
- [x] `adapted_book.json` — **44 章 / 6417 段**（gitignore，本地）

#### LLM 抽取（试点：第 22 章）
- [x] 全球史版提示词：`prompts/sys_entity_relation_extraction.md`
- [x] `scripts/extract_chapter.py` — DeepSeek 按章抽取，chunk 缓存
- [x] `knowledge_store.py` — `data/store/chapter_22.json`（35 chunks）
- [x] 抽取统计（原始 mention 累计）：

| 类型 | 数量 |
|------|------|
| 实体 mention | 227 |
| 地点 mention | 202 |
| 事件 mention | 79 |
| 关系 mention | 143 |

#### 实体融合（试点：第 22 章）
- [x] `entity_resolution.py` — Union-Find、政权/宗教/文明分类、事件去重、泛称过滤
- [x] `model/unified.py` — 统一知识库 schema
- [x] `data/unified_knowledge.json`（gitignore，本地）

| 类型 | 融合后唯一数 |
|------|-------------|
| 人物 | 58 |
| 政权 | 24 |
| 地点 | 102 |
| 事件 | 68 |
| 关系 | 135 |

**融合样例**：
- `克里斯托弗·哥伦布` + `哥伦布` → 1 人
- `哥伦布发现美洲` / `哥伦布首次航行` → `哥伦布首航发现美洲`
- `国王` 等泛称已过滤，不作为独立节点

#### 年份索引（全书 44 章）
- [x] `gh_pipeline/time_parsing.py` — BCE/CE、世纪、章节标题年份范围
- [x] `scripts/build_segment_year_index.py` — 6417 段落级索引
- [x] `scripts/build_chapter_year_index.py` — 章起止年 + `juan_end_year`
- [x] `scripts/build_year_index.py` — 一键构建并发布到 visualization

---
- [x] `scripts/geocode_locations.py` — Nominatim + `data/location_geocode_hints.json` 手工覆盖
- [x] `scripts/merge_geocoding_into_unified_kb.py` — 坐标回填 unified KB
- [x] `scripts/build_geography.py` — 一键 geocode → merge → publish
- [x] 102/102 地点有 WGS84 坐标；地图 Tab 可展示

---

### 3.2 未完成 / 待做

| 项 | 优先级 | 说明 |
|----|--------|------|
| 年份索引流水线 | — | ~~`build_segment_year_index.py`、`build_chapter_year_index.py`~~ 已完成 |
| 其余 43 章 LLM 抽取 | P1 | 按章批跑，成本与 API 需评估 |
| Wikidata 对齐 | P3 | 降低全球同名消歧错误率 |
| 对话式 RAG | P4 | 远期目标 |
| OpenSpec 人工 LGTM | — | `tasks.md` 4.4 待确认 |

---

## 四、目录与关键文件

```
global-history/
├── docs/
│   ├── PROJECT_PLAN_AND_STATUS.md    ← 本文件（计划 + 进度）
│   ├── OpenSpec-Superpowers-实战指导手册.md
│   └── superpowers/specs/2026-06-19-global-history-design.md
├── openspec/changes/global-history-mvp/
│   ├── proposal.md / design.md / tasks.md
│   └── specs/{book-structure,book-ingest,text-pipeline,global-visualization}/
├── sources/
│   ├── book_structure.json           # 公开：章节目录
│   └── private/全球通史.epub          # 本地：版权正文（gitignore）
├── adapted_book.json                 # 本地：6417 段结构化文本（gitignore）
├── data/
│   ├── store/chapter_22.json         # LLM 抽取缓存（gitignore）
│   ├── store/chapter_22_summary.json
│   ├── location_geocode_hints.json   # 地名查询覆盖 + 已知坐标
│   ├── location_geocoding.json       # 地理编码缓存（gitignore）
│   └── unified_knowledge.json        # 融合知识库（gitignore）
├── visualization/                    # fork 自 zizhitongjian，第 22 章试点
├── model/                            # Pydantic 数据模型
├── prompts/sys_entity_relation_extraction.md
├── scripts/
│   ├── ingest_book.py
│   ├── extract_chapter.py
│   ├── summarize_extraction.py
│   ├── validate_book_structure.py
│   ├── geocode_locations.py
│   ├── merge_geocoding_into_unified_kb.py
│   ├── build_geography.py
│   └── publish_visualization_data.py
├── entity_resolution.py
├── knowledge_store.py
└── tests/                            # 8 tests passing
```

---

## 五、常用命令

```bash
# 在仓库根目录

# 测试
uv run pytest -q

# 校验章节目录
uv run python scripts/validate_book_structure.py

# 导入 EPUB（若重新导入）
uv run python scripts/ingest_book.py --input sources/private/全球通史.epub

# LLM 抽取（需 DEEPSEEK_API_KEY）
uv run python scripts/extract_chapter.py --chapter 22

# 抽取摘要
uv run python scripts/summarize_extraction.py --chapter 22

# 实体融合
uv run python entity_resolution.py --chapter 22

# 年份索引（全书 44 章）
uv run python scripts/build_year_index.py

# 地理编码 + 发布可视化数据
uv run python scripts/build_geography.py

# 本地预览（关系网 / 地图）
cd visualization && npm run dev
# http://127.0.0.1:5173/?tab=map

# OpenSpec 校验
openspec validate global-history-mvp
openspec status --change global-history-mvp
```

---

## 六、OpenSpec + Superpowers 工作流位置

| 阶段 | 工具 | 本项目状态 |
|------|------|-----------|
| P0 brainstorming | Superpowers | ✅ 设计文档已写 |
| P1 propose | OpenSpec `/opsx-propose` | ✅ `global-history-mvp` 四件套 |
| P2 人工 LGTM | 用户确认 | ⏳ 待确认 |
| P3 writing-plans | Superpowers | ⏳ 未正式拆实现计划 |
| P4 apply | `/opsx-apply` + 编码 | 🟡 已编码至第 22 章垂直切片 |
| P5 validate | pytest + openspec validate | ✅ 当前通过 |
| P6 archive | `/opsx-archive` | ⏳ MVP 未归档 |

---

## 七、下一步建议（按优先级）

### 近期（1–2 周）
1. **用户 Review** OpenSpec change → LGTM
2. ~~**年份索引**~~ — 已完成（44 章起止年 + 段落级索引）
3. **批量抽取 23–44 章** — 1500 年后部分优先

### 中期（1 月）
4. ~~**地理编码**~~ — 第 22 章 102 地点已补坐标，地图 Tab 可演示
5. ~~**前端 MVP**~~ — 第 22 章试点可浏览；待年份索引完善时间轴
6. **批量抽取** — 1500 年后部分（第 22–44 章）优先

### 远期
7. 全书 44 章抽取 + 全量融合
8. Wikidata 实体对齐
9. 在线 Demo 部署

---

## 八、风险与约束

| 风险 | 缓解 |
|------|------|
| 译本版权 | 正文仅本地，不进 Git |
| LLM 成本（全书） | 按章缓存、断点续跑、先扩 1500 年后 |
| 全球同名实体 | Wikidata 对齐（V2）；当前 Union-Find + 黑名单 |
| 古代地名坐标不准 | UI 标注「近似位置」；Pleiades 优先 |

---

## 九、垂直切片验收（第 22 章）

当前已打通：

```
EPUB → adapted_book.json → extract_chapter.py → chapter_22.json
  → entity_resolution.py → unified_knowledge.json
```

**尚未打通**：

```
全书批量抽取（23–44 章）
```

**已打通（年份 + 地理 + 可视化）**：

```
adapted_book.json → build_year_index.py → chapter_year_index.json
  → geocode → publish → npm run dev（章↔年份联动可用）
```

---

## 十、变更记录

| 日期 | 内容 |
|------|------|
| 2026-06-19 | 创建仓库、OpenSpec MVP、EPUB 导入 44 章 |
| 2026-06-19 | 第 22 章 LLM 抽取完成（35 chunks） |
| 2026-06-19 | 第 22 章实体融合完成（unified_knowledge.json） |
| 2026-06-19 | 可视化前端 fork + 第 22 章数据发布，本地可浏览 |
| 2026-06-19 | 年份索引流水线完成（44 章起止年，段落级 segment_year_index） |
