const pptxgen = require("pptxgenjs");
const path = require("path");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "DeepReCy";
pptx.company = "CS599 Project";
pptx.subject = "DeepResearch Agent project introduction and demo";
pptx.title = "DeepResearch Agent 项目介绍与演示";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};
pptx.defineLayout({ name: "WIDE", width: 13.333, height: 7.5 });
pptx.layout = "WIDE";

const C = {
  ink: "172033",
  muted: "667085",
  line: "D9E1EA",
  blue: "2563EB",
  cyan: "0891B2",
  green: "059669",
  amber: "D97706",
  red: "DC2626",
  bg: "F7FAFC",
  white: "FFFFFF",
  dark: "111827",
  purple: "7C3AED",
};

function addBg(slide) {
  slide.background = { color: C.bg };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 13.333,
    h: 0.12,
    fill: { color: C.blue },
    line: { color: C.blue },
  });
}

function title(slide, text, sub) {
  slide.addText(text, {
    x: 0.55,
    y: 0.35,
    w: 8.8,
    h: 0.45,
    fontFace: "Microsoft YaHei",
    fontSize: 23,
    bold: true,
    color: C.ink,
    margin: 0,
    breakLine: false,
  });
  if (sub) {
    slide.addText(sub, {
      x: 0.58,
      y: 0.82,
      w: 9.8,
      h: 0.28,
      fontSize: 9.5,
      color: C.muted,
      margin: 0,
    });
  }
}

function foot(slide, page) {
  slide.addText(`DeepResearch Agent | CS599 Project | ${page}`, {
    x: 9.9,
    y: 7.12,
    w: 2.9,
    h: 0.18,
    fontSize: 7,
    color: "8A94A6",
    align: "right",
    margin: 0,
  });
}

function chip(slide, text, x, y, color = C.blue, w) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w: w || Math.max(0.9, text.length * 0.13 + 0.35),
    h: 0.32,
    rectRadius: 0.06,
    fill: { color: "FFFFFF", transparency: 0 },
    line: { color, transparency: 10 },
  });
  slide.addText(text, {
    x: x + 0.1,
    y: y + 0.07,
    w: (w || Math.max(0.9, text.length * 0.13 + 0.35)) - 0.2,
    h: 0.15,
    fontSize: 7.4,
    bold: true,
    color,
    align: "center",
    margin: 0,
  });
}

function box(slide, text, x, y, w, h, color, opts = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.08,
    fill: { color: opts.fill || C.white },
    line: { color: opts.line || color, transparency: opts.lineT ?? 10, width: 1.2 },
    shadow: opts.shadow ? { type: "outer", color: "B8C2D0", opacity: 0.12, blur: 1.5, angle: 45, distance: 1 } : undefined,
  });
  slide.addText(text, {
    x: x + 0.18,
    y: y + 0.16,
    w: w - 0.36,
    h: h - 0.25,
    fontSize: opts.fontSize || 11,
    bold: opts.bold ?? true,
    color: opts.textColor || C.ink,
    valign: "mid",
    align: opts.align || "center",
    margin: 0,
    fit: "shrink",
  });
}

function bullet(slide, items, x, y, w, opts = {}) {
  slide.addText(
    items.map((t) => ({ text: t, options: { bullet: { type: "bullet" } } })),
    {
      x,
      y,
      w,
      h: opts.h || 2.2,
      fontSize: opts.fontSize || 12,
      color: opts.color || C.ink,
      breakLine: true,
      paraSpaceAfterPt: 8,
      margin: 0,
      fit: "shrink",
    }
  );
}

function sectionLabel(slide, text, x, y, color) {
  slide.addText(text, {
    x,
    y,
    w: 2.4,
    h: 0.25,
    fontSize: 8,
    bold: true,
    color,
    margin: 0,
  });
}

