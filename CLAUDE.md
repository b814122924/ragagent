# CLAUDE.md — 项目宪法（SmartBrief / proj05）

> 本文件是本项目（`c:\Users\13691\Documents\Code\260601-GPKJ\05_multi-agent\proj05`）的最高约定文档。
> **每次进入本项目的会话，都必须先读取本文件，并优先于其他常规约定遵守。**
> 文件内容随项目演进保持更新。

## 项目概述

多智能体协作开发课程项目（proj05）。当前迭代：**第 27 节《全栈评测与最终交付》**，代码位于 `smartbrief/` 子项目（代号 SmartBrief）。**项目完结（v27.0）**。

## 当前里程碑（v27.0）——自动化评测体系与全栈最终交付

在 v26（RAG 知识库 + 智能体记忆）之上，本迭代新增**评测引擎**与**前端最终联调**，形成"可运行、可演示、可评测"的完整全栈应用。

- **评测引擎（`backend/evaluation/`）**
  - `metrics.py`：五维指标体系（纯计算，无依赖，便于单测）——任务成功率（≥90%）/ 平均耗时（≤120s，失败用例不计）/ P95 耗时 / 平均 ReAct 循环次数（≤8 次，= Action 日志条数）/ 关键词覆盖率（≥70%，报告全文子串匹配）/ 记忆命中率（≥30%，有 memory_hits 的任务占比）；`compute_metrics` 返回 `{summary, targets, met}`；`build_markdown` 生成含指标表 + 用例明细表的 Markdown 报告
  - `runner.py`：**10 个标准测试用例**（`TEST_CASES`，行业对齐 `data/templates/`：储能×2 / 消费电子×3 / 智能家居 / 出行 / 新能源 / 工业 / 个护，每个附带预期关键词列表。**当前仅启用第 1 个用例（快速验证链路），其余 9 个已注释、按需恢复**）；`start_evaluation()` 同步返回 eval_id + `asyncio.create_task(_execute)` 后台执行（**运行时并发锁 `_running`，运行中重复触发抛 RuntimeError → API 400**）；单用例异常被 `_run_single_case` 捕获计入失败（不中断整轮），整体层异常才置 failed；每完成一个用例 `set_progress` 更新进度
- **评测持久化（`db/evaluation_repository.py` + `data.db` 的 `evaluation_reports` 表）**：create（running）/ set_progress / finish（completed + results/metrics/report_md）/ fail；**`fail_running_interrupted`：后端启动（main.py lifespan）把遗留 running 评测置为 failed**（与任务侧 paused 归位同理，防评测中心进度条卡死、按钮禁用）；结构化字段 results/metrics 以 JSON 存取；列表接口不返回大文本（详情单查）
- **评测 API**：`POST /evaluation/run`（返回 `{eval_id, status, total_cases}`）、`GET /evaluation/reports`（分页列表）、`GET /evaluation/reports/{id}`（执行中返回进度，完成返回结果）、`DELETE /evaluation/reports/{id}`（删历史评测；**运行中返回 400**，否则后台任务仍写进度、前端轮询 404 会造成混乱）
- **报告展示 API**：`GET /tasks/{id}/report` —— 最终报告 Markdown + `executive_summary {total_time（created_at→updated_at）, react_loops, memory_hit_count}`；未完成任务 / 任务不存在返回 404
- **前端**：新增「评测中心」（Evaluation.vue，路由 `/evaluation`：运行评测 → 进度条 2s 轮询 → 六张指标卡实测 vs 目标 + 达标标签 → **ECharts 五维雷达图**（成功率/关键词覆盖率/记忆命中率/耗时达标分/循环达标分，归一化 0~100）→ 用例明细表 → Markdown 报告 → 历史评测对比 + **历史评测「删除」**（确认弹窗，运行中禁用、后端 400））、「报告中心」（Reports.vue，路由 `/reports`，**顶导航 TAB**：已完成任务 = 已生成报告列表，主题/任务 ID/生成时间/报告耗时 + **主题搜索框（`keyword` 模糊匹配）+ 时间排序下拉（`order=desc|asc`）** + 分页 + 「查看」跳转 `/report/:taskId` + 「删除」级联日志带确认）与「报告展示」（ReportView.vue，路由 `/report/:taskId`：执行摘要卡 + Markdown 富文本 + 导出 Word/PDF，**返回按钮回「报告中心」**）；报告入口一律走「报告中心」列表，任务详情页不设报告按钮；App 菜单新增「评测中心」「报告中心」；`api/evaluation.ts` + `tasks.ts` 新增 `fetchTaskReport` + fetchTasks 扩展 `keyword/order` 参数（`GET /tasks` 后端新增两参数，`list_tasks` 参数化 LIKE 防注入）；前端新增依赖 **echarts**
- **一键启动**：`start.bat`（Windows：后端独立窗口 + 前端前台）/ `start.sh`（Linux/Mac：后端后台 + trap 回收）
- **容器化部署（`deploy/`，按需扩展，含云服务器版）**：Docker Compose 二镜像编排（后端 + nginx 前端）；构建上下文=仓库根（`.dockerignore` 在根目录）；后端镜像保持 `backend/` 与 `mcp_servers/` 平级（MCP 子进程按 parents[2] 相对路径拉起）；`entrypoint.sh` 首启把 RAG seed 复制进空卷（`cp -n` 幂等，卷 `smartbrief_backend_data` 挂 `/app/backend/data`）；nginx 反代 `/api` → backend:8002 + SPA 回退；配置一律走 `deploy/.env`（镜像内无密钥）；`data.db`/`checkpoints.db`/`*_config.json` 在容器可写层（重建容器重置，README 提供 bind 方案）；**云服务器部署**：`export-images.sh/.bat`（docker save 打包）→ `deploy-to-server.sh/.bat <user@host>`（scp 上传 + 云端 docker load + `docker-compose.prod.yml`（无 build）up -d；本地 deploy/.env 存在则一并上传，缺失则云端生成示例并提示编辑）
- **测试**：新增 `tests/test_evaluation.py`（指标/仓储/runner，runner 打桩 `workflow.run_task` 且场景包在同一 `asyncio.run` 内等待后台任务落库）+ `tests/test_evaluation_api.py`（三个 API + report 接口 + `fail_running_interrupted`/lifespan 清理用例，`start_evaluation` 打桩避免 create_task 未等待告警）；报告中心搜索排序新增仓储层 + API 层用例（见 `test_task_repository.py` / `test_tasks_api.py`）；后续任务保持后端全量 pytest 通过 + 前端 `vue-tsc --noEmit` / `npm run build` 通过
- **版本**：`main.py` version=27.0.0；`package.json` version=0.27.0

