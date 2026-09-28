## Context

绿field 项目，目标是用 **OpenSpec + Superpowers** 交付全球通史知识图谱 MVP。

**书籍**
- 《全球通史：从史前史到 21 世纪》第 7 版
- 作者 L. S. Stavrianos；译者王皖强、刘北成；北大出版社
- 结构：8 编 44 章；**1500 年**为上下册/时代分界（第 21 章末 → 第 22 章起）

**方法论来源**: zizhitongjian 流水线（adapted_book → store → entity_resolution → unified_knowledge → visualization）

**硬约束**
- 译本全文 **不得** 进入公开 Git
- 用户将正版 EPUB 放入 `sources/private/` 本地导入

## Goals / Non-Goals

**Goals (MVP)**
- 章节目录 manifest 可校验（44 章、1500 分界）
- EPUB 导入脚本产出 `adapted_book.json`
- 数据契约与 zizhitongjian 对齐并扩展（文明/宗教/Wikidata）
- OpenSpec specs 可测试；tasks 可驱动 `/opsx-apply`

**Non-Goals (本 change)**
- 完整前端可视化（阶段 2 change）
- 全书 LLM 抽取跑完
- PDF 导入（后续 task）

## Decisions

### D1: 独立仓库

| 选项 | 结论 |
|------|------|
| 并入 zizhitongjian | ❌ 拒绝 — 版权、域模型、品牌不同 |
| 独立 global-history | ✅ 采用 |
| monorepo 公共 core | 🔜 V2 再抽包 |

### D2: 文本结构（对标 zizhitongjian 的「卷」）

```
Part (编) → Chapter (章) → Paragraph (段)
```

`adapted_book.json` 段落字段：

```json
{
  "part_index": 1,
  "part_title_cn": "史前人类",
  "era": "pre-1500",
  "chapter_index": 1,
  "title_cn": "人类——食物采集者",
  "paragraph_index": 12,
  "text": "...",
  "segment_start_time_raw": null
}
```

### D3: 时间约定

| 输入 | 数值年 |
|------|--------|
| `753 BCE` / `前753年` | -753 |
| `1500 CE` / `公元1500年` | 1500 |
| `circa 500 BCE` | -500 + confidence 0.7 |
| `early 5th century BCE` | 区间 [-499, -400] |

公元前用 **负数**，与 zizhitongjian 一致。

### D4: 实体类型扩展

| 类型 | 说明 |
|------|------|
| person | 人物 |
| polity | 国家/帝国 |
| civilization | 文明圈 |
| religion | 宗教/思想体系 |
| location | 地点 |
| organization | 组织/军队 |
| event | 事件 |
| relation | 人物/势力关系 |

统一实体建议带 `wikidata_id`（可选），便于全球消歧。

### D5: 地理编码

| 阶段 | 方案 |
|------|------|
| V1 | Wikidata 坐标 → fallback Nominatim |
| 中国史地点 | 可选高德（与 zizhitongjian 相同脚本模式） |

输出 WGS84 `[lng, lat]`；古代地名 UI 标注「近似」。

### D6: 版权与 Git 边界

```
sources/private/     → gitignore（用户 EPUB）
adapted_book.json    → gitignore（含正文）
data/store/          → gitignore
demo/                → 仅脱敏样章（≤1 章摘要，不含大段译文）
```

### D7: 流水线阶段（完整版）

```
ingest_book.py
  → build_segment_year_index.py
  → build_chapter_year_index.py
  → knowledge_extraction.py (LLM)
  → entity_resolution.py
  → geocode_locations.py (optional)
  → validate_artifacts.py
  → publish → visualization/public/data/
```

本 change 实现：**ingest + structure + 契约 + 测试**；其余为 tasks 占位。

## Risks

| 风险 | 缓解 |
|------|------|
| EPUB 章节标题格式不一致 | ingest 支持多种 regex；人工 override |
| 北大译本与英文版章节差异 | 以中文第 7 版目录为准 |
| 版权 | 正文仅本地；公开 repo 只有目录元数据 |
| 全球同名实体 | Wikidata 对齐 + 时间/地点约束 |

## Open Questions

- [ ] 用户是否已有 EPUB 文件路径？（决定 ingest 实测）
- [ ] MVP 试点章节：建议第 7 章「中国文明」或第 22 章「伊比利亚扩张」
- [ ] 前端是否 fork zizhitongjian visualization 整目录？
