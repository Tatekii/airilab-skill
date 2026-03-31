#!/bin/bash
# AiriLab Worker 后台启动脚本
# 用于在 skill 安装后自动启动后台服务

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
WORKER_SCRIPT="$SKILL_DIR/scheduler/worker.py"
LOG_FILE="$SKILL_DIR/scheduler/worker.log"
PID_FILE="$SKILL_DIR/scheduler/worker.pid"

echo "🚀 AiriLab Worker 自动启动脚本"
echo "=" | tr -d '\n' && printf '%.0s=' {1..50} && echo

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  Worker 已经在运行 (PID: $OLD_PID)"
        echo "💡 如需重启，先执行：kill $OLD_PID"
        exit 0
    else
        echo "🧹 清理过期的 PID 文件"
        rm -f "$PID_FILE"
    fi
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：找不到 python3"
    exit 1
fi

# 检查 worker 脚本
if [ ! -f "$WORKER_SCRIPT" ]; then
    echo "❌ 错误：找不到 worker 脚本：$WORKER_SCRIPT"
    exit 1
fi

# 启动 worker
echo "📍 Worker 路径：$WORKER_SCRIPT"
echo "📄 日志文件：$LOG_FILE"
echo ""

nohup python3 "$WORKER_SCRIPT" > "$LOG_FILE" 2>&1 &
WORKER_PID=$!

# 保存 PID
echo "$WORKER_PID" > "$PID_FILE"

# 等待启动
sleep 2

# 检查是否成功启动
if ps -p "$WORKER_PID" > /dev/null 2>&1; then
    echo "✅ Worker 已成功启动！"
    echo ""
    echo "📊 进程信息:"
    echo "   PID: $WORKER_PID"
    echo "   日志：tail -f $LOG_FILE"
    echo "   停止：kill $WORKER_PID"
    echo ""
    
    # 显示最近日志
    echo "📋 最近日志:"
    tail -5 "$LOG_FILE" | sed 's/^/   /'
    
    exit 0
else
    echo "❌ Worker 启动失败！"
    echo ""
    echo "📄 错误日志:"
    tail -20 "$LOG_FILE" | sed 's/^/   /'
    
    rm -f "$PID_FILE"
    exit 1
fi
