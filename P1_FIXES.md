# P1 问题修复报告

**修复日期**: 2026-03-31  
**修复者**: AI Assistant  
**状态**: ✅ 已完成

---

## 📋 修复清单

| # | 问题 | 优先级 | 状态 | 文件 |
|---|------|--------|------|------|
| 1 | systemd 服务配置 | P1 | ✅ 完成 | `scripts/install-systemd-service.sh` |
| 2 | logging 模块 | P1 | ✅ 完成 | `scheduler/worker.py` |
| 3 | Token 验证改进 | P1 | ✅ 完成 | `core/config.py` |
| 4 | 简化项目选择 | P1 | ✅ 完成 | `core/project.py` |

---

## 1️⃣ systemd 服务配置

### 问题
Worker 需要手动启动，没有开机自启

### 解决方案
创建 systemd 服务安装脚本

**文件**: `scripts/install-systemd-service.sh`

**使用方法**:
```bash
# 安装服务
chmod +x scripts/install-systemd-service.sh
./scripts/install-systemd-service.sh
```

**服务配置**:
```ini
[Unit]
Description=AiriLab Background Worker for task polling
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/ec2-user/.openclaw/skills/airilab/scheduler/worker.py
Restart=always
RestartSec=10
User=ec2-user
WorkingDirectory=/home/ec2-user/.openclaw/skills/airilab/scheduler

[Install]
WantedBy=default.target
```

**常用命令**:
```bash
# 查看状态
systemctl --user status airilab-worker

# 停止服务
systemctl --user stop airilab-worker

# 重启服务
systemctl --user restart airilab-worker

# 查看日志
journalctl --user -u airilab-worker -f
```

---

## 2️⃣ logging 模块

### 问题
使用 `print()` 而非 logging，不便于调试和日志管理

### 解决方案
全面替换为 Python logging 模块

**文件**: `scheduler/worker.py`

**配置**:
```python
import logging

LOG_FILE = Path(__file__).parent / 'worker.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('airilab-worker')
```

**日志级别使用**:
- `logger.info()` - 正常操作（任务完成、处理中）
- `logger.warning()` - 警告（Token 即将过期、未知状态）
- `logger.error()` - 错误（任务失败、网络错误）
- `logger.debug()` - 调试信息（详细流程）

**日志输出示例**:
```
2026-03-31 11:40:15 - airilab-worker - INFO - 🔍 检查任务：977f1b72-3e22-4dc3-93da-c360da9ffef2 (尝试 1/120)
2026-03-31 11:40:15 - airilab-worker - INFO - ✅ 任务完成：977f1b72-3e22-4dc3-93da-c360da9ffef2
2026-03-31 11:40:16 - airilab-worker - INFO - 📬 通知已写入：/home/ec2-user/.openclaw/completions/airilab_977f1b72_20260331_114016.md
```

---

## 3️⃣ Token 验证改进

### 问题
`is_token_valid()` 只做格式检查，不验证是否过期

### 解决方案
解析 JWT payload 的 `exp` 字段检查过期时间

**文件**: `core/config.py`

**修改前**:
```python
def is_token_valid(self, token: str) -> bool:
    # 只检查格式
    parts = token.split('.')
    if len(parts) != 3:
        return False
    if len(token) < 50:
        return False
    return True  # ❌ 没有验证过期时间
```

**修改后**:
```python
def is_token_valid(self, token: str) -> bool:
    try:
        import base64
        import json
        
        parts = token.split('.')
        if len(parts) != 3:
            return False
        
        # 解析 payload
        payload = parts[1]
        payload += '=' * (-len(payload) % 4)  # 补全 padding
        decoded = json.loads(base64.urlsafe_b64decode(payload))
        
        # 检查过期时间
        exp = decoded.get('exp')
        if exp:
            expiry = datetime.fromtimestamp(exp)
            if datetime.now() >= expiry:
                return False  # 已过期
        
        return True
    except Exception:
        return False
```

**影响**:
- ✅ 自动检测 Token 是否过期
- ✅ 避免使用过期 Token 导致 API 调用失败
- ✅ 提前提示用户重新登录

---

## 4️⃣ 简化项目选择

### 问题
`parse_selection()` 支持太多格式，容易混淆

### 解决方案
简化为只支持 projectId 或项目名称

**文件**: `core/project.py`

**修改前**:
```python
# 支持 3 种格式：
"170923"              # projectId
"用 My Project 1"      # 项目名称
"选择 团队 1 项目 2"     # 序号（复杂）
```

**修改后**:
```python
# 只支持 2 种格式：
"170923"              # projectId（纯数字）
"My Project 1"        # 项目名称（模糊匹配）
```

**代码变更**:
```python
def parse_selection(self, user_input: str, projects: List[Dict]) -> Optional[Dict]:
    user_input = user_input.strip()
    
    # 1. 尝试解析 projectId（纯数字）
    if user_input.isdigit():
        project_id = int(user_input)
        # ... 查找匹配的项目
    
    # 2. 尝试解析项目名称（模糊匹配）
    for team in projects:
        for proj in team.get('projects', []):
            proj_name = proj.get('projectName', '')
            if user_input.lower() in proj_name.lower():
                return {...}
    
    return None
```

**影响**:
- ✅ 减少用户困惑
- ✅ 降低解析错误
- ✅ 代码更简洁

---

## 📊 测试验证

### 1. 测试 systemd 服务
```bash
# 安装服务
./scripts/install-systemd-service.sh

# 验证状态
systemctl --user status airilab-worker
```

### 2. 测试 logging
```bash
# 启动 worker
python3 scheduler/worker.py

# 检查日志
tail -f scheduler/worker.log
```

### 3. 测试 Token 验证
```python
from core.config import AiriLabConfig
config = AiriLabConfig()
token = config.get_token()
print(config.is_token_valid(token))  # 应该返回 True 或 False（如果过期）
```

### 4. 测试项目选择
```python
from core.project import AiriLabProject
proj = AiriLabProject()

# 测试 projectId
result = proj.parse_selection("170923", projects)

# 测试项目名称
result = proj.parse_selection("My Project", projects)
```

---

## 📁 文件变更清单

| 文件 | 变更类型 | 行数变化 | 说明 |
|------|---------|---------|------|
| `scripts/install-systemd-service.sh` | 新增 | +45 | systemd 服务安装脚本 |
| `scripts/P1_FIXES.md` | 新增 | +200 | 本文档 |
| `scheduler/worker.py` | 修改 | +50 / -30 | logging 模块 |
| `core/config.py` | 修改 | +30 / -15 | Token 验证 |
| `core/project.py` | 修改 | +20 / -30 | 简化项目选择 |
| `core/update_*.py` | 临时 | 已删除 | 更新脚本（已清理） |

---

## 🎯 后续工作

### P2 优先级（可选优化）
1. 添加单元测试
2. 配置文件化 API 端点
3. 填充 workflows/ 目录
4. 添加 requirements.txt
5. 添加开发者文档

### P3 优先级（长期）
1. 添加重试机制
2. 性能监控
3. 多用户并发支持

---

**修复完成时间**: 2026-03-31 11:40 UTC  
**下一步**: 测试 systemd 服务并验证所有功能正常
