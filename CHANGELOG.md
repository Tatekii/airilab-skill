# AiriLab Skill 更新日志

## [1.1.0] 2026-03-31 - P0 问题修复

### ✅ 已修复

#### 1. 新增 `scripts/fetch.py`
- 获取已完成任务的输出结果
- 支持 JSON 和文本两种输出格式
- 返回所有生成图片的 URL 列表
- 自动识别工作流类型（MJ/Upscale/Atmosphere）

**使用示例**:
```bash
# 文本输出
python3 scripts/fetch.py --job-id <job_id>

# JSON 输出（供程序调用）
python3 scripts/fetch.py --job-id <job_id> --format json
```

#### 2. 实现用户通知机制 (`scheduler/worker.py`)
- 使用 OpenClaw completions 目录发送消息
- 支持多图片 Markdown 格式展示
- 包含 Job ID、工具类型、图片数量等信息
- 失败任务也会发送错误通知

**通知格式**:
```markdown
✅ **任务完成！**

📋 **Job ID**: `xxx`
🎨 **工具**: MJ

🖼️  **生成结果**:

![图片 1](url1)
![图片 2](url2)
...

_共 4 张图片_
```

#### 3. 改进 `process_job()` 函数
- 正确解析 `fetch.py` 的 JSON 输出
- 传递所有图片 URL 给通知函数
- 添加工具类型到通知消息
- 改进错误处理逻辑

### 📁 文件变更

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `scripts/fetch.py` | 新增 | 任务结果获取脚本 |
| `scheduler/worker.py` | 修改 | 实现通知机制 |
| `CHANGELOG.md` | 新增 | 更新日志 |

### 🧪 测试建议

1. **测试 fetch.py**:
   ```bash
   python3 ~/.openclaw/skills/airilab/scripts/fetch.py --job-id <existing_job_id>
   ```

2. **测试完整流程**:
   - 提交一个图像生成任务
   - 启动 worker: `python3 scheduler/worker.py`
   - 检查 completions 目录是否生成通知文件

### ⚠️ 注意事项

- 确保 Token 有效（有效期 7 天）
- 确保项目配置正确
- worker 需要持续运行才能轮询任务

---

## [1.0.0] 2026-03-31 - 初始整合版本

整合 airi-auth, airi-upload, airi-project, api-list 四个技能。
