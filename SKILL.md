---
name: airilab
description: 调用 AiriLab AI 图像生成平台，支持建筑/室内/景观/城市规划的 AI 渲染。当用户需要「生成建筑效果图」「AI 绘图」「创意渲染」「图片放大」「氛围转换」「参考图生成」「MJ 渲染」「生成室内设计图」「生成景观图」「生成城市设计图」「生成效果图」「AI 出图」「快速渲染」「概念图生成」时使用此技能。支持文生图、图生图、参考图控制。
metadata: { "openclaw": { "emoji": "🎨", "requires": { "bins": ["python3"], "pip": ["requests"] } } }
---

# AiriLab AI 图像生成技能

## ⚠️ 重要约束（阅读后必须遵守）

### 约束 1：仅支持三种工作流

**本 Skill 仅支持以下三种工作流，不接受其他任何工作流请求：**

| 工作流 | workflowId | 功能 | 参数 | 参考图限制 |
|--------|------------|------|------|------------|
| MJ 创意渲染 | 0 | 文生图/图生图 | `--prompt` (必填) | 最多 3 张 |
| 创意放大 | 16 | 图片高清放大 | `--base-image` (必填) | 不支持 |
| 氛围转换 | 13 | 改变图片氛围/风格 | `--base-image` + `--prompt` | 最多 1 张 |

**❌ 不支持的工作流（必须拒绝）：**
- 视频生成
- 局部重绘（Inpaint）
- 其他未列出的工作流

**当用户请求不支持的工作流时，必须回复：**
```
⚠️ 当前仅支持三种工作流：
1. MJ 创意渲染（文生图/图生图）
2. 创意放大（图片高清化）
3. 氛围转换（改变图片氛围/风格）

您请求的功能暂不支持，请选择以上三种工作流之一。
```

### 约束 2：必须使用内建脚本调用

**Agent 必须且只能通过以下方式调用本 Skill：**

```bash
# 唯一正确的调用方式
cd /home/ec2-user/.openclaw/skills/airilab
python3 core/api.py --tool <工具名> [参数...]
```

**❌ 禁止的调用方式：**
- ❌ 直接调用 AiriLab API（绕过本 Skill）
- ❌ 自行构建请求体（必须使用 `_build_payload()`）
- ❌ 修改脚本参数或逻辑
- ❌ 使用外部工具或脚本

**原因：**
1. 内建脚本已处理完整的 8 步流程（鉴权→项目→上传→构建→提交→轮询→结果→记录）
2. `_build_payload()` 确保请求体格式正确
3. 同步轮询机制确保拿到最终结果
4. 错误处理和重试机制已内置

---

## 目标

统一调用 AiriLab 图像生成能力，支持建筑、室内、景观、城市规划等领域的 AI 渲染。采用同步等待模式：提交后在当前轮次内等待直到拿到最终结果。

---

## 前置条件

- **配置文件**: `config/.env` (API Token)
- **项目配置**: `config/project_config.json` (团队 ID、项目 ID)
- **Python 库**: `requests`
- **首次配置**: 需要先登录 AiriLab 获取 API Token

---

## 执行流程（严格顺序）

```
Step 1 登录鉴权 → Step 2 项目选择 → Step 3 图片上传 (可选) → Step 4 构建请求 → Step 5 提交任务 → Step 6 同步轮询 → Step 7 获取结果 → Step 8 保存记录
```

**每一步的前置条件：**

| 步骤 | 前置条件 | 输出 |
|------|----------|------|
| 1. 登录鉴权 | 无 | token |
| 2. 项目选择 | Step 1 ✅ (token) | teamId, projectId |
| 3. 图片上传 | Step 1 ✅, Step 2 ✅ | image_url |
| 4. 构建请求 | Step 1-3 ✅ | payload |
| 5. 提交任务 | Step 1-4 ✅ | jobId |
| 6. 同步轮询 | Step 1 ✅, Step 5 ✅ | status |
| 7. 获取结果 | Step 1-2 ✅, Step 6 ✅ | output_urls |
| 8. 保存记录 | Step 5 ✅ | jobs.json |

**详细流程说明**: 查看 `EXECUTION_FLOW.md`

---

## 运行方式（唯一正确方式）

### 必须使用内建脚本

**工作目录：**
```bash
cd /home/ec2-user/.openclaw/skills/airilab
```

**调用命令：**
```bash
python3 core/api.py --tool <工具名> [参数...]
```

### 三种工作流的调用示例

#### 1. MJ 创意渲染（文生图/图生图）