// 1
{
  const s = pptx.addSlide();
  s.background = { color: "0F172A" };
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: "0F172A" }, line: { color: "0F172A" } });
  s.addShape(pptx.ShapeType.arc, { x: 8.9, y: -0.5, w: 4.5, h: 4.5, line: { color: "38BDF8", transparency: 15, width: 2 } });
  s.addShape(pptx.ShapeType.arc, { x: 7.8, y: 3.5, w: 5.6, h: 3.4, line: { color: "34D399", transparency: 25, width: 1.5 } });
  s.addText("DeepResearch Agent", {
    x: 0.72,
    y: 1.05,
    w: 8.9,
    h: 0.65,
    fontSize: 34,
    bold: true,
    color: C.white,
    margin: 0,
  });
  s.addText("深度搜索与研究辅助 AI Agent 系统", {
    x: 0.76,
    y: 1.85,
    w: 7.3,
    h: 0.34,
    fontSize: 17,
    color: "C7D2FE",
    margin: 0,
  });
  s.addText("面向复杂研究主题，自动完成意图拆解、多源检索、内容过滤、综合分析、报告撰写与知识库沉淀。", {
    x: 0.78,
    y: 2.45,
    w: 7.15,
    h: 0.82,
    fontSize: 14,
    color: "E5E7EB",
    fit: "shrink",
    margin: 0,
    breakLine: false,
  });
  const chips = ["Next.js", "FastAPI", "LangGraph", "PostgreSQL", "Chroma", "SSE"];
  chips.forEach((c, i) => chip(s, c, 0.78 + i * 1.18, 3.55, ["38BDF8", "34D399", "A78BFA", "FBBF24", "60A5FA", "F472B6"][i], 0.95));
  box(s, "用户输入\n研究主题 / PDF", 8.25, 1.18, 1.55, 0.9, "38BDF8", { fill: "1E293B", textColor: C.white, lineT: 0 });
  box(s, "Agent 工作流\n规划 → 检索 → 综合", 10.05, 2.48, 1.8, 0.9, "34D399", { fill: "1E293B", textColor: C.white, lineT: 0 });
  box(s, "研究报告\nMarkdown / 知识库", 8.75, 4.28, 1.8, 0.9, "FBBF24", { fill: "1E293B", textColor: C.white, lineT: 0 });
  s.addShape(pptx.ShapeType.line, { x: 9.8, y: 1.72, w: 0.8, h: 0.8, line: { color: "94A3B8", width: 1.2, beginArrowType: "none", endArrowType: "triangle" } });
  s.addShape(pptx.ShapeType.line, { x: 10.75, y: 3.38, w: -0.65, h: 0.82, line: { color: "94A3B8", width: 1.2, beginArrowType: "none", endArrowType: "triangle" } });
  s.addText("项目介绍与演示 PPT", { x: 0.78, y: 6.74, w: 3.2, h: 0.2, fontSize: 8, color: "94A3B8", margin: 0 });
}

// 2
{
  const s = pptx.addSlide();
  addBg(s); title(s, "项目背景与目标", "把一次复杂的资料调研，压缩为可观察、可复用、可沉淀的 Agent 流程"); foot(s, 2);
  box(s, "传统调研痛点", 0.72, 1.55, 3.55, 3.75, C.red, { fill: "FFF7F7", shadow: true });
  bullet(s, ["检索关键词需要反复调整", "资料来源分散，质量难判断", "阅读、摘录、整理耗时", "报告与知识库难以复用"], 1.0, 2.35, 3.0, { fontSize: 11.2 });
  box(s, "DeepResearch Agent 目标", 4.9, 1.55, 3.55, 3.75, C.blue, { fill: "F8FBFF", shadow: true });
  bullet(s, ["自动拆解研究主题", "多源检索并保留来源", "按策略迭代优化结果", "生成结构化 Markdown 报告"], 5.18, 2.35, 3.0, { fontSize: 11.2 });
  box(s, "项目交付形态", 9.08, 1.55, 3.55, 3.75, C.green, { fill: "F6FEF9", shadow: true });
  bullet(s, ["Web 前端可交互演示", "FastAPI 后端服务", "数据库与向量库支持", "一键启动脚本与部署仓库"], 9.36, 2.35, 3.0, { fontSize: 11.2 });
}

