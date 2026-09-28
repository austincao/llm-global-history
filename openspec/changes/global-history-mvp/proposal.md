## Why

《全球通史》（斯塔夫里阿诺斯，第 7 版北大译本）时间线完整、以 1500 年为界，适合做成 **全球年鉴式检索** 的历史知识图谱。现有 [zizhitongjian](https://github.com/JY0284/zizhitongjian) 已验证「结构化文本 → LLM 抽取 → 实体融合 → 交互可视化」方法论，但全球通史需要独立工程（版权、全球地理、多文明实体、BCE/CE 纪年）。

本 change 交付 **MVP 垂直切片**：章节目录 + 本地 EPUB 导入 + 数据契约 + 流水线骨架，为后续 LLM 抽取与前端可视化奠基。

## What Changes

- 新建独立仓库 `global-history`，OpenSpec + Superpowers 工作流
- 公开 **8 编 44 章** 目录元数据（`sources/book_structure.json`）
- 用户自备正版 EPUB → `scripts/ingest_book.py` → `adapted_book.json`（gitignore）
- 定义 MVP 数据模型与流水线阶段（design.md）
- 版权边界：正文不进 Git；`sources/private/` 永久 gitignore

## Capabilities

### New Capabilities

- `book-ingest`: 合法 EPUB 本地导入，按章切分为段落结构
- `book-structure`: 8 编 44 章目录与 1500 年时代分界元数据
- `text-pipeline`: 段落年份索引、LLM 抽取、实体融合、统一 KB（骨架 + 契约）
- `global-visualization`: 时间轴 / 关系网 / 地图（阶段 2，本 change 仅契约）

### Modified Capabilities

（无 — 绿field 项目）

## Impact

- **新仓库**: 独立 `global-history` / `llm-global-history` 仓库（与 zizhitongjian 分离）
- **参考实现**: zizhitongjian（只借鉴，不合并仓库）
- **版权**: 不下载、不提交译本全文
- **后续依赖**: DeepSeek API（抽取）、Nominatim/Wikidata（地理编码）

## MVP 范围外（Non-Goals）

- 对话式「问通史」RAG 聊天
- 全书 44 章一次性 LLM 抽取（先 1–2 章试点）
- 多语言原文对照
- 历史边界多边形（V1 仅点坐标）
