# DeepResearch Agent

深度搜索与研究辅助 AI Agent 系统。项目现在内嵌 `MCP_Visual` 多模态能力，支持在研究任务中上传 PDF、图片和音频：PDF 会提取文本，图片会进行视觉分析与 OCR，音频会转写并摘要，所有附件上下文都会进入研究规划、综合分析和最终报告。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 14, React, Tailwind CSS, Shadcn UI, TanStack Query, Zustand |
| 后端 | FastAPI, Python 3.11+, LangGraph, Prisma |
| 数据库 | PostgreSQL + Chroma |
| Agent | LangGraph 状态机 + Tavily 搜索 + OpenAI SDK |
| 多模态 | MCP_Visual / multimodal-mcp，支持图片分析、OCR、音频转写和音频摘要 |

## 项目结构

```text
DeepReCy/
├── backend/              # FastAPI 后端与 Agent 工作流
│   ├── app/
│   │   ├── api/routes/   # API 路由
│   │   ├── agents/       # LangGraph 节点、策略、工具
│   │   ├── services/     # LLM/搜索/PDF/向量/多模态服务
│   │   ├── core/         # 配置/加密/异常
│   │   └── db/           # 数据库层
│   └── prisma/schema.prisma
├── frontend/             # Next.js 前端
├── MCP_Visual/           # 可独立运行的多模态 MCP 服务
├── tools/                # 辅助脚本
└── docker-compose.yml    # PostgreSQL + Chroma + Redis
```

## 快速开始

### 1. 配置环境变量

```powershell
Copy-Item .env.example .env
```

至少填写：

| 变量 | 描述 | 必填 |
|------|------|------|
| `DATABASE_URL` | PostgreSQL 连接字符串 | 是 |
| `CHROMA_HOST` / `CHROMA_PORT` | Chroma 服务地址 | 是 |
| `ENCRYPTION_KEY` | API Key 加密密钥，至少 32 字符 | 是 |
| `TAVILY_API_KEY` | Tavily 搜索 API Key；为空时部分搜索走模拟/降级逻辑 | 否 |
| `OPENAI_API_KEY` | MCP_Visual 图片/音频分析使用；若 UI 里选择 OpenAI 且未设置此变量，会复用用户 OpenAI key | 多模态必需 |
| `MCP_VISUAL_ALLOWED_DIRS` | MCP_Visual 允许读取的本地目录；默认后端上传目录会自动加入 | 否 |
| `MCP_VISUAL_MAX_FILE_MB` | 图片/音频分析文件大小限制 | 否 |
| `OPENAI_VISION_MODEL` | 图片分析与 OCR 模型 | 否 |
| `OPENAI_TRANSCRIBE_MODEL` | 音频转写模型 | 否 |

### 2. 启动基础设施

```powershell
docker compose up -d
```

这会启动：

- PostgreSQL: `localhost:5432`
- Chroma: `localhost:8000`
- Redis: `localhost:6379`

### 3. 安装并启动后端

```powershell
cd backend
python -m pip install -r requirements.txt
npm install
npx prisma migrate dev --name init
python run.py
```

`backend/requirements.txt` 会以 editable 方式安装 `../MCP_Visual`，因此后端可以内嵌调用图片和音频分析能力。后端运行在 http://localhost:8000。

### 4. 安装并启动前端

```powershell
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:3000。

### 5. 一键启动

Windows PowerShell 可使用：

```powershell
.\start.ps1 -Install
.\start.ps1
```

`-Install` 会安装后端、前端和本地 `MCP_Visual` 依赖。

## 使用流程

1. 打开 http://localhost:3000/settings。
2. 配置 LLM 提供商、模型和 API Key。
3. 回到首页，输入研究主题。
4. 可选上传一个附件：PDF、图片或音频。
5. 选择研究策略并点击「开始深度研究」。
6. 在研究页面查看 Agent 工作流进度和最终 Markdown 报告。

附件处理方式：

| 附件类型 | 处理方式 |
|----------|----------|
| PDF | 提取前 4000 字文本作为上传上下文 |
| 图片 | 调用 MCP_Visual 进行视觉摘要、对象识别和 OCR |
| 音频 | 调用 MCP_Visual 进行转写、摘要和关键要点提取 |

如果未配置可用 OpenAI key，图片和音频分析会被跳过，研究任务本身不会中断。

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/settings` | GET/POST | 获取/保存用户设置 |
| `/api/research/start` | POST | 启动研究任务 |
| `/api/research/{id}/stream` | GET | SSE 流式获取研究进度 |
| `/api/research/{id}/report` | GET | 获取完整报告 |
| `/api/library` | GET/POST | 笔记列表/创建 |
| `/api/library/{id}` | GET/PUT/DELETE | 笔记 CRUD |
| `/api/library/search` | GET | 语义搜索笔记 |
| `/api/upload/pdf` | POST | 兼容旧版本，仅上传 PDF |
| `/api/upload/media` | POST | 上传 PDF、图片或音频，返回 `{ fileId, filename, size, mediaType }` |

## Deep Research 工作流

```text
用户输入 + 附件上下文
  → 意图拆解 Planning
  → 多源检索 Search
  → 内容过滤 Filter
  → 综合分析 Synthesis
  → 报告撰写 Draft
```

多模态附件上下文会进入 Planning、Synthesis 和 Draft 阶段，让 Agent 在拆解问题、交叉综合和写报告时都能使用图片/OCR/音频转写信息。

## MCP_Visual 独立调试

主应用默认内嵌调用 `MCP_Visual`，不需要单独启动 MCP 服务。如需调试独立 MCP Server：

```powershell
cd MCP_Visual
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
$env:OPENAI_API_KEY = "sk-..."
$env:MCP_VISUAL_ALLOWED_DIRS = "D:\media,D:\DeepReCy\backend\uploads"
multimodal-mcp http --host 127.0.0.1 --port 8765
```

健康检查：

```powershell
curl http://127.0.0.1:8765/health
```

MCP endpoint:

```text
http://127.0.0.1:8765/mcp
```

## 开发与测试

后端测试：

```powershell
pytest backend/tests
```

MCP_Visual 测试：

```powershell
pytest MCP_Visual/tests
```

前端检查：

```powershell
cd frontend
npm run lint
```

## 开发说明

- 前端使用 Next.js 14 App Router。
- 后端使用 FastAPI，支持异步 SSE 响应。
- 数据库使用 Prisma ORM。
- API Key 使用 AES-256-GCM 加密存储。
- Chroma 用于笔记语义搜索。
- MCP_Visual 工具已注册到 Agent 工具系统：`vision_analyze`、`ocr_image`、`audio_transcribe`、`audio_summarize`、`media_qa`。