// 3
{
  const s = pptx.addSlide();
  addBg(s); title(s, "系统总体架构", "前端负责研究入口、进度展示与知识库；后端负责任务编排、Agent 执行、数据持久化与外部服务集成"); foot(s, 3);
  sectionLabel(s, "Client", 0.8, 1.28, C.blue);
  box(s, "Next.js 14\nReact / Tailwind\nTanStack Query / Zustand", 0.72, 1.65, 2.25, 1.45, C.blue, { shadow: true });
  sectionLabel(s, "API Layer", 3.45, 1.28, C.cyan);
  box(s, "FastAPI\nREST API + SSE Stream\nSettings / Research / Library / Upload", 3.3, 1.65, 2.55, 1.45, C.cyan, { shadow: true });
  sectionLabel(s, "Agent Layer", 6.35, 1.28, C.purple);
  box(s, "LangGraph\nPlanning / Search / Filter\nSynthesis / Draft / Evaluation", 6.18, 1.65, 2.85, 1.45, C.purple, { shadow: true });
  sectionLabel(s, "Data & Services", 9.6, 1.28, C.green);
  box(s, "PostgreSQL\n用户设置 / 研究任务 / 笔记", 9.38, 1.65, 2.82, 0.72, C.green, { shadow: true });
  box(s, "Chroma\n向量检索 / 语义搜索", 9.38, 2.55, 2.82, 0.72, C.green, { shadow: true });
  box(s, "OpenAI / DeepSeek / Anthropic\nTavily / PDF Parser", 9.38, 3.45, 2.82, 0.72, C.green, { shadow: true });
  const arrows = [
    [2.97, 2.38, 0.33, 0],
    [5.85, 2.38, 0.33, 0],
    [9.03, 2.38, 0.35, 0],
    [7.6, 3.1, 0, 1.1],
    [7.6, 4.2, 1.78, -0.3],
  ];
  arrows.forEach(([x, y, w, h]) => s.addShape(pptx.ShapeType.line, { x, y, w, h, line: { color: "7A8799", width: 1.2, endArrowType: "triangle" } }));
  box(s, "SSE 实时推送：步骤、质量评分、来源与最终报告", 3.0, 4.95, 6.95, 0.68, C.amber, { fill: "FFFBEB", fontSize: 12 });
  box(s, "安全：API Key AES-256-GCM 加密存储；CORS 支持本地与局域网演示", 3.0, 5.85, 6.95, 0.68, C.blue, { fill: "EFF6FF", fontSize: 12 });
}

// 4
{
  const s = pptx.addSlide();
  addBg(s); title(s, "Deep Research 工作流", "从用户输入到报告输出，Agent 以 LangGraph 状态机方式组织节点与条件路由"); foot(s, 4);
  const steps = [
    ["Planning", "意图理解\n拆解子问题", C.blue],
    ["Search", "多源检索\nWeb / 学术 / PDF", C.cyan],
    ["Evaluate", "质量评估\n覆盖度判断", C.amber],
    ["Filter", "内容筛选\n去噪与证据整理", C.green],
    ["Synthesis", "交叉验证\n综合分析", C.purple],
    ["Draft", "报告撰写\nMarkdown 输出", C.red],
  ];
  steps.forEach(([name, desc, color], i) => {
    const x = 0.58 + i * 2.05;
    box(s, `${name}\n${desc}`, x, 2.0, 1.58, 1.12, color, { fill: "FFFFFF", textColor: C.ink, fontSize: 10.5, shadow: true });
    if (i < steps.length - 1) s.addShape(pptx.ShapeType.line, { x: x + 1.58, y: 2.56, w: 0.45, h: 0, line: { color: "8A94A6", width: 1.1, endArrowType: "triangle" } });
  });
  s.addShape(pptx.ShapeType.line, { x: 5.25, y: 3.18, w: -2.58, h: 1.18, line: { color: C.amber, width: 1.2, dash: "dash", endArrowType: "triangle" } });
  s.addText("当质量或覆盖度不足时，自动回到检索/查询优化节点继续迭代", {
    x: 2.15,
    y: 4.5,
    w: 5.1,
    h: 0.28,
    fontSize: 11.5,
    color: C.amber,
    bold: true,
    margin: 0,
  });
  bullet(s, ["支持 factual / analytical / exploratory / comparative 四类研究策略", "节点间通过条件路由控制迭代次数与报告修订", "前端实时展示当前步骤、质量分数、来源列表和最终报告"], 1.0, 5.25, 11.3, { h: 1.25, fontSize: 12 });
}

// 5
{
  const s = pptx.addSlide();
  addBg(s); title(s, "核心功能", "围绕研究任务的完整闭环：配置、输入、执行、报告、沉淀"); foot(s, 5);
  const cards = [
    ["模型配置", "支持 OpenAI、Anthropic、DeepSeek；API Key 加密存储。", C.blue],
    ["研究任务", "输入主题，选择研究策略，可上传 PDF 作为参考。", C.green],
    ["实时进度", "通过 SSE 显示 Agent 步骤、迭代轮次和质量评分。", C.cyan],
    ["报告生成", "输出 Markdown 报告，保留参考来源，可下载。", C.purple],
    ["知识库", "保存报告为笔记，支持列表、详情、搜索与导出。", C.amber],
    ["开发运维", "Docker Compose 基础设施，一键启动前后端。", C.red],
  ];
  cards.forEach(([h, b, c], i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.75 + col * 4.15;
    const y = 1.55 + row * 2.15;
    box(s, h, x, y, 3.45, 0.46, c, { fill: c, textColor: C.white, lineT: 0, fontSize: 13 });
    box(s, b, x, y + 0.46, 3.45, 1.18, c, { fill: C.white, lineT: 15, fontSize: 11, bold: false, shadow: true });
  });
}

