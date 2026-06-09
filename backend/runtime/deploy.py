"""
Deploy Engine — 启动 Agent 生成的代码作为可访问服务
"""
import subprocess
import os
import time
import signal
from pathlib import Path
from typing import Optional

DEPLOY_PIDS: dict[str, int] = {}
DEPLOY_PORTS: dict[str, int] = {}
_next_port = 9001


class DeployEngine:
    """部署引擎 — 启动生成的服务进程并管理生命周期"""

    @staticmethod
    def deploy(pipeline_id: str, workspace_dir: str) -> dict:
        """
        启动生成的 FastAPI 服务，返回访问信息
        """
        global _next_port
        ws = Path(workspace_dir)

        # 查找 main.py
        main_file = None
        for candidate in [
            ws / "app" / "main.py",
            ws / "main.py",
            ws / "src" / "main.py",
        ]:
            if candidate.exists():
                main_file = candidate
                break

        if not main_file:
            # 查找任意 .py 文件作为入口
            py_files = list(ws.rglob("*.py"))
            if py_files:
                main_file = py_files[0]
            else:
                return {"success": False, "error": "未找到可执行的 .py 文件"}

        # 分配端口
        port = _next_port
        _next_port += 1

        # 先安装依赖
        req_file = ws / "requirements.txt"
        if req_file.exists():
            subprocess.run(
                ["python3", "-m", "pip", "install", "-q", "-r", str(req_file)],
                capture_output=True, timeout=30,
            )

        # Kill old process
        old_pid = DEPLOY_PIDS.get(pipeline_id)
        if old_pid:
            try:
                os.kill(old_pid, signal.SIGTERM)
            except:
                pass

        # 启动新进程
        try:
            proc = subprocess.Popen(
                ["python3", "-m", "uvicorn", f"app.main:app", "--host", "0.0.0.0", "--port", str(port)],
                cwd=str(ws),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )
            DEPLOY_PIDS[pipeline_id] = proc.pid
            DEPLOY_PORTS[pipeline_id] = port
            time.sleep(1)  # 给 uvicorn 一点启动时间
            return {
                "success": True,
                "pid": proc.pid,
                "port": port,
                "url": f"http://localhost:{port}",
                "entry": str(main_file.relative_to(ws)),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def status(pipeline_id: str) -> dict:
        pid = DEPLOY_PIDS.get(pipeline_id)
        port = DEPLOY_PORTS.get(pipeline_id)
        if not pid:
            return {"deployed": False, "status": "not_deployed"}
        try:
            os.kill(pid, 0)
            return {"deployed": True, "status": "running", "pid": pid, "port": port, "url": f"http://localhost:{port}"}
        except OSError:
            return {"deployed": False, "status": "stopped", "port": port}

    @staticmethod
    def stop(pipeline_id: str):
        pid = DEPLOY_PIDS.pop(pipeline_id, None)
        DEPLOY_PORTS.pop(pipeline_id, None)
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
            except:
                pass
