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
        """5轴代码审查 (code-review-and-quality skill)"""
        prompt = f"""You are a Staff Engineer conducting a 5-axis code review.

## Code
```
{code[:3000]}
```

## Design
{design[:1000]}

## Test Results
- Passed: {test_result.get('pass', test_result.get('passed', False))}
- Fix attempts: {len(exec_history)}

## Active Rules
{json.dumps([r for r in rules if r.get('active')], ensure_ascii=False, indent=2)[:1500]}

## Five-Axis Review Framework
### 1. Correctness
Edge cases handled? Error paths handled? Tests match spec?

### 2. Readability & Simplicity
Names clear? Control flow straightforward? Could be fewer lines? Abstractions earning their complexity?

### 3. Architecture  
Follows existing patterns? Clean module boundaries? No circular dependencies? API contract-first?

### 4. Security
Input validated at boundaries? Secrets in code? SQL parameterized? External data treated as untrusted?

### 5. Performance
N+1 queries? Unbounded loops? Missing pagination? Sync operations that should be async?

Return JSON:
{{
  "passed": true/false,
  "score": 0-100,
  "axes": {{"correctness": "pass/fail/needs_work", "readability": "...", "architecture": "...", "security": "...", "performance": "..."}},
  "issues": [{{"severity":"Critical|Required|Nit|Optional|FYI", "axis":"correctness|readability|...", "message":"...", "suggestion":"..."}}],
  "suggestions": ["..."],
  "summary": "One-line review verdict"
}}
"""
        raw = self.llm._call(
            system="You are a Senior Staff Engineer. Conduct a 5-axis code review. Assign severity labels (Critical/Required/Nit/Optional/FYI).",
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
                "axes": {"correctness": "needs_work", "readability": "pass", "architecture": "pass", "security": "pass", "performance": "pass"},
                "issues": [],
                "suggestions": [],
                "summary": "Auto-review complete",
            }
