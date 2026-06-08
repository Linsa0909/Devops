@echo off
chcp 65001 >nul
setlocal

:: AI Factory CLI — Windows 启动包装器
set "SCRIPT_DIR=%~dp0"
set "PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%"

:: 尝试使用后端虚拟环境的 Python
if exist "%SCRIPT_DIR%..\backend\.venv\Scripts\python.exe" (
    "%SCRIPT_DIR%..\backend\.venv\Scripts\python.exe" "%SCRIPT_DIR%cli.py" %*
) else (
    python "%SCRIPT_DIR%cli.py" %*
)
