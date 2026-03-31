#!/bin/bash
# AiriLab Worker systemd 服务安装脚本

set -e

SERVICE_NAME="airilab-worker"
SERVICE_FILE="/etc/systemd/user/${SERVICE_NAME}.service"
WORKER_SCRIPT="/home/ec2-user/.openclaw/skills/airilab/scheduler/worker.py"
WORK_DIR="/home/ec2-user/.openclaw/skills/airilab/scheduler"
USER="ec2-user"

echo "🔧 正在安装 ${SERVICE_NAME} 服务..."

# 创建 systemd 服务文件
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=AiriLab Background Worker for task polling
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 ${WORKER_SCRIPT}
Restart=always
RestartSec=10
User=${USER}
WorkingDirectory=${WORK_DIR}
StandardOutput=append:${WORK_DIR}/worker.systemd.log
StandardError=append:${WORK_DIR}/worker.systemd.log
Environment="PYTHONUNBUFFERED=1"

# 资源限制
LimitNOFILE=65535
Nice=10

[Install]
WantedBy=default.target
EOF

echo "✅ 服务文件已创建：$SERVICE_FILE"

# 重新加载 systemd
systemctl --user daemon-reload
echo "✅ systemd 配置已重载"

# 启用服务
systemctl --user enable "$SERVICE_NAME"
echo "✅ 服务已启用（开机自启）"

# 启动服务
systemctl --user start "$SERVICE_NAME"
echo "✅ 服务已启动"

# 显示状态
echo ""
echo "📊 服务状态："
systemctl --user status "$SERVICE_NAME" --no-pager

echo ""
echo "💡 常用命令："
echo "   查看状态：systemctl --user status $SERVICE_NAME"
echo "   停止服务：systemctl --user stop $SERVICE_NAME"
echo "   重启服务：systemctl --user restart $SERVICE_NAME"
echo "   查看日志：journalctl --user -u $SERVICE_NAME -f"
