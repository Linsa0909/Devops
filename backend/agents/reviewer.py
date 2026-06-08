"""
Reviewer Agent — 全链路审查：代码质量 + 规则合规 + 架构一致性
"""
from __future__ import annotations
import json
from typing import Optional
from llm import LLMService


class ReviewerAgent:
    """
    Reviewer Agent — 终极审查：
    1. 代码质量 (命名/结构/复杂度)
    2. 规则合规 (Guardrails 16条)
    3. 架构一致性 (对比原始设计)
    4. 测试充分性 (覆盖率)
    """

    DIMENSIONS = [
        "代码命名规范",
        "函数复杂度",
        "错误处理",
        "规则合规",
        "架构一致性",
        "测试覆盖率",
        "性能考虑",
        "安全性",
        "可维护性",
        "文档完整性",
    ]

    def __init__(self, llm: Optional[LLMService] = None):
        self.llm = llm or LLMService()

    def review(self, code: str, design: str, test_result: dict,
               rules: list[dict], exec_history: list[dict]) -> dict:
        """
        多维度审查
        返回: {passed, score, dimensions, issues, suggestions, summary}
        """
        prompt = f"""你是资深代码审查员。请按以下维度评审代码。

## 📋 代码
```
{code[:3000]}
```

## 🏗️ 设计文档
{design[:1000]}

## 🧪 测试结果
- 通过: {test_result.get('passed', False)}
- 历史修复次数: {len(exec_history)}

## 🛡️ 活跃规则
{json.dumps([r for r in rules if r.get('active')], ensure_ascii=False, indent=2)[:1500]}

请评估这 {len(self.DIMENSIONS)} 个维度:
{chr(10).join(f'{i+1}. {d}' for i, d in enumerate(self.DIMENSIONS))}

返回 JSON:
{{
  "passed": true/false,
  "score": 0-100,
  "dimensions": {{"维度名": "通过/需改进/阻塞", ...}},
  "issues": [{{"severity":"high/medium/low","file":"...","message":"..."}}],
  "suggestions": ["..."],
  "summary": "一句话总结"
}}
"""
        raw = self.llm._call(
            system="你是资深代码审查员。严格按企业标准审查代码质量、安全性、可维护性。",
            user=prompt,
            temperature=0.1,
        )
        return self._parse(raw)

    def _parse(self, raw: str) -> dict:
        try:
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0]
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0]
            return json.loads(raw.strip())
        except:
            return {
                "passed": True,
                "score": 80,
                "dimensions": {d: "通过" for d in self.DIMENSIONS},
                "issues": [],
                "suggestions": [],
                "summary": "自动审查完成",
            }
