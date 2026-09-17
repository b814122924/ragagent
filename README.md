# SmartBrief · 多智能体报告生成平台

> 第 27 节（全栈评测与最终交付）终结版本（v27.0）

本版本在 v26（RAG 知识库 + 智能体记忆）基础上，完成**自动化评测体系**与**全栈最终联调**：标准用例批量执行 + 五维指标（成功率 / 平均耗时 / P95 / ReAct 循环次数 / 关键词覆盖率 / 记忆命中率）+ 雷达图与 Markdown 评测报告，新增「评测中心」「报告中心」「报告展示」页面，提供一键启动脚本，项目完结。

**第 27 节核心能力**：

- **自动化评测引擎**（`backend/evaluation/`）：`runner.py`（10 个固定测试用例，覆盖储能 / 消费电子 / 出行 / 新能源等行业，每个用例附带预期关键词列表；逐个调用 `workflow.run_task` 批量执行并记录耗时 / 成功与否 / ReAct 循环次数 / 关键词覆盖率 / 记忆命中。**当前仅启用第 1 个用例（快速验证链路），其余已在 `TEST_CASES` 中注释、按需恢复**）+ `metrics.py`（五维指标体系与目标值：成功率 ≥90% / 平均耗时 ≤120s / 平均 ReAct ≤8 次 / 关键词覆盖率 ≥70% / 记忆命中率 ≥30%）
- **评测报告持久化**：`data.db` 新增 `evaluation_reports` 表（`db/evaluation_repository.py`），评测执行中即可轮询进度（completed_cases），完成后统一落 JSON 结果 + 指标 + Markdown 总结（替换早期规划的文件方案）；**后端重启会自动把遗留 running 评测置为 failed**（`fail_running_interrupted`，评测中心进度条不卡死、可重新触发）
- **评测 API**：`POST /evaluation/run`（立即返回 eval_id，后台执行，并发保护）/ `GET /evaluation/reports`（历史列表）/ `GET /evaluation/reports/{id}`（进度或完整结果）
- **报告展示 API**：`GET /tasks/{id}/report`（最终报告 Markdown + 执行摘要：总耗时 / ReAct 行动次数 / 记忆命中数）
- **评测中心页**（`/evaluation`，Evaluation.vue）：运行评测 → 进度条（2s 轮询）→ 六张指标卡 + **ECharts 五维雷达图** + 用例明细表 + Markdown 报告预览 + 历史评测对比
- **报告中心页**（`/reports`，Reports.vue，顶导航 TAB）：展示全部已生成报告（已完成任务）列表，支持**按主题搜索**（`keyword` 模糊匹配）+ **时间排序**（最新/最久在前）+ 分页 + 「查看」（跳转 `/report/:taskId` 报告展示页）+ 「删除」（级联日志，带确认）
- **报告展示页**（`/report/:taskId`，ReportView.vue）：Markdown 富文本渲染 + 图表图片容器 + 执行摘要卡 + 导出 Word / PDF
- **一键启动**：`start.bat`（Windows）/ `start.sh`（Linux/Mac）

---

### 第 26 节里程碑（v26.0，历史保留）

本版本在 v25（A2A 审核循环）基础上，为智能体注入「记忆」能力：**RAG 知识库**（模板 / 术语 / 上传文档）+ **长期记忆**（历史报告复用）+ **短期记忆**（Checkpointer 断点续跑，服务中断任务自动暂停可一键恢复），并新增知识库管理页与任务管理增强。

**第 26 节核心能力**：

- **RAG 知识库（复用 zhiqida-rag）**：新增 `backend/rag/`（embeddings / loaders / chunkers / vectorstores / store 门面）；ChromaDB 双集合 `rag_collection`（模板 5 份 + 术语 30 条 + 用户上传，seed 幂等）+ `memory_collection`（历史报告）；SiliconFlow bge-m3 向量化 + md5 稳定 ID 去重
  - Planner 规划前检索**模板**结构做 Few-shot；Writer 撰写时检索**术语**注入 prompt，并新增「RAG 检索到 N 条相关术语」Thought 日志
- **长期记忆**：任务成功自动 `remember()`；Planner 规划前 `recall()` 相似历史报告，命中写入 `memory_hits` 落库并在任务详情「长期记忆命中」卡片展示；知识库页提供开关（**逻辑开关**，关闭不删数据）
- **短期记忆 / 断点续跑**：LangGraph Checkpointer（`checkpoints.db`，SqliteSaver）；服务中断遗留任务重启自动标记 **paused（已暂停）**，「恢复执行」从 checkpoint 续跑（仅 paused / failed 生效，无快照自动从头兜底）
- **知识库管理页**（`/knowledge`）：分类统计 + 长期记忆开关、文档列表（分类筛选：全部 / 模板 / 术语 / 文档）、上传（模板 / 术语 / 文档）、查看 chunk 详情弹窗、删除、RAG 检索测试
- **任务管理增强**：任务列表 / 详情支持「删除」（级联 ReAct 日志）与「恢复」（操作随状态收敛：运行中 / 已完成不显示恢复）

---

### 第 25 节里程碑（v25.0，历史保留）

本版本在 v24（LangGraph 多智能体编排）基础上，引入 **Agent-to-Agent（A2A）审核循环**：报告草稿生成后由第二个智能体 **Reviewer** 按质量标准审核，不通过则由第三个智能体 **Rewriter** 按审核意见覆盖式返工，直至通过或达到循环上限（默认 3 次）后强制输出；同时完成 **工程容错加固** 与任务详情的审核过程可视化。

