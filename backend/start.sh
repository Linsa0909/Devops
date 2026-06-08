echo "🚀 AgentDev OS — 启动后端服务"
echo "================================"
echo ""

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv .venv
fi

echo "📦 激活虚拟环境..."
source .venv/bin/activate

echo "📦 安装依赖..."
pip install -r requirements.txt -q

# 检查 .env
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  未找到 .env 文件，从 .env.example 复制..."
    cp .env.example .env
    echo "   → 请编辑 .env 填入 DEEPSEEK_API_KEY"
    echo "   → 或留空使用 Mock 模式"
    echo ""
fi

echo ""
echo "🌐 启动 FastAPI 服务 (http://localhost:8000)"
echo "   API 文档: http://localhost:8000/docs"
echo "   Ctrl+C 停止"
echo ""

cd "$(dirname "$0")"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
