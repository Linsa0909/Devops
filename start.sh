#!/bin/bash
# AgentDev OS — 一键启动 (Gitea + AgentDev OS)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 获取局域网 IP
LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
[ -z "$LAN_IP" ] && LAN_IP=$(ip addr show eth0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)
[ -z "$LAN_IP" ] && LAN_IP=$(ip route get 1 2>/dev/null | grep -oP 'src \K\S+')

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║        🚀 AgentDev OS                       ║"
echo "║  端到端软件需求 Agent 平台                    ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# ---- 0. 安装依赖 + 确保 env ----
cd "$SCRIPT_DIR/backend"
if [ ! -d ".venv" ]; then
    echo "📦 首次运行 — 创建虚拟环境..."
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install fastapi uvicorn pydantic httpx python-dotenv aiofiles click pyyaml python-docx PyPDF2 python-multipart sqlalchemy python-jose passlib bcrypt pytest -q 2>/dev/null

[ ! -f ".env" ] && cp .env.example .env

# ---- 1. Gitea 仓库服务 ----
GITEA_GIT_DIR="/tmp/repos/devops.git"
if [ ! -d "$GITEA_GIT_DIR" ]; then
    echo "📦 [0/2] 初始化本地 Git 仓库..."
    mkdir -p /tmp/repos && git init --bare "$GITEA_GIT_DIR" 2>/dev/null
    echo "   ✅ Git bare repo: $GITEA_GIT_DIR"
fi

# ---- 2. 释放端口 ----
for port in 8000 3000; do
    OLD_PID=$(lsof -ti:$port 2>/dev/null)
    [ -n "$OLD_PID" ] && kill -9 "$OLD_PID" 2>/dev/null
done

# ---- 3. 启动 ----
echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║   🟢 服务已启动                              ║"
echo "║                                              ║"
echo "║   本机访问:                                   ║"
echo "║     AgentDev OS:  http://localhost:8000      ║"
if [ -n "$LAN_IP" ]; then
    echo "║     API 文档:     http://localhost:8000/docs ║"
    echo "║                                              ║"
    echo "║   局域网访问 (同 WiFi 设备):                  ║"
    echo "║     AgentDev OS:  http://$LAN_IP:8000        ║"
    echo "║     API 文档:     http://$LAN_IP:8000/docs   ║"
else
    echo "║     API 文档:     http://localhost:8000/docs ║"
fi
echo "║                                              ║"
echo "║   按 Ctrl+C 停止                              ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

exec uvicorn main:app --host 0.0.0.0 --port 8000
