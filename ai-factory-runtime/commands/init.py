"""AI Factory — init 命令: 创建项目脚手架"""
from __future__ import annotations
import os
import shutil
from pathlib import Path
from utils.config import AIConfig

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def cmd_init(project_name: str, config: AIConfig):
    """创建 FastAPI + React 项目骨架"""
    project_path = Path.cwd() / project_name

    if project_path.exists():
        print(f"❌ 目录已存在: {project_path}")
        return

    print(f"🚀 创建项目: {project_name}")
    print(f"   路径: {project_path}")
    print()

    # 创建目录结构
    dirs = [
        "backend/app",
        "backend/app/api",
        "backend/app/models",
        "backend/app/services",
        "backend/tests",
        "frontend/src/components",
        "frontend/src/pages",
        "frontend/src/hooks",
        "frontend/src/styles",
        ".ai-factory",
    ]
    for d in dirs:
        (project_path / d).mkdir(parents=True, exist_ok=True)
        (project_path / d / ".gitkeep").touch()

    # 生成 backend/requirements.txt
    _write(project_path / "backend" / "requirements.txt", """\
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.9.0
httpx==0.27.0
python-dotenv==1.0.0
""")

    # 生成 backend/app/main.py
    _write(project_path / "backend" / "app" / "main.py", """\
\"\"\"AI Factory — 自动生成项目入口\"\"\"
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="{project_name}", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {{"status": "ok", "project": "{project_name}"}}
""".format(project_name=project_name))

    # 生成 frontend/package.json
    _write(project_path / "frontend" / "package.json", """\
{{
  "name": "{project_name}",
  "private": true,
  "version": "0.1.0",
  "scripts": {{
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "tailwindcss": "^4.0.0"
  }},
  "devDependencies": {{
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^6.0.0"
  }}
}}
""".format(project_name=project_name))

    # 生成 frontend/index.html
    _write(project_path / "frontend" / "index.html", """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{project_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50">
  <div id="root"></div>
  <script type="module" src="/src/main.jsx"></script>
</body>
</html>
""".format(project_name=project_name))

    # 生成 frontend/src/main.jsx
    _write(project_path / "frontend" / "src" / "main.jsx", """\
import React from 'react'
import ReactDOM from 'react-dom/client'

function App() {{
  return (
    <div class="flex h-screen items-center justify-center">
      <div class="text-center">
        <h1 class="text-3xl font-bold text-slate-800">🚀 {project_name}</h1>
        <p class="text-slate-500 mt-2">AI Factory — 自动化开发流水线</p>
      </div>
    </div>
  )
}}

ReactDOM.createRoot(document.getElementById('root')).render(<App />)
""".format(project_name=project_name))

    # 生成 .ai-factory/config.yaml
    config_content = """\
# AI Factory Runtime Configuration
deepseek:
  api_key: "${{DEEPSEEK_API_KEY}}"
  base_url: "https://api.deepseek.com"

runtime:
  coverage_threshold: 85

gates:
  require_to_design: human_confirm
  test_to_dev: human_confirm
  review_to_deploy: always_required

quality:
  coverage_min: 85
  ruff: must_pass
  mypy: must_pass
"""
    _write(project_path / ".ai-factory" / "config.yaml", config_content)

    # 生成 .env.example
    _write(project_path / ".env.example", """\
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
""")

    # 生成 README.md
    _write(project_path / "README.md", """\
# {project_name}

使用 AI Factory 自动创建的 FastAPI + React 项目。

## 启动

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

## AI Factory 流水线

```bash
ai-factory submit "{project_name}" -d "功能描述"
ai-factory status
ai-factory gate approve -p <task_id> -g Gate1
```
""".format(project_name=project_name))

    print("✅ 项目骨架创建完成!")
    print(f"   目录: {project_path}")
    print()
    print("   下一步:")
    print(f"   cd {project_name}")
    print("   ai-factory submit '第一个功能'")
    print()


def _write(path: Path, content: str):
    """写入文件"""
    path.write_text(content, encoding="utf-8")
