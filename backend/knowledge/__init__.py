"""
AgentDev OS — 知识沉淀引擎
Artifacts + Snapshots + Trace + History + Telemetry
"""
import json
import os
from datetime import datetime
from typing import Optional
from models import Pipeline, Artifact, ArtifactType


KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge")


class KnowledgeEngine:
    """知识沉淀引擎 — 保存全链路资产"""

    @staticmethod
    def ensure_dirs(pipeline_id: str):
        """确保知识目录存在"""
        base = os.path.join(KNOWLEDGE_DIR, pipeline_id)
        for sub in ["prompts", "codes", "reports", "snapshots", "traces"]:
            os.makedirs(os.path.join(base, sub), exist_ok=True)
        return base

    @staticmethod
    def save_artifact(pipeline: Pipeline, artifact: Artifact) -> str:
        """保存产物到磁盘"""
        base = KnowledgeEngine.ensure_dirs(pipeline.id)
        filepath = os.path.join(base, artifact.path.lstrip("/"))
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(artifact.content)
        pipeline.artifacts.append(artifact)
        pipeline.logs.append(f"[Knowledge] 保存产物: {artifact.name} → {filepath}")
        return filepath

    @staticmethod
    def save_snapshot(pipeline: Pipeline) -> str:
        """保存流水线快照 (完整状态)"""
        base = KnowledgeEngine.ensure_dirs(pipeline.id)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(base, "snapshots", f"snapshot_{timestamp}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(pipeline.model_dump(), f, ensure_ascii=False, indent=2, default=str)
        pipeline.logs.append(f"[Knowledge] 快照保存: {filepath}")
        return filepath

    @staticmethod
    def get_prompts(pipeline: Pipeline) -> list[Artifact]:
        """获取所有提示词产物"""
        return [a for a in pipeline.artifacts if a.type == ArtifactType.PROMPT]

    @staticmethod
    def get_knowledge_assets(pipeline: Pipeline) -> dict:
        """获取知识资产汇总"""
        return {
            "prompts": [a.model_dump() for a in pipeline.artifacts if a.type == ArtifactType.PROMPT],
            "requirements": [a.model_dump() for a in pipeline.artifacts if a.type == ArtifactType.REQUIREMENT],
            "designs": [a.model_dump() for a in pipeline.artifacts if a.type == ArtifactType.DESIGN],
            "codes": [a.model_dump() for a in pipeline.artifacts if a.type == ArtifactType.CODE],
            "test_reports": [a.model_dump() for a in pipeline.artifacts if a.type == ArtifactType.TEST_REPORT],
            "review_reports": [a.model_dump() for a in pipeline.artifacts if a.type == ArtifactType.REVIEW_REPORT],
            "trace": pipeline.logs[-50:],
            "metrics": {
                "total_tasks": len(pipeline.tasks),
                "completed_tasks": sum(1 for t in pipeline.tasks if t.completed_at),
                "total_artifacts": len(pipeline.artifacts),
                "gates_passed": sum(1 for g in pipeline.gates if g.status.value == "APPROVED"),
                "duration_seconds": (datetime.now() - pipeline.created_at).total_seconds() if pipeline.created_at else 0,
            },
        }

    @staticmethod
    def get_history(pipeline: Pipeline) -> list[dict]:
        """获取全链路追溯信息"""
        return [
            {"type": "task", "id": t.id, "name": t.name, "agent": t.agent,
             "status": t.status.value, "started": str(t.started_at or ""),
             "completed": str(t.completed_at or ""), "error": t.error}
            for t in pipeline.tasks
        ]
