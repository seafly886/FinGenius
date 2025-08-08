# FinGenius Web 前端

这是 FinGenius 股票分析系统的 Web 前端界面。

## 功能特性

- 🎯 **一键分析**: 输入股票代码，点击按钮即可开始分析
- 📊 **实时输出**: 实时显示分析过程中的控制台输出
- 📋 **分析报告**: 自动生成并显示HTML格式的分析报告
- 📈 **历史记录**: 保存分析历史，方便回顾
- 💾 **报告下载**: 支持下载分析报告到本地

## 使用方法

### 1. 启动服务器

```bash
# 方法1: 使用启动脚本（推荐）
python start_web.py

# 方法2: 直接启动后端服务器
python backend/server.py
```

### 2. 访问前端

打开浏览器访问: http://localhost:8000

### 3. 开始分析

1. 在输入框中输入股票代码（如：000001）
2. 点击"一键分析"按钮
3. 系统会自动调用 `python main.py 000001` 命令
4. 实时输出区域会显示分析过程
5. 分析完成后会自动生成并显示报告

## 技术架构

- **前端**: Vue.js 3 + Tailwind CSS
- **后端**: Python + Starlette + Uvicorn
- **通信**: Server-Sent Events (SSE) 实现实时输出
- **分析引擎**: 原有的 FinGenius 分析系统

## API 接口

- `POST /api/analyze` - 启动股票分析
- `GET /api/stream/{session_id}` - 获取实时输出流
- `GET /api/report/{report_path}` - 获取报告内容
- `GET /api/download/{report_path}` - 下载报告文件
- `GET /api/view/{report_path}` - 在浏览器中查看报告

## 文件结构

```
frontend/
├── index.html          # 主页面
├── app.js             # Vue.js 应用逻辑
└── README.md          # 说明文档

backend/
└── server.py          # 后端API服务器

start_web.py           # 启动脚本