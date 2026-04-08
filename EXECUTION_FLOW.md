# AiriLab Skill 完整执行流程

## 流程总览

```
用户请求 → 鉴权检查 → 项目选择 → 图片上传 (可选) → 构建请求 → 提交任务 → 同步轮询 → 获取结果 → 保存记录
```

**核心原则：每一步都有前置条件，必须按顺序执行**

---

## Step 1: 用户登录鉴权

### 触发时机
- 首次使用 skill
- Token 过期或无效
- Token 文件不存在

### 前置条件
- 用户手机号
- 能接收短信验证码

### 执行流程

```python
# 1. 检查现有 Token
config.get_token() → token

# 2. 验证 Token 格式
config.is_token_valid(token) → bool
# 检查:
# - JWT 格式正确 (3 段)
# - 未过期 (exp 字段)
# - 长度 ≥ 50

# 3. 验证 Token 有效性
auth.validate_token(token) → bool
# 调用 GET /api/user/getUserInfo
# 检查 HTTP 200

# 4. 如需登录
auth.send_verification_code(phone) → 发送验证码
auth.verify_code(phone, code) → 获取新 Token
config.save_token(token, phone) → 保存到 config/.env
```

### 输出
```python
{
    "authenticated": True/False,
    "needs_login": True/False,
    "token": "eyJhbGc...",
    "message": "authenticated"
}
```

### 失败处理
- ❌ Token 不存在 → 需要登录
- ❌ Token 格式错误 → 需要登录
- ❌ Token 已过期 → 需要登录
- ❌ API 验证失败 → 需要登录

### 相关文件
- `core/auth.py` - 认证管理
- `core/config.py` - Token 存储
- `config/.env` - Token 文件

---

## Step 2: Team 和 Project 选择

### 触发时机
- 首次使用
- 项目配置不存在
- 用户主动切换项目

### 前置条件
- ✅ **Step 1 已完成** - 必须有有效 Token

### 执行流程

```python
# 1. 检查现有项目配置
config.get_project() → project_config
# 检查 config/project_config.json
# 必需字段：teamId, projectId, projectName

# 2. 如无配置，获取团队和项目列表
project.get_teams_and_projects(token) → List[Dict]
# GET /api/Team/GetUserTeams
# GET /api/Accounts/GetAllProjectsUser?teamId={teamId}

# 3. 展示项目列表
project.display_projects(teams_and_projects) → str

# 4. 用户选择
project.parse_selection(user_input, projects) → selected_project
# 支持:
# - projectId (数字)
# - 项目名称 (模糊匹配)

# 5. 保存配置
config.save_project(teamId, projectId, projectName) → bool
```

### 输出
```python
{
    "teamId": 52,
    "projectId": 130538,
    "projectName": "lowcode_debug",
    "selected_at": "2026-04-08T04:00:00"
}
```

### 失败处理
- ❌ 无 Token → 返回 Step 1
- ❌ API 调用失败 → 重试或提示网络错误
- ❌ 选择无效 → 重新选择

### 相关文件
- `core/project.py` - 项目管理
- `core/config.py` - 项目配置存储
- `config/project_config.json` - 项目配置文件

---

## Step 3: 按需上传图片（仅当需要参考图/底图时）

### 触发时机
- 用户提供本地图片文件
- 工作流需要参考图或底图

### 前置条件
- ✅ **Step 1 已完成** - 必须有有效 Token
- ✅ **Step 2 已完成** - 必须有 teamId
- 本地图片文件存在

### 执行流程

```python
# 1. 检查文件
Path(file_path).exists() → bool

# 2. 上传图片
upload.upload_image(
    file_path=file_path,
    image_part="base-image" | "reference-image" | "mask-image",
    team_id=teamId
) → Dict

# POST /api/Workflow/UploadMedia
# Headers: Authorization: Bearer {token}
# Files: myFile (image/jpeg)
# Data: imagePart, teamId
```

### 输出
```python
{
    "success": True,
    "url": "https://airi-production.s3.cn-north-1.amazonaws.com.cn/...",
    "message": "Upload succeeded"
}
```

### 失败处理
- ❌ Token 不存在 → 返回 Step 1
- ❌ 文件不存在 → 提示文件路径错误
- ❌ 配额超限 (status=203) → 提示充值
- ❌ 网络错误 → 重试

