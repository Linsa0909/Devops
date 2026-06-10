"""Git Push Engine — push workspace code to local bare repo"""
import subprocess
import os
from pathlib import Path

LOCAL_REPO = "/tmp/repos/devops.git"
# Ensure repo directory exists
import os as _os
_os.makedirs(os.path.dirname(LOCAL_REPO), exist_ok=True)
if not _os.path.exists(LOCAL_REPO):
    subprocess.run(["git", "init", "--bare", LOCAL_REPO], capture_output=True)


class GitPushEngine:
    """Push workspace code to local bare git repo"""
    
    def __init__(self, gitea_url: str = "", user: str = "devops", password: str = ""):
        pass

    def push_workspace(self, workspace_dir: str, repo_name: str, description: str = "") -> dict:
        ws = Path(workspace_dir)
        if not ws.exists():
            return {"success": False, "error": f"workspace {workspace_dir} 不存在"}
        
        files = [str(p.relative_to(ws)) for p in ws.rglob("*") if p.is_file() and not p.name.startswith(".")]
        
        try:
            # Write .gitignore
            (ws / ".gitignore").write_text("__pycache__/\n*.pyc\n.env\n*.db\n")
            
            # git init + add + commit
            subprocess.run(["git", "init"], cwd=str(ws), capture_output=True, check=False)
            subprocess.run(["git", "config", "user.email", "agent@devops.local"], cwd=str(ws), capture_output=True)
            subprocess.run(["git", "config", "user.name", "AgentDev OS"], cwd=str(ws), capture_output=True)
            subprocess.run(["git", "add", "-A"], cwd=str(ws), capture_output=True)
            subprocess.run(["git", "commit", "-m", f"🚀 {description[:100]}"], cwd=str(ws), capture_output=True)
            
            # Push to local bare repo
            if os.path.exists(LOCAL_REPO):
                subprocess.run(["git", "remote", "remove", "origin"], cwd=str(ws), capture_output=True)
                subprocess.run(["git", "remote", "add", "origin", LOCAL_REPO], cwd=str(ws), capture_output=True)
                result = subprocess.run(
                    ["git", "push", "-u", "origin", "master", "--force"],
                    cwd=str(ws), capture_output=True, text=True, timeout=10,
                )
                return {
                    "success": result.returncode == 0,
                    "repo_url": LOCAL_REPO,
                    "files": files,
                    "push_output": (result.stdout + result.stderr)[:500],
                }
            return {"success": False, "error": "local repo not found", "files": files}
        except Exception as e:
            return {"success": False, "error": str(e)}