### 上一里程碑（v26.0）——智能体记忆（RAG 知识库 + 长期 / 短期记忆）

在 v25（A2A 审核循环）之上，本迭代为智能体注入“记忆”能力：RAG 知识库 + 长期记忆（历史报告）+ 短期记忆（Checkpointer 断点续跑）。

- **RAG 知识库（复用 zhiqida-rag 实现）**：新增 `backend/rag/` 包 —— `embeddings.py`（SiliconFlow bge-m3，`.env` 读取 `EMBEDDING_*`）、`loaders.py`（txt/md/docx/pdf/xlsx）、`chunkers.py`（RecursiveChunker）、`vectorstores.py`（ChromaVectorStore，**md5 稳定 ID** 去重）、`store.py`（双集合门面 + seed）
  - ChromaDB 双集合：`rag_collection`（模板 5 份 + 术语 30 条 + 用户上传）+ `memory_collection`（历史报告），持久化于 `backend/data/chroma_db`
  - 文档分类与文案统一为 **模板 / 术语 / 文档**（`category = template | terminology | upload`），三类均可上传入库、列表筛选、查看 chunk 详情与删除
  - Planner 规划前检索**模板**类做结构 Few-shot（`_build_few_shot` 合并模板命中）
  - Writer 撰写时 `_retrieve_terms()` 检索相关术语注入 prompt（`search_rag_terms`），并在日志流新增一条 `Thought` 日志「RAG 检索到 N 条相关术语：…」（无命中提示未找到）
  - 预置数据：`data/templates/template_1..5_*.md`（5 份模板）+ `data/terminologies.txt`（30 条术语，main.py lifespan 幂等 seed，只补只插不覆盖）
- **长期记忆 + 运行时开关**：任务成功自动 `remember()` 写入（`memory_collection`，md5 去重）；Planner 生成 Plan 前 `recall()` 检索相似历史报告做 Few-shot，命中写入 `state.memory_hits` 并随任务落库（`tasks.memory_hits` 列，status API 返回，前端 TaskDetail「长期记忆命中」卡片展示）。知识库页提供 `GET /memory/status` + `POST /memory/toggle` 运行时开关 —— **逻辑开关而非删除**：关闭后 remember/recall 短路，已存数据原样保留，重新开启即恢复可用
- **短期记忆 / 断点续跑 + paused 状态**：`backend/memory/checkpointer.py` —— LangGraph Checkpointer（`task_id` 即 `thread_id`）。已装 `langgraph-checkpoint-sqlite`（v3.1.1+ API 变更：`from_conn_string` 返回**连接生命周期管理器**，须经 `open_checkpointer()` 后 `async with` 持有连接再 compile/invoke；任何打开失败自动降级进程内 MemorySaver 单例）
  - **意外中断 → paused**：进程崩溃/重启遗留的 running 任务，由 main.py lifespan 启动扫描自动标记 `paused`（`mark_interrupted_tasks_as_paused`）
  - `POST /tasks/{id}/resume` 调 `workflow.run_task(resume=True)`：有 checkpoint 快照则从断点续跑，无快照自动从头重跑兜底；resume 仅对 `paused`/`failed` 生效，`completed` 返回 400