### 图片类型
| image_part | 用途 | 工作流 |
|------------|------|--------|
| base-image | 底图 | upscale, atmosphere |
| reference-image | 参考图 | MJ (≤3 张), atmosphere (≤1 张) |
| mask-image | 蒙版图 | inpaint (未实现) |

### 相关文件
- `core/upload.py` - 图片上传
- `config/.env` - Token

---

## Step 4: 构建不同工作流的 API 请求

### 触发时机
- 鉴权和项目配置完成后
- 图片上传完成后（如有）

### 前置条件
- ✅ **Step 1 已完成** - 必须有有效 Token
- ✅ **Step 2 已完成** - 必须有项目配置
- ✅ **Step 3 已完成** - 如有本地图片需先上传

### 执行流程

```python
# 强约束：必须使用 _build_payload() 方法
# 禁止 direct payload override

api._build_payload(
    workflow_id=workflow_id,
    project=project_config,
    base_image=base_image_url,      # 可选
    prompt=prompt_text,             # 可选
    reference_images=ref_urls,      # 可选
    image_count=4,                  # 可选
    **kwargs
) → payload_dict
```

### 工作流参数

#### 4.1 MJ 创意渲染 (workflowId=0)
```python
{
    "workflowId": 0,
    "prompt": "现代建筑外观，玻璃幕墙",
    "additionalPrompt": "现代建筑外观，玻璃幕墙",
    "referenceImage": [{"url": url1, "type": 0}, ...],  # ≤3 张
    "imageCount": 4,
    "designLibraryId": 99,
    "styleId": 9999,
    # ... 其他固定参数
}
```

**前置条件：**
- prompt 必填
- reference_images 可选（≤3 张）

#### 4.2 创意放大 (workflowId=16)
```python
{
    "workflowId": 16,
    "baseImage": "https://...",
    "initialCNImage": None,
    "additionalPrompt": "",
    "referenceImage": [],  # 不支持参考图
    "imageCount": 1,
    "width": 1288,
    "height": 816,
    # ... 其他固定参数
}
```

**前置条件：**
- base_image 必填
- 不支持参考图

#### 4.3 氛围转换 (workflowId=13)
```python
{
    "workflowId": 13,
    "baseImage": "https://...",
    "prompt": "转换为夜晚氛围",
    "additionalPrompt": "转换为夜晚氛围",
    "referenceImage": [{"url": url, "type": 0}],  # ≤1 张
    "imageCount": 4,
    # ... 其他固定参数
}
```

**前置条件：**
- base_image 必填
- prompt 必填
- reference_image 可选（≤1 张）

### 强约束
1. ✅ 必须由 `_build_payload()` 统一生成
2. ❌ 禁止 direct payload override
3. ✅ 参考图数量限制必须检查

### 相关文件
- `core/api.py` - `_build_payload()` 方法

---

## Step 5: 提交任务

### 触发时机
- payload 构建完成后

### 前置条件
- ✅ **Step 1 已完成** - 必须有有效 Token
- ✅ **Step 2 已完成** - 必须有项目配置
- ✅ **Step 4 已完成** - 必须有合法 payload

### 执行流程

```python
# 1. 构建请求头
headers = {
    "Authorization": f"Bearer {token}",
    "referer": f"https://cn.airilab.com/stdio/workspace/{projectId}",
    "content-type": "application/json",
}

# 2. 提交任务
response = requests.post(
    "https://cn.airilab.com/api/Universal/Generate",
    headers=headers,
    json=payload,
    timeout=30
)

# 3. 解析结果
result = response.json()
job_id = result.get("data", {}).get("jobId")
```

### 输出
```python
{
    "success": True,
    "job_id": "xxx-xxx-xxx",
    "message": "提交成功"
}
```

### 失败处理
- ❌ status != 200 → 返回 API 错误信息
- ❌ jobId 缺失 → 返回错误
- ❌ 网络错误 → 重试或返回错误

### 相关文件
- `core/api.py` - `submit_task()` 方法
- API: `POST /api/Universal/Generate`

---

## Step 6: 同步轮询等待

### 触发时机
- 任务提交成功后
- **在当前调用内阻塞等待**

### 前置条件
- ✅ **Step 5 已完成** - 必须有 jobId
- ✅ **Step 1 已完成** - 必须有有效 Token

### 执行流程