**第 25 节核心能力**：

- **A2A 审核循环**：工作流升级为 `Planner→Scheduler→Reviewer→（通过→END / 打回→Rewriter→Reviewer）`
  - **Reviewer**：按 3 条质量标准（≥2 个具体数据点 / 引用信息来源 / 正文字数≥1000）评审草稿，输出结构化 `{passed, comments}`（解析容错，LLM 失败时放行不阻塞）
  - **Rewriter**：prompt 注入研究主题 + 研究数据摘要，按意见覆盖式重写，**严禁更换/编造主题**（修复"报告被重写成无关主题"）
  - **循环上限 3 次**：前 2 次打回返工，第 3 次仍不过则**强制通过**并给草稿追加 ⚠️ 警告标记
- **多轮审核历史**：每轮审核追加 `review_history {round, passed, comments}`（`tasks` 表独立列持久化，_MIGRATIONS 幂等迁移）；`iteration / max_iterations / passed / forced_pass` 随任务落库并由 `GET /tasks/{id}/status` 返回
- **审核日志可追溯**：Reviewer 的 Observation 携带本轮意见原文；任务详情页按「第 N 次审核」**分轮展示**意见气泡，与日志流中的审核小节一一对应
- **工程容错**：MCP 工具调用超时 5s + 重试 2 次；Scheduler 单 Agent 步骤超时跳过（Researcher 30s / **Writer 撰写整稿放宽 120s**）；杜绝单步卡死拖垮工作流
- **技能注入双通道**（single_agent）：已启用技能 schema 并入 LLM tools 参数（重名排除）+ `_skill_banner()` 技能名片拼入 system prompt
- **前端 TaskDetail 增强**：A2A 结果卡片（分轮意见 / 通过-打回-强制标签 / 循环进度）+ 执行计划「A2A 审核循环」节点 + 日志流按真实时序分节

---

### 第 24 节里程碑（v24.0，历史保留）

本版本在 v23（技能池与技能管理）基础上，引入 **LangGraph 多智能体编排**：基于 **Plan-and-Execute + ReAct** 范式，将「关键词 → 执行计划 → ReAct 推理 → 输出草稿」的完整链路落地，并提前接入 **SQLite 业务持久化**（任务 / ReAct 日志），提供任务提交、任务列表、任务详情的完整前后端闭环。

**第 24 节核心能力**：

- **Planner**：根据主题生成 2-5 步执行计划（含依赖关系，JSON 容错解析 + 降级计划）
- **Scheduler**：按 `depends_on` 依赖派发步骤给 Researcher / Writer
- **ReAct Researcher**：Thought→Action(web_search)→Observation 循环（最多 3 轮）
- **ReAct Writer**：基于研究数据撰写报告草稿
- **SQLite 持久化**：任务与 ReAct 日志落库（`backend/data.db`），重启不丢，支撑任务列表/详情查询
- **任务系统 API**：`POST /generate`、`GET /tasks`（分页+过滤）、`GET /tasks/{id}/status`
- **前端三页**：任务提交（Home.vue）、任务列表（Tasks.vue，状态 Tab + 分页 + 查看按钮）、任务详情（TaskDetail.vue，Plan 看板 + ReAct 日志流 + 报告草稿富文本展示 + 导出 Word/PDF）

**v23 技能池**（保留）：

- **抽象层**：`BaseSkill` / `SkillInput` / `SkillOutput` / `SkillRegistry`
- **内置技能**：4 个 mock 技能（搜索 / 分析 / 写作 / 审核），启动时注册，**只读（不可删除 / 修改），支持开关**
- **自定义技能**：表单创建（持久化为 `skills_pool/<name>/skill.md`）、编辑、删除；可选 `skill.py`（继承 `BaseSkill`）动态加载；`.zip` 技能包导入（校验路径穿越与 2MB 大小上限）
- **试运行**：内置技能直接返回 mock 结果；自定义技能按 `skill.md` 指令调用 LLM 执行
- **技能开关**：内置 / 自定义技能均支持开关，开关状态统一持久化到 `backend/skill_config.json`（与 `tool_config.json` 模式一致，不写入 skill.md）；禁用的技能不可试运行，AI 对话中也会被过滤（`/` 命令与 `+ 技能` 列表不再展示，直接输入 `/技能名` 会提示"已禁用"）

**工具管理**：内置工具与 MCP 工具分开管理，均支持开关；MCP 支持自定义添加（填写名称、URL、传输方式等）、编辑与删除，配置持久化到 `backend/tool_config.json` 与 `backend/mcp_config.json`。MCP 传输支持 **stdio 子进程**、**Streamable HTTP** 与 **HTTP + SSE（旧版）** 三种方式。

## 技术栈

- **后端**：Python 3.10+ / FastAPI / OpenAI SDK / python-dotenv / **LangChain ≥ 1.0** / **LangGraph** / sqlite3 / **ChromaDB + SiliconFlow bge-m3（RAG 向量库，第 26 节）** / **langgraph-checkpoint-sqlite（短期记忆 Checkpointer）**
- **前端**：Vue 3 + Vite + TypeScript + Element Plus + Axios + Vue Router（报告渲染：marked + DOMPurify；PDF 导出：html2pdf.js）

## 工作原理（工具调用闭环）

