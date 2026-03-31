#!/usr/bin/env python3
"""
AiriLab 后台轮询守护进程

职责：
1. 定期查询 pending 状态的任务
2. 检查任务状态
3. 完成后获取结果并通知用户

运行方式：
- 手动：python3 ~/.openclaw/skills/airilab/scheduler/worker.py
- 后台：nohup python3 worker.py > worker.log 2>&1 &
- systemd: 创建 systemd 服务（推荐）

依赖：
- airilab.core (内置)
"""

import sqlite3
import json
import time
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# ==================== Logging 配置 ====================

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

# 添加 airilab 到路径
AIRILAB_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(AIRILAB_PATH))

# ==================== 配置 ====================

SCRIPTS_DIR = Path(__file__).parent.parent / 'scripts'
DATA_DIR = Path(__file__).parent
DB_PATH = DATA_DIR / 'jobs.db'
POLL_INTERVAL = 15  # 轮询间隔（秒）
MAX_ATTEMPTS = 60  # 最大轮询次数（15 分钟 = 60 次 * 15 秒）
TIMEOUT_MINUTES = 15  # 超时时间（分钟）

# 状态常量
STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"


def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            chat_id TEXT NOT NULL,
            tool TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            submitted_at TEXT,
            started_at TEXT,
            completed_at TEXT,
            input_params TEXT,
            output_url TEXT,
            thumbnail_url TEXT,
            error_message TEXT,
            attempts INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_user ON jobs(user_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_submitted ON jobs(submitted_at)
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ 数据库初始化完成")


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def save_job(job_id: str, user_id: str, chat_id: str, tool: str, input_params: dict):
    """保存新任务"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO jobs 
        (job_id, user_id, chat_id, tool, status, submitted_at, input_params)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        job_id, user_id, chat_id, tool, STATUS_PENDING,
        datetime.now().isoformat(), json.dumps(input_params)
    ))
    
    conn.commit()
    conn.close()
    logger.info(f"💾 任务已保存：{job_id}")


def get_pending_jobs():
    """获取所有 pending 状态的任务"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM jobs 
        WHERE status IN (?, ?) 
        ORDER BY submitted_at ASC
        LIMIT 50
    ''', (STATUS_PENDING, STATUS_PROCESSING))
    
    jobs = cursor.fetchall()
    conn.close()
    
    if jobs:
        logger.debug(f"📋 获取到 {len(jobs)} 个待处理任务")
    
    return jobs


def update_job_status(job_id: str, status: str, output_url: str = None, 
                      thumbnail_url: str = None, error_message: str = None):
    """更新任务状态"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if status == STATUS_COMPLETED:
        cursor.execute('''
            UPDATE jobs 
            SET status = ?, completed_at = ?, output_url = ?, thumbnail_url = ?
            WHERE job_id = ?
        ''', (status, datetime.now().isoformat(), output_url, thumbnail_url, job_id))
        logger.info(f"✅ 任务状态更新为完成：{job_id}")
    
    elif status == STATUS_FAILED:
        cursor.execute('''
            UPDATE jobs 
            SET status = ?, completed_at = ?, error_message = ?
            WHERE job_id = ?
        ''', (status, datetime.now().isoformat(), error_message, job_id))
        logger.warning(f"❌ 任务状态更新为失败：{job_id} - {error_message}")
    
    else:
        cursor.execute('''
            UPDATE jobs 
            SET status = ?, attempts = attempts + 1
            WHERE job_id = ?
        ''', (status, job_id))
        logger.debug(f"⏳ 任务状态更新：{job_id} -> {status}")
    
    conn.commit()
    conn.close()


def check_job_status(job_id: str) -> str:
    """检查任务状态"""
    script_path = SCRIPTS_DIR / 'check_status.py'
    
    try:
        result = subprocess.run(
            ['python3', str(script_path), '--job-id', job_id],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # 检查是否有鉴权错误
        if '需要鉴权' in result.stdout or '未找到 Token' in result.stdout:
            logger.warning(f"🔐 鉴权错误：Token 可能过期 (job: {job_id})")
            return "auth_error"
        
        # 解析输出
        for line in result.stdout.split('\n'):
            if '状态:' in line:
                status = line.split(':')[1].strip()
                logger.debug(f"🔍 任务 {job_id} 状态：{status}")
                return status
        
        logger.warning(f"⚠️ 无法解析任务状态：{job_id}")
        return "unknown"
        
    except subprocess.TimeoutExpired:
        logger.error(f"⏱️ 检查任务状态超时：{job_id}")
        return "error"
    except Exception as e:
        logger.error(f"❌ 检查任务状态失败 {job_id}: {e}")
        return "error"


def fetch_result(job_id: str) -> dict:
    """获取任务结果"""
    script_path = SCRIPTS_DIR / 'fetch.py'
    
    try:
        result = subprocess.run(
            ['python3', str(script_path), '--job-id', job_id, '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # 检查是否有鉴权错误
        if '需要鉴权' in result.stdout or '未找到 Token' in result.stdout:
            logger.warning(f"🔐 鉴权错误：Token 可能过期 (job: {job_id})")
            return {'error': 'auth_required'}
        
        # 解析 JSON 输出
        try:
            # 查找 JSON 部分（可能在输出中间）
            import re
            json_match = re.search(r'\{.*\}', result.stdout, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                logger.info(f"✅ 成功获取任务结果 {job_id}: {len(parsed.get('output_urls', []))} 张图片")
                return parsed
            else:
                # 尝试直接解析整个输出
                parsed = json.loads(result.stdout.strip())
                logger.info(f"✅ 成功获取任务结果 {job_id}")
                return parsed
        except json.JSONDecodeError as e:
            logger.error(f"❌ 解析结果失败 {job_id}: {e}")
            logger.error(f"原始输出：{result.stdout}")
            return {'error': 'parse_failed', 'raw': result.stdout}
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏱️ 获取任务结果超时：{job_id}")
        return {'error': 'timeout'}
    except Exception as e:
        logger.error(f"❌ 获取任务结果失败 {job_id}: {e}")
        return {'error': str(e)}


def notify_user(user_id: str, chat_id: str, job_id: str, status: str, 
                output_urls: list = None, error_message: str = None,
                tool: str = None):
    """
    通知用户任务完成
    
    使用 OpenClaw 的文件通知机制：
    1. 生成消息文件到 completions 目录
    2. OpenClaw 会自动读取并发送
    """
    from pathlib import Path
    
    # OpenClaw completions 目录
    COMPLETIONS_DIR = Path.home() / '.openclaw' / 'completions'
    COMPLETIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    completion_file = COMPLETIONS_DIR / f"airilab_{job_id}_{timestamp}.md"
    
    if status == STATUS_COMPLETED:
        # 生成 Markdown 格式的消息
        lines = [
            f"✅ **任务完成！**",
            "",
            f"📋 **Job ID**: `{job_id}`",
            f"🎨 **工具**: {tool or 'AiriLab'}",
            "",
            f"🖼️  **生成结果**:",
            ""
        ]
        
        # 添加所有图片（Markdown 格式）
        if output_urls:
            for i, url in enumerate(output_urls, 1):
                lines.append(f"![图片{i}]({url})")
                lines.append("")
        
        lines.append(f"_共 {len(output_urls) or 0} 张图片_")
        
        message = "\n".join(lines)
        
    else:
        message = f"""❌ **任务失败**

📋 **Job ID**: `{job_id}`
⚠️  **错误**: {error_message or '未知错误'}

请重试或联系管理员。"""
    
    # 写入 completion 文件
    try:
        with open(completion_file, 'w', encoding='utf-8') as f:
            f.write(message)
        logger.info(f"📬 通知已写入：{completion_file}")
    except Exception as e:
        logger.error(f"❌ 写入通知失败：{e}")
    
    # 同时保存到通知日志
    log_file = DATA_DIR / 'notifications.log'
    with open(log_file, 'a') as f:
        f.write(f"{datetime.now().isoformat()} | {user_id} | {chat_id} | {job_id} | {status}\n")


def process_job(job):
    """处理单个任务"""
    job_id = job['job_id']
    user_id = job['user_id']
    chat_id = job['chat_id']
    attempts = job['attempts']
    tool = job['tool']
    submitted_at = job['submitted_at']
    
    # 检查是否超过最大轮询次数
    if attempts >= MAX_ATTEMPTS:
        logger.warning(f"⚠️ 任务超时：{job_id} (尝试 {attempts} 次)")
        update_job_status(job_id, STATUS_FAILED, error_message=f"轮询超时（>{TIMEOUT_MINUTES}分钟）")
        notify_user(user_id, chat_id, job_id, STATUS_FAILED, 
                   error_message=f"任务处理超时（>{TIMEOUT_MINUTES}分钟），请重试", tool=tool)
        return
    
    # 检查是否超过时间限制（15 分钟）
    try:
        submitted_time = datetime.fromisoformat(submitted_at)
        elapsed = (datetime.now() - submitted_time).total_seconds() / 60  # 分钟
        
        if elapsed > TIMEOUT_MINUTES:
            logger.warning(f"⚠️ 任务超时：{job_id} (已等待 {elapsed:.1f} 分钟)")
            update_job_status(job_id, STATUS_FAILED, error_message=f"任务超时（{elapsed:.1f}分钟）")
            notify_user(user_id, chat_id, job_id, STATUS_FAILED, 
                       error_message=f"任务处理超时（{elapsed:.1f}分钟），请重试", tool=tool)
            return
    except Exception as e:
        logger.error(f"❌ 解析提交时间失败 {job_id}: {e}")
    
    # 检查任务状态
    logger.info(f"🔍 检查任务：{job_id} (尝试 {attempts + 1}/{MAX_ATTEMPTS}, 已等待 {elapsed:.1f}分钟)")
    status = check_job_status(job_id)
    
    if status == "completed":
        logger.info(f"✅ 任务完成：{job_id}")
        
        # 获取结果
        result = fetch_result(job_id)
        
        if result.get('error'):
            logger.error(f"❌ 获取结果失败 {job_id}: {result.get('error')}")
            update_job_status(job_id, STATUS_FAILED, error_message=f"获取结果失败：{result.get('error')}")
            notify_user(user_id, chat_id, job_id, STATUS_FAILED, 
                       error_message=f"获取结果失败：{result.get('error')}", tool=tool)
            return
        
        output_urls = result.get('output_urls', [])
        thumbnail_url = result.get('thumbnail_url', '')
        result_tool = result.get('toolset', tool)
        
        # 更新数据库
        update_job_status(job_id, STATUS_COMPLETED, 
                         output_url=json.dumps(output_urls), 
                         thumbnail_url=thumbnail_url)
        
        # 通知用户
        notify_user(user_id, chat_id, job_id, STATUS_COMPLETED, 
                   output_urls=output_urls, tool=result_tool)
        
    elif status == "failed" or status == "error" or status == "auth_error":
        logger.error(f"❌ 任务失败：{job_id} (状态：{status})")
        
        error_msg = "Token 过期，请重新登录" if status == "auth_error" else f"API 返回状态：{status}"
        update_job_status(job_id, STATUS_FAILED, error_message=error_msg)
        notify_user(user_id, chat_id, job_id, STATUS_FAILED, 
                   error_message=error_msg, tool=tool)
    
    elif status in ["queued", "sending_now", "processing"]:
        # 仍在处理中
        new_status = STATUS_PROCESSING if status != "queued" else STATUS_PENDING
        update_job_status(job_id, new_status)
        logger.info(f"⏳ 处理中：{job_id} ({status})")
    
    else:
        logger.warning(f"⚠️ 未知状态：{job_id} ({status})")
        update_job_status(job_id, STATUS_PENDING)


def run():
    """主循环"""
    logger.info("=" * 60)
    logger.info("🚀 AiriLab 后台轮询守护进程启动")
    logger.info("=" * 60)
    logger.info(f"📂 数据目录：{DATA_DIR}")
    logger.info(f"💾 数据库：{DB_PATH}")
    logger.info(f"⏱️  轮询间隔：{POLL_INTERVAL}秒")
    logger.info(f"🔄 最大尝试：{MAX_ATTEMPTS}次（{TIMEOUT_MINUTES}分钟）")
    logger.info(f"⚠️  超时限制：{TIMEOUT_MINUTES}分钟")
    logger.info("按 Ctrl+C 停止...")
    
    # 初始化数据库
    init_db()
    
    try:
        while True:
            # 获取 pending 任务
            pending_jobs = get_pending_jobs()
            
            if pending_jobs:
                logger.info(f"📋 发现 {len(pending_jobs)} 个待处理任务")
                
                for job in pending_jobs:
                    try:
                        process_job(job)
                    except Exception as e:
                        logger.error(f"❌ 处理任务失败 {job['job_id']}: {e}")
            else:
                logger.debug("💤 无待处理任务，休眠中...")
            
            # 休眠
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("👋 守护进程已停止")


if __name__ == "__main__":
    run()
