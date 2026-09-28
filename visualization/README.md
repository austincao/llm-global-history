# 全球通史 · 知识图谱（前端）

基于 React + TypeScript + Vite 的可视化前端，展示《全球通史》知识图谱中的事件、人物关系与地理分布。

> 方法论参考 [zizhitongjian](https://github.com/JY0284/zizhitongjian) 的可视化模式；本目录已改为全球通史品牌与数据契约。

## 功能

- 时间轴：按年份浏览事件
- 关系网络：D3 力导向图
- 地图：Leaflet 展示地点
- 筛选：章范围 / 年份范围（URL 可分享）
- RAG 问答：经 Vite 代理访问本地 FastAPI

## 开发

在仓库根目录先发布运行时数据，再启动前端：

```bash
# 仓库根目录
uv run python scripts/publish_visualization_data.py

cd visualization
npm install
npm run dev
```

浏览器打开 http://localhost:5173 。

```bash
npm run build
npm run preview
```

## 运行时数据

应用读取：

- `public/data/unified_knowledge.json`
- `public/data/juan_year_index.json`（与流水线章索引兼容的文件名）

缺失时页面会报加载错误。`public/data/` 下 JSON 默认 gitignore，由根目录流水线生成后发布。

## 技术栈

React 19 · TypeScript · Vite · Tailwind CSS · D3 · Leaflet