- **任务删除**：`DELETE /tasks/{id}` 级联删除任务与 ReAct 日志（列表/详情「删除」带确认弹窗）
- **知识库管理页（KnowledgeBase.vue，路由 `/knowledge`）**：分类统计卡（模板/术语/文档）+ 长期记忆开关与报告数、文档列表（分类筛选：全部/模板/术语/文档）、上传（分类单选 模板/术语/文档，支持 txt/md/docx/pdf/xlsx）、「查看」chunk 弹窗（含元数据）、「删除」、RAG 检索测试
- **API**：`GET/POST /knowledge/documents`、`GET/DELETE /knowledge/document`、`POST /knowledge/search`、`GET /memory/search`、`GET /memory/status`、`POST /memory/toggle`、`DELETE /tasks/{id}`、`POST /tasks/{id}/resume`
- **前端**：新增知识库页与 `api/knowledge.ts`；App 菜单新增「知识库」；TaskDetail「长期记忆命中」卡片 + 「恢复执行」仅 paused 展示；任务列表/详情操作随状态收敛（运行中/已完成不显示恢复）
- **测试**：新增 `tests/test_rag.py` / `test_memory.py` / `test_agent_rag_memory.py` / `test_knowledge_api.py` + checkpointer/resume/paused 用例（autouse 关嵌入 Key + tmp_path 隔离）；后端全量 pytest **312** 项通过，前端 `vue-tsc --noEmit` / `npm run build` 通过

### 历史里程碑（v25.0）——A2A 审核循环与工程容错

在 v24（多智能体 Plan-and-Execute）之上，本迭代新增 **Agent-to-Agent（A2A）审核循环**、**工程容错加固**，并升级前端任务详情展示。

- **A2A 审核循环（核心）**
  - 图结构由线性升级为条件分支：`START → Planner → Scheduler → Reviewer →（通过 → END / 打回 → Rewriter → Reviewer）`，由 `route_after_review` 条件边驱动循环
  - 新增 `agents/reviewer.py`（质量评审：3 条标准 = ①≥2 个具体数据点 ②引用信息来源 ③正文字数≥1000；输出 `{passed, comments}` JSON 容错解析）与 `agents/rewriter.py`（覆盖式重写：prompt 注入**研究主题 + 研究数据摘要**，严禁更换/编造主题）
  - **循环上限 `max_iterations = 3`**（默认并随任务落库）：前 2 次打回返工，第 3 次仍不过则**强制通过**，草稿末尾追加 `> ⚠️ 部分章节未通过校验（已强制输出）`
  - **多轮审核历史 `review_history`**：每轮审核追加 `{round, passed, comments}`（`round = iteration + 1`，与 ReAct 日志「审核 · 第 N 次」小节一一对应），`tasks` 表独立列持久化；`review_comments` 保留为"最后一轮意见"兼容旧字段
  - Reviewer 的 Observation 日志携带**本轮意见原文**；`iteration / max_iterations / passed / forced_pass` 均随任务落库并由 `GET /tasks/{id}/status` 返回
- **工程容错（单点失败不拖垮工作流）**
  - MCP 工具调用：单次超时 5s（`MCP_CALL_TIMEOUT_SECONDS`）+ 失败重试 2 次（`MCP_CALL_RETRIES`）；Server 连接超时 `CONNECT_TIMEOUT_SECONDS = 8`（前端"已保存但连接失败"提示的配套）
  - Scheduler 步骤超时跳过：Researcher 单步 30s（`AGENT_STEP_TIMEOUT_SECONDS`）；**Writer 撰写整稿单独放宽 120s（`WRITER_STEP_TIMEOUT_SECONDS`）**，避免整稿被 30s 误杀成占位草稿
  - 修复：Rewriter 锚定主题与研究数据（杜绝"草稿被重写成无关主题"）；超时步骤降级并解锁后续依赖，不阻塞工作流
- **技能注入双通道（single_agent 联动技能池）**：通道一将已启用技能生成的 schema 并入 LLM tools 参数（重名技能排除）；通道二 `_skill_banner()` 把技能名片动态拼入 system prompt
- **前端 TaskDetail 增强**：A2A 结果卡片（按 `review_history` **分轮展示**意见气泡 + 通过/打回/强制标签 + 循环进度文案）、执行计划看板末尾追加「A2A 审核循环」节点、ReAct 日志流按真实时序分节（规划阶段 / 步骤 N / 🔍 A2A 审核·第 N 次 / ✏️ A2A 改写返工）
- **测试**：新增 `tests/test_reviewer.py` / `tests/test_rewriter.py`，扩展 mcp_client / single_agent / scheduler / workflow 用例；全量 pytest 通过（>260 项）