// 6
{
  const s = pptx.addSlide();
  addBg(s); title(s, "前端设计与交互", "Next.js App Router 构建主要页面，兼顾研究入口、任务追踪和知识库管理"); foot(s, 6);
  box(s, "首页\n输入研究主题\n选择研究策略\n上传 PDF", 0.75, 1.55, 2.6, 1.5, C.blue, { shadow: true });
  box(s, "设置页\n选择 LLM Provider\n选择模型\n保存 API Key", 3.88, 1.55, 2.6, 1.5, C.green, { shadow: true });
  box(s, "研究页\nSSE 实时进度\n报告流式展示\n保存/复制/下载", 7.0, 1.55, 2.6, 1.5, C.purple, { shadow: true });
  box(s, "知识库\n笔记列表\n搜索/导出\n详情编辑", 10.12, 1.55, 2.6, 1.5, C.amber, { shadow: true });
  s.addShape(pptx.ShapeType.line, { x: 3.35, y: 2.3, w: 0.5, h: 0, line: { color: "8A94A6", endArrowType: "triangle", width: 1.1 } });
  s.addShape(pptx.ShapeType.line, { x: 6.48, y: 2.3, w: 0.5, h: 0, line: { color: "8A94A6", endArrowType: "triangle", width: 1.1 } });
  s.addShape(pptx.ShapeType.line, { x: 9.6, y: 2.3, w: 0.5, h: 0, line: { color: "8A94A6", endArrowType: "triangle", width: 1.1 } });
  sectionLabel(s, "技术实现", 0.9, 4.0, C.blue);
  bullet(s, ["React 18 + Tailwind CSS：页面结构清晰、响应式布局", "TanStack Query：知识库数据获取、缓存与刷新", "Zustand：本地设备 ID、模型设置和 API Key 状态", "React Markdown：报告内容直接渲染为可读文档"], 1.0, 4.38, 5.1, { h: 1.65, fontSize: 11.5 });
  sectionLabel(s, "用户体验", 7.05, 4.0, C.green);
  bullet(s, ["研究过程中持续反馈，避免长时间黑盒等待", "报告支持复制、Markdown 下载和保存知识库", "策略标签与质量评分帮助理解 Agent 决策", "一键启动脚本降低本地演示门槛"], 7.15, 4.38, 5.2, { h: 1.65, fontSize: 11.5 });
}

// 7
{
  const s = pptx.addSlide();
  addBg(s); title(s, "后端 API 与数据模型", "FastAPI 提供研究任务、设置、上传和知识库 API，数据库保存用户配置与研究结果"); foot(s, 7);
  const endpoints = [
    ["/api/settings", "GET / POST", "获取与保存模型配置"],
    ["/api/research/start", "POST", "启动研究任务"],
    ["/api/research/{id}/stream", "GET", "SSE 获取任务进度"],
    ["/api/research/{id}/report", "GET", "获取完整报告"],
    ["/api/library", "GET / POST", "笔记列表与创建"],
    ["/api/upload/pdf", "POST", "上传 PDF"],
  ];
  s.addTable(
    [["端点", "方法", "说明"], ...endpoints],
    {
      x: 0.78,
      y: 1.35,
      w: 6.35,
      h: 3.55,
      border: { type: "solid", color: C.line, pt: 0.5 },
      fill: "FFFFFF",
      color: C.ink,
      fontSize: 8.8,
      margin: 0.05,
      autoFit: false,
      colW: [2.45, 1.25, 2.65],
      rowH: [0.32, 0.42, 0.42, 0.42, 0.42, 0.42, 0.42],
    }
  );
  box(s, "User\n设备 ID / Provider / Model\n加密 API Key", 8.0, 1.48, 3.25, 0.88, C.blue, { shadow: true });
  box(s, "ResearchTask\n查询 / 策略 / 进度\n报告 / 来源 / 质量分", 8.0, 2.72, 3.25, 0.88, C.purple, { shadow: true });
  box(s, "Note\n标题 / 内容 / 来源\n语义搜索索引", 8.0, 3.96, 3.25, 0.88, C.green, { shadow: true });
  s.addText("数据层：SQLAlchemy Async + PostgreSQL；迁移结构由 Prisma schema 管理。", {
    x: 0.82,
    y: 5.45,
    w: 10.8,
    h: 0.3,
    fontSize: 12,
    bold: true,
    color: C.ink,
    margin: 0,
  });
}

