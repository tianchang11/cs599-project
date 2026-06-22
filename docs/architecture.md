# DeepResearch Agent 架构说明

## 总体架构

DeepResearch Agent 采用前后端分离和 Agent 工作流编排架构：

```text
Next.js 前端
  -> FastAPI API 层
  -> 异步任务管理层
  -> LangGraph Agent 工作流
  -> 搜索工具 / MCP_Visual / PostgreSQL / Chroma
```

前端负责任务创建、附件上传、设置管理、进度展示和报告操作。后端负责接口、配置、任务生命周期和 SSE 推送。LangGraph 负责研究任务的状态机编排。工具与数据层提供检索、多模态分析、任务持久化和知识库语义搜索能力。

## Agent 工作流

核心节点包括：

- `planning`: 将研究主题拆解为多个子查询。
- `tool_search` / `search`: 调用 Web Search 和 Academic Search 获取资料。
- `evaluate_quality`: 评估检索结果质量，决定是否优化查询。
- `adaptive_control`: 根据质量和覆盖度控制迭代深度。
- `filter`: 对搜索结果进行相关性筛选和摘要。
- `synthesis`: 综合多源资料，识别共识、冲突、主题和缺口。
- `evaluate_coverage`: 判断研究是否覆盖原始问题。
- `draft`: 生成 Markdown 研究报告。
- `evaluate_report`: 评估报告质量，必要时回到起草节点。

## 多模态集成

`MCP_Visual` 以内嵌 Python 包方式接入后端。上传文件统一进入 `/api/upload/media`：

- PDF: 使用 PyMuPDF 提取文本。
- 图片: 调用 `vision_analyze` 和 `ocr_image`。
- 音频: 调用 `audio_transcribe` 和 `audio_summarize`。

分析结果统一格式化为 `uploaded_context`，并注入 Planning、Synthesis 和 Draft 阶段。

## 数据层

- PostgreSQL: 存储用户设置、研究任务、步骤日志、报告和知识库笔记。
- Chroma: 支持知识库语义搜索。
- Uploads: 保存 PDF、图片和音频附件。

## 安全与可观测性

- API Key 使用后端加密存储。
- `.env`、上传文件、日志和依赖目录通过 `.gitignore` 排除。
- 上传文件限制类型和大小。
- MCP_Visual 本地路径读取限制在允许目录。
- 研究任务通过 SSE 推送步骤、质量评分和错误状态。
