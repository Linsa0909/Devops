"""
AgentDev OS — 人工闸门系统 (Gates)
Gate1: 需求→设计   (PM 审查)
Gate2: 测试→部署   (Tester 审查)
Gate3: 发布终审     (Reviewer 审查, 不可跳过)
HUMAN_REQUIRED 升级机制
"""
from datetime import datetime
from typing import Optional
from models import Pipeline, Gate, GateStatus, PipelineStatus, TaskStatus


class GateEngine:
    """闸门引擎 — 管理 3 道人工审批关口"""

    @staticmethod
    def get_pending_gate(pipeline: Pipeline) -> Optional[Gate]:
        """获取当前待审批的闸门"""
        for gate in pipeline.gates:
            if gate.status == GateStatus.PENDING:
                return gate
        return None

    @staticmethod
    def approve(pipeline: Pipeline, gate_id: str, approved_by: str = "admin", comment: str = "") -> bool:
        """批准闸门放行"""
        gate = next((g for g in pipeline.gates if g.id == gate_id), None)
        if not gate or gate.status != GateStatus.PENDING:
            return False

        gate.status = GateStatus.APPROVED
        gate.approved_by = approved_by
        gate.comment = comment
        gate.decided_at = datetime.now()
        pipeline.status = PipelineStatus.RUNNING

        pipeline.logs.append(f"[Gate] ✅ {gate_id} 已批准 (by {approved_by}) — {comment or '无备注'}")

        # 推进对应任务
        if gate_id == "Gate1":
            # 完成 Gate1 任务节点，解锁 DESIGN 阶段
            for task in pipeline.tasks:
                if task.status == TaskStatus.REQUIREMENT_REVIEW:
                    task.status = TaskStatus.DESIGN_APPROVED
                    task.completed_at = datetime.now()
                    break
            pipeline.current_stage = "ANALYSIS"

        elif gate_id == "Gate2":
            for task in pipeline.tasks:
                if task.status == TaskStatus.CODE_REVIEW:
                    task.status = TaskStatus.TEST_PASSED
                    task.completed_at = datetime.now()
                    break
            pipeline.current_stage = "QA"

        elif gate_id == "Gate3":
            for task in pipeline.tasks:
                if task.status == TaskStatus.REVIEW_PENDING:
                    task.status = TaskStatus.DEPLOYING
                    task.started_at = datetime.now()
                    break
            pipeline.current_stage = "RELEASE"

        pipeline.updated_at = datetime.now()
        return True

    @staticmethod
    def reject(pipeline: Pipeline, gate_id: str, rejected_by: str = "admin", reason: str = "") -> bool:
        """驳回闸门，触发 HUMAN_REQUIRED 升级"""
        gate = next((g for g in pipeline.gates if g.id == gate_id), None)
        if not gate or gate.status != GateStatus.PENDING:
            return False

        gate.status = GateStatus.REJECTED
        gate.approved_by = rejected_by
        gate.comment = reason
        gate.decided_at = datetime.now()

        pipeline.logs.append(f"[Gate] ❌ {gate_id} 已驳回 (by {rejected_by}) — {reason}")

        # HUMAN_REQUIRED 升级：回退到上一个阶段
        if gate_id == "Gate1":
            for task in pipeline.tasks:
                if task.status == TaskStatus.REQUIREMENT_REVIEW:
                    task.status = TaskStatus.REQUIREMENT_GEN  # 重新生成
                    break
        elif gate_id == "Gate2":
            for task in pipeline.tasks:
                if task.status == TaskStatus.CODE_REVIEW:
                    task.status = TaskStatus.CODE_GENERATING  # 重新生成代码
                    break
        elif gate_id == "Gate3":
            for task in pipeline.tasks:
                if task.status == TaskStatus.REVIEW_PENDING:
                    task.status = TaskStatus.VERIFY_RUNNING  # 重新验证
                    break

        pipeline.status = PipelineStatus.RUNNING
        pipeline.updated_at = datetime.now()
        return True

    @staticmethod
    def can_skip_gate(gate_id: str) -> bool:
        """检查闸门是否可跳过 (Gate3 不可跳过)"""
        skip_policy = {
            "Gate1": True,   # 可跳过 (在配置中可设置)
            "Gate2": True,   # 可跳过
            "Gate3": False,  # 强制不可跳过
        }
        return skip_policy.get(gate_id, True)