// 8
{
  const s = pptx.addSlide();
  addBg(s); title(s, "Agent 策略与质量控制", "系统不是单次调用模型，而是根据研究策略组织多节点执行与迭代"); foot(s, 8);
  box(s, "研究策略", 0.8, 1.45, 2.1, 0.42, C.blue, { fill: C.blue, textColor: C.white, lineT: 0 });
  bullet(s, ["factual：快速事实回答", "analytical：深度分析", "exploratory：探索发现", "comparative：对比分析"], 0.95, 2.05, 3.4, { h: 1.55, fontSize: 11 });
  box(s, "质量控制", 4.35, 1.45, 2.1, 0.42, C.green, { fill: C.green, textColor: C.white, lineT: 0 });
  bullet(s, ["搜索质量评分", "覆盖度评分", "报告质量评分", "低于阈值自动修订"], 4.5, 2.05, 3.4, { h: 1.55, fontSize: 11 });
  box(s, "可观察性", 7.9, 1.45, 2.1, 0.42, C.purple, { fill: C.purple, textColor: C.white, lineT: 0 });
  bullet(s, ["任务状态持久化", "步骤日志记录", "SSE 实时推送", "来源列表随报告保存"], 8.05, 2.05, 3.4, { h: 1.55, fontSize: 11 });
  s.addShape(pptx.ShapeType.chevron, { x: 2.78, y: 4.7, w: 1.0, h: 0.5, fill: { color: "DDEBFF" }, line: { color: C.blue } });
  s.addText("策略选择", { x: 1.35, y: 4.8, w: 1.3, h: 0.2, fontSize: 10, bold: true, color: C.ink, margin: 0 });
  s.addText("节点执行", { x: 4.1, y: 4.8, w: 1.3, h: 0.2, fontSize: 10, bold: true, color: C.ink, margin: 0 });
  s.addShape(pptx.ShapeType.chevron, { x: 5.2, y: 4.7, w: 1.0, h: 0.5, fill: { color: "EAFBF2" }, line: { color: C.green } });
  s.addText("质量评估", { x: 6.55, y: 4.8, w: 1.4, h: 0.2, fontSize: 10, bold: true, color: C.ink, margin: 0 });
  s.addShape(pptx.ShapeType.chevron, { x: 7.7, y: 4.7, w: 1.0, h: 0.5, fill: { color: "FEF3C7" }, line: { color: C.amber } });
  s.addText("报告输出", { x: 9.05, y: 4.8, w: 1.4, h: 0.2, fontSize: 10, bold: true, color: C.ink, margin: 0 });
}

// 9
{
  const s = pptx.addSlide();
  addBg(s); title(s, "安全与工程化设计", "围绕本地演示、配置安全、服务可用性和开发效率做工程补强"); foot(s, 9);
  const rows = [
    ["API Key 安全", "AES-256-GCM 加密存储，前端只保存本地状态，后端按设备 ID 读取配置。"],
    ["跨域与本地演示", "CORS 支持 localhost、127.0.0.1 及常见局域网地址的任意端口。"],
    ["异步任务", "研究任务通过后台协程执行，前端通过 SSE 订阅进度。"],
    ["基础设施", "Docker Compose 提供 PostgreSQL、Chroma、Redis 服务。"],
    ["质量验证", "后端单测覆盖 Agent 节点、策略、工具、注册器和安全模块。"],
    ["一键启动", "start.ps1 / start.bat 同时启动 Docker、后端与前端。"],
  ];
  rows.forEach(([h, b], i) => {
    const y = 1.28 + i * 0.82;
    box(s, h, 0.82, y, 2.25, 0.48, [C.blue, C.green, C.purple, C.amber, C.cyan, C.red][i], { fill: [C.blue, C.green, C.purple, C.amber, C.cyan, C.red][i], textColor: C.white, lineT: 0, fontSize: 10.5 });
    box(s, b, 3.18, y, 8.8, 0.48, C.line, { fill: C.white, lineT: 35, fontSize: 10.2, bold: false, align: "left" });
  });
}

