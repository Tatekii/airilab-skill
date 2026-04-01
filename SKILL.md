---
name: airilab
description: 统一调用 AiriLab 图像生成能力（MJ 创意渲染、创意放大、氛围转换）并自动处理登录、项目选择、异步任务轮询与结果回推。用户发送图像生成/改图/放大/风格转换相关请求时使用。
---

# AiriLab Skill

## 目标
- 将 AiriLab SaaS 的多接口流程封装为可对话调用的单一技能。
- 在调用图像能力前，自动保证登录态与项目上下文有效。
- 通过后台 worker 追踪异步任务并主动回推结果。

## 能力范围
- 鉴权：手机号 + 验证码登录，持久化 token。
- 项目管理：拉取团队/项目、选择项目、持久化项目上下文。
- 图像工作流：
  - `workflowId=0` MJ 创意渲染（文生图/参考图生成）
  - `workflowId=16` 创意放大
  - `workflowId=13` 氛围转换（天气/季节/光照语义转换）
- 异步任务：提交后轮询状态，完成后拉取记录并通知用户。

## 触发规则
当用户表达以下意图时自动触发：
- 生成图像：如“生成 4 张建筑立面图”“MJ 渲染”。
- 图像编辑：如“把这张图改成冬季夜景”“换成雨天氛围”。
- 图像增强：如“放大这张图”“创意放大”“超分辨率”。

优先判断信号：
1. 用户上传了图像。
2. 指令包含生成/改图/放大/风格转换等语义。

## 前置条件（强约束）
1. 调用任何 AiriLab 接口前必须检查登录态。
2. 提交图像任务前必须存在已选项目（`teamId/projectId/projectName`）。
3. 登录失效时必须引导手机号验证码登录，不要求用户提供 token。

## 工作流参数约束

### 1) MJ 创意渲染（`workflowId=0`）
- 必填：`prompt`
- 可选：`referenceImage`（最多 3 张）、`imageCount`（1-4）

### 2) 创意放大（`workflowId=16`）
- 必填：`baseImage`
- 可选：`width`、`height`

### 3) 氛围转换（`workflowId=13`）
- 必填：`baseImage`
- 可选：`prompt`、`referenceImage`（最多 1 张）、`imageCount`

## 异步任务处理（强约束）
轮询任务状态与查询生成记录必须分离：
- 轮询状态接口：`GET /api/Universal/Job/{jobId}`
  - 状态字段来源：`data.status`
- 记录查询接口：`POST /api/CrudRouters/getOneRecord`
  - 仅在状态为 `completed` 后调用

脚本职责：
- `scripts/check_status.py`：只做状态轮询，输出 `status:<value>`。
- `scripts/fetch.py`：只做记录查询，返回生成 URL 列表等结果。
- `scheduler/worker.py`：负责任务生命周期与通知。

## 本地持久化
- `config/.env`：token 与登录相关信息。
- `config/project_config.json`：当前项目上下文。
- `scheduler/jobs.db`：异步任务状态。
- `scheduler/worker.log`：worker 运行日志。

## 运行命令
```bash
# 安装依赖
python -m pip install -r ~/.openclaw/skills/airilab/requirements.txt

# 查看配置状态
python ~/.openclaw/skills/airilab/core/config.py status

# 启动后台 worker
~/.openclaw/skills/airilab/scripts/start-worker.sh
```

## 故障处理
- `missing_token`：引导用户登录。
- `missing_project`：引导用户选择项目。
- `timeout` / 轮询超时：任务标记失败并通知用户重试。
- 记录查询 `success=false`：按失败处理，不得误判成功。

## 相关文件
- `core/config.py`
- `core/auth.py`
- `core/project.py`
- `core/upload.py`
- `core/api.py`
- `scripts/check_status.py`
- `scripts/fetch.py`
- `scheduler/worker.py`
- `SPEC.md`
