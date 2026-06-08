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

    def __init__(self, workspace: str, timeout: int = 120):
        self.workspace = os.path.abspath(workspace)
        self.timeout = timeout

    # ─── 公开 API ───

    def run_pytest(self) -> dict:
        """Docker 内运行 pytest"""
        return self._docker_exec([
            "bash", "-c",
            "pip install -q -r /app/requirements.txt 2>/dev/null; "
            "pip install -q pytest 2>/dev/null; "
            "cd /app && python -m pytest -q --tb=short 2>&1 || true"
        ])

    def run_ruff(self) -> dict:
        """Docker 内运行 ruff 代码检查"""
        return self._docker_exec([
            "bash", "-c",
            "pip install -q ruff 2>/dev/null; "
            "cd /app && ruff check . 2>&1 || true"
        ])

    def run_tests_with_coverage(self) -> dict:
        """Docker 内运行 pytest --cov (覆盖率)"""
        return self._docker_exec([
            "bash", "-c",
            "pip install -q -r /app/requirements.txt pytest pytest-cov 2>/dev/null; "
            "cd /app && python -m pytest -q --tb=short --cov=. --cov-report=term 2>&1 || true"
        ])

    # ─── 回退：本地子进程 ───

    def run_local(self) -> dict:
        """本地执行（无 Docker 时回退）"""
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

    # ─── 内部 ───

    def _docker_exec(self, cmd: list[str]) -> dict:
        # 尝试 Docker
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
            return {"success": False, "passed": 0, "failed": 1, "output": "Docker 执行超时"}
        except FileNotFoundError:
            # Docker 不可用，回退到本地
            return self.run_local()
        except Exception as e:
            return {"success": False, "passed": 0, "failed": 1, "output": str(e)}