```text
用户输入（自然语言提示词）
   │
   ▼
① 单智能体组装 messages（含对话历史）
   │
   ▼
② 调用大模型（携带 内置工具 Schema + MCP 工具 Schema）
   │
   ├── 模型返回 tool_calls？ ─── 否 ──→ ③ 直接返回最终回答
   │
   └── 是
       ▼
④ 按工具名路由执行：
   ├── 内置工具（current_time / calculator）→ 本地 Python 函数（受开关控制）
     └── MCP 工具 → MCP 管理器（ClientSession）按 Server 路由：
         ├── stdio Server（内置 web_search，FastMCP）→ 子进程 stdio 会话
         ├── Streamable HTTP Server（自定义，如 12306）→ 自动完成 initialize/session 握手
         └── HTTP + SSE Server（旧版，如 Fetch）→ 官方 sse_client 会话
       │
       ▼
⑤ 工具结果追加回 messages（role: tool）→ 回到 ②（最多 5 轮）
```

「内置工具」与「MCP 工具」的区别：

| 类型 | 实现位置 | 特点 |
|------|---------|------|
| 内置（Function Calling） | 后端 `tools/builtin_tools.py`，普通 Python 函数 + JSON Schema | 进程内直接执行，演示标准 function calling |
| MCP 工具（内置 stdio） | `mcp_servers/web_search_server.py`（FastMCP Server） | 后端启动时以子进程拉起，演示 stdio 传输 |
| MCP 工具（自定义 HTTP） | 后端 `mcp_client/mcp_client.py`（官方 ClientSession + streamable_http） | 用户添加远程 Server（如 ModelScope 12306），演示 Streamable HTTP 与工具自动发现 |
| MCP 工具（自定义 SSE） | 后端 `mcp_client/mcp_client.py`（官方 ClientSession + sse_client） | 用户添加旧版 SSE Server（如 ModelScope Fetch），演示 HTTP + SSE 传输 |

## 目录结构