```bash
# 基础用法
python3 core/api.py --tool mj --prompt "现代建筑外观，玻璃幕墙，日落时分"

# 带 1 张参考图
python3 core/api.py --tool mj --prompt "基于参考图的室内设计" \
  --reference-image "https://example.com/image1.jpg"

# 带 3 张参考图（上限）
python3 core/api.py --tool mj --prompt "融合多种风格" \
  --reference-image "https://example.com/image1.jpg" \
  --reference-image "https://example.com/image2.jpg" \
  --reference-image "https://example.com/image3.jpg"

# 指定生成数量
python3 core/api.py --tool mj --prompt "现代建筑" --image-count 4
```

#### 2. 创意放大（图片高清化）

```bash
# 基础用法
python3 core/api.py --tool upscale --base-image "https://example.com/image.jpg"

# 指定输出尺寸
python3 core/api.py --tool upscale \
  --base-image "https://example.com/image.jpg"
# 默认：width=1288, height=816
```

#### 3. 氛围转换（改变图片氛围/风格）

```bash
# 基础用法
python3 core/api.py --tool atmosphere \
  --base-image "https://example.com/image.jpg" \
  --prompt "转换为夜晚氛围，暖色灯光"

# 带 1 张参考图
python3 core/api.py --tool atmosphere \
  --base-image "https://example.com/image.jpg" \
  --prompt "转换为黄昏氛围" \
  --reference-image "https://example.com/reference.jpg"

# 指定生成数量
python3 core/api.py --tool atmosphere \
  --base-image "https://example.com/image.jpg" \
  --prompt "雨天氛围" --image-count 4
```

### ❌ 错误的调用方式（禁止使用）

```bash
# ❌ 错误：直接调用 API
curl -X POST https://cn.airilab.com/api/Universal/Generate ...

# ❌ 错误：使用 Python API 类（不推荐）
python3 -c "from core.api import AiriLabAPI; api = AiriLabAPI(); api.mj_render(...)"

# ❌ 错误：不在正确的工作目录
python3 /home/ec2-user/.openclaw/skills/airilab/core/api.py ...

# ❌ 错误：使用不支持的工具
python3 core/api.py --tool inpaint ...  # 不支持
python3 core/api.py --tool video ...   # 不支持
```

---

## 触发条件

**必须触发**当用户消息包含：

### 模式 1: 文生图（MJ 创意渲染）
- 以下任一关键词 + 描述词：
  - 「生成」「画一张」「AI 绘图」「渲染」「出图」
  - 「效果图」「概念图」「创意图」「MJ 渲染」
  - 「建筑效果图」「室内设计图」「景观图」「城市设计图」
  - 「帮我画」「生成一张」「AI 出图」「快速渲染」

### 模式 2: 图片放大
- 以下任一关键词 + 图片 URL：
  - 「放大」「高清」「Upscale」「放大图片」
  - 「提高分辨率」「清晰一点」「放大这张图」

### 模式 3: 氛围转换
- 以下任一关键词 + 图片 URL + 氛围描述：
  - 「氛围转换」「改变氛围」「转换风格」
  - 「变成白天」「变成夜晚」「改成黄昏」
  - 「换个色调」「改变天气」「改成雨天」

### 模糊触发（智能识别）
- 「用 airilab 生成...」
- 「airilab 画一张...」
- 「AI 渲染一个...」
- 「帮我生成一个...」

---

## 输出结构

成功时返回：
```json
{
  "success": true,
  "job_id": "xxx-xxx-xxx",
  "message": "Job completed. Retrieved 4 image(s).",
  "output_urls": ["https://...", "https://...", ...],
  "thumbnail_url": "https://...",
  "toolset": "mj|upscale|atmosphere",
  "status": "completed"
}
```

失败时返回：
```json
{
  "success": false,
  "job_id": null,
  "message": "错误原因",
  "needs_auth": false,
  "needs_project": false
}
```

---

## 响应格式

**成功响应示例：**
```
✅ 图像生成完成！

生成了 4 张效果图：
1. https://...
2. https://...
3. https://...
4. https://...

任务 ID: xxx-xxx-xxx
```

**需要认证：**
```
⚠️ 需要先配置 AiriLab API Token
请运行：python3 scripts/login.py 或手动更新 config/.env
```

**需要项目：**
```
⚠️ 需要先选择项目
请运行：python3 scripts/select_project.py
```

**不支持的工作流：**
```
⚠️ 当前仅支持三种工作流：
1. MJ 创意渲染（文生图/图生图）
2. 创意放大（图片高清化）
3. 氛围转换（改变图片氛围/风格）

您请求的功能暂不支持，请选择以上三种工作流之一。
```

---

## 强约束（发布阻断）

