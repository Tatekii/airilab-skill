# AiriLab Skill 规格说明书（SPEC）

版本：1.2.0  
日期：2026-04-01  
状态：Draft

## 1. 文档目的
本规格说明书用于定义 `airilab` Skill 的产品边界、功能需求、接口约束、运行机制与验收标准，作为开发、测试、运维和后续迭代的统一依据。

## 2. 背景与目标
`airilab` Skill 是对 AiriLab SaaS 图像能力的统一封装，目标是让用户通过自然语言完成图像相关任务，并自动处理以下关键环节：
- 登录鉴权（手机验证码）
- 团队/项目选择与持久化
- 图像上传与任务提交
- 异步任务轮询与结果回传

核心目标：
1. 让用户无需理解底层 API 结构即可完成图像任务。
2. 在 token 失效、项目缺失、任务超时等异常情况下可恢复、可提示。
3. 对异步任务提供稳定、可解析、可追踪的状态链路。

## 3. 范围
### 3.1 In Scope
- AiriLab 账号登录态管理
- 项目上下文管理（teamId/projectId/projectName）
- 三类工作流任务提交：
  - MJ 创意渲染
  - 创意放大
  - 氛围转换
- 后台轮询任务状态并推送结果
- 本地持久化配置与任务状态

### 3.2 Out of Scope
- 自定义工作流编辑器
- 多租户权限隔离平台化改造
- 图像内容审核策略实现
- Web 前端界面开发

## 4. 术语与定义
- Job：一次异步生成任务实例，由后端返回 `jobId` 唯一标识。
- Workflow：后端图像生成流程，不同流程共享同一提交接口，通过 payload 差异区分。
- Ready 状态：当前具备「有效 token + 已选项目」的可提交条件。

## 5. 系统概览
## 5.1 模块划分
- `core/config.py`：Token 与项目配置持久化
- `core/auth.py`：登录与 Token 有效性检查
- `core/project.py`：团队/项目查询与选择
- `core/upload.py`：媒体上传
- `core/api.py`：任务 payload 构建与任务提交
- `scripts/check_status.py`：单任务状态查询脚本
- `scripts/fetch.py`：任务结果拉取脚本
- `scheduler/worker.py`：后台轮询与通知

## 5.2 关键运行目录
- 配置目录：`~/.openclaw/skills/airilab/config`
- 运行目录：`~/.openclaw/skills/airilab/scheduler`
- 通知目录：`~/.openclaw/completions`

## 6. 核心流程
## 6.1 鉴权流程
1. 读取本地 Token。
2. 若缺失或失效，提示用户手机号 + 验证码登录。
3. 登录成功后保存 Token 与更新时间。
4. 所有需要调用 AiriLab API 的功能必须先校验登录态。

约束：
- 不要求用户手工粘贴 token。
- token 失效后必须触发重新登录引导。

## 6.2 项目选择流程
1. 使用有效 Token 拉取用户团队/项目。
2. 用户按 `projectId` 或项目名选择。
3. 保存 `teamId/projectId/projectName` 到本地配置。

约束：
- 未选项目时不得提交图像任务。
- 项目配置缺失应返回明确错误并提示选择。

## 6.3 任务提交流程
1. 根据用户意图映射工作流。
2. 构建对应 payload 并提交到统一生成接口。
3. 若 `status == 200` 且返回 `jobId`，视为提交成功。
4. 记录任务并进入异步轮询。

## 6.4 异步轮询与结果流程
1. Worker 定时扫描待处理任务（默认每 15 秒）。
2. 调用“Job 状态接口”（轮询接口）查询任务状态。
3. 仅当状态为 `completed` 时，调用“记录查询接口”拉取结果。
4. 写入数据库状态并通过 completions 目录回推结果消息。

## 7. 功能需求（Functional Requirements）
- FR-001 鉴权：系统必须支持手机号验证码登录并持久化 token。
- FR-002 鉴权校验：所有 API 调用前必须校验登录态。
- FR-003 项目管理：系统必须支持拉取、选择、显示、清理项目配置。
- FR-004 上传能力：系统必须支持图片上传并返回 URL。
- FR-005 任务提交：系统必须支持三类工作流任务提交并返回 jobId。
- FR-006 任务轮询：系统必须支持后台轮询 pending/processing 任务。
- FR-007 结果拉取：系统必须支持通过 jobId 拉取最终图片 URL 列表。
- FR-008 结果通知：系统必须生成 Markdown 通知并写入 completions 目录。
- FR-009 失败处理：系统必须在鉴权失败、超时、解析失败时写入失败状态与原因。

## 8. 接口契约
## 8.1 外部 API（AiriLab）
- 登录：`/api/Accounts/Login`
- 获取团队：`/api/Team/GetUserTeams`
- 获取项目：`/api/Accounts/GetAllProjectsUser`
- 上传：`/api/Workflow/UploadMedia`
- 提交生成：`/api/Universal/Generate`
- Job 状态轮询接口：`GET /api/Universal/Job/{jobId}`
- 记录查询接口：`/api/CrudRouters/getOneRecord`

