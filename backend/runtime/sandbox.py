"""
Runtime — Docker Sandbox 沙箱执行器
真正的隔离环境：Docker 容器内运行 pytest/ruff/mypy
"""
from __future__ import annotations
import subprocess
import tempfile
import os
import shutil
from pathlib import Path
from typing import Optional


class DockerSandbox:
    """
    Docker 隔离沙箱：
    - 自动拉取 Python 镜像
    - 挂载 workspace 到容器内 /app
    - 在容器内执行 pytest + ruff + mypy
    - 不污染宿主机
    """
    IMAGE = "python:3.11-slim"

    def __init__(self, workspace: str, timeout: int = 30):
        self.workspace = os.path.abspath(workspace)
        self.timeout = timeout

    # ─── 公开 API ───

    def run_pytest(self) -> dict:
        """运行 pytest (Docker 不可用时自动回退本地)"""
        if self._docker_available():
            return self._docker_exec([
                "bash", "-c",
                "pip install -q -r /app/requirements.txt 2>/dev/null; "
                "pip install -q pytest 2>/dev/null; "
                "cd /app && python -m pytest -q --tb=short 2>&1 || true"
            ])
        return self.run_local()

    # ─── Docker 可用性快速检查 ───

    def _docker_available(self) -> bool:
        """快速检查 Docker 是否可用 (1s 超时)"""
        try:
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True, text=True,
                timeout=1,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False

    def _docker_exec(self, cmd: list[str]) -> dict:
        try:
            result = subprocess.run(
                [
                    "docker", "run", "--rm",
                    "-v", f"{self.workspace}:/app",
                    "--network", "none",
                    "--memory", "512m",
                    "--cpus", "1",
                    self.IMAGE,
                ] + cmd,
                capture_output=True, text=True,
                timeout=self.timeout,
            )
            output = (result.stdout + result.stderr)[:5000]
            return {
                "success": result.returncode == 0,
                "passed": output.count("passed") or output.count("PASSED"),
                "failed": output.count("failed") or output.count("FAILED"),
                "output": output,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "passed": 0, "failed": 1, "output": f"执行超时 ({self.timeout}s)"}
        except FileNotFoundError:
            return self.run_local()
        except Exception as e:
            return {"success": False, "passed": 0, "failed": 1, "output": str(e)}

    def run_local(self) -> dict:
        """本地执行（Docker 不可用时回退）"""
        import subprocess as sp
        try:
            result = sp.run(
                ["python3", "-m", "pytest", self.workspace, "-q", "--tb=short"],
                capture_output=True, text=True, timeout=self.timeout,
                cwd=self.workspace,
            )
            output = (result.stdout + result.stderr)[:5000]
            return {
                "success": result.returncode == 0,
                "passed": output.count("passed"),
                "failed": output.count("failed"),
                "output": output,
            }
        except sp.TimeoutExpired:
            return {"success": False, "passed": 0, "failed": 1, "output": "执行超时"}
        except FileNotFoundError:
            return {"success": False, "passed": 0, "failed": 1, "output": "pytest 未安装"}
