"""
Git Push Engine — 自动创建仓库 + 推送代码到 Gitea
"""
from __future__ import annotations
import subprocess
import os
import json
import urllib.request
from pathlib import Path
from typing import Optional

GITEA_URL = "http://localhost:3000"
GITEA_USER = "devops"
GITEA_PASS = "devops123"


class GitPushEngine:
    """自动 git init + push 到 Gitea 仓库"""

    def __init__(self, gitea_url: str = GITEA_URL, user: str = GITEA_USER, password: str = GITEA_PASS):
        self.gitea_url = gitea_url.rstrip("/")
        self.user = user
        self.password = password
        self._token: Optional[str] = None

    def ensure_token(self) -> Optional[str]:
        """获取或创建 API token"""
        if self._token:
            return self._token
        try:
            # Create token via Gitea API
            data = json.dumps({"name": "agentdev-ci"}).encode()
            req = urllib.request.Request(
                f"{self.gitea_url}/api/v1/users/{self.user}/tokens",
                data=data, method="POST",
                headers={"Content-Type": "application/json"},
            )
            # Basic auth
            import base64
            auth = base64.b64encode(f"{self.user}:{self.password}".encode()).decode()
            req.add_header("Authorization", f"Basic {auth}")
            resp = urllib.request.urlopen(req, timeout=5)
            result = json.loads(resp.read())
            self._token = result.get("sha1", "")
        except Exception:
            self._token = None
        return self._token

    def create_repo(self, repo_name: str, description: str = "") -> Optional[str]:
        """创建 Gitea 仓库，返回 clone URL"""
        token = self.ensure_token()
        if not token:
            return None

        try:
            data = json.dumps({
                "name": repo_name,
                "description": description,
                "private": False,
                "auto_init": False,
            }).encode()
            req = urllib.request.Request(
                f"{self.gitea_url}/api/v1/user/repos",
                data=data, method="POST",
                headers={"Content-Type": "application/json", "Authorization": f"token {token}"},
            )
            resp = urllib.request.urlopen(req, timeout=5)
            result = json.loads(resp.read())
            return result.get("clone_url", "")
        except Exception as e:
            return None

    def push_workspace(self, workspace_dir: str, repo_name: str, description: str = "") -> dict:
        """
        将 workspace 目录推送到 Gitea 仓库
        返回: {"success": bool, "repo_url": str, "files": list}
        """
        workspace = Path(workspace_dir)
        if not workspace.exists():
            return {"success": False, "error": f"workspace {workspace_dir} 不存在"}

        # 1. 创建 Gitea 仓库
        repo_url = self.create_repo(repo_name, description)
        if not repo_url:
            # 回退：不推送但返回文件列表
            files = [str(p.relative_to(workspace)) for p in workspace.rglob("*") if p.is_file()]
            return {"success": False, "error": "无法创建 Gitea 仓库", "files": files}

        # 2. git init + add + commit + push
        try:
            # 添加 .gitignore
            (workspace / ".gitignore").write_text("__pycache__/\n*.pyc\n.env\n*.db\n")

            subprocess.run(["git", "init"], cwd=str(workspace), capture_output=True, check=False)
            subprocess.run(["git", "config", "user.email", "agent@devops.local"], cwd=str(workspace), capture_output=True)
            subprocess.run(["git", "config", "user.name", "AgentDev OS"], cwd=str(workspace), capture_output=True)
            subprocess.run(["git", "add", "-A"], cwd=str(workspace), capture_output=True)
            subprocess.run(["git", "commit", "-m", f"🚀 AgentDev OS 自动生成: {description}"], cwd=str(workspace), capture_output=True)

            # 推送 (使用 Basic Auth)
            push_url = repo_url.replace("://", f"://{self.user}:{self.password}@")
            result = subprocess.run(
                ["git", "push", "-u", push_url, "master"],
                cwd=str(workspace), capture_output=True, text=True, timeout=30,
            )
            files = [str(p.relative_to(workspace)) for p in workspace.rglob("*") if p.is_file()]
            return {
                "success": result.returncode == 0,
                "repo_url": repo_url,
                "files": files,
                "push_output": result.stdout + result.stderr,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
