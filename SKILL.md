---
name: airilab
description: 统一调用 AiriLab 图像生成与任务管理能力（MJ 创意渲染 workflowId=0、创意放大 workflowId=16、氛围转换 workflowId=13），自动处理登录鉴权、项目选择、任务提交、状态轮询与结果回推。
---

# AiriLab Skill

## 目标
- 将 AiriLab 多接口流程封装为单一可对话能力。
- 调用图像能力前自动保证登录态与项目上下文有效。
- 使用后台 worker 处理异步任务并主动推送结果。

## 能力范围
- 鉴权：手机号 + 验证码登录，持久化 token。
- 项目：拉取团队/项目并持久化当前项目。
- 工作流：
  - `workflowId=0`：MJ 创意渲染
  - `workflowId=16`：创意放大
  - `workflowId=13`：氛围转换
- 异步：提交后交由 worker 轮询并通知。

## 触发规则
以下意图触发本 skill：
- 文生图、参考图生成、MJ 渲染。
- 创意放大、高清放大、长边 4K。
- 氛围转换（季节/天气/昼夜）。
- 登录 AiriLab、选择项目、查询任务状态与结果。

关键词示例：
- MJ：`mj`、`midjourney`、`文生图`、`渲染`
- 放大：`创意放大`、`4k`、`超分`
- 氛围：`氛围转换`、`atmosphere`、`夜景`、`雨天`
- 流程：`登录`、`验证码登录`、`选择项目`、`jobId`

## 前置条件（强约束）
1. 调用任何 AiriLab API 前必须先校验登录态。
2. 提交任务前必须存在已选项目（`teamId/projectId/projectName`）。
3. token 失效时必须引导验证码登录，不要求用户手工提供 token。

## 工作流参数约束
### 1) MJ 创意渲染（`workflowId=0`）
- 必填：`prompt`
- 可选：`referenceImage`（最多 3 张）、`imageCount`

### 2) 创意放大（`workflowId=16`）
- 必填：`baseImage`
- 可选：`width`、`height`

### 3) 氛围转换（`workflowId=13`）
- 必填：`baseImage`
- 可选：`prompt`、`referenceImage`（最多 1 张）、`imageCount`

## Payload 构建强约束（发布阻断）
- 所有图像工作流请求体必须由 `core/api.py::_build_payload(...)` 统一生成。
- 禁止在 agent 对话执行层、临时脚本或其他模块中手工拼装 `payload`。
- 禁止 direct payload override。
- 需要新增字段时，先改 `_build_payload(...)`，再由 `submit_task(...)` 发送。

## 异步任务处理（强约束）
- 状态轮询与记录查询必须分离：
  - 轮询接口：`GET /api/Universal/Job/{jobId}`（状态来源 `data.status`）
  - 记录查询：`POST /api/CrudRouters/getOneRecord`
- 脚本职责：
  - `scripts/check_status.py`：只做状态轮询，输出 `status:<value>`
  - `scripts/fetch.py`：只做记录查询
  - `scheduler/worker.py`：生命周期编排与通知

## Async Round-Exit Rule（发布阻断）
- 提交成功（`success=true` 且 `job_id` 非空）后，必须立即结束当前对话轮次。
- 同一轮中禁止继续轮询、等待或拉取结果。
- 必须明确告知用户“后台完成后会自动通知”。
- 保持机器可读信号：`round_complete=true`、`notify_async=true`。

## 本地持久化
- 运行根目录：优先 `AIRILAB_HOME`，默认 `~/.openclaw/skills/airilab`
- `config/.env`：token 相关
- `config/project_config.json`：项目上下文
- `scheduler/jobs.json`：任务缓存
- `scheduler/job_events.jsonl`：事件流日志
- `scheduler/worker.log`：worker 日志
- `scheduler/worker.pid`：worker 单实例锁

## 运行命令
```bash
python -m pip install -r ~/.openclaw/skills/airilab/requirements.txt
python ~/.openclaw/skills/airilab/core/config.py status
python ~/.openclaw/skills/airilab/core/config.py health
~/.openclaw/skills/airilab/scripts/health.sh
~/.openclaw/skills/airilab/scripts/post-install.sh
~/.openclaw/skills/airilab/scripts/start-worker.sh
```

## 故障处理
- `missing_token`：引导登录
- `missing_project`：引导选项目
- `timeout`：标记失败并通知重试
- `fetch success=false`：严格标记失败

## 相关文件
- `core/config.py`
- `core/auth.py`
- `core/project.py`
- `core/upload.py`
- `core/api.py`
- `core/job_store.py`
- `scripts/check_status.py`
- `scripts/fetch.py`
- `scripts/job_trace.py`
- `scheduler/worker.py`
- `SPEC.md`

## Agent 执行约束（强约束）
- Agent 必须执行可执行步骤，不将命令转嫁给用户。
- 缺参时仅询问必要参数，不输出“请你手工执行命令”。
- 登录只向用户索取最小输入：`phone` 与 `code`。
- 执行后返回结果摘要（成功/失败、关键字段、下一步）。
