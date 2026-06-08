"""
AgentDev OS — Guardrails 规则引擎
4 类 × 16 条规则 + Scope forbidden + 自定义规则
"""
from typing import Optional
from models import Rule, RuleCategory, Pipeline


class GuardrailEngine:
    """规则引擎 — 检查和执行规则"""

    # Scope Forbidden 关键词列表
    FORBIDDEN_SCOPES = [
        "/etc/passwd", "/etc/shadow", "/root/.ssh",
        "rm -rf", "DROP TABLE", "DELETE FROM",
        "os.system(", "subprocess.Popen", "exec(",
    ]

    # Convergence 停止条件
    MAX_CONSECUTIVE_RETRIES = 5
    MAX_TOKENS_PER_TASK = 100_000
    MAX_EXECUTION_SECONDS = 300

    @staticmethod
    def check_rule(rule: Rule, context: dict) -> tuple[bool, Optional[str]]:
        """
        检查单条规则
        返回: (passed, error_message)
        """
        if not rule.active:
            return True, None  # 未激活的规则跳过

        code = context.get("code", "")
        logs = context.get("logs", "")
        api_spec = context.get("api_spec", "")

        checks = {
            # R-1: Token 检查
            "R-1": lambda: ("jira_token" not in code.lower() and "jira_token" not in logs.lower(),
                            "检测到 Jira Token 明文"),
            # R-2: 数据脱敏
            "R-2": lambda: (not any(kw in logs for kw in ["password=", "token=", "secret=", "api_key="]),
                            "日志包含敏感信息"),
            # R-4: Token 过期
            "R-4": lambda: ("expire" in api_spec.lower() or "exp" in api_spec.lower(),
                            "API Token 未设置过期时间"),
            # R-7: LIMIT 分页
            "R-7": lambda: ("LIMIT" in code.upper() or "limit" in code.lower(),
                            "数据库查询缺少 LIMIT 分页"),
            # R-9: 前后端分离
            "R-9": lambda: (not any(kw in code for kw in ["SELECT", "INSERT INTO", "DROP"]),
                            "前端代码包含 SQL 语句"),
            # R-12: TailwindCSS
            "R-12": lambda: ("style={{" not in code,
                             "检测到行内 style 样式 (违反 TailwindCSS 规范)"),
            # R-13: Scope 越权
            "R-13": lambda: (not any(fs in code for fs in GuardrailEngine.FORBIDDEN_SCOPES),
                             f"代码访问了禁止 Scope: {[s for s in GuardrailEngine.FORBIDDEN_SCOPES if s in code]}"),
            # R-14: 日志脱敏
            "R-14": lambda: (not any(kw in logs for kw in ["password", "token", "secret"]),
                             "日志包含未脱敏的敏感信息"),
        }

        check_fn = checks.get(rule.id)
        if check_fn:
            passed, err = check_fn()
            rule.passed = passed
            return passed, err if not passed else None

        # 默认通过
        rule.passed = True
        return True, None

    @staticmethod
    def check_all_rules(pipeline: Pipeline, context: dict) -> list[dict]:
        """检查所有激活规则，返回结果列表"""
        results = []
        for rule in pipeline.rules:
            passed, error = GuardrailEngine.check_rule(rule, context)
            results.append({
                "rule_id": rule.id,
                "title": rule.title,
                "category": rule.category.value,
                "passed": passed,
                "error": error,
            })
        return results

    @staticmethod
    def add_custom_rule(pipeline: Pipeline, title: str, category: str = "自定义", description: str = "") -> Rule:
        """追加自定义规则"""
        next_id = len(pipeline.rules) + 1
        rule = Rule(
            id=f"R-{next_id}",
            category=RuleCategory(category),
            title=title,
            description=description or "用户追加的自定义规则。",
            active=True,
        )
        pipeline.rules.append(rule)
        pipeline.logs.append(f"[Guardrails] 追加自定义规则 R-{next_id}: {title}")
        return rule

    @staticmethod
    def toggle_rule(pipeline: Pipeline, rule_id: str, active: bool):
        """开关规则"""
        for rule in pipeline.rules:
            if rule.id == rule_id:
                rule.active = active
                pipeline.logs.append(f"[Guardrails] 规则 {rule_id} → {'激活' if active else '关闭'}")
                break
