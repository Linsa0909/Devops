"""
Developer Agent v3 — 基于骨架增量生成 + 自动补全依赖导入
"""
from __future__ import annotations
import json, re, os
from typing import Optional
from llm import LLMService
from agents.writer import WorkspaceWriter
from runtime.sandbox import DockerSandbox
from runtime.retry_loop import RetryLoop
from runtime.template import ProjectTemplate


class DeveloperAgent:

    def __init__(self, workspace: str = "workspace", llm: Optional[LLMService] = None):
        self.workspace = workspace
        self.llm = llm or LLMService()
        self.writer = WorkspaceWriter(workspace)
        self.sandbox = DockerSandbox(workspace)
        self.retry = RetryLoop(self.sandbox, self.writer, self.llm)

    def execute(self, requirement: str, design: str, rules: list[dict]) -> dict:
        tmpl = ProjectTemplate(self.workspace)
        tmpl.scaffold()

        rules_text = "\n".join([f"- [{r.get('id','?')}] {r.get('title','?')}" for r in rules if r.get('active', True)])[:500]

        # Skills constraints (from addyosmani/agent-skills)
        skills_constraints = """
## API Design Constraints (api-and-interface-design)
- Contract first: define types BEFORE implementation
- Consistent error semantics: all errors return {"code": "ERROR_CODE", "message": "..."} 
- Validate at boundaries: Pydantic at route level, not internal functions
- Backward compatibility: new fields are optional, never remove/change existing fields
- Pagination: list endpoints MUST support ?page=1&size=20

## TDD Constraints (test-driven-development)
- Write test BEFORE implementation (RED → GREEN → REFACTOR)
- One assertion per concept per test
- DAMP over DRY: each test tells a complete story
- Prefer real implementations over mocks
- Arrange-Act-Assert pattern in every test

## Frontend Constraints (frontend-ui-engineering)
- Design system tokens, not raw hex/px values
- Consistent spacing scale (0.25rem increments)
- WCAG 2.1 AA: keyboard accessible, ARIA labels, focus management
- Meaningful empty/error/loading states
"""

        prompt = f"""You are a Staff Python engineer. Fill ONLY the 4 business logic files.

## Target files (generate these 4)
1. app/models/__init__.py — SQLAlchemy models (define ALL ORM classes here)
2. app/schemas/request.py — Pydantic request/response models
3. app/services/logic.py — Business logic CRUD functions  
4. app/api/router.py — FastAPI router (/api/v1 prefix)

## Requirement
{requirement[:2000]}

## Design
{design[:1000]}

## Constraints
{rules_text}

{skills_constraints}

## JSON Output format (MUST return exactly 4 files):
{{"files": [
  {{"file_path": "app/models/__init__.py", "content": "from app.models.base import Base\\nfrom sqlalchemy import ...\\n\\nclass Message(Base): ..."}},
  {{"file_path": "app/schemas/request.py", "content": "from pydantic import ..."}},
  {{"file_path": "app/services/logic.py", "content": "from sqlalchemy.orm import Session\\n..."}},
  {{"file_path": "app/api/router.py", "content": "from fastapi import APIRouter, Depends\\n..."}}
]}}
Only output JSON, no explanation."""
        # ── Step 2: LLM 生成 (带超时) ──
        llm_output = None
        try:
            import threading as _t
            results = []
            def _call():
                try:
                    results.append(self.llm._call(
                        system="You are a Python engineer. ONLY return valid JSON. No markdown.",
                        user=prompt, temperature=0.2,
                    ))
                except Exception as e:
                    results.append(e)
            t = _t.Thread(target=_call, daemon=True)
            t.start()
            t.join(timeout=25)  # 25s timeout
            if not results:
                raise TimeoutError("DeepSeek call timed out (45s)")
            if isinstance(results[0], Exception):
                raise results[0]
            llm_output = results[0]
        except Exception as e:
            print(f"[DeveloperAgent] LLM call failed: {e}")
            llm_output = '{"files": []}'
        
        files = self._parse_files(llm_output)

        # ── Write generated files ──
        for f in files:
            self.writer.write([f])

        # ── Auto-fix missing model stubs ──
        self._fix_missing_stubs()

        # ── pytest ──
        loop_result = self.retry.execute_with_retry(files)

        return {
            "passed": loop_result["passed"],
            "attempts": loop_result["attempts"],
            "files": files,
            "file_tree": self.writer.tree(),
            "fix_history": loop_result.get("history", []),
            "final_output": loop_result.get("final_output", ""),
        }

    # ─── Auto-fix missing imports ───
    def _fix_missing_stubs(self):
        """Scan all Python files for from/import references to nonexistent modules.
        Auto-generate stub files for any missing local imports."""
        py_files = []
        for root, dirs, fnames in os.walk(self.workspace):
            for fn in fnames:
                if fn.endswith(".py") and "__pycache__" not in root:
                    py_files.append(os.path.join(root, fn))

        # Find all `from app.models.xxx import YYY` that refer to missing files
        missing = {}
        for fp in py_files:
            content = open(fp).read()
            for m in re.finditer(r'from\s+(app\.\w+(?:\.\w+)*)\s+import', content):
                mod_path = m.group(1).replace(".", "/") + ".py"
                full_path = os.path.join(self.workspace, mod_path)
                if not os.path.exists(full_path):
                    # Create stub
                    parts = mod_path.split("/")
                    stub_content = ""
                    if parts[-1] != "__init__.py":
                        class_name = os.path.splitext(parts[-1])[0].title().replace("_", "")
                        stub_content = f"# Auto-generated stub for {m.group(1)}\n\nclass {class_name}:\n    pass\n"
                    else:
                        stub_content = f"# Auto-generated stub for {m.group(1)}\n"
                    dir_path = os.path.dirname(full_path)
                    os.makedirs(dir_path, exist_ok=True)
                    open(full_path, "w").write(stub_content)

    # ─── Parse ───
    def _parse_files(self, raw: str) -> list[dict]:
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            for p in raw.split("```"):
                if "{" in p and "files" in p: raw = p; break
        try:
            data = json.loads(raw.strip())
            return data.get("files", [])
        except:
            return [{"file_path": "app/api/router.py", "content": f"# Generated\n{raw[:2000]}"}]
