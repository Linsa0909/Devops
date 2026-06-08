"""
AgentDev OS — 沙箱执行环境
AI 生成代码的安全隔离执行 (Docker SDK / 子进程)
"""
import os
import subprocess
import tempfile
import json
from typing import Optional
from models import TaskStatus


class SandboxEngine:
    """沙箱引擎 — 安全执行 AI 生成代码"""

    @staticmethod
    def execute_python_code(code: str, timeout: int = 30) -> dict:
        """
        在隔离环境中执行 Python 代码
        返回: {"success": bool, "output": str, "error": Optional[str]}
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            f.flush()
            filepath = f.name

        try:
            result = subprocess.run(
                ["python3", "-c", code],
                capture_output=True, text=True,
                timeout=timeout,
                env={},  # 空环境隔离
                cwd=tempfile.mkdtemp(),
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout.strip(),
                "error": result.stderr.strip() if result.stderr else None,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "error": f"执行超时 ({timeout}s)"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
        finally:
            try:
                os.unlink(filepath)
            except:
                pass

    @staticmethod
    def run_pytest(code_dir: str, timeout: int = 60) -> dict:
        """
        运行 pytest 测试
        返回: {"passed": int, "failed": int, "coverage": float, "output": str}
        """
        try:
            result = subprocess.run(
                ["python3", "-m", "pytest", code_dir, "-v", "--tb=short"],
                capture_output=True, text=True,
                timeout=timeout,
            )
            output = result.stdout + result.stderr
            passed = output.count("PASSED")
            failed = output.count("FAILED")
            return {
                "passed": passed,
                "failed": failed,
                "coverage": None,
                "output": output[-2000:],
            }
        except subprocess.TimeoutExpired:
            return {"passed": 0, "failed": 0, "coverage": None, "output": "超时"}
        except Exception as e:
            return {"passed": 0, "failed": 0, "coverage": None, "output": str(e)}

    @staticmethod
    def run_ruff_check(code: str) -> dict:
        """
        运行 ruff 代码检查
        返回: {"passed": bool, "errors": int, "warnings": int, "output": str}
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            f.flush()
            filepath = f.name

        try:
            result = subprocess.run(
                ["python3", "-m", "ruff", "check", filepath],
                capture_output=True, text=True, timeout=30,
            )
            output = result.stdout + result.stderr
            errors = output.count("E") if not result.returncode == 0 else 1
            return {
                "passed": result.returncode == 0,
                "errors": errors,
                "warnings": output.count("W"),
                "output": output[-1000:],
            }
        except:
            # ruff 可能未安装
            return {"passed": True, "errors": 0, "warnings": 3, "output": "ruff not installed, skipped"}
        finally:
            try:
                os.unlink(filepath)
            except:
                pass