```text
smartbrief/
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── single_agent.py         # 单智能体：Function Calling 循环（技能注入双通道，第 25 节）
│   │   ├── planner.py              # Planner（第 24 节）：生成 Plan
│   │   ├── scheduler.py            # Scheduler（第 24/25 节）：按依赖派发 + 单 Agent 步骤超时跳过（30s/120s）
│   │   ├── react_researcher.py     # ReAct Researcher（第 24 节）：web_search 循环
│   │   ├── react_writer.py         # ReAct Writer（第 24 节）：撰写报告草稿
│   │   ├── reviewer.py             # Reviewer（第 25 节 A2A）：3 条标准评审草稿，维护 review_history
│   │   └── rewriter.py             # Rewriter（第 25 节 A2A）：注入主题+数据，按意见覆盖式重写
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py                # AgentState(TypedDict)（第 24/25/26 节：A2A 审核字段 + memory_hits）
│   │   └── workflow.py             # LangGraph 工作流 + route_after_review 条件边 + run_task()（第 24/25 节；第 26 节：checkpointer 续跑 + remember）
│   ├── memory/                     # 记忆（第 26 节）
│   │   ├── __init__.py
│   │   ├── checkpointer.py         # 短期记忆：open_checkpointer（SqliteSaver async with，降级 MemorySaver）+ has_checkpoint/list_snapshots
│   │   └── long_term_memory.py     # 长期记忆：remember/recall/search_memory + 运行时开关
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py             # SQLite 连接管理 + 建表 + _MIGRATIONS 幂等迁移（第 24/25/26/27 节：memory_hits 列 + evaluation_reports 表）
│   │   ├── task_repository.py      # 任务/日志 CRUD（第 24/25/26 节：JSON 字段 + paused 中断标记 + memory_hits）
│   │   └── evaluation_repository.py # 评测报告 CRUD（第 27 节：create/set_progress/finish/fail/fail_running_interrupted/get/list）
│   ├── llm/
│   │   ├── __init__.py
│   │   └── client.py               # OpenAI 兼容接口封装（.env 读取配置）
│   ├── tools/
│   │   ├── __init__.py
│   │   └── builtin_tools.py        # 内置工具：current_time / calculator（注册表 + 开关持久化）
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── base_skill.py           # 抽象层：BaseSkill / SkillInput / SkillOutput
│   │   ├── registry.py             # SkillRegistry（内置技能禁删/禁改）
│   │   ├── mock_skills.py          # 内置 mock 技能：搜索 / 分析 / 写作 / 审核（只读）
│   │   └── skills_manager.py       # 技能池：create/update/delete/import/run + skill.md 解析
│   ├── skills_pool/                # 自定义技能持久化目录（<name>/skill.md [+skill.py]）
│   ├── mcp_client/
│   │   ├── __init__.py
│   │   └── mcp_client.py           # MCP 管理器：stdio/http/sse 连接、多 Server 增删改与开关
│   ├── evaluation/                 # 评测引擎（第 27 节）
│   │   ├── __init__.py
│   │   ├── metrics.py              # 五维指标计算 + 达标判定 + Markdown 报告生成
│   │   └── runner.py               # 10 个标准用例 + 批量执行（并发保护 + 进度落库）
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py               # /chat、/tools、/skills、/generate、/tasks（删除/恢复/report）、/knowledge、/memory、/evaluation、/health
│   ├── rag/                        # RAG 知识库（第 26 节，复用 zhiqida-rag）
│   │   ├── __init__.py
│   │   ├── embeddings.py           # SiliconFlow bge-m3 嵌入（EMBEDDING_* 环境变量，懒加载）
│   │   ├── loaders.py              # Document + 策略 Loader（txt/md/docx/pdf/xlsx）
│   │   ├── chunkers.py             # RecursiveChunker（512 字 + 64 重叠）
│   │   ├── vectorstores.py         # ChromaVectorStore（cosine + md5 稳定 ID）
│   │   └── store.py                # DB 门面：双集合缓存 + seed/ingest/list/search/delete/get_document_chunks
│   ├── data.db                     # SQLite 业务库（tasks / task_logs，第 24 节；evaluation_reports，第 27 节）
│   ├── data/chroma_db              # ChromaDB 持久化（rag_collection / memory_collection，第 26 节）
│   ├── data/templates/             # 5 份报告模板 seed（template_1..5_*.md）
│   ├── data/terminologies.txt      # 30 条行业术语 seed
│   ├── checkpoints.db              # LangGraph Checkpointer 短期记忆（第 26 节）
│   ├── .env.example                # 环境变量示例（含 EMBEDDING_BASE_URL / EMBEDDING_API_KEY / EMBEDDING_MODEL）
│   ├── tool_config.json            # 内置工具开关（运行时生成）
│   ├── mcp_config.json             # MCP Server 配置（运行时生成）
│   ├── requirements.txt            # 含 langchain/langgraph（>=1.0）、chromadb、langgraph-checkpoint-sqlite 等
│   └── main.py                     # FastAPI 启动入口（init_db + 技能池 + 拉起 MCP Server + seed 知识库 + 遗留 running→paused）
├── mcp_servers/
│   ├── __init__.py
│   └── web_search_server.py        # 内置 MCP Server：web_search（FastMCP，stdio 传输）
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── chat.ts             # 对话 API 封装
│   │   │   ├── tools.ts            # 工具列表 API 封装
│   │   │   ├── skills.ts           # 技能 API 封装（CRUD / 导入 / 试运行）
│   │   │   ├── tasks.ts            # 任务 API 封装（提交 / 列表 / 状态 / 删除 / 恢复 / 报告 + 类型）
│   │   │   ├── knowledge.ts        # 知识库 API 封装（文档列表 / 上传 / 删除 / 查看 / 检索 + 记忆开关，第 26 节）
│   │   │   └── evaluation.ts       # 评测 API 封装（运行 / 历史列表 / 详情轮询，第 27 节）
│   │   ├── views/
│   │   │   ├── Home.vue            # 任务提交页（第 24 节）
│   │   │   ├── Tasks.vue           # 任务列表页（第 24/26 节：状态 Tab + 分页 + 查看/删除/恢复）
│   │   │   ├── TaskDetail.vue      # 任务详情页（第 24-27 节：Plan 看板 + 日志时间序分节 + A2A 意见卡片 + 长期记忆命中 + 恢复执行 + 报告富文本/导出）
│   │   │   ├── KnowledgeBase.vue   # 知识库管理页（第 26 节：分类统计/筛选/上传/查看/删除/检索 + 记忆开关）
│   │   │   ├── Evaluation.vue      # 评测中心页（第 27 节：运行评测 + 进度条 + 指标卡 + 雷达图 + 用例明细 + 历史对比）
│   │   │   ├── Reports.vue         # 报告中心页（第 27 节：已生成报告列表 + 主题搜索 + 时间排序 + 查看/删除 + 分页）
│   │   │   ├── ReportView.vue      # 报告展示页（第 27 节：Markdown 渲染 + 执行摘要 + 导出 Word/PDF）
│   │   │   ├── Chat.vue            # AI 对话页（含工具调用记录 + 清空按钮）
│   │   │   ├── ToolMonitor.vue     # 工具监控页
│   │   │   └── SkillCenter.vue     # 技能中心页（卡片网格 + 新增/编辑/删除/导入/试运行）
│   │   ├── router/index.ts
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   └── vite.config.ts
├── start.bat / start.sh             # 一键启动脚本（第 27 节，Windows / Linux-Mac）
└── README.md
```

## 启动步骤

### 1. 配置 .env（backend/.env）

```bash
cd backend
cp .env.example .env
```

编辑 `.env`，填入真实 API 信息。支持**任意 OpenAI 兼容接口**，例如：

| 服务 | OPENAI_BASE_URL | OPENAI_MODEL |
|------|----------------|--------------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Kimi（Moonshot） | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| Ollama（本地） | `http://localhost:11434/v1` | `qwen2.5:7b` |

```env
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-xxxx
OPENAI_MODEL=gpt-4o-mini

# RAG 知识库嵌入（第 26 节）：SiliconFlow bge-m3；未配置时知识库为空但不影响任务执行
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_API_KEY=sk-xxxx
EMBEDDING_MODEL=BAAI/bge-m3
```

### 2. 启动后端（端口 8002）

```bash
cd backend
pip install -r requirements.txt   # 含 langchain>=1.0 / langgraph>=1.0
uvicorn main:app --reload --port 8002
```

验证：

