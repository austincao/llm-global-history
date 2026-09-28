# Global History — 全球通史知识图谱

> 基于 **L. S. Stavrianos《全球通史：从史前史到 21 世纪》**（第 7 版，北大译本）构建的全球年鉴式历史知识库与交互可视化。
>
> 方法论参考 [zizhitongjian](https://github.com/JY0284/zizhitongjian)；工程组织采用 **OpenSpec（需求契约）+ Superpowers（执行流程）**。

## 在线 Demo

（MVP 完成后部署）

## 书籍来源说明（重要）

**本仓库不包含受版权保护的译本全文。**

请将您合法获得的 EPUB/PDF/TXT 放入 `sources/private/`（已 gitignore），再运行导入脚本：

```bash
# 1. 放置文件（示例）
cp ~/Downloads/全球通史第7版.epub sources/private/

# 2. 解析为结构化段落
uv run python scripts/ingest_book.py --input sources/private/全球通史第7版.epub

# 3. 输出 adapted_book.json（默认 gitignore）
```

合法获取渠道：纸质书、京东/当当、得到 App 电子书、学校图书馆等。

## 工程结构

```
global-history/
├── openspec/                 # OpenSpec 需求契约（proposal / design / specs / tasks）
├── docs/superpowers/         # Superpowers 设计文档与实现计划
├── sources/
│   ├── book_structure.json   # 8 编 44 章目录（公开元数据）
│   └── private/              # 用户自备正文（gitignore）
├── data/                     # 流水线产物（大部分 gitignore）
├── model/                    # Pydantic 数据模型
├── scripts/                  # 构建与导入脚本
└── visualization/            # React 前端（后续阶段）
```

## OpenSpec + Superpowers 工作流

| 阶段 | 工具 | 产出 |
|------|------|------|
| P0 对齐需求 | Superpowers `brainstorming` | `docs/superpowers/specs/*-design.md` |
| P1 写契约 | OpenSpec `/opsx-propose` | `openspec/changes/global-history-mvp/` |
| P2 人工 Review | 你回复 **LGTM** | — |
| P3 拆计划 | Superpowers `writing-plans` | `docs/superpowers/plans/*.md` |
| P4 实现 | `/opsx-apply` + TDD | 代码 + 测试 |
| P5 验收 | `openspec validate` | — |
| P6 归档 | `/opsx-archive` | 基线 `openspec/specs/` |

详见 [docs/OpenSpec-Superpowers-实战指导手册.md](docs/OpenSpec-Superpowers-实战指导手册.md)。

## 文档

| 文档 | 说明 |
|------|------|
| [PROJECT_PLAN_AND_STATUS.md](docs/PROJECT_PLAN_AND_STATUS.md) | **完整计划 + 当前进度**（主文档） |
| [PROGRESS_SNAPSHOT.md](docs/PROGRESS_SNAPSHOT.md) | 一页纸进度快照 |
| [OpenSpec-Superpowers-实战指导手册.md](docs/OpenSpec-Superpowers-实战指导手册.md) | 工作流操作说明 |
| [2026-06-19-global-history-design.md](docs/superpowers/specs/2026-06-19-global-history-design.md) | Superpowers 设计 spec |

## 当前 Change

**进度总览**：见 [docs/PROJECT_PLAN_AND_STATUS.md](docs/PROJECT_PLAN_AND_STATUS.md)  
**快速快照**：见 [docs/PROGRESS_SNAPSHOT.md](docs/PROGRESS_SNAPSHOT.md)

```bash
openspec status --change global-history-mvp
openspec validate global-history-mvp
```

在 Cursor 中：

```
/opsx-propose 继续完善 global-history-mvp
/opsx-apply global-history-mvp
```

## 本地开发（MVP 阶段）

```bash
# Python
uv sync
uv run pytest -q

# 发布可视化数据 + 启动前端

# 1. 确保已有 unified_knowledge.json
uv run python entity_resolution.py --chapter 22

# 2. 发布到 visualization/public/data/
uv run python scripts/publish_visualization_data.py

# 3. 启动前端
cd visualization && npm install && npm run dev
```

浏览器打开 http://localhost:5173 ，默认展示 **第 22 章** 试点数据。

## 许可证

本仓库代码与工程文档采用 [MIT](LICENSE) 许可。

**译本正文仍受版权保护**：请勿提交 `sources/private/`、`adapted_book.json` 或含大段原文的流水线产物。本仓仅提供目录元数据、抽取工具与可视化代码。

## 参考

- 原书：斯塔夫里阿诺斯《全球通史》第 7 版（北大出版社）
- 方法论样板：[zizhitongjian](https://github.com/JY0284/zizhitongjian)
- OpenSpec：https://openspec.dev/
- Superpowers：https://github.com/obra/superpowers
