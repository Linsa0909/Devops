"""
Code Execution Loop — 项目上下文收集器
项目树 + API 契约 + 数据库 Schema + 编码规范 → 提升代码生成质量
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional


class ProjectContext:
    """收集项目上下文，注入到 Developer Agent 的 Prompt 中"""

    def __init__(self, workspace_root: str):
        self.root = Path(workspace_root)

    def gather(self, requirement: str, design: str, rules: list[dict]) -> dict:
        """收集所有上下文"""
        return {
            "project_tree":      self._tree(),
            "api_contract":       self._api_contract(design),
            "database_schema":    self._db_schema(design),
            "coding_style":       self._style_guide(rules),
            "requirement":        requirement,
            "design":             design,
        }

    def build_prompt(self, ctx: dict) -> str:
        """构造注入上下文的 Prompt"""
        return f"""你是资深开发工程师。请根据以下完整项目上下文生成可运行的代码。

## 📁 项目结构
{ctx['project_tree']}

## 🔌 API 契约
{ctx['api_contract']}

## 🗄️ 数据库模式
{ctx['database_schema']}

## 🎨 编码规范
{ctx['coding_style']}

## 📋 需求
{ctx['requirement']}

## 🏗️ 架构设计
{ctx['design']}

## 输出要求
返回 JSON 对象:
{{
  "files": [
    {{
      "file_path": "app/main.py",
      "content": "# 完整代码...",
      "test_file_path": "tests/test_main.py",
      "test_content": "# 单元测试..."
    }}
  ]
}}
每个文件都必须包含对应的测试文件。
"""

    # ─── 私有 ───

    def _tree(self) -> str:
        """生成项目目录树"""
        lines = [f"📁 {self.root.name}/"]
        for dirpath, dirnames, filenames in os.walk(self.root):
            depth = len(Path(dirpath).relative_to(self.root).parts)
            prefix = "│  " * max(depth - 1, 0) + ("├── " if depth > 0 else "")
            for d in sorted(dirnames):
                if d.startswith(".") or d in ("__pycache__", "node_modules", ".venv"):
                    continue
                lines.append(f"{prefix}📁 {d}/")
            for f in sorted(filenames):
                if f.startswith(".") or f.endswith(".pyc"):
                    continue
                lines.append(f"{prefix}📄 {f}")
        return "\n".join(lines[:200])  # 截断

    def _api_contract(self, design: str) -> str:
        """从设计文档提取 API 契约"""
        # 简单提取 — 生产环境可用 LLM 结构化
        lines = []
        for line in design.split("\n"):
            if any(kw in line.upper() for kw in ("POST", "GET", "PUT", "DELETE", "PATH", "ENDPOINT", "API")):
                lines.append(line.strip())
        return "\n".join(lines) if lines else "标准 RESTful API 契约 (从设计文档提取)"

    def _db_schema(self, design: str) -> str:
        """从设计文档提取数据库模式"""
        lines = []
        for line in design.split("\n"):
            if any(kw in line for kw in ("数据库", "表", "字段", "索引", "Schema", "Model", "Column")):
                lines.append(line.strip())
        return "\n".join(lines) if lines else "标准关系模型 (PostgreSQL/SQLite)"

    def _style_guide(self, rules: list[dict]) -> str:
        """从规则引擎提取编码规范"""
        lines = []
        for r in rules:
            if r.get("active"):
                lines.append(f"- [{r.get('id', '?')}] {r.get('title', '?')}: {r.get('description', '')}")
        return "\n".join(lines) if lines else "- 遵循 PEP 8\n- 类型注解\n- 文档字符串"
