#!/bin/bash
# AgentDev OS — 一键启动 (后端 + 前端)
echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║        🚀 AgentDev OS 启动脚本              ║"
echo "║  端到端软件需求 Agent 平台                   ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 1. 启动后端
echo "📦 [1/2] 启动后端服务 (FastAPI)..."
cd "$SCRIPT_DIR/backend"

# 虚拟环境
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt -q

# 安装 CLI 依赖
echo "📦 [1.5/2] 安装 CLI 工具依赖..."
pip install click pyyaml httpx -q 2>/dev/null
echo "   ✅ CLI 可用: ai-factory submit '需求' -d '描述'"

# .env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  已创建 .env，请编辑填入 DEEPSEEK_API_KEY（留空=MOCK模式）"
fi

# 释放占用端口
OLD_PID=$(lsof -ti:8000 2>/dev/null)
if [ -n "$OLD_PID" ]; then
    echo "⚠️  端口 8000 被占用 (PID: $OLD_PID)，正在释放..."
    kill -9 $OLD_PID 2>/dev/null
    sleep 1
fi

# 后端后台运行 (不需要 --reload，因为后台服务重启靠脚本本身)
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 验证后端启动 (最多重试 20 次，每次 0.5s，共 10s)
READY=0
for i in $(seq 1 20); do
    sleep 0.5
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        READY=1
        break
    fi
    echo -n "."
done
echo ""
if [ "$READY" -eq 1 ]; then
    echo "   ✅ 后端就绪 (http://localhost:8000)"
    echo "   📖 API 文档: http://localhost:8000/docs"
else
    echo "   ❌ 后端启动超时 (PID: $BACKEND_PID)"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# 2. 打开前端
echo ""
echo "🌐 [2/2] 服务已就绪"
echo ""
echo "   访问地址: http://localhost:8000 (前后端联动)"
echo "   API 文档: http://localhost:8000/docs"
echo ""
echo "   CLI 命令:"
echo "   ./ai-factory submit '需求名称' -d '需求描述'"
echo "   ./ai-factory status <task_id>"
echo "   ./ai-factory gate approve -p <task_id> -g Gate1"
echo ""

# 尝试自动打开
if command -v xdg-open &> /dev/null; then
    xdg-open "$SCRIPT_DIR/index.html" 2>/dev/null
elif command -v open &> /dev/null; then
    open "$SCRIPT_DIR/index.html" 2>/dev/null
fi

echo "╔═══════════════════════════════════════════════╗"
echo "║   🟢 已启动                                  ║"
echo "║   http://localhost:8000                      ║"
echo "║                                              ║"
echo "║   按 Ctrl+C 停止                              ║"
echo "╚═══════════════════════════════════════════════╝"

# 等待后台进程
wait $BACKEND_PID