### 历史能力（v23–v24，保留）

- 单智能体对接大模型（OpenAI 兼容接口），通过自然语言提示词触发工具调用
- 内置工具（Function Calling）：`current_time` / `calculator`
- MCP 工具：`web_search`（JSON-RPC 2.0 over stdio，独立子进程）
- 技能池（Skills）：技能（Skill）是比工具更高一层的能力单元
  - 抽象层：`BaseSkill` / `SkillInput` / `SkillOutput` / `SkillRegistry`
  - 内置 4 个 mock 技能（search / analysis / writing / review），**只读（不可删除/修改），支持开关**
  - 自定义技能：表单创建（持久化为 `skills_pool/<name>/skill.md`）、可选 `skill.py` 动态加载、`.zip` 技能包导入（校验路径穿越与大小）
  - **技能开关**：内置/自定义均支持开关（`PUT /skills/{name}/enabled`），开关状态统一持久化到 `backend/skill_config.json`（与 `tool_config.json` 模式一致，不写入 skill.md）；禁用的技能不可试运行，AI 对话 `/` 与 `+ 技能` 自动过滤
- **多智能体编排（第 24 节）**：基于 LangGraph 的 Plan-and-Execute + ReAct
  - `planner.py`（Planner 生成 Plan）、`scheduler.py`（按依赖派发）、`react_researcher.py` / `react_writer.py`（ReAct 循环）
  - 工作流：`graph/workflow.py`（v24 为线性 `START→Planner→Scheduler→END`；**v25 已升级为带 Reviewer 条件边 + Rewriter 循环的 A2A 图**，`run_task()` 落库）
  - **SQLite 业务持久化**（`backend/db/` + `backend/data.db`）：`tasks` / `task_logs` 表，任务与 ReAct 日志落库，重启不丢
  - **任务系统**：`POST /generate` 提交任务 → `GET /tasks` 列表 → `GET /tasks/{id}/status` 状态轮询
- 前端：任务提交页（Home.vue）+ 任务列表页（Tasks.vue）+ 任务详情页（TaskDetail.vue，Plan 看板 + ReAct 日志流 + 长期记忆命中 + A2A 审核 + 断点续跑 + 报告草稿富文本展示/导出 Word/PDF）+ 知识库页（KnowledgeBase.vue）+ AI 对话页（Chat.vue）+ 工具监控页（ToolMonitor.vue）+ 技能中心页（SkillCenter.vue）

## 技术栈

- 后端：Python 3.10+ / FastAPI / OpenAI SDK / python-dotenv / **LangChain ≥ 1.0（严禁 1.0 之前版本）** / **LangGraph（多智能体编排）** / **ChromaDB + SiliconFlow bge-m3（RAG 向量库，第 26 节）** / **langgraph-checkpoint-sqlite（短期记忆 Checkpointer，已安装，v3.x 需 `async with` 打开连接）**
- 前端：Vue 3 + Vite + TypeScript + Element Plus + Axios + Vue Router（报告渲染：marked + DOMPurify；PDF 导出：html2pdf.js；雷达图：**ECharts**，第 27 节）
- MCP：
  - Server 端：官方 **FastMCP**（`mcp_servers/web_search_server.py`，stdio 传输）
  - Client 端：官方 `mcp` SDK 的 **ClientSession**（`backend/mcp_client/mcp_client.py`）
    - 传输方式由 Server 的 `kind` / `transport` 字段决定：`stdio`（内置 Server 子进程）、`http`（Streamable HTTP，如 ModelScope 12306）、`sse`（HTTP+SSE 旧版，如 ModelScope Fetch）
    - FastMCP 只提供 Server 能力，Client 必须使用官方 SDK，二者分工明确

## 关键约定（必须遵守）

