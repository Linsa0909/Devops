#!/bin/bash
# AgentDev OS — 一键启动 (Gitea + AgentDev OS)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║        🚀 AgentDev OS                       ║"
echo "║  端到端软件需求 Agent 平台                    ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# ---- 0. Gitea 仓库服务 ----
GITEA_DIR="$SCRIPT_DIR/backend/gitea"
if [ -f "$GITEA_DIR/gitea" ]; then
    echo "📦 [0/2] 启动 Gitea 仓库服务..."
    cd "$GITEA_DIR"
    chmod +x gitea 2>/dev/null

    # 首次初始化
    if [ ! -f "gitea.db" ]; then
        ./gitea migrate -c app.ini 2>/dev/null
        GITEA_WORK_DIR="$GITEA_DIR/data" ./gitea admin user create \
            --admin --username devops --password devops123 --email devops@local \
            -c app.ini 2>/dev/null
    fi

    # 释放 3000 端口
    OLD_GIT=$(lsof -ti:3000 2>/dev/null)
    [ -n "$OLD_GIT" ] && kill -9 $OLD_GIT 2>/dev/null

    nohup ./gitea web --port 3000 -c app.ini > /dev/null 2>&1 &
    echo "   ✅ Gitea: http://localhost:3000 (devops/devops123)"
else
    echo "   ⚠️  Gitea 未找到，跳过 (Git 推送将不可用)"
fi

# ---- 1. AgentDev OS 后端 ----
cd "$SCRIPT_DIR/backend"
echo "📦 [1/2] AgentDev OS 后端..."

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install fastapi uvicorn pydantic httpx python-dotenv aiofiles click pyyaml python-docx PyPDF2 -q
else
    source .venv/bin/activate
fi

[ ! -f ".env" ] && cp .env.example .env

OLD_8K=$(lsof -ti:8000 2>/dev/null)
[ -n "$OLD_8K" ] && kill -9 $OLD_8K 2>/dev/null

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║   🟢 启动完成                                ║"
echo "║   AgentDev OS: http://localhost:8000         ║"
echo "║   Gitea 仓库:  http://localhost:3000         ║"
echo "║   API 文档:    http://localhost:8000/docs    ║"
echo "║                                              ║"
echo "║   按 Ctrl+C 停止                              ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

exec uvicorn main:app --host 0.0.0.0 --port 8000
