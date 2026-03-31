---
name: airilab
description: AiriLab 统一技能 - AI 图像生成、转换、超分辨率。**触发场景**：用户发送图片并要求修改/转换/生成/放大/风格变化，如"把这张图变成冬季""生成 4 张变体""放大图片""换个天气""MJ 渲染"等图像相关指令时自动调用此技能。
homepage: https://cn.airilab.com
metadata: { "openclaw": { "emoji": "🎨", "requires": { "bins": ["curl", "python3"] } } }
---

# AiriLab 统一技能

> ⚙️ **v1.0 完全整合版** - 整合鉴权、上传、项目、API 调用于一体

---

## 🎯 功能概览

**AiriLab 统一技能** 整合了以下功能：

| 模块 | 原技能 | 功能 |
|------|--------|------|
| **鉴权** | airi-auth | Token 管理、验证码登录 |
| **上传** | airi-upload | 图片上传到 S3 |
| **项目** | airi-project | 团队和项目管理 |
| **API** | api-list | 图像生成、转换、超分辨率 |

---

## 🚀 快速开始

### 触发场景

当用户发送以下类型的消息时，**自动调用此技能**：

| 用户指令示例 | 触发的工作流 |
|-------------|-------------|
| "把这张图片转为冬季夜晚" | 氛围转换 (13) |
| "生成 4 张变体" / "MJ 渲染" | MJ 创意渲染 (4) |
| "放大这张图" / "超分辨率" | 创意超分辨率 (16) |
| "换个天气" / "改成雨天" | 氛围转换 (13) |
| "基于这张图生成类似的" | MJ 创意渲染 (4) |
| "高清放大" / "upscale" | 创意超分辨率 (16) |
| [发送图片] + "帮我处理一下" | 根据上下文判断 |

**关键识别点**：
- ✅ 用户发送了图片
- ✅ 指令中包含：转换/生成/放大/变体/风格/天气/季节/MJ/超分 等关键词
- ✅ 表达了图像修改的意图

### 首次使用流程

```
1. 用户：把这张图片转为冬季夜晚
   ↓
2. Bot: 检测到需要登录，请提供手机号
   ↓
3. 用户：13828760860
   ↓
4. Bot: 验证码已发送，请回复 6 位验证码
   ↓
5. 用户：961057
   ↓
6. Bot: ✅ 登录成功！正在处理...
   ↓
7. Bot: ✅ 图片已上传！请选择项目：
        【项目 1】My Project 1
        【项目 2】new project
        ...
   ↓
8. 用户：用 1
   ↓
9. Bot: ✅ 任务已提交！Job ID: xxx
        完成后将自动推送结果
   ↓
10. [后台轮询]
    ↓
11. Bot: ✅ 图片生成完成！
        ![图片 1](url)
        ![图片 2](url)
        ...
```

---

## 🛠️ 支持的工作流

| 工作流 | workflowId | 必填参数 | 可选参数 | 说明 |
|--------|-----------|---------|---------|------|
| **MJ 创意渲染** | `4` | `prompt` | `referenceImage` (≤3 张) | MidJourney 驱动 |
| **创意超分辨率** | `16` | `baseImage` | 无 | AI 增强放大 |
| **氛围转换** | `13` | `baseImage` | `prompt`, `referenceImage` (≤1 张) | 天气/季节转换 |

---

## ⚠️ Payload 强约束定义

### 1️⃣ MJ 创意渲染 (workflowId: 4)

**必填参数：**
- `prompt` (string): 提示词描述

**可选参数：**
- `referenceImage` (array): 参考图数组，**最多 3 张**
- `imageCount` (number): 生成图片数量 (1-4)

**示例：**
```json
{
  "workflowId": 4,
  "prompt": "modern building, glass facade, sunset",
  "referenceImage": [
    {"url": "https://.../ref1.jpg", "type": 0},
    {"url": "https://.../ref2.jpg", "type": 0}
  ],
  "imageCount": 4,
  "language": "chs",
  "teamId": 0,
  "projectId": 130538,
  "projectName": "lowcode"
}
```

---

### 2️⃣ 创意超分辨率 (workflowId: 16)

**必填参数：**
- `baseImage` (string): 待放大的图片 URL

**可选参数：**
- `width` (number): 目标宽度 (默认 1288)
- `height` (number): 目标高度 (默认 816)

**示例：**
```json
{
  "workflowId": 16,
  "baseImage": "https://.../original.jpg",
  "width": 1288,
  "height": 816,
  "language": "chs",
  "teamId": 0,
  "projectId": 130538,
  "projectName": "lowcode"
}
```

---

### 3️⃣ 氛围转换 (workflowId: 13)

**必填参数：**
- `baseImage` (string): 基图 URL

**可选参数：**
- `prompt` (string): 氛围描述
- `referenceImage` (array): 参考图数组，**最多 1 张**
- `imageCount` (number): 生成图片数量

**示例：**
```json
{
  "workflowId": 13,
  "baseImage": "https://.../base.jpg",
  "prompt": "winter night, snow covered, evening",
  "referenceImage": [
    {"url": "https://.../ref.jpg", "type": 0}
  ],
  "imageCount": 4,
  "language": "chs",
  "teamId": 0,
  "projectId": 130538,
  "projectName": "lowcode"
}
```

---

## 📁 配置管理

### 配置文件位置

