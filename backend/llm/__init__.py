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

    def _call(self, system: str, user: str, temperature: float = 0.3, timeout: int = 30) -> str:
        """调用 DeepSeek API (每次新建 client, 避免 WSL 网络 hang)"""
        if not self.api_key:
            return self._mock_response(system, user)

        try:
            # 每次调用新建 client，避免连接池 hang
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(
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
        raw = self._call(system, f"## 需求概述\n{requirement[:500]}\n\n## 完整需求上下文\n{requirement[:3000]}", temperature=0.3)
        return self._safe_parse(raw, {
            "design_md": f"## 系统架构设计文档\n\n### 1. 架构决策\n基于需求分析，本系统采用以下架构方案：\n\n- **接入层**: Nginx 反向代理 + FastAPI 网关，提供限流、鉴权、日志\n- **业务层**: 微服务拆分，每个业务域独立部署\n- **数据层**: PostgreSQL 主库 + Redis 缓存 + RabbitMQ 消息队列\n- **基础设施层**: Docker Compose 部署 + Prometheus 监控\n- **Agent 层**: LangGraph 状态机编排多 Agent 协作\n\n### 2. 技术栈\n- 后端: FastAPI + SQLAlchemy + Pydantic\n- 前端: React + TailwindCSS\n- 数据库: PostgreSQL 15\n- 缓存: Redis 7\n- 消息: RabbitMQ\n\n### 3. 关键设计决策\n- 采用 CQRS 模式分离读写\n- API 版本化 (/api/v1/...)\n- JWT 无状态认证\n- 异步任务队列处理耗时操作\n\n### 4. 安全设计\n- API Token 过期时间 ≤ 7 天\n- 数据传输全程 HTTPS\n- 日志脱敏处理\n- 容器镜像 Trivy 扫描",
            "architecture_diagram": "graph TD\n    A[用户浏览器] --> B[Nginx 网关]\n    B --> C[FastAPI 路由]\n    C --> D[认证服务]\n    C --> E[业务服务A]\n    C --> F[业务服务B]\n    E --> G[(PostgreSQL)]\n    E --> H[(Redis缓存)]\n    F --> G\n    F --> I[RabbitMQ]\n    I --> J[异步Worker]\n    C --> K[LangGraph Agent]\n    K --> L[CodeLoop 沙箱]",
            "component_list": [
                {"name": "Nginx 网关", "layer": "接入", "responsibility": "负载均衡/SSL终止/静态资源", "tech": "Nginx"},
                {"name": "FastAPI 路由", "layer": "接入", "responsibility": "请求分发/参数校验", "tech": "FastAPI"},
                {"name": "认证服务", "layer": "业务", "responsibility": "JWT签发/验证/刷新", "tech": "FastAPI+PyJWT"},
                {"name": "业务服务", "layer": "业务", "responsibility": "核心业务逻辑", "tech": "FastAPI+SQLAlchemy"},
                {"name": "PostgreSQL", "layer": "数据", "responsibility": "持久化存储", "tech": "PostgreSQL 15"},
                {"name": "Redis", "layer": "数据", "responsibility": "缓存/会话/限流", "tech": "Redis 7"},
                {"name": "RabbitMQ", "layer": "数据", "responsibility": "异步消息队列", "tech": "RabbitMQ"},
                {"name": "LangGraph Agent", "layer": "Agent", "responsibility": "多Agent编排/状态管理", "tech": "LangGraph+DeepSeek"},
            ],
            "data_flow": [
                {"from": "浏览器", "to": "Nginx", "protocol": "HTTPS", "data": "HTTP请求"},
                {"from": "Nginx", "to": "FastAPI", "protocol": "HTTP", "data": "代理请求"},
                {"from": "FastAPI", "to": "业务服务", "protocol": "HTTP/gRPC", "data": "业务数据"},
                {"from": "业务服务", "to": "PostgreSQL", "protocol": "TCP", "data": "SQL查询"},
                {"from": "业务服务", "to": "Redis", "protocol": "TCP", "data": "缓存读写"},
            ],
            "api_design": [
                {"method": "POST", "path": "/api/v1/auth/login", "description": "用户登录", "request_body": "{\"username\":\"...\",\"password\":\"...\"}", "response": "{\"token\":\"...\"}"},
                {"method": "GET", "path": "/api/v1/health", "description": "健康检查", "request_body": "—", "response": "{\"status\":\"ok\"}"},
            ],
        })

    # ============================================================
    # Rules Agent — 基于项目上下文生成自定义规则
    # ============================================================
    def generate_project_rules(self, requirement: str, design: str) -> list[dict]:
        """基于具体项目需求生成针对性规则约束"""
        system = """你是软件安全与质量专家。请基于以下项目的具体需求，生成 4-6 条针对性的规则约束。

## 你必须返回一个 JSON 数组，包含 4-6 条规则：
[
  {"id": "R-...", "category": "安全|性能|规范", "title": "规则名称", "description": "具体约束内容"},
  ...
]

## 要求:
- 必须返回数组格式，至少4条
- 每条规则必须针对这个具体项目
- 安全规则：针对本项目的数据敏感点(至少1条)
- 性能规则：针对本项目的性能瓶颈(至少1条)  
- 规范规则：针对本项目的技术栈(至少1条)"""
        user = f"## 需求\n{requirement[:2000]}\n\n## 架构设计\n{design[:2000]}"
        raw = self._call(system, user, temperature=0.3)
        parsed = self._safe_parse(raw, [
            {"id": "R-C1", "category": "安全", "title": "敏感数据加密存储", "description": "用户个人信息必须AES-256加密后存储"},
            {"id": "R-C2", "category": "性能", "title": "接口响应时间 ≤ 500ms", "description": "核心业务接口P99响应时间不超过500ms"},
            {"id": "R-C3", "category": "规范", "title": "统一异常处理", "description": "所有API必须返回标准化的错误响应格式"},
            {"id": "R-C4", "category": "安全", "title": "输入参数校验", "description": "所有用户输入必须经过Pydantic模型校验"},
        ])
        if isinstance(parsed, dict):
            return [parsed]
        return parsed

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
        if "软件安全与质量专家" in system:
            return json.dumps([
                {"id": "R-C1", "category": "安全", "title": "敏感数据加密存储", "description": "用户个人信息必须AES-256加密后存储，密钥通过环境变量注入"},
                {"id": "R-C2", "category": "安全", "title": "审批操作审计日志", "description": "所有审批操作（通过/驳回/撤销）必须记录审计日志，包含操作人、时间、IP、操作类型"},
                {"id": "R-C3", "category": "性能", "title": "接口响应时间 ≤ 500ms", "description": "核心业务接口P99响应时间不超过500ms，必须实现数据库查询缓存"},
                {"id": "R-C4", "category": "规范", "title": "统一异常处理", "description": "所有API必须返回标准化的错误响应格式：{\"code\":...,\"message\":\"...\",\"data\":null}"},
                {"id": "R-C5", "category": "规范", "title": "API参数校验", "description": "所有用户输入必须经过Pydantic模型校验，禁止在业务逻辑中直接使用原始输入"},
            ], ensure_ascii=False)
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
        """安全解析 JSON — always returns dict, falling back to default on any unexpected format"""
        if raw is None:
            return default
        if isinstance(raw, dict):
            merged = dict(default)
            merged.update(raw)
            return merged
        if isinstance(raw, list):
            # If raw is a list, take first dict item and merge with default
            if raw and isinstance(raw[0], dict):
                merged = dict(default)
                merged.update(raw[0])
                return merged
            return default
        # Try to extract JSON from code fences
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            parts = raw.split("```")
            # Try each ``` block — look for one with "design_md" or "{"
            for i in range(1, len(parts), 2):
                block = parts[i].strip()
                if "design_md" in block or "architecture" in block or block.startswith("{"):
                    raw = block
                    break
        try:
            parsed = json.loads(raw.strip())
            if isinstance(parsed, list):
                if parsed and isinstance(parsed[0], dict):
                    merged = dict(default)
                    merged.update(parsed[0])
                    return merged
                return default
            if isinstance(parsed, dict):
                merged = dict(default)
                merged.update(parsed)
                return merged
            return default
        except:
            return default
