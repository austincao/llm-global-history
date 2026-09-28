# 书籍正文存放说明

## 为什么不能自动下载

《全球通史》第 7 版（北大出版社，王皖强、刘北成译本）为 **受版权保护的出版物**。
本仓库 **不会** 也不应包含全书正文或从盗版站点抓取的内容。

## 你需要做什么

1. 通过合法渠道获取电子版或自行 OCR/录入：
   - 纸质书 + 扫描（个人学习用途）
   - 京东 / 当当 / 得到 App 等正版电子书
   - 学校图书馆借阅

2. 将文件放入本目录（已被 `.gitignore` 忽略）：

```bash
mkdir -p sources/private
cp /path/to/your/全球通史第7版.epub sources/private/
```

3. 运行导入脚本：

```bash
uv sync
uv run python scripts/ingest_book.py \
  --input sources/private/全球通史第7版.epub \
  --structure sources/book_structure.json \
  --output adapted_book.json
```

## 支持的格式（MVP）

| 格式 | 支持状态 |
|------|----------|
| EPUB | ✅ MVP 已实现基础解析 |
| PDF | 🔜 后续（需 pdftotext / pymupdf） |
| TXT | 🔜 后续（按章节标题切分） |

## 输出

- `adapted_book.json`：按 **编 → 章 → 段** 结构化的段落列表
- 默认 **不提交** 到 Git

## 章节目录

公开可用的 8 编 44 章结构见同目录上一级的 `book_structure.json`（仅元数据，不含正文）。
