"""Runtime — Test Runner (local pytest, uses venv python)"""
import subprocess
import os
import sys


class DockerSandbox:
    """Test Runner — 使用 venv 的 Python 运行 pytest"""

    def __init__(self, workspace: str, timeout: int = 30):
        self.workspace = os.path.abspath(workspace)
        self.timeout = timeout
        self.python = sys.executable  # Use the venv's python

    def run_pytest(self) -> dict:
        """运行 pytest, 使用 venv python + PYTHONPATH"""
        env = dict(os.environ)
        env["PYTHONPATH"] = self.workspace + ":" + env.get("PYTHONPATH", "")
        try:
            result = subprocess.run(
                [self.python, "-m", "pytest", ".", "-q", "--tb=line", "-p", "no:warnings"],
                capture_output=True, text=True, timeout=self.timeout,
                cwd=self.workspace, env=env,
            )
            output = (result.stdout + result.stderr)[:5000]
            return {
                "success": result.returncode == 0,
                "passed": output.count(" passed") or output.count("PASSED"),
                "failed": output.count(" failed") or output.count("FAILED"),
                "output": output,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "passed": 0, "failed": 1, "output": f"超时({self.timeout}s)"}
        except Exception as e:
            return {"success": False, "passed": 0, "failed": 1, "output": str(e)}
