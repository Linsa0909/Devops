"""
Fix Agent — 根据 pytest 错误日志自动修复代码
输入: 失败的代码 + pytest 错误输出
输出: 修复后的代码
"""
from __future__ import annotations
import json
import re
from typing import Optional
from llm import LLMService


class FixerAgent:
    """修复 Agent — 专门分析 pytest 失败日志并生成修复补丁"""

    def __init__(self, llm: Optional[LLMService] = None):
        self.llm = llm or LLMService()

    def analyze_failure(self, output: str) -> dict:
        """
        分析 pytest 输出，提取失败信息
        返回: {failed_tests: [...], error_type: str, root_cause: str}
        """
        failed_tests = []
        for line in output.split("\n"):
            if "FAILED" in line or "ERROR" in line:
                failed_tests.append(line.strip()[:200])
            if "AssertionError" in line:
                failed_tests.append(f"Assertion: {line.strip()[:200]}")

        return {
            "failed_tests": failed_tests[:10],
            "total_errors": output.count("FAILED") + output.count("ERROR"),
            "raw": output[:3000],
        }

    def fix(self, analysis: dict, code: str) -> str:
        """
        基于分析结果修复代码
        返回: 修复后的代码
        """
        prompt = f"""你是 Fix Agent。以下代码的测试失败了，请修复。

## 失败分析
{json.dumps(analysis, ensure_ascii=False, indent=2)[:2000]}

## 当前代码
{code[:4000]}

## 要求
- 修复所有导致测试失败的问题
- 保持代码结构和命名不变
- 返回修复后的完整代码
"""
        return self.llm._call(
            system="你是 Fix Agent。根据测试失败日志，修复代码使得 pytest 全部通过。只返回修复后的代码。",
            user=prompt,
            temperature=0.1,
        )

    def suggest_improvements(self, history: list[dict]) -> list[str]:
        """
        根据修复历史给出改进建议
        返回: 建议列表
        """
        if not history:
            return ["初次生成即通过 — 无需改进"]

        suggestions = []
        if len(history) >= 3:
            suggestions.append("⚠️ 多次修复未通过，建议人工审查需求分解是否合理")
        if len(history) >= 5:
            suggestions.append("🔴 达到最大重试次数，建议拆分模块逐一实现")

        # 分析常见错误模式
        all_output = " ".join(h.get("output", "") for h in history)
        if "ImportError" in all_output:
            suggestions.append("📦 检查依赖声明 — 存在 ImportError")
        if "AssertionError" in all_output:
            suggestions.append("🧪 测试断言需要调整")

        return suggestions