说明：API 细节以后端实际响应为准，本规格只定义调用目标与关键字段。
说明补充：
- Job 状态轮询接口与记录查询接口是两套不同语义的接口，禁止混用。
- 状态轮询接口用于返回 `queued/pending/processing/completed/failed` 等状态。
- 记录查询接口用于在任务已完成后读取生成记录（图片 URL、workflow 信息等）。

轮询接口调用约定：
- Method：`GET`
- URL：`http://cn.airilab.com/api/Universal/Job/{jobId}`
- Headers：
- `accept: application/json`
- `Authorization: Bearer {token}`
- 成功判定：
- 顶层 `status == 200`
- 任务状态字段来源：`data.status`
- 当 `data.status == "completed"` 时视为任务完成

## 8.2 内部脚本状态协议（强约束）
`check_status.py` 必须输出机器可读行：
- `status:pending`
- `status:processing`
- `status:completed`
- `status:failed`
- `status:error`

错误补充输出：
- `error:missing_token`
- `error:missing_project`
- `error:api_<...>` / `error:network_<...>`

Worker 必须以该协议解析状态，不依赖中文提示文本。
Worker 状态来源必须是 `GET /api/Universal/Job/{jobId}` 的 `data.status`，不得通过记录查询接口推断状态。

## 8.3 轮询与记录查询分离约束（强约束）
- SC-001 `check_status.py` 只负责“状态轮询语义”，不得承担结果拉取职责。
- SC-002 `fetch.py` 只负责“记录查询语义”，不得用于判断排队中/处理中状态。
- SC-003 Worker 流程必须先轮询状态，再按状态触发记录查询。
- SC-004 若状态接口返回未完成，系统不得调用记录查询接口进行“探测式查询”。

## 9. 工作流规范
当前支持：
- `MJ 创意渲染`：后端 `workflowId=0`
- `创意放大`：后端 `workflowId=16`
- `氛围转换`：后端 `workflowId=13`

实现注意：
- `core/api.py` 中对外方法与内部参数存在映射（如 `workflow_id=0/15` 对应具体 workflowId），后续重构应统一命名，避免语义混淆。

## 10. 数据持久化规范
## 10.1 配置文件
- `.env`：保存 `AIRILAB_API_KEY`、`AIRILAB_PHONE`、更新时间
- `project_config.json`：保存 `teamId/projectId/projectName/selected_at`

## 10.2 任务数据库
文件：`scheduler/jobs.json`  
关键字段：
- `job_id`、`user_id`、`chat_id`、`tool`
- `status`（pending/processing/completed/failed）
- `submitted_at`、`completed_at`
- `output_url`、`thumbnail_url`、`error_message`
- `attempts`

## 11. 非功能性要求（NFR）
- NFR-001 稳定性：轮询与结果解析应可长期运行，不因日志文案变更失效。
- NFR-002 可观测性：Worker 必须输出结构化日志并可定位失败原因。
- NFR-003 可移植性：子脚本调用应使用当前解释器（`sys.executable`），避免环境差异。
- NFR-004 安全性：本地配置文件不得提交到仓库；token 泄露需可快速轮换。

## 12. 错误处理策略
- 鉴权失败：标记任务失败，提示重新登录。
- 项目缺失：阻断提交或轮询，提示先选择项目。
- 轮询超时：超过 `TIMEOUT_MINUTES` 或 `MAX_ATTEMPTS` 标记失败。
- 结果拉取失败：`success=false` 视为失败，不得误判成功。
- 接口语义错误：若将记录查询结果用于替代状态轮询，视为实现缺陷并阻断发布。

## 13. 运行与部署要求
依赖：
- Python 3.9+
- `requests>=2.31.0`

启动方式：
- 前台：`python scheduler/worker.py`
- 后台：`scripts/start-worker.sh`

## 14. 验收标准（Acceptance Criteria）
- AC-001 当 token 缺失时，`check_status.py` 输出 `status:error` + `error:missing_token`。
- AC-002 当项目配置缺失时，任务提交返回 `needs_project=true`。
- AC-003 任务提交成功时，返回非空 `jobId`。
- AC-004 任务完成后，`jobs.json` 对应记录状态变为 `completed`，并写入输出 URL。
- AC-005 结果拉取 `success=false` 时，任务状态必须为 `failed`。
- AC-006 worker 在 Linux/macOS/Windows（同 Python 环境）下均可调用子脚本。
- AC-007 轮询状态与查询记录必须使用两套独立语义接口，测试中不得互相替代。

## 15. 风险与后续优化
- R-001 新增工作流时需同步更新常量与 payload 映射（`WORKFLOW_MJ/UPSCALE/ATMOSPHERE`），避免隐式分支回归。
- R-002 当前项目包含历史文档编码混杂，建议统一 UTF-8。
- R-003 建议补充自动化测试（状态协议、任务生命周期、配置恢复）。
- R-004 建议在安全流程中加入 token 轮换与敏感信息扫描。
- R-005 当前实现中状态与记录查询仍可能存在耦合，需按本 SPEC 完成彻底解耦。

## 16. 变更记录
- 2026-04-01：基于现有实现与草案，补全并结构化 SPEC，加入状态协议、验收标准、NFR 与风险项。
- 2026-04-01：明确 Job 轮询接口为 `GET /api/Universal/Job/{jobId}`，状态字段来源为 `data.status`。