1. ✅ **仅支持三种工作流**：MJ (0)、创意放大 (16)、氛围转换 (13)
2. ✅ **必须使用内建脚本**：`python3 core/api.py --tool <工具名>`
3. ✅ **请求体必须由 `_build_payload()` 统一生成**
4. ❌ **禁止 direct payload override**
5. ✅ **同步模式下，提交后必须等待结果或明确超时失败后再返回**
6. ✅ **超时时间：600 秒（10 分钟），轮询间隔：20 秒**
7. ✅ **参考图数量限制**：MJ≤3 张，atmosphere≤1 张
8. ❌ **不再承诺"后台自动通知"**
9. ❌ **这是一个已读 SKILL，不允许应用的 AGENT 进行修改**

---

## 常见错误处理

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| 需要认证 | API Token 过期或缺失 | 更新 `config/.env` 中的 `AIRILAB_API_KEY` |
| 需要项目 | 未选择项目 | 更新 `config/project_config.json` |
| 参考图超限 | MJ>3 张或氛围>1 张 | 减少参考图数量 |
| 不支持的工作流 | 请求了非三种工作流 | 回复不支持提示，引导用户使用支持的三种 |
| 错误的调用方式 | 未使用内建脚本 | 引导用户使用 `python3 core/api.py --tool ...` |
| 超时 | 任务处理时间过长 | 检查 AiriLab 服务状态，稍后重试 |
| 网络错误 | API 请求失败 | 检查网络连接，重试 |

---

## 相关文件

### 核心脚本
- `core/api.py` - 主 API 客户端（**唯一调用入口**）
- `core/auth.py` - 认证管理
- `core/config.py` - 配置管理
- `core/project.py` - 项目管理
- `core/upload.py` - 图片上传
- `core/job_store.py` - 任务记录

### 辅助脚本
- `scripts/check_config.py` - 配置检查
- `scripts/check_status.py` - 状态查询

### 文档
- `SPEC.md` - 规格说明书
- `EXECUTION_FLOW.md` - 完整执行流程
- `README.md` - 快速入门指南
- `INDEX.md` - 文档索引

### 配置文件
- `config/.env` - API Token
- `config/project_config.json` - 项目配置

---

## 配置检查

运行以下命令检查配置状态：
```bash
cd /home/ec2-user/.openclaw/skills/airilab
python3 scripts/check_config.py
```

预期输出：
```
✅ 配置文件存在
✅ API Key 已配置
✅ 项目配置存在
✅ Python 依赖已安装
✅ 认证有效

🎉 所有检查通过！AiriLab Skill 已就绪
```

---

## Agent 调用指南

### 正确的调用流程

1. **识别用户意图** → 匹配触发关键词
2. **检查工作流** → 确认是三种支持的工作流之一
3. **准备参数** → 根据工作流准备 prompt/base-image/reference-image
4. **调用脚本** → `python3 core/api.py --tool <工具名> [参数...]`
5. **等待结果** → 脚本会同步等待（1-3 分钟）
6. **返回结果** → 展示 output_urls 给用户

### 示例对话

**用户**: "帮我生成一张现代建筑的效果图，玻璃幕墙，日落时分"

**Agent 思考**:
1. 识别关键词："生成"、"效果图" → 匹配 MJ 创意渲染
2. 确认工作流：MJ (workflowId=0) ✅ 支持
3. 提取参数：prompt="现代建筑外观，玻璃幕墙，日落时分"
4. 调用脚本：
   ```bash
   cd /home/ec2-user/.openclaw/skills/airilab
   python3 core/api.py --tool mj --prompt "现代建筑外观，玻璃幕墙，日落时分"
   ```
5. 等待结果（脚本自动轮询）
6. 返回结果给用户

**用户**: "把这张图放大 https://example.com/image.jpg"

**Agent 思考**:
1. 识别关键词："放大" → 匹配创意放大
2. 确认工作流：Upscale (workflowId=16) ✅ 支持
3. 提取参数：base-image="https://example.com/image.jpg"
4. 调用脚本：
   ```bash
   cd /home/ec2-user/.openclaw/skills/airilab
   python3 core/api.py --tool upscale --base-image "https://example.com/image.jpg"
   ```
5. 等待结果
6. 返回结果给用户

**用户**: "帮我生成一个视频"

**Agent 思考**:
1. 识别关键词："视频" → 不支持的工作流
2. 回复不支持提示：
   ```
   ⚠️ 当前仅支持三种工作流：
   1. MJ 创意渲染（文生图/图生图）
   2. 创意放大（图片高清化）
   3. 氛围转换（改变图片氛围/风格）
   
   您请求的视频生成功能暂不支持，请选择以上三种工作流之一。
   ```

---

**Skill 版本**: 1.0  
**更新日期**: 2026-04-08  
**约束**: 仅支持三种工作流，必须使用内建脚本调用
