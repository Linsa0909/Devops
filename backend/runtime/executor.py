"""
Runtime — Code Executor (本地进程执行器)
pytest/ruff/mypy 的轻量封装
"""
from __future__ import annotations
import subprocess
import os
from pathlib import Path


class CodeExecutor:
    """代码执行器 — 运行 pytest / ruff / mypy 并收集结果"""

    def __init__(self, workspace: str, timeout: int = 60):
        self.workspace = os.path.abspath(workspace)
        self.timeout = timeout
        self._ensure_workspace()

    def run_pytest(self) -> dict:
        """运行 pytest"""
        return self._run([
            "python3", "-m", "pytest",
            self.workspace,
            "-q", "--tb=short",
            f"--rootdir={self.workspace}",
        ])

    def run_ruff(self) -> dict:
        """运行 ruff 代码检查"""
        try:
            return self._run([
                "python3", "-m", "ruff", "check", self.workspace,
            ])
        except:
            return {"success": True, "output": "ruff 未安装，跳过", "errors": 0}

    def run_tests_suite(self) -> dict:
        """完整测试套件 (pytest + ruff)"""
        # 先安装依赖
        req_file = os.path.join(self.workspace, "requirements.txt")
        if os.path.exists(req_file):
            subprocess.run(
                ["python3", "-m", "pip", "install", "-q", "-r", req_file],
                capture_output=True, cwd=self.workspace, timeout=30,
            )

        pytest_result = self.run_pytest()
        ruff_result = self.run_ruff()

        return {
            "pytest": pytest_result,
            "ruff": ruff_result,
            "all_passed": pytest_result["success"] and ruff_result.get("success", True),
        }

    # ─── 内部 ───

    def _run(self, cmd: list[str]) -> dict:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True, text=True,
                timeout=self.timeout,
            )
            output = (result.stdout + result.stderr)[:5000]
            return {
                "success": result.returncode == 0,
                "passed": output.count("passed") or output.count("PASSED"),
                "failed": output.count("failed") or output.count("FAILED"),
                "errors": output.count("ERROR"),
                "output": output,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "passed": 0, "failed": 1, "errors": 0, "output": f"执行超时 ({self.timeout}s)"}
        except FileNotFoundError as e:
            return {"success": False, "passed": 0, "failed": 1, "errors": 0, "output": f"命令未找到: {e}"}
        except Exception as e:
            return {"success": False, "passed": 0, "failed": 1, "errors": 0, "output": str(e)}

    def _ensure_workspace(self):
        os.makedirs(self.workspace, exist_ok=True)
