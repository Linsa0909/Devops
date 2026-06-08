"""AI Factory — 配置加载器"""
from __future__ import annotations
import os
import yaml
from pathlib import Path
from typing import Optional

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


class AIConfig:
    """AI Factory 配置"""

    def __init__(self, config_path: Optional[Path] = None):
        path = config_path or DEFAULT_CONFIG_PATH
        self._raw = {}
        if path.exists():
            with open(path, encoding="utf-8") as f:
                self._raw = yaml.safe_load(f) or {}

    @property
    def deepseek_api_key(self) -> str:
        key = self._raw.get("deepseek", {}).get("api_key", "")
        return os.path.expandvars(key)

    @property
    def deepseek_base_url(self) -> str:
        return self._raw.get("deepseek", {}).get("base_url", "https://api.deepseek.com")

    @property
    def coverage_threshold(self) -> int:
        return self._raw.get("runtime", {}).get("coverage_threshold", 85)

    @property
    def coverage_min(self) -> int:
        return self._raw.get("quality", {}).get("coverage_min", 85)

    @property
    def ruff_policy(self) -> str:
        return self._raw.get("quality", {}).get("ruff", "must_pass")

    @property
    def mypy_policy(self) -> str:
        return self._raw.get("quality", {}).get("mypy", "must_pass")

    @property
    def gate_policy(self, gate_name: str = "") -> str:
        gates = self._raw.get("gates", {})
        mapping = {
            "Gate1": gates.get("require_to_design", "human_confirm"),
            "Gate2": gates.get("test_to_dev", "human_confirm"),
            "Gate3": gates.get("review_to_deploy", "always_required"),
        }
        return mapping.get(gate_name, "human_confirm")

    def to_dict(self) -> dict:
        return self._raw


# 全局默认配置
default_config = AIConfig()
