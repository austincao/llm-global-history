# Global History MVP — Design Spec

> Superpowers brainstorming 产出 · 2026-06-19
> OpenSpec change: `global-history-mvp`

## 目标

基于斯塔夫里阿诺斯《全球通史》第 7 版（北大译本），构建全球年鉴式历史知识图谱 MVP。

## 范围

**In scope (MVP change)**
- 独立仓库 + OpenSpec 契约
- 8 编 44 章公开目录
- 用户自备 EPUB 本地导入
- 流水线设计与测试骨架

**Out of scope**
- 全书 LLM 抽取
- 生产级前端
- 盗版文本下载

## 架构

见 `openspec/changes/global-history-mvp/design.md`。

## 1500 年分界

| 部分 | 编 | 章 | 时代 |
|------|----|----|------|
| 上册 | 1–5 | 1–21 | pre-1500 |
| 下册 | 6–8 | 22–44 | post-1500 |

## 下一步

1. 用户 Review 本 spec + OpenSpec change → 回复 **LGTM**
2. 见 [PROJECT_PLAN_AND_STATUS.md](../../PROJECT_PLAN_AND_STATUS.md) 第七节「下一步建议」

## 历史进度

- 2026-06-19：第 22 章抽取 + 融合完成，详见 [PROJECT_PLAN_AND_STATUS.md](../../PROJECT_PLAN_AND_STATUS.md)
