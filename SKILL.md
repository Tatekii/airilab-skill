---
name: airilab
description: 统一调用 AiriLab 图像生成能力（MJ/创意放大/氛围转换），采用同步等待模式：提交后在当前轮次内等待直到拿到最终结果。
---

# AiriLab Skill

## 目标
- 统一 AiriLab 图像工作流调用。
- 自动处理登录鉴权与项目上下文。
- 在 OpenClaw 中采用同步模式，避免依赖不可用的主动推送机制。

## 架构结论（OpenClaw）
- OpenClaw 不会主动消费 `~/.openclaw/completions/`，因此不能依赖 worker 主动通知。
- 任务时长通常 1-3 分钟，不采用 HEARTBEAT 轮询方案。
- 统一改为：提交成功后在当前调用内轮询，直到拿到结果或超时。

## 工作流支持
- `workflowId=0`：MJ 创意渲染（支持参考图，最多 3 张）
- `workflowId=16`：创意放大
- `workflowId=13`：氛围转换（支持参考图，最多 1 张）

## 强约束
1. 请求体必须由 `core/api.py::_build_payload(...)` 统一生成。
2. 禁止 direct payload override。
3. 同步模式下，提交后必须等待结果或明确超时失败后再返回。
4. 不再承诺“后台自动通知”。

## 运行方式
- 推荐直接调用 `core/api.py`：
```bash
python core/api.py --tool mj --prompt "..."
python core/api.py --tool upscale --base-image "..."
python core/api.py --tool atmosphere --base-image "..." --prompt "..."
```

参考图参数：
```bash
# MJ 最多 3 张
python core/api.py --tool mj --prompt "..." \
  --reference-image "url1" --reference-image "url2" --reference-image "url3"

# 氛围转换最多 1 张
python core/api.py --tool atmosphere --base-image "..." --prompt "..." \
  --reference-image "url1"
```

## 相关文件
- `core/api.py`
- `core/auth.py`
- `core/config.py`
- `core/project.py`
- `core/upload.py`
- `scripts/check_status.py`
- `scripts/fetch.py`
- `SPEC.md`