- 健康检查：访问 <http://localhost:8002/api/v1/health>，应返回 `{"status":"ok","mcp_server":true}`
- 工具列表：访问 <http://localhost:8002/api/v1/tools>，应返回内置工具（current_time / calculator）与 MCP 工具（web_search）
- MCP Server 列表：访问 <http://localhost:8002/api/v1/tools/mcp>，应显示内置 `web_search_server` 与已添加的自定义 Server（如 12306 / Fetch）及其工具
- 技能列表：访问 <http://localhost:8002/api/v1/skills>，应返回 4 个内置技能（mock_search / mock_analyze / mock_write / mock_review）
- 知识库列表：访问 <http://localhost:8002/api/v1/knowledge/documents>，应返回 seed 的 5 份模板 + 30 条术语（第 26 节，需配置 `EMBEDDING_*`）

### 3. 启动前端（端口 5174）

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 <http://localhost:5174>，自动进入「任务提交」页面；导航栏含「任务提交」「任务列表」「报告中心」「知识库」「评测中心」「AI 对话」「工具监控」「技能中心」八个页面。

> 前端已通过 Vite 代理将 `/api` 请求转发到后端（见 `vite.config.ts`），无需额外配置跨域。

### 3.5 一键启动（第 27 节）

依赖安装完成后，可跳过手动分别启动，直接运行：

- **Windows**：双击 `start.bat`（后端独立窗口启动 + 前端前台启动）
- **Linux / Mac**：`./start.sh`（后端后台启动，前端退出时自动回收后端进程）

### 3.6 容器化部署（deploy/）

如需 Docker 容器化部署（nginx 反代 + 后端镜像 + 数据卷），见 [deploy/README.md](deploy/README.md)：

- 前置：Docker Engine + Docker Compose v2；`cd deploy && cp .env.example .env` 填入 API Key
- 一键：`./start.sh`（Linux/Mac）或 `start.bat`（Windows）
- 访问：前端 <http://localhost:8080>，健康检查 <http://localhost:8002/api/v1/health>

### 4. 多智能体任务演示（第 24–26 节）

1. 打开 <http://localhost:5174/home>，输入研究主题（如"智能手表 2025 市场分析"）→「生成研究报告」。
2. 自动跳转任务详情页：左侧 Plan 看板逐步完成，右侧 ReAct 日志流逐条滚动（Thought→Action→Observation）。Writer 每个撰写步骤前，日志会出现「RAG 检索到 N 条相关术语：…」的 Thought（第 26 节 RAG 术语注入）。
3. 若 Planner 规划时命中相似历史报告，顶部出现「长期记忆命中」卡片（第 26 节，展示相似度与结构标签）——第一次执行通常无历史，成功后该报告会成为后续任务的长期记忆。
4. 全部研究步骤完成后进入 **A2A 审核循环**：右侧日志流出现「🔍 A2A 审核 · 第 N 次」→ 若打回出现「✏️ A2A 改写返工」→ 再次审核；顶部 A2A 结果卡片按轮分组展示每轮意见与判定（通过 / 打回返工 / 强制通过）。
5. 任务完成后，底部报告草稿以富文本展示，右上角可「导出 Word」「导出 PDF」。
6. 返回「任务列表」页查看全部历史任务（状态 Tab + 分页），支持「删除」（级联日志，带确认）与「恢复」（仅"已暂停"任务展示，第 26 节）。

### 5. 知识库与记忆演示（第 26 节）

1. 打开「知识库」页（<http://localhost:5174/knowledge>）：分类统计卡展示模板 / 术语 / 文档数量与长期记忆开关；文档列表含 5 份模板 + 30 条术语（seed），可用分类筛选（全部 / 模板 / 术语 / 文档）。
2. 「上传」选择分类（模板 / 术语 / 文档）上传 txt / md / docx / pdf / xlsx 文件，入库后立即出现在列表；「查看」弹窗展示该文件切出的全部 chunk 与元数据；「删除」移除该文件全部 chunk（模板/术语预置文档删除后重启会被 seed 回补）。
3. 「RAG 检索测试」输入行业问题，返回语义最相似的 chunk（与 Writer 的术语注入同一条检索链路）。
4. 统计卡上的长期记忆开关：关闭后暂停记忆写入与检索（计数显示 —），**已存报告不删除**；重新开启即恢复。
5. 断点续跑演示：任务执行中停止后端进程 → 重启后端后，该任务自动标记「已暂停」（见后端启动日志提示）→ 在任务列表或详情点「恢复执行」，从最近 checkpoint 断点续跑。

### 6. 评测与报告演示（第 27 节）

1. **报告中心**：打开「报告中心」（`/reports`）→ 列表展示全部已生成报告（主题 / 任务 ID / 生成时间 / 报告耗时）→ 支持**按主题搜索**（输入关键词回车或点「搜索」，可清空恢复全量）与**时间排序**（最新在前 / 最久在前）→ 「查看」进入「报告展示」页（`/report/:taskId`：执行摘要卡 + Markdown 富文本报告 + 导出 Word / PDF）→ 「删除」移除报告（级联日志，带确认弹窗，支持分页）。
2. **运行评测**：打开「评测中心」（`/evaluation`）→「运行评测」→ 立即返回 eval_id 并开始后台批量执行用例（当前 `TEST_CASES` 仅启用 1 个、快速跑完；恢复注释的用例后按用例数耗时，期间页面每 2 秒轮询显示进度条）。
3. **查看结果**：评测完成后展示六张指标卡（成功率 / 平均耗时 / P95 / ReAct 次数 / 关键词覆盖率 / 记忆命中率，含目标值与达标标签）、**ECharts 五维雷达图**、Markdown 评测报告与各用例明细（耗时 / 循环次数 / 覆盖率 / 强制通过标记）。
4. **历史对比**：评测中心上方「历史评测」表格列出全部历史评测（持久化于 `data.db` 的 `evaluation_reports` 表），点击任意一行即可查看该次报告——重启后端后依然可查；**中断遗留的 running 评测在后端重启时自动标记为失败**（进度条不卡死，可重新触发）。
5. **并发保护**：评测执行中再次点击「运行评测」会提示"评测已在运行中"（后端 400，避免重复触发）。

