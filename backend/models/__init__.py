"""AgentDev OS — 核心数据模型"""
from __future__ import annotations
from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================
# 流水线阶段 (Pipeline Stage)
# ============================================================
class Stage(str, Enum):
    IDEA        = "IDEA"
    ANALYSIS    = "ANALYSIS"       # Gate1: 需求 → 设计
    GUARDRAILS  = "GUARDRAILS"
    EXECUTION   = "EXECUTION"      # Gate2: 代码审查
    QA          = "QA"
    VERIFY      = "VERIFY"         # Gate3: 发布审查
    RELEASE     = "RELEASE"


# ============================================================
# 任务状态 (17 状态 FSM)
# ============================================================
class TaskStatus(str, Enum):
    # REQ 阶段
    PENDING             = "PENDING"
    IDEA_SUBMITTED      = "IDEA_SUBMITTED"
    IDEA_ANALYZING      = "IDEA_ANALYZING"
    REQUIREMENT_GEN     = "REQUIREMENT_GEN"
    REQUIREMENT_REVIEW  = "REQUIREMENT_REVIEW"   # ← Gate1
    # DESIGN 阶段
    DESIGN_GEN          = "DESIGN_GEN"
    DESIGN_REVIEW       = "DESIGN_REVIEW"
    DESIGN_APPROVED     = "DESIGN_APPROVED"
    # DEV 阶段
    CODE_GENERATING     = "CODE_GENERATING"
    CODE_GENERATED      = "CODE_GENERATED"
    CODE_REVIEW         = "CODE_REVIEW"           # ← Gate2
    # TEST 阶段
    TEST_RUNNING        = "TEST_RUNNING"
    TEST_PASSED         = "TEST_PASSED"
    TEST_FAILED         = "TEST_FAILED"
    TEST_FIXING         = "TEST_FIXING"           # Self-healing
    # VERIFY 阶段
    VERIFY_RUNNING      = "VERIFY_RUNNING"
    VERIFY_PASSED       = "VERIFY_PASSED"
    VERIFY_FAILED       = "VERIFY_FAILED"
    # REVIEW 阶段
    REVIEW_PENDING      = "REVIEW_PENDING"        # ← Gate3
    # DEPLOY 阶段
    DEPLOYING           = "DEPLOYING"
    DEPLOYED            = "DEPLOYED"
    KNOWLEDGE_EXTRACTED = "KNOWLEDGE_EXTRACTED"


# ============================================================
# 任务节点 (DAG 节点)
# ============================================================
class TaskNode(BaseModel):
    id: str
    name: str
    status: TaskStatus
    agent: str                         # 负责 Agent: pm/architect/developer/tester/reviewer/devops
    depends_on: list[str] = []         # 上游依赖
    output: Optional[str] = None       # 产出物路径
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retries: int = 0
    error: Optional[str] = None


# ============================================================
# 规则定义 (Guardrails)
# ============================================================
class RuleCategory(str, Enum):
    SECURITY   = "安全"
    PERFORMANCE = "性能"
    STYLE      = "规范"
    CUSTOM     = "自定义"


class Rule(BaseModel):
    id: str
    category: RuleCategory
    title: str
    description: str
    active: bool = True
    passed: Optional[bool] = None      # 规则审查结果


# ============================================================
# 人工闸门 (Gate)
# ============================================================
class GateStatus(str, Enum):
    PENDING   = "PENDING"
    APPROVED  = "APPROVED"
    REJECTED  = "REJECTED"


class Gate(BaseModel):
    id: str                               # Gate1 / Gate2 / Gate3
    name: str
    stage: Stage
    status: GateStatus = GateStatus.PENDING
    approved_by: Optional[str] = None
    comment: Optional[str] = None
    decided_at: Optional[datetime] = None


# ============================================================
# 产物 (Artifact)
# ============================================================
class ArtifactType(str, Enum):
    PROMPT        = "prompt"
    REQUIREMENT   = "requirement"
    DESIGN        = "design"
    CODE          = "code"
    TEST_REPORT   = "test_report"
    REVIEW_REPORT = "review_report"
    KNOWLEDGE     = "knowledge"


class Artifact(BaseModel):
    id: str
    type: ArtifactType
    name: str
    path: str
    content: str = ""
    task_id: str
    created_at: datetime = Field(default_factory=datetime.now)


# ============================================================
# 流水线任务 (Pipeline Task)
# ============================================================
class PipelineStatus(str, Enum):
    IDLE        = "IDLE"
    RUNNING     = "RUNNING"
    GATE_WAIT   = "GATE_WAIT"       # 等待人工审批
    FAILED      = "FAILED"
    COMPLETED   = "COMPLETED"


class Pipeline(BaseModel):
    id: str
    name: str
    description: str
    status: PipelineStatus = PipelineStatus.IDLE
    current_stage: Stage = Stage.IDEA
    tasks: list[TaskNode] = []
    rules: list[Rule] = []
    gates: list[Gate] = []
    artifacts: list[Artifact] = []
    logs: list[str] = []
    progress: int = 0                # 0-100
    language: str = "python"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None


# ============================================================
# API 请求/响应
# ============================================================
class IdeaSubmitRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)

class GateActionRequest(BaseModel):
    pipeline_id: str
    gate_id: str
    action: str                         # approve / reject
    comment: Optional[str] = None

class RuleToggleRequest(BaseModel):
    rule_id: str
    active: bool

class AddRuleRequest(BaseModel):
    pipeline_id: str
    title: str
    category: str = "自定义"
    description: str = ""

class PipelineResponse(BaseModel):
    id: str
    name: str
    description: str
    status: PipelineStatus
    current_stage: Stage
    progress: int
    tasks: list[TaskNode]
    rules: list[Rule]
    gates: list[Gate]
    artifacts: list[Artifact]
    logs: list[str]
    error: Optional[str] = None

class ProductListResponse(BaseModel):
    products: list[dict]