1. **API 密钥配置**：一律在 `backend/.env` 中配置（`OPENAI_BASE_URL` / `OPENAI_API_KEY` / `OPENAI_MODEL`），代码通过 `python-dotenv` 读取，禁止硬编码密钥。
2. **端口规范**：后端 `8002`，前端 `5174`（如被占用，调整后需同步更新 Vite 代理）。
3. **前后端分离开发**：新功能先搭骨架（类型 / API 封装 / 路由 / 组件签名），再补具体逻辑与演示数据。
4. **不用 .venv**：后端依赖直接安装到全局 Python 环境（当前为 C:\Python313），启动前执行 `pip install -r requirements.txt`。
5. **服务启动**：后端 `uvicorn main:app --port 8002`（自动拉起 MCP Server）；前端 `npm run dev`。
6. **语言**：代码注释、文档、对话一律使用中文。
7. **LangChain / LangGraph 版本（第 24 节强约束）**：`langchain>=1.0.0`、`langchain-core>=1.0.0`、`langgraph>=1.0.0`，**严禁使用 1.0 之前的 langchain**；升级依赖后必须重新运行 `pytest tests/` 确认不回归。
8. **SQLite 职责边界（第 24 节）**：
   - `backend/data.db`（`db/database.py` + `db/task_repository.py`）：**业务数据**（任务 / ReAct 日志），由 `task_repository` 显式写入，`task_id` 作主键。
   - `checkpoints.db`：第 26 节 LangGraph Checkpointer 的**图运行时状态**，框架自动写入，二者互不干扰。
   - 结构化字段（plan / completed_steps / research_data）以 JSON 文本存取，序列化封装在 `task_repository` 内，业务层无感知。
   - `run_task()` 不负责创建任务初始记录（由 API 层 `create_task` 负责），只执行图 + 最终落库；ReAct 日志经 `_persist_logs()` 批量写入 `task_logs`。
9. **技能（Skills）约定（第 23 节）**：
   - 内置技能只读：`PUT /skills/{name}`、`DELETE /skills/{name}` 对 builtin 技能返回 400「内置技能不可修改/删除」。
   - 自定义技能持久化到 `backend/skills_pool/<name>/`，`skill.md`（frontmatter + 正文）必需，`skill.py`（BaseSkill 子类）可选。
   - zip 导入必须校验路径穿越与解压大小（上限 2MB），顶层目录或根目录需存在 `skill.md`。
   - 技能名规则：`^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$`；分类限 `search|analysis|writing|review`。
   - **技能开关**：`PUT /skills/{name}/enabled`（内置/自定义均可）；开关状态统一持久化到 `backend/skill_config.json`（不写入 skill.md，`init()` 时加载应用）；`run_skill` 对被禁用技能抛 400「技能已禁用」，AI 对话前端过滤禁用技能。
10. **MCP（第 22 节）约定**：
    - 添加/编辑 MCP Server 请求含 `transport` 字段，限 `http` / `sse`（请求模型层校验，非法返回 422）。
    - 连接阶段有超时保护（`CONNECT_TIMEOUT_SECONDS = 8`），失败时记录 `last_error` 但配置仍保存；前端提示「已保存，但连接失败」而非误报失败。
    - Server id 用 `uuid4().hex[:8]` 生成，禁止用基于列表长度的递增 id（删除后再添加会静默覆盖已有 Server）。
11. **测试要求（必须遵守）**：
    - 每个模块必须有对应的 `test_<module>.py` 测试文件（测试位于 `backend/tests/`）。
    - 运行命令：`pytest tests/ -v`。
    - 覆盖率要求：**核心模块覆盖率 100%，整体 ≥ 80%**（使用 pytest-cov，命令 `pytest tests/ -v --cov=agents --cov=llm --cov=tools --cov=mcp_client --cov=api --cov=skills --cov=mcp_servers --cov=db --cov=graph --cov-report=term-missing`）。
    - 新增/修改功能后必须补充或更新对应测试，保证覆盖率不下降。
    - 运行测试时设置 `PYTHONDONTWRITEBYTECODE=1` 并将输出重定向到文件读取，避免沙箱 pycache 报错淹没结果。
12. **A2A 审核循环约定（第 25 节）**：
    - 强制通过阈值：审核不通过且 `iteration >= max_iterations` 时改为强制通过（默认 `max_iterations = 3`，落库透传给前端），草稿追加 ⚠️ 警告标记。
    - 每轮审核必须向 `review_history` **追加**记录 `{round, passed, comments}`（`round = iteration + 1`），严禁覆盖历史；`review_comments` 始终保存"最后一轮意见"。
    - 新增结构化落库字段必须同步五处：`db/database.py` 建表列 + `_MIGRATIONS` 幂等 ALTER + `task_repository` 的 `_JSON_FIELDS`/`_ALLOWED_UPDATE`/反序列化 + `workflow.run_task` 落库 + 前端类型，缺一不可。
    - Reviewer 评审标准写在 `agents/reviewer.py` 的 `SYSTEM_PROMPT`（3 条）；调整评审规则只改这一处。
    - Reviewer/对草稿的审核意见需同时出现在 Observation 日志（便于详情页与卡片分轮对应）。
