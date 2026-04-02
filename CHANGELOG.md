# AiriLab Skill 更新日志

## [1.4.7] 2026-04-02 - 提交后强制结束本轮对话

### 变更
- 在 `core/api.py` 的提交结果中新增机器可读字段：`round_complete`、`notify_async`。
- 当提交成功（`success=true` 且 `job_id` 非空）时，显式标记本轮应立即结束。

### 新增
- 在 `SKILL.md` 增加“同轮禁止轮询（same-round no-poll）”发布阻断规则。
- 在 `SPEC.md` 增加对应架构约束，禁止提交成功后继续同步等待。

## [1.4.6] 2026-04-02 - 强制仅允许 `_build_payload` 构建工作流请求体

### 修复
- 清理 `core/api.py` 中氛围转换分支被手工拼装污染的问题。
- 将错误的 `null` 字面量替换为 Python `None`。

### 变更
- 在 `submit_task(...)` 增加防护：拒绝任何 direct payload override。
- 在 `SKILL.md` 与 `SPEC.md` 增加“请求体必须由 `_build_payload(...)` 统一生成”的发布阻断规则。

## [1.4.5] 2026-04-02 - 本地缓存切换为 JSON（不再使用 SQLite）

### 变更
- 本地任务缓存改为 `scheduler/jobs.json`。
- 生命周期事件流改为 `scheduler/job_events.jsonl`。
- `scheduler/worker.py` 改为只读写 JSON 缓存。
- `core/config.py health` 改为输出 `jobs_file`（JSON 缓存路径）。
- `scripts/job_trace.py` 改为仅从 JSON 文件读取任务与事件。

## [1.4.4] 2026-04-02 - 入队持久化与任务链路追踪

### 新增
- 新增共享存储模块 `core/job_store.py`。
- 增加任务事件流记录（提交、轮询、失败、完成等）。
- 新增 `scripts/job_trace.py`，支持按 `jobId` 查看任务主记录与事件时间线。

### 修复
- 提交成功后立即落本地队列，确保 worker 可稳定拾取任务。

## [1.4.3] 2026-04-02 - 上传额度超限处理

### 修复
- `core/upload.py` 增加对以下返回的专门处理：
  - `status: 203`
  - `message: "Standard Generation limit exceeded"`
- 上传失败时返回明确额度不足提示，不再使用泛化错误。

## [1.4.2] 2026-04-01 - 异步提交文案约束

### 变更
- 提交成功文案明确：本轮结束，后台完成后异步通知。
- `SKILL.md` 同步约束：提交成功后必须结束本轮对话。

## [1.4.1] 2026-04-01 - 轮询终态规则调整

### 变更
- `scheduler/worker.py` 中仅 `status=processing` 视为进行中。
- 其他状态视为流程结束并立即尝试拉取结果。

### 修复
- 移除与新规则冲突的重试分支。
- 终态后拉取失败时，记录终态与失败细节并标记任务失败。

## [1.4.0] 2026-04-01 - 安装与自启动重构

### 新增
- 新增 `scripts/post-install.sh`：初始化目录、安装依赖、健康检查、配置自启动、确保 worker 启动。

### 变更
- `.gitignore` 增加本地运行产物忽略规则（`config/`、`scheduler/`、`*.db`、`*.log`、`*.pid`）。

### 移除
- 移除历史安装脚本与过期文档，统一到新安装流程。

## [1.3.0] 2026-04-01 - 运行时稳健性与登录规则

### 变更
- OTP 发送成功判定改为严格匹配：`status == 200` 且 `message == "Otp sent"`。
- OTP 失败时透传后端 `message`。

### 新增
- 新增 `core/paths.py`，统一运行时路径解析（支持 `AIRILAB_HOME` 覆盖）。
- 新增 `core/config.py health` 与 `scripts/health.sh` 健康检查能力。

### 修复
- 统一 `config/status/fetch/worker` 的持久化路径。
- worker 增加单实例 PID 锁与启动自检。

## [1.2.0] 2026-04-01 - Worker 稳定性修复

### 修复
- `check_status.py` 标准化输出 `status:<value>`。
- 移除状态查询中的硬编码项目参数，改为配置读取。
- worker 子进程调用统一使用 `sys.executable`。
- 结果拉取 `success=false` 时严格判定任务失败。

### 新增
- 新增 `requirements.txt`（`requests>=2.31.0`）。

## [1.1.0] 2026-03-31 - P0 问题修复

### 修复
- 新增 `scripts/fetch.py` 用于已完成任务的结果拉取。
- 完善 worker 通知机制（成功/失败均有通知）。
- 优化 `process_job()` 的结果解析与错误处理路径。

## [1.0.0] 2026-03-31 - 初始整合版本

- 整合 `airi-auth`、`airi-upload`、`airi-project`、`api-list` 能力。
