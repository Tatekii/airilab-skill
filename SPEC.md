# AiriLab Skill 规格说明书（SPEC）

版本：1.4.7  
日期：2026-04-02  
状态：Draft

## 1. 文档目的
本文档定义 `airilab` Skill 的产品边界、接口契约、执行约束与验收标准，作为开发、测试与发布的一致依据。

## 2. 背景与目标
`airilab` Skill 用于统一封装 AiriLab 图像能力，支持在对话中完成：
- 登录鉴权（手机号 + 验证码）
- 项目上下文选择（teamId/projectId/projectName）
- 图像上传与任务提交
- 异步任务轮询与结果通知

目标：
1. 用户无需理解底层 API 即可使用工作流。
2. 在 token 失效、项目缺失、超时等异常场景可恢复、可追踪。
3. 严格保证异步语义：提交成功后立即结束本轮，由后台通知最终结果。

## 3. 范围
### 3.1 In Scope
- 登录态管理与校验
- 项目查询、选择与持久化
- 三类工作流提交：
  - MJ 创意渲染（`workflowId=0`）
  - 创意放大（`workflowId=16`）
  - 氛围转换（`workflowId=13`）
- 后台轮询与结果回推
- JSON 本地缓存与日志追踪

### 3.2 Out of Scope
- 自定义工作流编排平台
- 多租户权限系统改造
- Web 前端开发
- 内容审核策略实现

## 4. 术语
- Job：一次异步生成任务，唯一标识为 `jobId`。
- Workflow：后端图像流程，通过 `workflowId` 区分。
- Ready：同时具备有效 token 与已选项目。

## 5. 架构模块
- `core/config.py`：配置与健康检查
- `core/auth.py`：登录与 token 校验
- `core/project.py`：团队/项目选择
- `core/upload.py`：媒体上传
- `core/api.py`：请求体构建与任务提交
- `core/job_store.py`：本地 JSON 缓存与事件流
- `scripts/check_status.py`：状态轮询脚本
- `scripts/fetch.py`：记录查询脚本
- `scripts/job_trace.py`：按 `jobId` 查询本地追踪
- `scheduler/worker.py`：后台轮询与通知

## 6. 关键流程
### 6.1 鉴权流程
1. 读取本地 token。
2. token 缺失或失效时，触发验证码登录。
3. 登录成功后保存 token。
4. 调用任何 AiriLab API 前必须校验登录态。

### 6.2 项目流程
1. 拉取团队/项目列表。
2. 用户按项目名或 `projectId` 选择。
3. 持久化 `teamId/projectId/projectName`。

### 6.3 提交流程
1. 根据意图映射 `workflowId`。
2. 仅通过 `_build_payload(...)` 构建请求体。
3. 调用 `/api/Universal/Generate`。
4. 成功返回 `jobId` 后立即入队本地缓存，交由 worker 处理。

### 6.4 异步流程
1. worker 定时扫描待处理任务。
2. 先调用状态接口轮询任务。
3. 再按规则调用记录查询接口拉取结果。
4. 写入缓存并推送通知。

## 7. 功能需求（FR）
- FR-001 支持验证码登录与 token 持久化。
- FR-002 所有任务调用前必须校验登录态。
- FR-003 支持项目选择与持久化。
- FR-004 支持图片上传并返回 URL。
- FR-005 支持三类工作流提交并返回 `jobId`。
- FR-006 支持后台轮询 pending/processing 任务。
- FR-007 支持按 `jobId` 拉取结果 URL。
- FR-008 支持结果通知落地到 completions。
- FR-009 支持失败状态落库与可追踪错误。

## 8. 接口契约
### 8.1 外部接口
- 登录：`/api/Accounts/Login`
- 获取团队：`/api/Team/GetUserTeams`
- 获取项目：`/api/Accounts/GetAllProjectsUser`
- 上传：`/api/Workflow/UploadMedia`
- 提交：`/api/Universal/Generate`
- 状态轮询：`GET /api/Universal/Job/{jobId}`
- 记录查询：`POST /api/CrudRouters/getOneRecord`