13. **步骤超时约定（第 25 节）**：Researcher 单步 30s（超时降级跳过）；Writer 撰写整稿 120s；新增长耗时 Agent 步骤时应按角色配置独立超时常量，不要复用 Researcher 的 30s。
14. **智能体记忆约定（第 26 节）**：
    - 文档分类限 `template | terminology | upload`，展示文案统一「模板 / 术语 / 文档」；上传文档默认 `upload`。预置 seed 只补只插（`skipped` 返回计数），严禁覆盖用户已删除的预置文档。
    - **长期记忆开关是逻辑开关**：关闭只让 `remember/recall` 短路，严禁删除 `memory_collection` 已有数据；新增影响记忆的功能需同步 `/memory/status` 计数口径（关闭时不查库、计数归 0）。
    - Checkpointer：`langgraph-checkpoint-sqlite` ≥3.x 的 `from_conn_string()` 返回**连接生命周期管理器**，compile/invoke 前必须 `async with`（见 `open_checkpointer`）；任何打开失败都必须降级进程内 MemorySaver，严禁因此让任务不可执行。重启会触发 lifespan 把遗留 running 任务标记为 paused，属预期行为。
    - 任务状态机：`running → completed | failed`；进程启动发现遗留 `running` 一律标记 `paused`（`mark_interrupted_tasks_as_paused`）；`resume` 仅对 `paused`/`failed` 生效，`completed` 返回 400；前端「恢复」按钮仅 `paused` 展示（运行中/已完成不显示）。
    - `memory_hits` 是第 26 节新增结构化落库字段，遵循第 12 条「五处同步」约定（`database._MIGRATIONS` / `task_repository._JSON_FIELDS` + `_ALLOWED_UPDATE` + 反序列化 / `workflow.run_task` 落库 / 前端类型）。
15. **评测与报告中心约定（第 27 节）**：
    - 评测用例固定 10 个（`evaluation/runner.py` 的 `TEST_CASES`），每个含 `topic` + `keywords`；主题刻意对齐 `data/templates/` 行业，保证模板 Few-shot / 术语注入可被观测。**当前仅启用第 1 个用例（快速验证链路），其余 9 个已注释**——恢复用例只需取消注释，切勿改动 `case_count()` / `_execute` 对 `len(TEST_CASES)` 的动态引用；测试中 `total_cases` 一律动态取 `runner.case_count()`，禁止硬编码 10。
    - **并发保护**：`runner._running` 运行时标志（`start_evaluation` 内检查置位），重复触发抛 `RuntimeError`，API 层转 400；测试用 autouse fixture 复位。
    - **失败口径**：单用例异常在 `_run_single_case` 内捕获（计入失败用例、成功率分母），仅整体执行层异常（如进度落库失败）由 `_execute` 捕获 → `evaluation_repository.fail`。
    - **评测记录生命周期**：`evaluation_reports` 表（`data.db`，建表 SQL 在 `database._SCHEMA`，与 tasks 同库）；create（running）→ set_progress 逐用例更新 → finish（completed + results/metrics/report_md）→ **delete（删除整行，无子表级联；运行中禁删 400）**；结构化字段 results/metrics 以 JSON 存取（`db/evaluation_repository.py` 白名单 `_ALLOWED_UPDATE` 同上），列表接口不返回大文本。
    - **中断收尾（与任务 paused 归位对称）**：进程重启遗留的 running 评测由 main.py lifespan 调 `evaluation_repository.fail_running_interrupted()` 统一置 failed（否则评测中心进度条卡死、「运行评测」禁用）；测试：仓储幂等用例 + TestClient lifespan 用例（后者必须临时重定向 MCP/工具配置，避免拉起真实子进程）。
    - **指标口径固定**（`evaluation/metrics.py`，改动需同步 `TARGETS` 与前端卡片/雷达图）：成功率=成功数/总任务数；平均耗时仅计成功任务；ReAct 次数=Action 日志条数；关键词覆盖率=按预期关键词对报告全文子串匹配（大小写不敏感）；记忆命中率=有 memory_hits 的任务占比。雷达图把耗时/循环归一化到 0~100 达标分。
    - **报告接口**：`GET /tasks/{id}/report` 仅 completed 任务返回（否则 404）；`executive_summary.total_time` 由 `created_at`→`updated_at` 解析（解析失败返回 null，前端显示 —）。
    - **报告中心数据源（`GET /tasks` 扩展）**：`list_tasks` 新增 `keyword`（topic LIKE %kw%，参数化占位防注入，可与 status 叠加）+ `order`（`desc`/`asc`，时间排序，非法值由 API 层 pattern 校验返回 422）；前端 Reports.vue 搜索框/排序下拉切换后回第 1 页。

## 目录结构

