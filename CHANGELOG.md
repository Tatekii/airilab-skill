# AiriLab Skill 更新日志

## [1.5.1] 2026-04-03 - 提交后强制结束本轮对话

### 变更
- 在 `core/api.py` 为api接口新增status字段api_count

## [1.5.0] 2026-04-02 - 切换为同步等待模式（OpenClaw 适配）

### Changed
- `core/api.py` 从“提交即返回”改为“提交后同步轮询直到拿到最终结果”。
- 成功返回中保留 `job_id`，并新增最终结果字段：`output_urls`、`thumbnail_url`、`toolset`、`status`。
- `notify_async` 在同步模式下固定为 `false`。

### Added
- 在 `core/api.py` 内新增状态轮询与结果拉取实现：
  - `_check_job_status(...)`
  - `_fetch_result(...)`
  - `_wait_for_result(...)`
- CLI 成功输出时直接打印结果 URL 列表，便于终端立即查看。

### Fixed
- 修复 OpenClaw 环境下“completions 不会被主动消费”导致的通知失效问题。
- 不再依赖 HEARTBEAT 方案，避免 1-3 分钟任务场景的延迟与不确定性。

### Notes
- 本次改动的直接原因：
  1. OpenClaw 不主动读取 completions。
  2. 任务时长短（1-3 分钟），同步等待更可靠。

## [1.4.7] 2026-04-02 - 提交后强制结束本轮对话

### 变更
- 在 `core/api.py` 的提交结果中新增机器可读字段：`round_complete`、`notify_async`。
- 当提交成功（`success=true` 且 `job_id` 非空）时，显式标记本轮应立即结束。

## [1.4.6] 2026-04-02 - 强制仅允许 `_build_payload` 构建工作流请求体

### 修复
- 清理 `core/api.py` 中氛围转换分支被手工拼装污染的问题。
- 将错误的 `null` 字面量替换为 Python `None`。

### 变更
- 在 `submit_task(...)` 增加防护：拒绝任何 direct payload override。

## [1.4.5] 2026-04-02 - 本地缓存切换为 JSON（不再使用 SQLite）

### 变更
- 本地任务缓存改为 `scheduler/jobs.json`。
- 生命周期事件流改为 `scheduler/job_events.jsonl`。

## [1.4.4] 2026-04-02 - 入队持久化与任务链路追踪

### 新增
- 新增共享存储模块 `core/job_store.py`。
- 新增 `scripts/job_trace.py`，支持按 `jobId` 查看任务主记录与事件时间线。

## [1.4.3] 2026-04-02 - 上传额度超限处理

### 修复
- `core/upload.py` 增加对 `status:203 / Standard Generation limit exceeded` 的专门处理。

## [1.4.2] 2026-04-01 - 异步提交文案约束

### 变更
- 提交成功文案明确：本轮结束，后台完成后异步通知。

## [1.4.1] 2026-04-01 - 轮询终态规则调整

### 变更
- `scheduler/worker.py` 中仅 `status=processing` 视为进行中。

## [1.4.0] 2026-04-01 - 安装与自启动重构
- 新增安装脚本与健康检查流程。

## [1.3.0] 2026-04-01 - 运行时稳健性与登录规则
- 强化 OTP 成功判定与运行时路径一致性。

## [1.2.0] 2026-04-01 - Worker 稳定性修复
- 统一状态输出与子脚本调用方式。

## [1.1.0] 2026-03-31 - P0 问题修复
- 新增结果拉取脚本并完善通知路径。

## [1.0.0] 2026-03-31 - 初始整合版本
- 整合 `airi-auth`、`airi-upload`、`airi-project`、`api-list` 能力。
