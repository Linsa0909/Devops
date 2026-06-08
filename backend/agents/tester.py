"""
Tester Agent — 分析 pytest 真实执行结果 (不凭空判断)
输入: Sandbox 执行结果 (pytest output)
输出: 结构化测试分析
"""
from __future__ import annotations
import json
from typing import Optional
from llm import LLMService


class TesterAgent:
    """
    测试 Agent：
    - 不再猜测代码是否有问题
    - 真正判断的是 pytest 的返回码
    - Agent 负责分析失败原因并给出修复建议
    """

    def __init__(self, llm: Optional[LLMService] = None):
        self.llm = llm or LLMService()

    def evaluate(self, exec_result: dict) -> dict:
        """
        基于真实执行结果进行评估
        exec_result: {success, passed, failed, output}
        返回: {pass, reason, fix_suggestion, metrics}
        """
        passed = exec_result.get("success", False)
        output = exec_result.get("output", "")
        passed_count = exec_result.get("passed", 0)
        failed_count = exec_result.get("failed", 0)

        # 如果全部通过，直接返回 (不消耗 LLM Token)
        if passed and failed_count == 0:
            return {
                "pass": True,
                "reason": f"所有 {passed_count} 个测试通过",
                "fix_suggestion": None,
                "metrics": {
                    "tests_passed": passed_count,
                    "tests_failed": 0,
                    "coverage": "N/A",
                },
            }

        # 分析失败原因
        analysis = self._analyze(output, passed_count, failed_count)

        return {
            "pass": False,
            "reason": analysis.get("reason", f"{failed_count} 个测试失败"),
            "fix_suggestion": analysis.get("suggestion", "需要人工审查"),
            "failure_analysis": analysis,
            "metrics": {
                "tests_passed": passed_count,
                "tests_failed": failed_count,
                "coverage": self._extract_coverage(output),
            },
        }

    def _analyze(self, output: str, passed: int, failed: int) -> dict:
        """LLM 分析 pytest 失败输出"""
        prompt = f"""分析以下 pytest 输出，给出失败原因和修复建议。

## 测试结果
- 通过: {passed}
- 失败: {failed}

## 输出
```
{output[:3000]}
```

返回 JSON:
{{
  "reason": "失败原因概括 (一句话)",
  "suggestion": "具体修复建议",
  "category": "ImportError|AssertionError|Timeout|LogicError|Other"
}}
"""
        raw = self.llm._call(
            system="你是测试分析工程师。分析 pytest 失败输出，给出精确的失败原因和修复建议。",
            user=prompt,
            temperature=0.1,
        )
        try:
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0]
            return json.loads(raw.strip())
        except:
            return {
                "reason": f"{failed} 个测试失败",
                "suggestion": "检查测试日志中的 FAILED/ERROR 行",
                "category": "Other",
            }

    def _extract_coverage(self, output: str) -> str:
        """从 pytest --cov 输出中提取覆盖率"""
        for line in output.split("\n"):
            if "TOTAL" in line and "%" in line:
                return line.strip()
        return "无覆盖率数据"
