"""
Developer Agent v2 — 基于项目骨架增量生成代码
1. 先用 ProjectTemplate 创建标准化 FastAPI 骨架 (config/auth/models/router/main)
2. 把项目树、API契约、DB模式、验收标准注入 Prompt
3. LLM 只填充业务逻辑文件 (models/schemas/services/router)
4. pytest 本地执行 + RetryLoop 修复
"""
from __future__ import annotations
import json
from typing import Optional
from llm import LLMService
from agents.writer import WorkspaceWriter
from runtime.sandbox import DockerSandbox
from runtime.retry_loop import RetryLoop
from runtime.template import ProjectTemplate


class DeveloperAgent:
    """开发 Agent v2 — 增量生成, 只填充业务逻辑, 不动骨架文件"""

    def __init__(self, workspace: str = "workspace", llm: Optional[LLMService] = None):
        self.workspace = workspace
        self.llm = llm or LLMService()
        self.writer = WorkspaceWriter(workspace)
        self.sandbox = DockerSandbox(workspace)
        self.retry = RetryLoop(self.sandbox, self.writer, self.llm)

    def execute(self, requirement: str, design: str, rules: list[dict]) -> dict:
        """生成代码 → 落盘 → 执行 → 修复 → 审核"""

        # ── Step 0: 创建项目骨架 ──
        tmpl = ProjectTemplate(self.workspace)
        tmpl.scaffold()

        # ── Step 1: 精简 Prompt ──
        rules_text = "\n".join([
            f"- [{r.get('id','?')}] {r.get('title','?')}"
            for r in rules if r.get('active', True)
        ])[:500]

        prompt = f"""你是 Staff Python 工程师。已有 FastAPI 骨架项目，只填充业务逻辑。

## 项目骨架 (只改以下4个文件, 其他不动)
- app/models/__init__.py (SQLAlchemy ORM)
- app/schemas/request.py (Pydantic)
- app/services/logic.py (CRUD)
- app/api/router.py (API路由, 前缀 /api/v1)

## 需求
{requirement[:2000]}

## 验收标准
- 所有端点在 /api/v1/ 前缀下
- 统一响应: {{"code":0,"message":"ok","data":...}}
- 测试位于 tests/test_api.py

## 约束
{rules_text}

返回JSON: {{"files": [{{"file_path":"...","content":"..."}}]}}
只返回JSON。"""

        llm_output = self.llm._call(
            system="你是 Python 工程师。只返回 JSON 格式文件列表。",
            user=prompt, temperature=0.2,
        )
        files = self._parse_files(llm_output)

        # ── Step 4: 写入文件 (保留骨架, 只覆盖业务文件) ──
        for f in files:
            self.writer.write([f])

        # ── Step 5: pytest 本地执行 ──
        loop_result = self.retry.execute_with_retry(files)

        return {
            "passed": loop_result["passed"],
            "attempts": loop_result["attempts"],
            "files": files,
            "file_tree": self.writer.tree(),
            "fix_history": loop_result.get("history", []),
            "final_output": loop_result.get("final_output", ""),
        }

    def _plan_tasks(self, requirement: str, design: str) -> str:
        """PlannerAgent — 拆解需求为具体开发任务"""
        prompt = f"""将以下需求拆解为 3-5 个具体的开发任务。每行一个任务。

## 需求
{requirement[:1500]}

## 设计
{design[:1000]}

只返回任务列表, 格式:
- 任务: 创建 [模型名] 数据表
- 任务: 实现 [功能] API 端点
- ...
"""
        try:
            raw = self.llm._call(
                system="你是技术项目经理。将需求拆解为开发任务。只返回任务列表。",
                user=prompt, temperature=0.1,
            )
            return raw[:800]
        except:
            return "- 任务: 创建数据模型\n- 任务: 实现 API 端点\n- 任务: 添加参数校验\n- 任务: 编写测试"

    def _parse_files(self, raw: str) -> list[dict]:
        """解析 LLM JSON 输出"""
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            parts = raw.split("```")
            for p in parts:
                if "{" in p and "files" in p:
                    raw = p; break
        try:
            data = json.loads(raw.strip())
            return data.get("files", [])
        except:
            return [{
                "file_path": "app/api/router.py",
                "content": f"# Generated\n{raw[:2000]}",
            }]