```python
def _wait_for_result(token, project, job_id):
    deadline = time.time() + SYNC_TIMEOUT_SECONDS  # 600 秒
    last_status = "pending"
    
    while time.time() < deadline:
        # 1. 检查状态
        status = _check_job_status(token, job_id)
        # GET /api/Universal/Job/{jobId}
        
        # 2. 记录事件（可选）
        append_job_event(job_id, "status_polled", f"Polled status: {status}")
        
        # 3. 判断状态
        if status in {"pending", "processing"}:
            time.sleep(SYNC_POLL_INTERVAL_SECONDS)  # 20 秒
            continue
        
        if status == "failed":
            return {"success": False, "status": "failed", ...}
        
        # 4. 状态完成，获取结果
        fetch_result = _fetch_result(token, project, job_id)
        return fetch_result
    
    # 5. 超时
    return {"success": False, "status": last_status, "message": "Timed out"}
```

### 状态流转
```
pending → processing → completed
                     → failed
```

### 关键参数
| 参数 | 值 | 说明 |
|------|-----|------|
| SYNC_TIMEOUT_SECONDS | 600 | 超时时间（10 分钟） |
| SYNC_POLL_INTERVAL_SECONDS | 20 | 轮询间隔 |

### 失败处理
- ❌ 状态检查失败 → 重试
- ❌ 任务失败 → 返回失败原因
- ❌ 超时 → 返回超时错误

### 相关文件
- `core/api.py` - `_wait_for_result()`, `_check_job_status()`
- API: `GET /api/Universal/Job/{jobId}`

---

## Step 7: 拉回结果

### 触发时机
- 轮询状态为 completed 后

### 前置条件
- ✅ **Step 1 已完成** - 必须有有效 Token
- ✅ **Step 2 已完成** - 必须有项目配置
- ✅ **Step 6 已完成** - 状态必须为 completed

### 执行流程

```python
def _fetch_result(token, project, job_id):
    payload = {
        "projectId": project["projectId"],
        "teamId": project["teamId"],
        "language": "chs",
        "desiredGenerationId": job_id,
    }
    
    response = requests.post(
        "https://cn.airilab.com/api/CrudRouters/getOneRecord",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        timeout=30
    )
    
    result = response.json()
    data = result.get("data", {})
    models = data.get("projectGenerationModel", [])
    
    # 提取图片 URL
    model = models[0]
    medias = model.get("projectMedias", [])
    output_urls = [m.get("url", "") for m in medias if m.get("url")]
    thumbnail_url = output_urls[0] if output_urls else None
    
    # 识别工作流类型
    workflow_name = model.get("workflowName", "unknown")
    toolset_map = {"MJ": "mj", "Upscale": "upscale", "Trans": "atmosphere"}
    toolset = toolset_map.get(workflow_name.split()[0], "unknown")
    
    return {
        "success": True,
        "output_urls": output_urls,
        "thumbnail_url": thumbnail_url,
        "toolset": toolset,
        "message": f"Fetched {len(output_urls)} image(s)"
    }
```

### 输出
```python
{
    "success": True,
    "output_urls": [
        "https://airi-production.s3.cn-north-1.amazonaws.com.cn/...",
        "https://airi-production.s3.cn-north-1.amazonaws.com.cn/...",
        ...
    ],
    "thumbnail_url": "https://...",
    "toolset": "mj",
    "message": "Fetched 4 image(s)"
}
```

### 失败处理
- ❌ status != 200 → 返回 API 错误
- ❌ 无 generation model → 返回错误
- ❌ 无输出媒体 → 返回错误（可能还在处理）

### 相关文件
- `core/api.py` - `_fetch_result()` 方法
- API: `POST /api/CrudRouters/getOneRecord`

---

## Step 8: 保存任务记录（可选）

### 触发时机
- 任务完成后（成功或失败）

### 前置条件
- ✅ **Step 5 已完成** - 必须有 jobId

### 执行流程

```python
# 1. 初始化数据库
init_job_store()

# 2. 保存任务记录
save_job_record(
    job_id=job_id,
    user_id=user_id,
    chat_id=chat_id,
    tool=tool,
    input_params={"workflow_id": workflow_id, "payload": payload}
)

# 3. 记录事件
append_job_event(job_id, "submitted", "Job accepted by API (sync mode)")
append_job_event(job_id, "status_polled", "Polled status: completed")
append_job_event(job_id, "completed", "Job finished")
```

