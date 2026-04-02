# AiriLab Skill 规格说明书（SPEC）

版本：1.5.0  
日期：2026-04-02  
状态：Draft

## 1. 文档目的
定义 `airilab` Skill 在 OpenClaw 环境下的同步执行架构、接口约束与验收标准。

## 2. 架构决策
### 2.1 决策结论
Skill 采用“同步等待结果”模式：
1. 提交任务。
2. 在当前调用内轮询状态。
3. 拉取最终结果后一次性返回。

### 2.2 决策原因
1. OpenClaw 不会主动读取 `~/.openclaw/completions/`，无法实现可靠主动推送。
2. 基于 HEARTBEAT 的延迟轮询不适用于 1-3 分钟短任务。
3. 用户更需要确定性结果而不是后台不确定通知。

## 3. 范围
### 3.1 In Scope
- 登录鉴权（手机号验证码）
- 项目上下文管理
- 三类工作流提交：
  - MJ 创意渲染（`workflowId=0`）
  - 创意放大（`workflowId=16`）
  - 氛围转换（`workflowId=13`）
- 提交后同步轮询直到完成/失败/超时
- 结果 URL 返回

### 3.2 Out of Scope
- 主动推送通知机制
- HEARTBEAT 异步检查机制
- 前端界面开发

## 4. 核心接口
- 提交：`POST /api/Universal/Generate`
- 状态：`GET /api/Universal/Job/{jobId}`
- 结果：`POST /api/CrudRouters/getOneRecord`

## 5. 关键流程
1. 校验登录与项目配置。
2. 通过 `_build_payload(...)` 构建请求体并提交。
3. 得到 `jobId` 后每 5 秒轮询状态。
4. 状态为 `completed` 时拉取结果。
5. 若 `failed` 或超时（210 秒）则返回失败。

## 6. 工作流参数规则
- MJ：支持 `referenceImage`，最多 3 张。
- 创意放大：不使用参考图。
- 氛围转换：支持 `referenceImage`，最多 1 张。

## 7. 强约束（发布阻断）
- 所有 payload 必须由 `_build_payload(...)` 统一生成。
- 禁止 direct payload override。
- 同步模式下不得返回“后台会自动通知”的误导文案。

## 8. 验收标准（AC）
- AC-001 提交成功后，调用在同一轮内继续执行直到拿到结果或超时。
- AC-002 返回结构包含 `output_urls`、`thumbnail_url`（成功时）。
- AC-003 MJ 参考图 >3 张时立即报错。
- AC-004 氛围转换参考图 >1 张时立即报错。
- AC-005 超时时返回明确超时错误，不假设后台通知。

## 9. 运行命令
```bash
python core/api.py --tool mj --prompt "..."
python core/api.py --tool upscale --base-image "..."
python core/api.py --tool atmosphere --base-image "..." --prompt "..."
```

## 10. 变更记录
- 2026-04-02：从“异步后台通知”切换为“同步等待结果”模式。
- 2026-04-02：明确原因：OpenClaw 不消费 completions，HEARTBEAT 不适配短任务时长。