## 功能演示（验收标准）

| 提示词 | 预期行为 |
|--------|---------|
| "现在几点了" | 触发内置 `current_time`，回答包含当前时间 |
| "计算 12*34+56 等于多少" | 触发内置 `calculator`，返回计算结果 |
| "搜索 便携储能 2026 市场" | 触发 MCP `web_search`，基于搜索结果总结回答 |

对话页面会以卡片形式展示每次工具调用的工具名、参数与结果；「工具监控」页面分两个 Tab 展示：

- **内置工具（Function Calling）**：current_time / calculator，可单独开关，展示分类与调用统计
- **MCP 工具**：内置 `web_search_server` 只可开关；自定义 Server 支持添加（名称 / URL / 描述 / 启用 / 传输方式）、编辑与删除，添加后立即发现工具；传输方式可选 Streamable HTTP（推荐）或 HTTP + SSE（旧版）

「技能中心」页面以卡片网格展示技能池：

- **内置技能**：mock_search（搜索）/ mock_analyze（分析）/ mock_write（写作）/ mock_review（审核），只读（无编辑 / 删除按钮）
- **自定义技能**：支持新增（标识 / 展示名 / 描述 / 分类 / 版本 / skill.md 正文）、编辑、删除与 `.zip` 技能包导入
- **试运行**：内置技能直接返回 mock 结果；自定义技能按 skill.md 指令调用 LLM 返回执行结果

> 说明：对话闭环与自定义技能试运行依赖真实 LLM API，请先在 `backend/.env` 填好 `OPENAI_API_KEY`。

