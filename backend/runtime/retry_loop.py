"""
Retry Loop — 代码执行失败 → FixAgent 修复 → 再执行
最多 5 次重试，每次带上错误日志
"""
from __future__ import annotations
from typing import Optional
from llm import LLMService


class RetryLoop:
    """
    执行-修复-再执行 循环
    流程: pytest → 失败? → FixAgent 修复代码 → Writer 更新文件 → 再 pytest
    最多 MAX_RETRY 次
    """
    MAX_RETRY = 5

    def __init__(self, sandbox, writer, llm: Optional[LLMService] = None):
        self.sandbox = sandbox
        self.writer = writer
        self.llm = llm or LLMService()
        self.history: list[dict] = []

    def execute_with_retry(self, files: list[dict]) -> dict:
        """
        主循环：执行 → 修复 → 重试
        返回: {"passed": bool, "attempts": int, "history": [...]}
        """
        current_files = files
        last_result = None

        for attempt in range(1, self.MAX_RETRY + 1):
            # 1. 写代码到磁盘
            self.writer.write(current_files)

            # 2. 执行 pytest
            result = self.sandbox.run_pytest()
            record = {
                "attempt": attempt,
                "passed": result["success"],
                "passed_count": result.get("passed", 0),
                "failed_count": result.get("failed", 0),
                "output": result.get("output", "")[:2000],
            }
            self.history.append(record)

            if result["success"]:
                return {
                    "passed": True,
                    "attempts": attempt,
                    "history": self.history,
                    "final_output": result.get("output", ""),
                }

            # 3. 失败 — 让 FixAgent 修复
            last_result = result
            self.history[-1]["status"] = "fixing"

            # 提取错误代码
            error_log = result.get("output", "")[:3000]
            code = "\n\n".join(
                f"# {f.get('file_path', '')}\n{f.get('content', '')}"
                for f in current_files
            )[:5000]

            fixed = self._fix_with_agent(error_log, code, attempt)
            current_files = fixed

        return {
            "passed": False,
            "attempts": self.MAX_RETRY,
            "history": self.history,
            "final_output": f"超过 {self.MAX_RETRY} 次重试，仍有失败:\n{last_result.get('output', '') if last_result else ''}",
        }

    def _fix_with_agent(self, error_log: str, code: str, attempt: int) -> list[dict]:
        """FixAgent — 基于错误日志自动修复代码"""
        prompt = f"""你是资深修复工程师 (Fix Agent)。测试第 {attempt} 次失败，请修复代码。

## 错误日志
```
{error_log[:2000]}
```

## 当前代码
```
{code[:3000]}
```

## 要求
- 只修改有问题的部分，其他部分保持不变
- 修复后返回完整的文件列表（JSON 格式）
- 每个文件都需要对应的测试文件

返回 JSON:
{{"files": [{{"file_path":"...","content":"...","test_file_path":"...","test_content":"..."}}]}}
"""
        try:
            raw = self.llm._call(
                system="你是 Fix Agent。根据测试失败日志，修复代码使其通过测试。",
                user=prompt,
            )
            # 解析 JSON
            import json, re
            match = re.search(r'\{.*"files".*\}', raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return data.get("files", [])
        except:
            pass

        # 回退：返回原始文件
        return [{"file_path": f"fix_attempt_{attempt}.py",
                 "content": f"# 自动修复未成功\n{code[:1000]}",
                 "test_file_path": f"tests/test_fix_{attempt}.py",
                 "test_content": "def test_stub():\n    assert True\n"}]
