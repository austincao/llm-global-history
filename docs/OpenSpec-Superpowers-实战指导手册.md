# Global History — OpenSpec + Superpowers 实战指导手册

> 本仓库使用 **OpenSpec（需求契约）+ Superpowers（执行流程）** 组织全球通史知识图谱项目。

## 流程总览

```mermaid
flowchart LR
  A[brainstorming] --> B[OpenSpec propose]
  B --> C[人工 LGTM]
  C --> D[writing-plans]
  D --> E[TDD 实现]
  E --> F[validate]
  F --> G[archive]
```

## 当前 Change

**ID:** `global-history-mvp`

```bash
# 在仓库根目录
openspec status --change global-history-mvp
openspec validate global-history-mvp
```

Cursor 命令：

```
/opsx-propose 完善全球通史 MVP
/opsx-apply global-history-mvp
/opsx-archive global-history-mvp
```

## 书籍导入（版权）

1. 合法获取第 7 版 EPUB/PDF
2. 放入 `sources/private/`（gitignore）
3. `uv run python scripts/ingest_book.py --input sources/private/你的文件.epub`

**禁止：** 在仓库中提交全书正文或从盗版站抓取。

## Capability 映射

| Capability | Spec 路径 |
|------------|-----------|
| book-structure | `openspec/changes/global-history-mvp/specs/book-structure/` |
| book-ingest | `openspec/changes/global-history-mvp/specs/book-ingest/` |
| text-pipeline | `openspec/changes/global-history-mvp/specs/text-pipeline/` |
| global-visualization | `openspec/changes/global-history-mvp/specs/global-visualization/` |

## 驱动 Agent 的话术

```
需求：按 openspec/changes/global-history-mvp/tasks.md 继续实现
范围：不提交 sources/private/ 与 adapted_book.json
流程：先读 proposal/design/specs，对照 Spec 验收，未完成项打勾
```

## 参考项目

- 方法论样板：[zizhitongjian](https://github.com/JY0284/zizhitongjian)
- OpenSpec / Superpowers 工作流说明：见本手册上文
- **计划与进度**：[PROJECT_PLAN_AND_STATUS.md](./PROJECT_PLAN_AND_STATUS.md)