### 输出文件
- `scheduler/jobs.json` - 任务记录
- `scheduler/job_events.jsonl` - 事件日志

### 相关文件
- `core/job_store.py` - 任务记录管理
- `scheduler/jobs.json` - 任务数据库
- `scheduler/job_events.jsonl` - 事件日志

---

## 完整流程依赖图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         用户请求                                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 1: 用户登录鉴权                                                 │
│ 前置条件：无                                                         │
│ 输出：token                                                         │
│ 失败 → 需要登录                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 2: Team 和 Project 选择                                         │
│ 前置条件：Step 1 ✅ (token)                                         │
│ 输出：teamId, projectId, projectName                               │
│ 失败 → 需要选择项目                                                  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 3: 按需上传图片（可选）                                          │
│ 前置条件：Step 1 ✅ (token), Step 2 ✅ (teamId)                     │
│ 输出：image_url(s)                                                  │
│ 失败 → 文件错误或配额超限                                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 4: 构建不同工作流的 API 请求                                      │
│ 前置条件：Step 1 ✅, Step 2 ✅, Step 3 ✅ (如有图片)                │
│ 输出：payload                                                       │
│ 强约束：必须使用_build_payload()                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 5: 提交任务                                                     │
│ 前置条件：Step 1 ✅, Step 2 ✅, Step 4 ✅                           │
│ 输出：jobId                                                         │
│ 失败 → API 错误                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 6: 同步轮询等待                                                 │
│ 前置条件：Step 1 ✅, Step 5 ✅ (jobId)                              │
│ 输出：status (completed/failed/timeout)                            │
│ 超时：600 秒，轮询间隔：20 秒                                          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 7: 拉回结果                                                     │
│ 前置条件：Step 1 ✅, Step 2 ✅, Step 6 ✅ (status=completed)        │
│ 输出：output_urls, thumbnail_url, toolset                          │
│ 失败 → 无输出媒体                                                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 8: 保存任务记录（可选）                                          │
│ 前置条件：Step 5 ✅ (jobId)                                         │
│ 输出：jobs.json, job_events.jsonl                                  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 返回最终结果给用户                                                    │
│ - 成功：展示 output_urls                                            │
│ - 失败：展示错误原因和解决方案                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 关键约束总结

### 顺序约束
1. 必须先鉴权，才能选择项目
2. 必须先有项目配置，才能构建 payload
3. 必须先上传图片（如有），才能构建 payload
4. 必须先提交任务，才能轮询
5. 必须先轮询到 completed，才能获取结果

### 强约束（发布阻断）
1. ✅ payload 必须由 `_build_payload()` 统一生成
2. ❌ 禁止 direct payload override
3. ✅ 同步模式下必须等待结果或超时
4. ✅ 参考图数量限制（MJ≤3, atmosphere≤1）
5. ❌ 不再承诺"后台自动通知"

### 错误处理原则
- 任何一步失败，立即返回错误信息
- 明确指出需要哪个前置条件
- 提供修复建议

---

## 使用示例

### 示例 1: MJ 创意渲染（无参考图）
```bash
# 1. 检查配置
python3 scripts/check_config.py

# 2. 直接调用（自动完成所有步骤）
python3 core/api.py --tool mj --prompt "现代建筑外观，玻璃幕墙"
```

### 示例 2: MJ 带参考图
```bash
# 参考图会自动上传（如果是本地文件）
python3 core/api.py --tool mj \
  --prompt "基于参考图的室内设计" \
  --reference-image "https://example.com/image.jpg"
```

### 示例 3: 创意放大
```bash
python3 core/api.py --tool upscale \
  --base-image "https://example.com/image.jpg"
```

### 示例 4: 氛围转换
```bash
python3 core/api.py --tool atmosphere \
  --base-image "https://example.com/image.jpg" \
  --prompt "转换为夜晚氛围，暖色灯光"
```

---

## 配置检查清单

运行前检查：
- [ ] `config/.env` 存在且包含有效 AIRILAB_API_KEY
- [ ] `config/project_config.json` 存在且包含 teamId, projectId
- [ ] Python 依赖 requests 已安装
- [ ] 网络连接正常

运行检查命令：
```bash
cd /home/ec2-user/.openclaw/skills/airilab
python3 scripts/check_config.py
```

---

**文档版本**: 1.0  
**更新日期**: 2026-04-08