### 8.2 状态轮询契约
- 请求：
  - Method：`GET`
  - URL：`http://cn.airilab.com/api/Universal/Job/{jobId}`
  - Headers：`accept: application/json`、`Authorization: Bearer {token}`
- 成功判定：顶层 `status == 200`
- 状态字段来源：`data.status`

### 8.3 内部脚本输出契约
`check_status.py` 必须输出机器可读行：
- `status:pending`
- `status:processing`
- `status:completed`
- `status:failed`
- `status:error`

可选错误补充：
- `error:missing_token`
- `error:missing_project`
- `error:api_<...>`
- `error:network_<...>`

## 9. 强约束（发布阻断）
### 9.1 轮询与查询语义分离
- SC-001 `check_status.py` 只负责状态轮询，禁止承担结果拉取。
- SC-002 `fetch.py` 只负责记录查询，禁止用于判定处理中状态。
- SC-003 worker 必须先轮询状态，再按规则触发记录查询。

### 9.2 Payload 构建统一
- SC-004 所有工作流请求体必须由 `core/api.py::_build_payload(...)` 统一生成。
- SC-005 禁止任何调用方直接拼装或覆盖 `payload`。

### 9.3 异步提交后立即结束本轮
- SC-006 当提交成功（`status==200` 且 `jobId` 非空）时，当前 agent 轮次必须立即结束。
- SC-007 提交成功后的同一轮内，禁止继续轮询、等待、拉取结果。
- SC-008 API 返回应提供机器字段驱动上层编排：`round_complete=true`、`notify_async=true`。

## 10. 数据持久化
### 10.1 配置
- `config/.env`：`AIRILAB_API_KEY`、手机号、更新时间
- `config/project_config.json`：项目上下文

### 10.2 任务缓存（JSON）
- `scheduler/jobs.json`：任务主记录
- `scheduler/job_events.jsonl`：任务生命周期事件流

任务关键字段：
- `job_id`、`user_id`、`chat_id`、`tool`
- `status`（pending/processing/completed/failed）
- `submitted_at`、`completed_at`
- `output_url`、`thumbnail_url`、`error_message`
- `attempts`

## 11. 非功能要求（NFR）
- NFR-001 稳定性：状态解析不得依赖中文文案。
- NFR-002 可观测性：必须可按 `jobId` 追踪全链路事件。
- NFR-003 可移植性：子脚本调用必须使用 `sys.executable`。
- NFR-004 安全性：本地敏感配置不得提交仓库。

## 12. 错误处理
- 鉴权失败：提示重新登录并标记失败。
- 项目缺失：阻断提交并提示选择项目。
- 轮询超时：超过阈值标记失败。
- 结果拉取失败：`success=false` 必须标记失败。
- 语义违规：轮询/查询混用、绕过 `_build_payload`、同轮继续等待，均视为发布阻断。

## 13. 运行要求
依赖：
- Python 3.9+
- `requests>=2.31.0`

启动：
- 前台：`python scheduler/worker.py`
- 后台：`scripts/start-worker.sh`

## 14. 验收标准（AC）
- AC-001 token 缺失时，`check_status.py` 输出 `status:error` 与 `error:missing_token`。
- AC-002 项目缺失时，提交返回 `needs_project=true`。
- AC-003 提交成功返回非空 `jobId`。
- AC-004 提交成功时返回 `round_complete=true`、`notify_async=true`。
- AC-005 提交成功后同轮不发生轮询与结果拉取。
- AC-006 任务完成后 `jobs.json` 状态变为 `completed` 且写入输出 URL。
- AC-007 拉取 `success=false` 时状态必须为 `failed`。
- AC-008 Linux/macOS/Windows 同 Python 环境可运行子脚本。

## 15. 风险与建议
- R-001 新增工作流时需同步更新常量与 `_build_payload`。
- R-002 文档必须统一 UTF-8，避免再次出现编码污染。
- R-003 建议补充自动化测试（提交、轮询、失败路径、异步结束规则）。

## 16. 变更记录
- 2026-04-01：明确轮询接口为 `GET /api/Universal/Job/{jobId}`，状态字段来自 `data.status`。
- 2026-04-02：新增 `_build_payload` 统一约束与“提交成功后同轮禁止轮询”约束。
