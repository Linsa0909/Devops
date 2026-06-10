"""Developer Agent v3 — 骨架增量 + subprocess LLM 调用"""
from __future__ import annotations
import json, re, os, subprocess, sys, tempfile
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
        skills_c = "\n## API: consistent errors, pagination, Pydantic validation\n## TDD: RED-GREEN-REFACTOR, DAMP, Arrange-Act-Assert\n"

        prompt = f"""Fill 4 target files:
1. app/models/__init__.py (SQLAlchemy ORM)
2. app/schemas/request.py (Pydantic)
3. app/services/logic.py (CRUD)
4. app/api/router.py (FastAPI, /api/v1 prefix)

Requirement: {requirement[:1500]}
Design: {design[:800]}
Rules: {rules_text}
{skills_c}

Output JSON: {{"files":[{{"file_path":"...","content":"..."}}]}}"""

        llm_output = '{"files": []}'
        # ── LLM: write script to temp file, run as subprocess with hard 60s timeout ──
        script = '''import httpx, os, json, sys
try:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        sys.stdout.write('{"files": []}')
        sys.exit(0)
    with httpx.Client(timeout=55) as c:
        r = c.post("https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
            json={"model": "deepseek-chat",
                  "messages": [{"role":"system","content":"You are a Python engineer. ONLY return valid JSON."},
                               {"role":"user","content":''' + repr(prompt) + '''}],
                  "temperature": 0.2, "max_tokens": 4096})
        sys.stdout.write(r.json()["choices"][0]["message"]["content"])
except Exception as e:
    sys.stdout.write('{"files": []}')
'''
        import tempfile, subprocess
        tf = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        tf.write(script)
        tf.close()
        try:
            env = os.environ.copy()
            r = subprocess.run([sys.executable, tf.name], capture_output=True, text=True, timeout=65, env=env)
            llm_output = r.stdout.strip() or '{"files": []}'
        except subprocess.TimeoutExpired:
            llm_output = '{"files": []}'
        finally:
            try: os.unlink(tf.name)
            except: pass

        files = self._parse_files(llm_output)
        for f in files:
            self.writer.write([f])
        self._fix_missing_stubs()

        loop_result = self.retry.execute_with_retry(files)
        return dict(passed=loop_result["passed"], attempts=loop_result["attempts"],
                    files=files, file_tree=self.writer.tree(),
                    fix_history=loop_result.get("history", []),
                    final_output=loop_result.get("final_output", ""))

    def _fix_missing_stubs(self):
        for root, dirs, fnames in os.walk(self.workspace):
            for fn in fnames:
                if not fn.endswith(".py") or "__pycache__" in root: continue
                c = open(os.path.join(root, fn)).read()
                for m in re.finditer(r'from\s+(app\.\w+(?:\.\w+)*)\s+import', c):
                    fp = os.path.join(self.workspace, m.group(1).replace(".", "/") + ".py")
                    if not os.path.exists(fp):
                        os.makedirs(os.path.dirname(fp), exist_ok=True)
                        open(fp, "w").write("# stub\n")

    def _parse_files(self, raw: str) -> list[dict]:
        if "```json" in raw: raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            for p in raw.split("```"):
                if "{" in p and "files" in p: raw = p; break
        try:
            data = json.loads(raw.strip())
            f = data.get("files", [])
            for x in f:
                if not isinstance(x.get("test_file_path"), str):
                    x.pop("test_file_path", None)
                    x.pop("test_content", None)
            return f
        except:
            return []
