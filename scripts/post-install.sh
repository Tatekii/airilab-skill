#!/bin/bash
# AiriLab Skill 安装后自动执行脚本
# 功能：配置 + 启动后台服务

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║     🎨 AiriLab Skill 安装后配置                   ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# Step 1: 检查 Token
echo "📝 Step 1/3: 检查登录状态..."
TOKEN_FILE="$SKILL_DIR/config/.env"

if [ ! -f "$TOKEN_FILE" ]; then
    echo "⚠️  检测到未登录状态"
    echo ""
    echo "💡 请使用以下方式之一登录："
    echo ""
    echo "   方式 1 - 命令行登录:"
    echo "   python3 $SKILL_DIR/core/auth.py login --phone <手机号>"
    echo ""
    echo "   方式 2 - 对话登录:"
    echo "   在聊天中发送任意图像修改指令，Bot 会自动引导登录"
    echo ""
else
    echo "✅ Token 已配置"
    PHONE=$(grep AIRILAB_PHONE "$TOKEN_FILE" 2>/dev/null | cut -d= -f2)
    if [ -n "$PHONE" ]; then
        echo "   手机号：$PHONE"
    fi
fi

echo ""

# Step 2: 检查项目配置
echo "📁 Step 2/3: 检查项目配置..."
PROJECT_FILE="$SKILL_DIR/config/project_config.json"

if [ ! -f "$PROJECT_FILE" ]; then
    echo "⚠️  未配置项目"
    echo "💡 首次使用图像功能时会自动引导选择项目"
else
    echo "✅ 项目已配置"
    PROJECT_NAME=$(python3 -c "import json; print(json.load(open('$PROJECT_FILE')).get('projectName', 'Unknown'))" 2>/dev/null || echo "Unknown")
    echo "   项目：$PROJECT_NAME"
fi

echo ""

# Step 3: 启动后台服务
echo "🚀 Step 3/3: 启动后台服务..."
echo ""

# 执行启动脚本
chmod +x "$SCRIPT_DIR/start-worker.sh"
"$SCRIPT_DIR/start-worker.sh"

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║           ✅ AiriLab Skill 配置完成！             ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""
echo "📚 使用指南:"
echo ""
echo "   1. 发送图像 + 修改指令，例如："
echo "      [发送图片] + '把这张图转为冬季夜晚'"
echo ""
echo "   2. 查看任务状态:"
echo "      python3 $SKILL_DIR/scripts/check_status.py --job-id <job_id>"
echo ""
echo "   3. 查看后台日志:"
echo "      tail -f $SKILL_DIR/scheduler/worker.log"
echo ""
echo "   4. 停止后台服务:"
echo "      kill \$(cat $SKILL_DIR/scheduler/worker.pid)"
echo ""
echo "💡 提示：后台服务会在下次登录时自动重启"
echo ""