| 配置 | 文件 | 说明 |
|------|------|------|
| **Token** | `~/.openclaw/skills/airilab/config/.env` | JWT Token |
| **项目** | `~/.openclaw/skills/airilab/config/project_config.json` | teamId, projectId, projectName |

### 配置命令

```bash
# 查看配置状态
python3 ~/.openclaw/skills/airilab/core/config.py status

# 清除 Token
python3 ~/.openclaw/skills/airilab/core/config.py clear-token

# 清除项目配置
python3 ~/.openclaw/skills/airilab/core/config.py clear-project

# 清除所有配置
python3 ~/.openclaw/skills/airilab/core/config.py clear-all
```

---

## 🔐 登录流程

### 自动登录

当 Token 不存在或失效时，系统会自动提示登录：

```
Bot: 检测到需要登录，请提供手机号
用户：13828760860
Bot: 验证码已发送，请回复 6 位验证码
用户：961057
Bot: ✅ 登录成功！
```

### 手动登录

```bash
# 发送验证码
python3 ~/.openclaw/skills/airilab/core/auth.py login --phone 13828760860

# 验证验证码
python3 ~/.openclaw/skills/airilab/core/auth.py login --phone 13828760860 --code 961057

# 退出登录
python3 ~/.openclaw/skills/airilab/core/auth.py logout
```

---

## 📊 项目管理

### 选择项目

首次使用时需要选择项目：

```
Bot: 请选择项目：
     【项目 1】My Project 1 (projectId: 170923)
     【项目 2】new project (projectId: 190175)
用户：用 1
Bot: ✅ 已选择：My Project 1
```

### 项目命令

```bash
# 列出所有项目
python3 ~/.openclaw/skills/airilab/core/project.py list

# 选择项目
python3 ~/.openclaw/skills/airilab/core/project.py select --selection "用 170923"

# 查看当前项目
python3 ~/.openclaw/skills/airilab/core/project.py show

# 清除项目配置
python3 ~/.openclaw/skills/airilab/core/project.py clear
```

---

## 🔄 后台调度器

### 启动调度器

```bash
# 前台运行（测试）
python3 ~/.openclaw/skills/airilab/scheduler/worker.py

# 后台运行
nohup python3 ~/.openclaw/skills/airilab/scheduler/worker.py > worker.log 2>&1 &

# systemd 服务（推荐）
sudo systemctl start airilab-worker
```

### 调度器功能

- 每 15 秒轮询 pending 任务
- 超时限制：15 分钟（超过视为失败）
- 完成后自动获取结果
- 失败时主动通知用户
- 任务状态持久化到 SQLite

---

## 📋 使用示例

### 示例 1：MJ 创意渲染

```
用户：生成一张现代高层办公楼的效果图
Bot: ✅ 任务已提交！Job ID: xxx
     完成后将自动推送结果
[后台轮询]
Bot: ✅ 图片生成完成！
     ![图片 1](url)
     ![图片 2](url)
     ...
```

### 示例 2：氛围转换

```
用户：把这张图片转为冬季夜晚 [图片]
Bot: ✅ 图片已上传！
     ✅ 任务已提交！Job ID: xxx
[后台轮询]
Bot: ✅ 图片生成完成！
     ![图片 1](url)
     ...
```

### 示例 3：超分辨率放大

```
用户：放大这张图片 [图片]
Bot: ✅ 图片已上传！
     ✅ 任务已提交！Job ID: xxx
[后台轮询]
Bot: ✅ 图片放大完成！
     ![图片](url)
```

---

## ⚠️ 禁止使用的字段

以下字段在所有工作流中都是**无效**的：

- ❌ `toolsetEntry`
- ❌ `toolsetLv2`
- ❌ `toolsetLv3`
- ❌ `*-container` (如 `prompt-container`, `styleReference-container`)
- ❌ 其他未在约束定义中列出的字段

---

## 📄 相关文件

| 文件 | 说明 |
|------|------|
| `core/config.py` | 统一配置管理 |
| `core/auth.py` | 鉴权管理 |
| `core/project.py` | 项目管理 |
| `core/upload.py` | 图片上传 |
| `core/api.py` | API 调用 |
| `workflows/` | 工作流定义 |
| `scheduler/worker.py` | 后台调度器 |
| `scripts/post-install.sh` | 安装后自动配置脚本 |
| `scripts/start-worker.sh` | 后台服务启动脚本 |

---

## 🔧 安装后自动启动

**AiriLab Skill 安装后会自动执行以下操作**:

1. ✅ 检查登录状态（Token 配置）
2. ✅ 检查项目配置
3. ✅ 自动启动后台调度器（worker）

**手动执行安装后配置**:
```bash
~/.openclaw/skills/airilab/scripts/post-install.sh
```

**后台服务管理**:
```bash
# 启动服务
~/.openclaw/skills/airilab/scripts/start-worker.sh

# 查看状态
ps aux | grep worker.py

# 查看日志
tail -f ~/.openclaw/skills/airilab/scheduler/worker.log

# 停止服务
kill $(cat ~/.openclaw/skills/airilab/scheduler/worker.pid)
```

**开机自启** (可选):
```bash
# 添加到 crontab
(crontab -l 2>/dev/null; echo "@reboot ~/.openclaw/skills/airilab/scripts/start-worker.sh") | crontab -
```

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | 2026-03-31 | 初始整合版本（整合 airi-auth, airi-upload, airi-project, api-list） |

---

_整合完成时间：2026-03-31_
_整合者：克斯托斯 -9 数据贤者_
