"""
Workspace Writer — 将 LLM 生成的代码落盘为真实项目文件
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime


class WorkspaceWriter:
    """将 Agent 生成的代码写入真实文件系统"""

    def __init__(self, root: str = "workspace"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def write(self, files: list[dict]) -> list[Path]:
        """
        写入文件列表
        files: [{"file_path":"app/main.py","content":"..."}]
        返回: 写入的文件路径列表
        """
        written = []
        for item in files:
            file_path = self.root / item["file_path"].lstrip("/")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(item["content"], encoding="utf-8")
            written.append(file_path)

            # 同时写入测试文件（如果有）
            if "test_file_path" in item and "test_content" in item:
                test_path = self.root / item["test_file_path"].lstrip("/")
                test_path.parent.mkdir(parents=True, exist_ok=True)
                test_path.write_text(item["test_content"], encoding="utf-8")
                written.append(test_path)

        return written

    def write_requirements(self, packages: list[str]) -> Path:
        """写入 requirements.txt"""
        req_path = self.root / "requirements.txt"
        req_path.write_text("\n".join(packages) + "\n", encoding="utf-8")
        return req_path

    def write_readme(self, content: str) -> Path:
        """写入 README"""
        readme_path = self.root / "README.md"
        readme_path.write_text(content, encoding="utf-8")
        return readme_path

    def tree(self) -> str:
        """列出当前工作区文件树"""
        lines = []
        for f in sorted(self.root.rglob("*")):
            if f.is_file() and ".venv" not in str(f) and "__pycache__" not in str(f):
                lines.append(str(f.relative_to(self.root)))
        return "\n".join(lines)

    def timestamp(self) -> Path:
        """创建时间戳子目录，用于版本管理"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.root = Path("workspace") / ts
        self.root.mkdir(parents=True, exist_ok=True)
        return self.root