## API 一览

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/v1/chat` | 单智能体对话（提示词触发工具调用） |
| GET | `/api/v1/tools` | 工具汇总（内置 + MCP 展开） |
| GET | `/api/v1/tools/builtin` | 内置工具列表（含开关状态） |
| PUT | `/api/v1/tools/builtin/{name}` | 内置工具开关 |
| GET | `/api/v1/tools/mcp` | MCP Server 列表（含工具、状态、错误信息） |
| POST | `/api/v1/tools/mcp` | 添加自定义 MCP Server（名称 / URL / 描述 / 启用 / 传输方式） |
| PUT | `/api/v1/tools/mcp/{id}` | 编辑自定义 MCP Server（可切换传输方式） |
| DELETE | `/api/v1/tools/mcp/{id}` | 删除自定义 MCP Server |
| PUT | `/api/v1/tools/mcp/{id}/enabled` | MCP Server 开关（内置与自定义均可） |
| POST | `/api/v1/tools/mcp/{id}/refresh` | 刷新某 Server 的工具列表 |
| GET | `/api/v1/tools/stats` | 工具调用统计 |
| GET | `/api/v1/skills` | 技能列表（含 builtin / source / skill_md） |
| POST | `/api/v1/skills` | 新增自定义技能（名称 / 展示名 / 分类 / 版本 / skill.md 正文） |
| PUT | `/api/v1/skills/{name}` | 编辑自定义技能（内置技能返回 400） |
| DELETE | `/api/v1/skills/{name}` | 删除自定义技能（内置技能返回 400） |
| POST | `/api/v1/skills/import` | 导入 `.zip` 技能包（multipart，校验路径与 2MB 大小） |
| POST | `/api/v1/skills/{name}/run` | 试运行技能（query + 可选 context） |
| POST | `/api/v1/generate` | 提交多智能体任务（`{"topic": "..."}`），返回 `task_id`（第 24 节） |
| GET | `/api/v1/tasks` | 任务列表（分页 `page`/`page_size` + 状态过滤 `status` + 主题搜索 `keyword` + 时间排序 `order=desc|asc`）（第 24 节 / 第 27 节报告中心） |
| GET | `/api/v1/tasks/{task_id}/status` | 任务状态 + Plan 进度 + ReAct 日志 + A2A 审核结果 + memory_hits 长期记忆命中（第 24/25/26 节） |
| DELETE | `/api/v1/tasks/{task_id}` | 删除任务（级联删除 ReAct 日志，第 26 节） |
| POST | `/api/v1/tasks/{task_id}/resume` | 恢复暂停/失败任务：从最近 checkpoint 断点续跑（completed 返回 400，第 26 节） |
| GET | `/api/v1/tasks/{task_id}/report` | 任务报告：最终报告 Markdown + 执行摘要（总耗时 / ReAct 次数 / 记忆命中，第 27 节） |
| POST | `/api/v1/evaluation/run` | 触发自动化评测：后台批量执行 10 个用例，立即返回 eval_id（并发保护，第 27 节） |
| GET | `/api/v1/evaluation/reports` | 历史评测报告列表（分页，第 27 节） |
| GET | `/api/v1/evaluation/reports/{eval_id}` | 评测报告详情：执行中返回进度 / 完成后返回结果 + 指标 + Markdown（第 27 节） |
| DELETE | `/api/v1/evaluation/reports/{eval_id}` | 删除历史评测报告（运行中返回 400；不存在返回 404，第 27 节） |
| GET | `/api/v1/knowledge/documents` | RAG 知识库文档列表（按 分类+source 聚合，第 26 节） |
| POST | `/api/v1/knowledge/documents` | 上传文档入库（multipart：file + category=template/terminology/upload，第 26 节） |
| GET | `/api/v1/knowledge/document?source=&category=` | 文档详情：返回该文件全部 chunk（第 26 节） |
| DELETE | `/api/v1/knowledge/document?source=&category=` | 删除文档（按 分类+source 清全部 chunk，第 26 节） |
| POST | `/api/v1/knowledge/search` | RAG 语义检索（query + k + 可选 category，第 26 节） |
| GET | `/api/v1/memory/search` | 长期记忆检索（历史报告，query + k，第 26 节） |
| GET | `/api/v1/memory/status` | 长期记忆开关状态 + 报告数（第 26 节） |
| POST | `/api/v1/memory/toggle` | 开启/关闭长期记忆（逻辑开关，不删数据，第 26 节） |
| GET | `/api/v1/health` | 健康检查（含 MCP Server 状态） |

## 验证清单（对应本节可运行标准）

### 第 27 节验证清单（全栈评测 + 前端最终联调）

- [x] 自动化评测引擎：10 个固定测试用例（覆盖储能 / 消费电子 / 出行 / 新能源等行业，每题附带预期关键词列表），逐个调用 `workflow.run_task` 批量执行（`backend/evaluation/runner.py`；**当前仅启用第 1 个用例，其余注释待恢复**）
- [x] 五维指标体系：任务成功率（目标 ≥90%）/ 平均耗时（≤120s）/ P95 耗时 / 平均 ReAct 循环次数（≤8 次）/ 关键词覆盖率（≥70%）/ 记忆命中率（≥30%）（`evaluation/metrics.py`，含达标判定）
- [x] 评测报告持久化：`data.db` 新增 `evaluation_reports` 表（`db/evaluation_repository.py`），评测执行中可轮询进度（completed_cases），完成后统一落 JSON 结果 + 指标 + Markdown 总结；**后端重启自动把中断遗留的 running 评测置为 failed**（`fail_running_interrupted`）
- [x] 评测 API：`POST /evaluation/run`（立即返回 eval_id，后台执行，运行中重复触发返回 400）/ `GET /evaluation/reports`（历史列表，分页）/ `GET /evaluation/reports/{id}`（执行中进度或完成结果）
- [x] 报告 API：`GET /tasks/{id}/report`（最终报告 Markdown + 执行摘要：总耗时 / ReAct 行动次数 / 记忆命中数；未完成任务返回 404）
- [x] 前端「评测中心」页（Evaluation.vue，路由 `/evaluation`）：运行评测 → 进度条（2s 轮询）→ 六张指标卡（实测 vs 目标 + 达标标签）+ ECharts 五维雷达图 + 用例明细表 + Markdown 报告 + 历史评测对比 + 「删除」历史评测（确认弹窗，运行中禁用）
- [x] 报告中心搜索/排序：`GET /tasks` 新增 `keyword`（主题模糊搜索）+ `order`（时间排序 desc/asc，非法值 422），`db/task_repository.list_tasks` 参数化 LIKE 防注入
- [x] 前端「报告中心」页（Reports.vue，路由 `/reports`，顶导航 TAB）：已生成报告列表（主题 / 任务 ID / 生成时间 / 报告耗时）+ **主题搜索框 + 时间排序下拉** + 分页 + 「查看」（跳转报告展示页 `/report/:taskId`）+ 「删除」（级联日志带确认）
- [x] 前端「报告展示」页（ReportView.vue，路由 `/report/:taskId`）：Markdown 富文本渲染 + 执行摘要卡 + 导出 Word / PDF；返回按钮回「报告中心」
- [x] 一键启动：`start.bat`（Windows）/ `start.sh`（Linux/Mac）
- [x] 后端新增测试通过（`tests/test_evaluation.py` + `tests/test_evaluation_api.py` 共 20 项，含评测遗留清理 / 报告中心搜索排序用例）；前端 `vue-tsc --noEmit` / `npm run build` 通过

- [x] 后端 FastAPI 服务启动成功（`http://localhost:8002`）
- [x] 前端 Vue3 开发服务器启动成功（`http://localhost:5174`）
- [x] 单智能体对接大模型（OpenAI 兼容接口，`.env` 读取配置）
- [x] 内置工具 `current_time` / `calculator`（Function Calling，可开关）
- [x] MCP 工具 `web_search`（FastMCP Server + 官方 ClientSession，stdio 自动拉起）
- [x] MCP 自定义添加 / 编辑 / 删除 / 开关（Streamable HTTP / HTTP + SSE，如 12306 / Fetch 已实测）
- [x] MCP 添加/编辑时 transport 字段校验（仅 http / sse），连接失败时返回 `last_error`，前端友好提示"已保存，但连接失败"
- [x] 提示词触发工具调用闭环（需配置真实 API Key）
- [x] 前端「AI 对话」页展示工具调用卡片、「工具监控」页双 Tab 管理内置与 MCP 工具
- [x] 技能抽象层：BaseSkill / SkillInput / SkillOutput / SkillRegistry（含内置禁删 / 禁改）
- [x] 内置 4 个 mock 技能（搜索 / 分析 / 写作 / 审核）启动时自动注册
- [x] 自定义技能表单创建 / 编辑 / 删除（持久化为 `skills_pool/<name>/skill.md`）
- [x] `.zip` 技能包导入（校验路径穿越与 2MB 大小上限；支持 skill.py 动态加载）
- [x] 技能试运行：内置 mock 直接返回；自定义技能按 skill.md 调用 LLM
- [x] 前端「技能中心」页：卡片网格 + 新增 / 编辑 / 删除 / 导入 / 试运行

