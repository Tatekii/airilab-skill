# AiriLab Skill 自动启动配置完成

**配置日期**: 2026-03-31  
**状态**: ✅ 已完成

---

## 🎯 实现功能

### 1. 安装后自动启动
**触发时机**: Skill 安装完成后  
**执行脚本**: `scripts/post-install.sh`

**自动执行流程**:
```
安装 Skill
    ↓
执行 post-install.sh
    ↓
1. 检查 Token 配置
2. 检查项目配置
3. 自动启动 worker
    ↓
显示使用指南
```

**输出示例**:
```
╔═══════════════════════════════════════════════════╗
║     🎨 AiriLab Skill 安装后配置                   ║
╚═══════════════════════════════════════════════════╝

📝 Step 1/3: 检查登录状态...
✅ Token 已配置
   手机号：13828760860

📁 Step 2/3: 检查项目配置...
✅ 项目已配置
   项目：test

🚀 Step 3/3: 启动后台服务...
✅ Worker 已成功启动！
```

---

### 2. 后台服务自动运行
**守护进程**: `scheduler/worker.py`  
**启动方式**: `scripts/start-worker.sh`

**功能**:
- ✅ PID 文件管理（避免重复启动）
- ✅ 日志输出到 `worker.log`
- ✅ 自动重启（通过 crontab @reboot）

**管理命令**:
```bash
# 启动
~/.openclaw/skills/airilab/scripts/start-worker.sh

# 查看状态
ps aux | grep worker.py

# 查看日志
tail -f ~/.openclaw/skills/airilab/scheduler/worker.log

# 停止
kill $(cat ~/.openclaw/skills/airilab/scheduler/worker.pid)
```

---

### 3. 开机自启
**机制**: crontab @reboot  
**配置命令**: `scripts/setup-autostart.sh`

**Cron 条目**:
```cron
@reboot /home/ec2-user/.openclaw/skills/airilab/scripts/start-worker.sh
```

**效果**: 系统重启后自动启动 worker

---

## 📁 新增文件

| 文件 | 用途 | 大小 |
|------|------|------|
| `scripts/post-install.sh` | 安装后配置脚本 | 2.0 KB |
| `scripts/start-worker.sh` | Worker 启动脚本 | 1.5 KB |
| `scripts/setup-autostart.sh` | 开机自启配置 | 0.9 KB |
| `scheduler/worker.pid` | PID 文件 | - |

---

## 🔧 使用流程

### 新用户首次安装

```bash
# 1. 安装 Skill（通过 OpenClaw）
openclaw skills install airilab

# 2. 自动执行配置（或手动执行）
~/.openclaw/skills/airilab/scripts/post-install.sh

# 3. 配置开机自启（可选）
~/.openclaw/skills/airilab/scripts/setup-autostart.sh
```

### 日常使用

```bash
# 发送图像修改指令
[发送图片] + "把这张图转为冬季夜晚"

# 后台自动处理：
# 1. 上传图片到 S3
# 2. 提交任务到 AiriLab API
# 3. worker 轮询任务状态
# 4. 完成后推送结果到聊天
```

### 查看任务状态

```bash
# 查看正在处理的任务
cat ~/.openclaw/skills/airilab/scheduler/jobs.db | sqlite3 "SELECT * FROM jobs WHERE status='pending'"

# 查看最近日志
tail -f ~/.openclaw/skills/airilab/scheduler/worker.log
```

---

## 📊 当前状态

```
=== Worker 状态 ===
进程状态：✅ 运行中
PID: 1195027
启动时间：2026-03-31 11:46:13
日志文件：/home/ec2-user/.openclaw/skills/airilab/scheduler/worker.log

=== 配置状态 ===
Token 配置：✅ 已登录 (138****0860)
项目配置：✅ test (190177)
开机自启：✅ 已配置

=== 任务状态 ===
待处理任务：1 个
最近任务：a5d320b4-d4ce-4c0d-8e4d-9aab865a9c32
```

---

## 🎯 自动启动机制对比

| 方案 | 优点 | 缺点 | 采用状态 |
|------|------|------|---------|
| **systemd 用户服务** | 标准、功能强 | EC2 环境权限问题 | ❌ 不兼容 |
| **systemd 系统服务** | 标准、功能强 | 需要 sudo | ❌ 未采用 |
| **crontab @reboot** | 简单、兼容性好 | 功能有限 | ✅ 已采用 |
| **nohup 后台** | 最简单 | 重启后需手动 | ✅ 配合使用 |

---

## 📝 SKILL.md 更新

**新增章节**:
- 🔧 安装后自动启动
- 相关文件列表
- 后台服务管理命令

**触发场景描述增强**:
- 添加了详细的用户指令示例
- 明确了自动调用的条件

---

## 🧪 测试验证

### 1. 测试 post-install.sh
```bash
./scripts/post-install.sh
# 输出：配置完成信息 ✅
```

### 2. 测试 start-worker.sh
```bash
./scripts/start-worker.sh
# 输出：Worker 已成功启动 ✅
```

### 3. 测试 worker 功能
```bash
# 查看日志
tail -f scheduler/worker.log
# 输出：轮询日志正常 ✅
```

### 4. 测试开机自启
```bash
# 验证 crontab
crontab -l | grep start-worker
# 输出：@reboot 配置存在 ✅
```

---

## 💡 最佳实践

### 1. 定期检查 worker 状态
```bash
# 添加到 HEARTBEAT.md
- 检查 airilab worker 是否运行
- 查看 scheduler/worker.log 有无错误
```

### 2. 日志轮转（可选）
```bash
# 添加到 crontab
0 0 * * * find ~/.openclaw/skills/airilab/scheduler -name "*.log" -mtime +7 -delete
```

### 3. 监控待处理任务
```bash
# 如果 pending 任务过多，检查 API 或 Token
python3 scripts/check_status.py --job-id <job_id>
```

---

## 🎉 总结

**AiriLab Skill 现在具备完整的自动启动能力**:

1. ✅ **安装后自动配置** - post-install.sh
2. ✅ **后台服务自动运行** - start-worker.sh
3. ✅ **开机自启** - crontab @reboot
4. ✅ **完善的日志管理** - logging 模块
5. ✅ **简单的管理命令** - 启动/停止/查看

**用户体验**:
- 安装后无需手动配置
- 任务完成后自动推送结果
- 系统重启后自动恢复服务

**维护简单**:
- 日志文件清晰
- PID 文件管理
- 标准脚本工具

---

**配置完成时间**: 2026-03-31 11:46 UTC  
**下一步**: 正常使用，享受自动化的便利！🚀
