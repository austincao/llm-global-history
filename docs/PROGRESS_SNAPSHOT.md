# 进度快照（Quick Reference）

> 详细说明见 [PROJECT_PLAN_AND_STATUS.md](./PROJECT_PLAN_AND_STATUS.md)

**项目**：斯塔夫里阿诺斯《全球通史》第 7 版 → 知识图谱 + 可视化  
**仓库**：本仓库（`llm-global-history` / `global-history`）  
**更新**：2026-06-19

## 一句话现状

**全书年份索引已就绪；第 22 章已完成抽取→融合→地理编码→可视化全链路。可开始批量抽取 23–44 章。**

## 完成度概览

| 模块 | 进度 |
|------|------|
| 工程 / OpenSpec | ██████████ 100% |
| EPUB 导入（44 章） | ██████████ 100% |
| 年份索引 | ██████████ 100% |
| LLM 抽取 | █░░░░░░░░░ ~2%（1/44 章） |
| 实体融合 | █░░░░░░░░░ ~2%（1/44 章） |
| 地理编码 | █░░░░░░░░░ ~2%（第 22 章 102/102 地点） |
| 可视化前端 | █████████░ ~95%（章↔年份联动 + 地图） |

## 年份索引（全书）

| 指标 | 数值 |
|------|------|
| 段落总数 | 6417 |
| 有显式年份的段落 | 1457 |
| 章起止年 | 44/44（含 BCE 负值） |

示例：第 22 章 `1500–1600`，第 3 章 `公元前3500–前1000`

## 第 22 章数据（当前唯一试点）

| 阶段 | 指标 |
|------|------|
| 段落 | 173 段 → 35 chunks |
| 抽取 | 227 实体 / 202 地点 / 79 事件 / 143 关系 |
| 融合 | 58 人 / 24 政权 / 102 地点 / 68 事件 / 135 关系 |
| 地理编码 | 102 地点全部有 WGS84 坐标 |

## 下一步

1. **自动进行中**：23–44 收尾 → **1–21 章批量抽取** → 全书融合验证
2. 全书完成后更新可视化默认范围为 1–44

## 全书规模（预估）

| 范围 | 章数 | Chunks |
|------|------|--------|
| 1–21（1500 年前） | 21 | ~617 |
| 22–44（1500 年后） | 23 | ~682 |
| **合计** | **44** | **~1,299** |

```bash
# 23–44 完成后自动跑 1–21（已在后台排队）
uv run python scripts/complete_full_book.py --wait-finish

# 手动触发（若 post-1500 已验证完毕）
uv run python scripts/complete_full_book.py --skip-wait
```

## 常用命令

```bash
# 年份索引（全书，需 adapted_book.json）
uv run python scripts/build_year_index.py

# 批量抽取 23–44 章（断点续跑）
uv run python scripts/batch_extract_chapters.py --start 23 --end 44

# 仅查看计划
uv run python scripts/batch_extract_chapters.py --dry-run

# 单章抽取 + 融合
uv run python scripts/extract_chapter.py --chapter 23
uv run python entity_resolution.py --chapter 23

# 地理编码 + 发布
uv run python scripts/build_geography.py

# 本地预览
cd visualization && npm run dev
```
