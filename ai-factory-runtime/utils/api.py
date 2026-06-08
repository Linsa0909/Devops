"""AI Factory — API 客户端"""
from __future__ import annotations
import httpx
from typing import Optional

DEFAULT_BACKEND_URL = "http://localhost:8000"


class APIClient:
    """与 AgentDev OS 后端通信的客户端"""

    def __init__(self, base_url: str = DEFAULT_BACKEND_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=60)

    def health(self) -> dict:
        """健康检查"""
        r = self.client.get(f"{self.base_url}/api/health")
        r.raise_for_status()
        return r.json()

    def start_pipeline(self, name: str, description: str) -> dict:
        """提交需求，启动流水线"""
        r = self.client.post(
            f"{self.base_url}/api/pipeline/start",
            json={"name": name, "description": description},
        )
        r.raise_for_status()
        return r.json()

    def get_status(self, task_id: str) -> dict:
        """获取流水线状态"""
        r = self.client.get(f"{self.base_url}/api/pipeline/status", params={"task_id": task_id})
        r.raise_for_status()
        return r.json()

    def gate_action(self, pipeline_id: str, gate_id: str, action: str, comment: str = "") -> dict:
        """审批闸门"""
        r = self.client.post(
            f"{self.base_url}/api/pipeline/gate",
            json={"pipeline_id": pipeline_id, "gate_id": gate_id, "action": action, "comment": comment},
        )
        r.raise_for_status()
        return r.json()

    def get_knowledge(self, pipeline_id: str) -> dict:
        """获取知识资产"""
        r = self.client.get(f"{self.base_url}/api/pipeline/knowledge/{pipeline_id}")
        r.raise_for_status()
        return r.json()

    def get_logs(self, pipeline_id: str) -> list:
        """获取日志"""
        r = self.client.get(f"{self.base_url}/api/pipeline/logs/{pipeline_id}")
        r.raise_for_status()
        return r.json().get("logs", [])

    def get_history(self, pipeline_id: str) -> list:
        """获取追溯"""
        r = self.client.get(f"{self.base_url}/api/pipeline/history/{pipeline_id}")
        r.raise_for_status()
        return r.json().get("trace", [])

    def list_products(self) -> list:
        """产物清单"""
        r = self.client.get(f"{self.base_url}/api/products/list")
        r.raise_for_status()
        return r.json().get("products", [])

    def toggle_rule(self, rule_id: str, active: bool) -> dict:
        r = self.client.post(
            f"{self.base_url}/api/pipeline/rules/toggle",
            json={"rule_id": rule_id, "active": active},
        )
        r.raise_for_status()
        return r.json()

    def add_rule(self, pipeline_id: str, title: str, category: str = "自定义", description: str = "") -> dict:
        r = self.client.post(
            f"{self.base_url}/api/pipeline/rules/add",
            json={"pipeline_id": pipeline_id, "title": title, "category": category, "description": description},
        )
        r.raise_for_status()
        return r.json()