```text
smartbrief/
├── backend/
│   ├── agents/
│   │   ├── single_agent.py      # 单智能体：Function Calling 循环
│   │   ├── planner.py           # Planner（第 24 节）：生成 Plan（2-5 步 JSON，容错解析 + 降级计划）
│   │   ├── scheduler.py         # Scheduler（第 24/25 节）：按 depends_on 派发 + 单 Agent 步骤超时跳过（Researcher 30s / Writer 120s）
│   │   ├── react_researcher.py  # ReAct Researcher（第 24 节）：Thought→Action(web_search)→Observation
│   │   ├── react_writer.py      # ReAct Writer（第 24 节）：Thought→Action(llm_gen)→Observation
│   │   ├── reviewer.py          # Reviewer（第 25 节 A2A）：按 3 条标准评审草稿，输出 {passed, comments}，维护 review_history
│   │   └── rewriter.py          # Rewriter（第 25 节 A2A）：注入主题+研究数据，按审核意见覆盖式重写
│   ├── graph/
│   │   ├── state.py             # AgentState(TypedDict)（第 24/25/26 节：A2A 审核字段 + memory_hits）
│   │   └── workflow.py          # LangGraph 工作流 + route_after_review 条件边 + run_task()（第 24/25 节；第 26 节：checkpointer 断点续跑 + remember 长期记忆）
│   ├── memory/                  # 记忆（第 26 节）
│   │   ├── checkpointer.py      #   短期记忆：open_checkpointer（SqliteSaver async with，失败降级 MemorySaver）+ has_checkpoint/list_snapshots
│   │   └── long_term_memory.py  #   长期记忆：remember/recall/search_memory + 运行时开关
│   ├── db/
│   │   ├── database.py          # SQLite 连接管理 + 建表 + _MIGRATIONS 幂等迁移（第 24-27 节：memory_hits 列 + evaluation_reports 表）
│   │   ├── task_repository.py   # 任务/日志 CRUD（第 24-27 节：JSON 字段 + paused 中断标记 + memory_hits + keyword/order 列表查询）
│   │   └── evaluation_repository.py # 评测报告 CRUD（第 27 节：create/set_progress/finish/fail/fail_running_interrupted/get/list）
│   ├── llm/client.py            # OpenAI 兼容接口封装
│   ├── tools/builtin_tools.py   # 内置工具（current_time / calculator）
│   ├── skills/                  # 技能池（第 23 节）
│   │   ├── base_skill.py        #   BaseSkill / SkillInput / SkillOutput
│   │   ├── registry.py          #   SkillRegistry（内置技能禁删/禁改 + set_enabled）
│   │   ├── mock_skills.py       #   4 个内置 mock 技能（只读，可开关）
│   │   └── skills_manager.py    #   生命周期：create/update/delete/import/run/set_enabled
│   ├── skills_pool/             # 自定义技能持久化目录（<name>/skill.md [+skill.py]）
│   ├── skill_config.json        # 技能开关统一持久化（内置 + 自定义）
│   ├── mcp_client/mcp_client.py # MCP Client（官方 SDK ClientSession：stdio + streamable_http + sse）
│   ├── evaluation/              # 评测引擎（第 27 节）
│   │   ├── metrics.py           #   五维指标计算 + 达标判定 + Markdown 报告生成
│   │   └── runner.py            #   10 个标准用例 TEST_CASES（当前仅启用第 1 个）+ start_evaluation/_execute 批量执行（并发锁 + 进度落库）
│   ├── api/routes.py            # /chat、/tools、/skills、/generate、/tasks（delete/resume/report + keyword/order）、/knowledge、/memory、/evaluation、/health
│   ├── rag/                     # RAG 知识库（第 26 节，复用 zhiqida-rag）
│   │   ├── embeddings.py        #   SiliconFlow bge-m3 嵌入（.env 读取 EMBEDDING_*，懒加载）
│   │   ├── loaders.py           #   Document + 策略 Loader（txt/md/docx/pdf/xlsx）
│   │   ├── chunkers.py          #   RecursiveChunker（512 字 + 64 重叠）
│   │   ├── vectorstores.py      #   ChromaVectorStore（cosine + md5 稳定 ID）
│   │   └── store.py             #   DB 门面：双集合缓存 + seed/ingest/list/search/delete/get_document_chunks
│   ├── data.db                  # SQLite 业务库（tasks / task_logs，第 24 节；evaluation_reports，第 27 节）
│   ├── data/chroma_db           # ChromaDB 持久化（rag_collection / memory_collection，第 26 节）
│   ├── data/templates/          # 5 份报告模板 seed（template_1..5_*.md）
│   ├── data/terminologies.txt   # 30 条行业术语 seed
│   ├── checkpoints.db           # LangGraph Checkpointer 短期记忆（第 26 节，SqliteSaver）
│   ├── .env / .env.example      # 含 EMBEDDING_BASE_URL / EMBEDDING_API_KEY / EMBEDDING_MODEL
│   └── main.py                  # 入口（init_db + 工具注册表 + 技能池 + 拉起 MCP Server + seed 知识库 + lifespan 遗留 running→paused / 遗留评测→failed）
├── mcp_servers/web_search_server.py  # 内置 MCP Server（FastMCP，stdio 传输）
├── frontend/                    # Vue3 + TS + Element Plus
│   ├── src/api/                 # chat.ts / tools.ts / skills.ts / tasks.ts（类型 + delete/resume/report）/ knowledge.ts（第 26 节）/ evaluation.ts（第 27 节）
│   └── src/views/               # Home / Tasks / TaskDetail / KnowledgeBase（第 26 节）/ Evaluation / Reports / ReportView（第 27 节）/ Chat / ToolMonitor / SkillCenter
├── start.bat / start.sh         # 本地开发一键启动（第 27 节：Windows / Linux-Mac）
├── deploy/                      # 容器化部署（第 27 节扩展，含云服务器版）
│   ├── docker-compose.yml       # 编排 backend + frontend（nginx 反代 + 健康检查 + 数据卷）
│   ├── docker-compose.prod.yml  # 云端编排：无 build，直接用 docker save/load 上传的镜像
│   ├── .env.example             # 容器环境变量（LLM / 嵌入 Key，本地 backend/.env 不随镜像）
│   ├── start.sh / start.bat     # 本地一键构建启动（纯 ASCII）
│   ├── export-images.sh / .bat  # 只打包：docker save → tar[.gz]（供手动上传）
│   ├── deploy-to-server.sh / .bat # 一键云端部署：构建 → save → scp → ssh load + prod up（.env 自动上传/生成提示）
│   ├── backend/Dockerfile + entrypoint.sh   # 后端镜像；entrypoint 首启把 RAG seed 复制进空卷（cp -n 幂等）
│   └── frontend/Dockerfile + nginx.conf     # 多阶段构建（node → nginx）；/api 反代 backend:8002 + SPA 回退
├── .dockerignore                # 构建上下文排除（node_modules / 运行期数据 / 密钥）
└── README.md                    # 启动与演示文档
```