### 第 26 节验证清单（智能体记忆：RAG 知识库 + 长期/短期记忆）

- [x] ChromaDB 双集合落地：`rag_collection`（模板 / 术语 / 上传）+ `memory_collection`（历史报告），SiliconFlow bge-m3 向量化 + md5 稳定 ID 去重，持久化于 `backend/data/chroma_db`
- [x] Seed 幂等：启动自动入库 5 份模板 + 30 条术语（只补只插不覆盖，`data/templates/` + `data/terminologies.txt`）
- [x] 知识库 API 闭环：文档列表（分类筛选）/ 上传（txt/md/docx/pdf/xlsx + 分类）/ 查看 chunk 详情 / 删除 / RAG 语义检索
- [x] Planner 注入模板 Few-shot + 长期记忆召回（`memory_hits` 落库，TaskDetail「长期记忆命中」卡片展示）
- [x] Writer 注入 RAG 术语（新增「RAG 检索到 N 条相关术语」Thought 日志）；任务成功自动 `remember()`
- [x] 长期记忆开关：`GET /memory/status` + `POST /memory/toggle`（逻辑开关，关闭暂停读写、不删数据，重新开启恢复）
- [x] 短期记忆 Checkpointer：SqliteSaver 节点快照落 `backend/checkpoints.db`；进程中断遗留 running 任务重启自动标记「已暂停」（paused），`POST /tasks/{id}/resume` 断点续跑（completed 返回 400）
- [x] 任务删除：`DELETE /tasks/{id}` 级联 ReAct 日志，列表/详情带确认弹窗
- [x] 前端知识库页（`/knowledge`）与管理增强：分类统计 + 记忆开关、列表筛选、上传、查看/删除、恢复按钮仅"已暂停"展示
- [x] 后端全量 pytest **312** 项通过；前端 `vue-tsc --noEmit` / `npm run build` 通过（新增 `test_rag.py` / `test_memory.py` / `test_agent_rag_memory.py` / `test_knowledge_api.py` / checkpointer-paused 用例）

### 第 25 节验证清单（A2A 审核循环 + 工程容错）

- [x] A2A 图跑通：`Planner→Scheduler→Reviewer→（通过→END / 打回→Rewriter→Reviewer）`，`route_after_review` 条件边驱动（实测 task 完整走完 3 次审核、2 次返工后通过）
- [x] Reviewer 按 3 条标准评审（≥2 数据点 / 引用来源 / 字数≥1000），输出结构化 `{passed, comments}`，非 JSON / 代码块 / 多余文字均容错解析，LLM 失败放行
- [x] Rewriter 注入研究主题 + 数据摘要覆盖式重写，严禁更换/编造主题（实测修复"报告被重写成无关主题"）
- [x] 循环上限默认 3 次：前 2 次打回返工、第 3 次仍不过强制通过并追加 ⚠️ 标记（`tests/test_reviewer.py` / `test_workflow.py` 覆盖）
- [x] `review_history` 按轮落库（tasks 新列 + _MIGRATIONS 幂等迁移，旧库自动补列）；`GET /tasks/{id}/status` 返回各轮意见与 `max_iterations`；`review_comments` 兼容保留
- [x] Reviewer 的 Observation 日志携带本轮意见原文，与详情页「第 N 次审核」意见分组一一对应
- [x] MCP 调用超时 5s + 重试 2 次；Researcher 单步 30s 超时跳过（降级解锁后续）；Writer 撰写整稿放宽 120s
- [x] 前端 TaskDetail：A2A 结果卡片分轮展示意见 / 执行计划「A2A 审核循环」节点 / 日志流按时间序分节（🔍审核 · ✏️改写返工）
- [x] 全量测试通过（新增 `test_reviewer.py` / `test_rewriter.py`，扩展 mcp_client / single_agent / scheduler / workflow 用例，>260 项）

### 第 24 节验证清单

- [x] LangGraph 工作流跑通 `Planner→Scheduler→ReAct Researcher→Writer`（线性图 `START→Planner→Scheduler→END`）
- [x] Planner 容错解析 + 降级计划；Scheduler 按 `depends_on` 派发；Researcher 最多 3 轮 ReAct；Writer 生成草稿
- [x] SQLite 持久化：任务与 ReAct 日志落库（`tasks` / `task_logs` 表），重启后端数据不丢
- [x] `POST /generate` 异步提交任务；`GET /tasks` 分页 + 状态过滤；`GET /tasks/{id}/status` 返回 Plan 进度 + 日志
- [x] 前端「任务提交」页（Home.vue）：输入主题提交并跳转详情
- [x] 前端「任务列表」页（Tasks.vue）：状态 Tab + 分页 + 查看按钮入口
- [x] 前端「任务详情」页（TaskDetail.vue）：Plan 看板 + ReAct 日志流（2s 轮询）+ 报告草稿富文本展示 + 导出 Word / PDF
- [x] 新增测试通过（`test_task_repository.py` / `test_plan_and_execute.py` / `test_workflow.py` / `test_tasks_api.py`，共 36 项）
