@echo off
chcp 65001 >nul
title AgentDev OS — 端到端软件需求 Agent 平台
cd /d "%~dp0"

echo ╔═══════════════════════════════════════════════╗
echo ║        🚀 AgentDev OS 一键启动               ║
echo ║  端到端软件需求 Agent 平台                    ║
echo ╚═══════════════════════════════════════════════╝
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 Python，请安装 Python 3.10+
    pause
    exit /b
)
echo ✅ Python 已安装

:: 进入 backend 目录
cd backend

:: 创建虚拟环境
if not exist ".venv" (
    echo 📦 创建虚拟环境...
    python -m venv .venv
)

:: 安装依赖
echo 📦 安装依赖...
call .venv\Scripts\activate.bat
pip install -r requirements.txt -q

:: 安装 CLI 依赖
echo 📦 安装 CLI 工具依赖...
pip install click pyyaml httpx -q

echo CLI 可用: ai-factory submit "需求名" -d "描述"

:: 释放占用端口
echo 🔌 检查端口 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo.

:: 检查 .env
if not exist ".env" (
    copy .env.example .env >nul
    echo ⚠️  已创建 .env，可编辑填入 DEEPSEEK_API_KEY
    echo    （留空则使用 Mock 模式）
)

echo.
echo 🌐 启动后端服务...
echo    访问地址: http://localhost:8000
echo    API 文档: http://localhost:8000/docs
echo    Ctrl+C 停止服务
echo.
echo ╔═══════════════════════════════════════════════╗
echo ║   🟢 服务启动中                               ║
echo ║   http://localhost:8000                      ║
echo ║                                              ║
echo ║   CLI: ai-factory submit "需求" -d "描述"    ║
echo ╚═══════════════════════════════════════════════╝
echo.

:: 启动后端 (不用 --reload)
uvicorn main:app --host 0.0.0.0 --port 8000

pause
