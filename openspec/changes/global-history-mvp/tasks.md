## 1. 工程初始化

- [x] 1.1 创建独立仓库 `global-history`
- [x] 1.2 `openspec init --tools cursor`
- [x] 1.3 创建 change `global-history-mvp`
- [x] 1.4 编写 README / AGENTS.md / .gitignore / pyproject.toml

## 2. 书籍元数据

- [x] 2.1 编写 `sources/book_structure.json`（8 编 44 章）
- [x] 2.2 编写 `scripts/validate_book_structure.py`
- [x] 2.3 编写 `tests/test_book_structure.py`
- [x] 2.4 编写 `sources/private/README.md`（版权说明）

## 3. 本地导入

- [x] 3.1 实现 `scripts/ingest_book.py`（EPUB → adapted_book.json）
- [x] 3.2 用户提供正版 EPUB 后实测 ingest 并记录章节匹配率（44/44 章，6417 段）
- [ ] 3.3 针对 EPUB 标题格式差异扩展 regex（若 3.2 失败）

## 4. OpenSpec 契约

- [x] 4.1 编写 proposal.md / design.md
- [x] 4.2 编写 specs: book-structure, book-ingest, text-pipeline, global-visualization
- [x] 4.3 运行 `openspec validate global-history-mvp` 通过
- [ ] 4.4 用户 Review → LGTM

## 5. 流水线骨架（post-LGTM）

- [x] 5.1 实现 `model/` 目录（role/action/event/location/extraction/unified）
- [x] 5.2 实现 `build_segment_year_index.py`（BCE/CE/circa）
- [x] 5.3 实现 `build_chapter_year_index.py`
- [x] 5.4 编写 LLM 提示词 `prompts/sys_entity_relation_extraction.md`（全球史版）
- [x] 5.5 试点抽取：第 22 章（35 chunks，227 实体 / 202 地点 / 79 事件 / 143 关系）

## 6. 实体融合（post-LGTM）

- [x] 6.1 实现 `entity_resolution.py`（Union-Find + 全球史实体分类）
- [x] 6.2 编写 `tests/test_entity_resolution.py`
- [x] 6.3 产出 `data/unified_knowledge.json`（第 22 章：58 人物 / 24 政权 / 102 地点 / 68 事件 / 135 关系）

## 7. 前端（独立 change: global-history-viz）

- [x] 7.1 Fork zizhitongjian `visualization/`
- [x] 7.2 章范围默认第22章；FilterControls 改为「章」；1500–1600 快速筛选
- [x] 7.3 全球地图坐标回填（第 22 章 102 地点，`scripts/build_geography.py`）

## 8. 验收

- [x] 8.1 `uv run pytest -q` 通过（8 tests）
- [x] 8.2 `openspec validate global-history-mvp` 通过
- [x] 8.3 至少 1 章完成 ingest → extract → unified KB 垂直切片（第 22 章）
- [x] 8.4 编写计划与进度文档 `docs/PROJECT_PLAN_AND_STATUS.md`
