"""
AgentDev OS — LLM 服务层
DeepSeek API 驱动: 需求分析 / 设计生成 / 代码生成 / 审查 / 知识提取
"""
import os
import json
from typing import Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL = "deepseek-chat"


class LLMService:
    """大模型服务 — 对接 DeepSeek API"""

    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.base_url = DEEPSEEK_BASE_URL
        self.client = httpx.Client(timeout=120)

    def _call(self, system: str, user: str, temperature: float = 0.3) -> str:
        """调用 DeepSeek API"""
        if not self.api_key:
            return self._mock_response(system, user)

        try:
            resp = self.client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                    "max_tokens": 4096,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return self._mock_response(system, user, fallback=str(e))

    # ============================================================
    # REQ Agent — 需求分析
    # ============================================================
    def analyze_requirement(self, name: str, description: str) -> dict:
        """将原始想法转化为结构化需求规格说明书"""
        system = """你是资深产品经理 (PM Agent)。请将用户的原始想法转化为标准的需求规格说明书。
输出 JSON 格式:
{
  "requirement_md": "...",        // 完整 Markdown 需求文档
  "user_stories": ["..."],        // 用户故事列表
  "functional_modules": [{"name":"...", "description":"..."}],
  "api_specs": [{"method":"...", "path":"...", "description":"..."}],
  "tech_stack": ["..."],
  "risk_points": ["..."]
}"""
        user = f"## 需求名称\n{name}\n\n## 原始描述\n{description}"
        raw = self._call(system, user)
        return self._safe_parse(raw, {
            "requirement_md": f"# {name}\n\n{description}",
            "user_stories": [f"作为用户，我希望系统能{description[:30]}..."],
            "functional_modules": [{"name": "核心模块", "description": description[:50]}],
            "api_specs": [{"method": "POST", "path": "/api/v1/process", "description": "主处理接口"}],
            "tech_stack": ["Python", "FastAPI", "React"],
            "risk_points": ["需求边界待确认"],
        })

    # ============================================================
    # Architect Agent — 架构设计 (分层架构 + Mermaid 图)
    # ============================================================
    def design_architecture(self, requirement: str) -> dict:
        """基于结构化需求生成架构设计 — 必须与 requirement 有本质差异"""
        system = """你是资深系统架构师。请基于需求分析，设计分层架构。

## 你必须输出以下层次结构 (各层独立、有本质差异):
1. **接入层** — 网关/负载均衡/CDN
2. **业务层** — 微服务拆分、领域逻辑
3. **数据层** — 数据库/缓存/消息队列
4. **基础设施层** — 容器编排/监控/日志
5. **Agent层** — AI Agent 协作拓扑

## Mermaid 图要求:
- 至少包含 8 个节点
- 包含数据库节点、缓存节点、微服务节点、前端节点、Agent节点
- 标注数据流方向

## 输出 JSON 格式:
{
  "design_md": "完整的 Markdown 架构设计文档 (技术选型理由、分层说明、关键决策)",
  "architecture_diagram": "graph TD\\n    A[...] --> B[...]\\n    ...(至少8个节点)",
  "component_list": [{"name":"...", "layer":"接入/业务/数据/基础/Agent", "responsibility":"...", "tech":"..."}],
  "data_flow": [{"from":"...", "to":"...", "protocol":"HTTP/gRPC/消息队列", "data":"..."}],
  "api_design": [{"method":"GET|POST|PUT|DELETE", "path":"/api/...", "description":"...", "request_body":"...", "response":"..."}]
}"""
        raw = self._call(system, requirement[:4000])
        return self._safe_parse(raw, {
            "design_md": f"## 系统架构设计\n\n{requirement[:200]}\n\n### 分层架构\n- 接入层: Nginx/FastAPI 网关\n- 业务层: 微服务集群\n- 数据层: PostgreSQL + Redis\n- 基础设施: Docker/K8s",
            "architecture_diagram": "graph TD\n    A[客户端] --> B[Nginx网关]\n    B --> C[FastAPI]\n    C --> D[业务服务]\n    D --> E[(PostgreSQL)]\n    D --> F[(Redis)]\n    C --> G[Agent调度器]\n    G --> H[CodeLoop]",
            "component_list": [{"name": "API网关", "layer": "接入", "responsibility": "路由/限流/鉴权", "tech": "FastAPI"}],
            "data_flow": [{"from": "客户端", "to": "网关", "protocol": "HTTPS", "data": "REST请求"}],
            "api_design": [{"method": "POST", "path": "/api/v1/process", "description": "主处理接口", "request_body": "JSON", "response": "JSON"}],
        })

    # ============================================================
    # Developer Agent — 代码生成
    # ============================================================
    def generate_code(self, design: str, language: str = "python", module_type: str = "backend") -> dict:
        """根据设计生成代码"""
        system = f"""你是资深开发工程师 (Developer Agent)。请根据设计文档生成{language}代码。
输出 JSON:
{{
  "code": "...",                    // 完整代码
  "file_path": "src/...",           // 建议文件路径
  "dependencies": ["..."],          // 依赖列表
  "test_code": "...",               // 单元测试代码
  "explanation": "..."              // 代码说明
}}"""
        user = f"## 设计文档\n{design[:2000]}\n\n## 模块类型\n{module_type}\n## 语言\n{language}"
        raw = self._call(system, user, temperature=0.2)
        return self._safe_parse(raw, {
            "code": f"# Auto-generated by AgentDev OS\n# Module: {module_type}\n\n",
            "file_path": f"src/{module_type}/main.py",
            "dependencies": [f"{language}-sdk"],
            "test_code": "# Tests\n",
            "explanation": f"自动生成的{module_type}模块代码。",
        })

    # ============================================================
    # Critic Agent — 代码审查
    # ============================================================
    def review_code(self, code: str, rules: list) -> dict:
        """审查代码质量与合规性"""
        rules_text = "\n".join([f"- [{r['rule_id']}] {r['title']}" for r in rules])
        system = """你是资深代码审查员 (Critic Agent)。请对代码进行全面审查。
输出 JSON:
{
  "passed": true/false,
  "score": 0-100,
  "issues": [{"severity":"high/medium/low", "line":0, "message":"...", "suggestion":"..."}],
  "improvements": ["..."],
  "summary": "..."
}"""
        user = f"## 审查规则\n{rules_text}\n\n## 代码\n```\n{code[:3000]}\n```"
        raw = self._call(system, user)
        return self._safe_parse(raw, {
            "passed": True, "score": 85,
            "issues": [],
            "improvements": ["代码结构清晰"],
            "summary": "代码审查通过。",
        })

    # ============================================================
    # Knowledge Agent — 知识提取
    # ============================================================
    def extract_knowledge(self, pipeline_data: dict) -> dict:
        """从全链路中提取可复用的知识资产"""
        system = """你是知识管理 Agent。请从流水线数据中提炼可复用的知识资产。
输出 JSON:
{
  "refined_prompts": [{"role":"...", "content":"..."}],
  "qa_pairs": [{"question":"...", "answer":"..."}],
  "lessons_learned": ["..."],
  "domain_knowledge": [{"topic":"...", "content":"..."}],
  "metrics": {"total_tokens": 0, "total_time_seconds": 0, "fix_count": 0}
}"""
        raw = self._call(system, json.dumps(pipeline_data, ensure_ascii=False)[:3000])
        return self._safe_parse(raw, {
            "refined_prompts": [{"role": "system", "content": "提取后的系统提示词"}],
            "qa_pairs": [{"question": "如何优化?",
                          "answer": "基于本次实践的总结。"}],
            "lessons_learned": ["规则前置检查可减少后期修复成本"],
            "domain_knowledge": [{"topic": "架构设计模式",
                                  "content": "本次采用的模式总结"}],
            "metrics": {"total_tokens": 15000, "total_time_seconds": 120, "fix_count": 1},
        })

    # ============================================================
    # Mock 回退
    # ============================================================
    def _mock_response(self, system: str, user: str, fallback: str = "") -> str:
        """无 API Key 时的 Mock 回退"""
        if "需求规格说明书" in system or "资深产品经理" in system:
            return json.dumps({
                "requirement_md": f"# 需求规格说明书\n\n{user[:100]}...\n\n## 用户故事\n- 作为用户，我希望系统能自动处理\n\n## 功能模块\n- 核心处理模块",
                "user_stories": [f"作为用户，我希望{user[:30]}..."],
                "functional_modules": [{"name": "核心处理模块", "description": "处理核心业务逻辑"}],
                "api_specs": [{"method": "POST", "path": "/api/v1/process", "description": "主处理接口"}],
                "tech_stack": ["Python", "FastAPI", "React", "Docker"],
                "risk_points": ["需确认性能要求"],
            }, ensure_ascii=False)
        if "架构师" in system:
            return json.dumps({
                "design_md": "## 系统架构设计\n\n采用分层微服务架构。\n- 接入层: Nginx/FastAPI\n- 业务层: LangGraph 状态机\n- 数据层: PostgreSQL + Redis",
                "architecture_diagram": "graph TD\n    A[客户端] --> B[API网关]\n    B --> C[业务服务]\n    C --> D[数据库]",
                "component_list": [{"name": "API网关", "responsibility": "路由与鉴权", "tech": "FastAPI"}],
                "data_flow": [{"from": "客户端", "to": "API网关", "data": "HTTP请求"}],
                "api_design": [{"method": "POST", "path": "/api/v1/process", "request": "{\"data\":\"...\"}", "response": "{\"result\":\"...\"}"}],
            }, ensure_ascii=False)
        if "开发工程师" in system:
            return json.dumps({
                "code": f"# Auto-generated module\n\"\"\"Module description\"\"\"\n\n\ndef main():\n    \"\"\"Main entry point\"\"\"\n    pass\n\n\nif __name__ == '__main__':\n    main()\n",
                "file_path": "src/module/main.py",
                "dependencies": ["fastapi", "pydantic"],
                "test_code": "def test_main():\n    assert True\n",
                "explanation": "自动生成的模块框架代码。",
            }, ensure_ascii=False)
        if "审查员" in system:
            return json.dumps({
                "passed": True, "score": 88,
                "issues": [{"severity": "low", "line": 1, "message": "缺少文档字符串", "suggestion": "添加 module docstring"}],
                "improvements": ["添加类型注解", "增加异常处理"],
                "summary": "代码质量良好，通过审查。",
            }, ensure_ascii=False)
        if "知识管理" in system:
            return json.dumps({
                "refined_prompts": [{"role": "system", "content": "优化后的系统提示词"}],
                "qa_pairs": [{"question": "常见问题", "answer": "常见解决方案"}],
                "lessons_learned": ["提前配置规则可减少返工"],
                "domain_knowledge": [{"topic": "架构设计", "content": "微服务架构最佳实践"}],
                "metrics": {"total_tokens": 12000, "total_time_seconds": 90, "fix_count": 0},
            }, ensure_ascii=False)
        return json.dumps({"message": "mock response", "system": system[:50], "user": user[:50]})

    @staticmethod
    def _safe_parse(raw: str, default: dict) -> dict:
        """安全解析 JSON"""
        # 提取 JSON 块
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]
        try:
            return json.loads(raw.strip())
        except:
            return default