// 10
{
  const s = pptx.addSlide();
  addBg(s); title(s, "演示流程", "建议 5-7 分钟完成一次端到端演示"); foot(s, 10);
  const steps = [
    ["1", "启动项目", "运行 .\\start.ps1，打开前端 http://localhost:3000"],
    ["2", "配置模型", "进入设置页，选择 Provider / Model，保存 API Key"],
    ["3", "发起研究", "首页输入研究主题，选择分析策略，可上传 PDF"],
    ["4", "观察执行", "研究页查看 Planning / Search / Filter / Synthesis / Draft 进度"],
    ["5", "查看报告", "阅读 Markdown 报告、来源列表与质量评分"],
    ["6", "沉淀知识", "保存到知识库，搜索、查看详情或导出 Markdown"],
  ];
  steps.forEach(([n, h, b], i) => {
    const x = i < 3 ? 0.9 : 7.0;
    const y = 1.35 + (i % 3) * 1.6;
    s.addShape(pptx.ShapeType.ellipse, { x, y: y + 0.05, w: 0.52, h: 0.52, fill: { color: C.blue }, line: { color: C.blue } });
    s.addText(n, { x, y: y + 0.17, w: 0.52, h: 0.15, fontSize: 9.5, bold: true, color: C.white, align: "center", margin: 0 });
    s.addText(h, { x: x + 0.75, y, w: 2.5, h: 0.28, fontSize: 13, bold: true, color: C.ink, margin: 0 });
    s.addText(b, { x: x + 0.75, y: y + 0.42, w: 4.2, h: 0.42, fontSize: 10.2, color: C.muted, margin: 0, fit: "shrink" });
  });
  box(s, "演示问题示例：\n“量子计算在金融风险管理中的应用现状与挑战”\n“对比 RAG 与 Agentic Search 在企业知识管理中的优缺点”", 1.2, 6.15, 10.9, 0.62, C.green, { fill: "F6FEF9", fontSize: 11.2 });
}

// 11
{
  const s = pptx.addSlide();
  addBg(s); title(s, "项目亮点与可扩展方向", "当前版本已经形成完整研究闭环，后续可继续增强评估、检索和部署能力"); foot(s, 11);
  box(s, "项目亮点", 0.85, 1.35, 2.35, 0.45, C.blue, { fill: C.blue, textColor: C.white, lineT: 0 });
  bullet(s, ["完整的前后端可运行系统", "LangGraph 状态机组织 Agent 工作流", "SSE 实时反馈提升可观察性", "支持多模型 Provider 与知识库沉淀", "测试、启动脚本、CORS 修复具备演示稳定性"], 1.05, 2.05, 4.65, { h: 2.75, fontSize: 12 });
  box(s, "可扩展方向", 7.0, 1.35, 2.35, 0.45, C.green, { fill: C.green, textColor: C.white, lineT: 0 });
  bullet(s, ["加入用户登录与权限体系", "增强学术搜索与引用格式生成", "支持批量文档与多模态资料", "加入任务队列与部署监控", "为评估节点接入标准化 benchmark"], 7.2, 2.05, 4.65, { h: 2.75, fontSize: 12 });
}

// 12
{
  const s = pptx.addSlide();
  s.background = { color: "111827" };
  s.addText("Q & A", {
    x: 0.88,
    y: 1.15,
    w: 5.0,
    h: 0.6,
    fontSize: 36,
    bold: true,
    color: C.white,
    margin: 0,
  });
  s.addText("DeepResearch Agent\n深度搜索与研究辅助 AI Agent 系统", {
    x: 0.95,
    y: 2.15,
    w: 5.5,
    h: 0.8,
    fontSize: 16,
    color: "CBD5E1",
    margin: 0,
    breakLine: true,
  });
  box(s, "GitHub\nhttps://github.com/tianchang11/cs599-project", 0.95, 4.55, 5.7, 0.78, "38BDF8", { fill: "1F2937", textColor: C.white, lineT: 0, fontSize: 12 });
  box(s, "本地演示\n.\\start.ps1 → http://localhost:3000", 0.95, 5.55, 5.7, 0.78, "34D399", { fill: "1F2937", textColor: C.white, lineT: 0, fontSize: 12 });
  box(s, "Research\nPlanning → Search → Filter → Synthesis → Draft", 7.45, 1.38, 4.25, 3.85, "94A3B8", { fill: "1F2937", textColor: C.white, fontSize: 17, lineT: 35 });
}

const out = path.join(process.cwd(), "DeepResearch-Agent-项目介绍与演示.pptx");
pptx.writeFile({ fileName: out });
