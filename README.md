# DeepResearch Agent

深度搜索与研究辅助 AI Agent 系统。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 14, React, Tailwind CSS, Shadcn UI, TanStack Query, Zustand |
| 后端 | FastAPI, Python 3.11+, LangGraph, Prisma |
| 数据库 | PostgreSQL + Chroma (向量数据库) |
| Agent | LangGraph 状态机 + Tavily 搜索 + OpenAI SDK |

## 项目结构

```
DeepResearch-Agent/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/routes/   # API 路由
│   │   ├── agents/       # LangGraph 工作流
│   │   ├── services/     # LLM/搜索/PDF/向量服务
│   │   ├── core/         # 配置/加密/异常
│   │   └── db/           # 数据库层
│   └── prisma/schema.prisma
├── frontend/             # Next.js 前端
└── docker-compose.yml    # PostgreSQL + Chroma
```

## 快速开始

### 1. 启动基础设施

```bash
docker-compose up -d
```

这将启动：
- PostgreSQL (localhost:5432)
- Chroma 向量数据库 (localhost:8000)

### 2. 配置后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
npx prisma migrate dev --name init

# 复制并编辑环境变量
cp ../.env.example ../.env
# 编辑 .env，填写 ENCRYPTION_KEY 和 TAVILY_API_KEY

# 启动后端
python run.py
```

后端运行在 http://localhost:8000

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端运行在 http://localhost:3000

### 4. 配置 API Key

1. 打开 http://localhost:3000/settings
2. 选择 LLM 提供商（OpenAI / Anthropic / DeepSeek）
3. 选择模型
4. 输入 API Key 并保存

### 5. 开始研究

1. 在首页输入研究主题
2. 可选：上传 PDF 作为额外参考
3. 点击「开始深度研究」
4. 在研究页面实时查看 Agent 工作流进度
5. 报告生成后，可保存到知识库或下载为 Markdown

## 环境变量

| 变量 | 描述 | 必填 |
|------|------|------|
| DATABASE_URL | PostgreSQL 连接字符串 | 是 |
| CHROMA_HOST | Chroma 服务地址 | 是 |
| ENCRYPTION_KEY | AES-256 加密密钥（32+字符） | 是 |
| TAVILY_API_KEY | Tavily 搜索 API Key | 否（提供模拟数据） |
| CORS_ORIGINS | 允许的跨域来源 | 否 |

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
| `/api/upload/pdf` | POST | 上传 PDF |

## Deep Research 工作流

```
用户输入 → 意图拆解(Planning) → 多源检索(Search)
        → 内容过滤(Filter) → 综合分析(Synthesis) → 报告撰写(Draft)
```

## 开发说明

- 前端使用 Next.js 14 App Router
- 后端使用 FastAPI，支持异步流式 SSE 响应
- 数据库使用 Prisma ORM，Prisma Client 已集成到后端
- API Key 使用 AES-256-GCM 加密存储
- Chroma 用于笔记的语义搜索（可选功能）