## 验证入口

- 健康检查：`GET http://localhost:8002/api/v1/health`
- 工具列表：`GET http://localhost:8002/api/v1/tools`
- 技能列表：`GET http://localhost:8002/api/v1/skills`
- 技能试运行：`POST http://localhost:8002/api/v1/skills/{name}/run`（`{"query":"帮我搜索 AI 动态"}`）
- 技能开关：`PUT http://localhost:8002/api/v1/skills/{name}/enabled`（`{"enabled": false}`）
- 对话闭环：`POST http://localhost:8002/api/v1/chat`（`{"message":"现在几点了","history":[]}`）
- 提交任务：`POST http://localhost:8002/api/v1/generate`（`{"topic":"智能手表 2025 市场"}`）
- 任务列表：`GET http://localhost:8002/api/v1/tasks?page=1&page_size=10`（可加 `status` / `keyword`（主题搜索）/ `order=desc|asc`（时间排序））
- 任务状态：`GET http://localhost:8002/api/v1/tasks/{task_id}/status`
- 恢复任务（断点续跑）：`POST http://localhost:8002/api/v1/tasks/{task_id}/resume`（仅 paused / failed 生效）
- 删除任务：`DELETE http://localhost:8002/api/v1/tasks/{task_id}`
- 任务报告：`GET http://localhost:8002/api/v1/tasks/{task_id}/report`（第 27 节，仅 completed 任务）
- 触发评测：`POST http://localhost:8002/api/v1/evaluation/run`（第 27 节，后台执行 `len(TEST_CASES)` 个用例，当前 1 个）
- 评测列表 / 详情：`GET http://localhost:8002/api/v1/evaluation/reports`、`GET .../evaluation/reports/{eval_id}`
- 删除评测：`DELETE http://localhost:8002/api/v1/evaluation/reports/{eval_id}`（运行中返回 400）
- 知识库列表：`GET http://localhost:8002/api/v1/knowledge/documents`
- 长期记忆开关与状态：`GET http://localhost:8002/api/v1/memory/status`、`POST http://localhost:8002/api/v1/memory/toggle`
- 前端演示：`http://localhost:5174/home`（任务提交）、`/tasks`（任务列表，含删除/恢复）、`/tasks/{id}`（详情：长期记忆命中 + 恢复执行）、`/reports`（报告中心：已生成报告列表 + 查看/删除，第 27 节）、`/report/{taskId}`（报告展示，第 27 节）、`/evaluation`（评测中心，第 27 节）、`/knowledge`（知识库管理）、`/chat`（AI 对话）、`/skills`（技能中心）
