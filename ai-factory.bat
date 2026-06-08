@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: AI Factory CLI — Windows 启动包装器
set "CLI_DIR=%~dp0ai-factory-runtime"
set "PYTHONPATH=%CLI_DIR%;%PYTHONPATH%"

:: 尝试使用后端虚拟环境的 Python
if exist "%~dp0backend\.venv\Scripts\python.exe" (
    "%~dp0backend\.venv\Scripts\python.exe" "%CLI_DIR%\cli.py" %*
) else (
    python "%CLI_DIR%\cli.py" %*
)
