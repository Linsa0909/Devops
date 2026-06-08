"""
AgentDev OS — 核心状态机
任务 DAG + 17 状态 FSM 编排
基于 ai-factory 架构: PM → Architect → Developer → Tester → Reviewer → DevOps
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from models import (
    Pipeline, PipelineStatus, Stage, TaskNode, TaskStatus,
    Gate, GateStatus, Rule, RuleCategory, Artifact, ArtifactType,
)


# ============================================================
# 默认 16 条规则 (4 类 × 4 条)
# ============================================================
DEFAULT_RULES: list[Rule] = [
    # 安全 (Security)
    Rule(id="R-1", category=RuleCategory.SECURITY,   title="禁止明文传输和存储 Jira Token",              description="必须通过环境变量或 K8s Secret 挂载。", active=True),
    Rule(id="R-2", category=RuleCategory.SECURITY,   title="数据脱敏审查规则",                           description="禁止将含商业机密的日志发送给公有大模型。", active=True),
    Rule(id="R-3", category=RuleCategory.SECURITY,   title="容器镜像必须通过 Trivy 漏洞扫描",            description="禁止发布高危/严重漏洞的镜像。", active=True),
    Rule(id="R-4", category=RuleCategory.SECURITY,   title="API Token 必须设置过期时间 ≤ 7 天",          description="防止 Token 泄露后长期可用。", active=True),
    # 性能 (Performance)
    Rule(id="R-5", category=RuleCategory.PERFORMANCE,title="LLM 响应超时阻断与流式降级",                  description="单次交互超过 15s 必须转为异步流式推送。", active=True),
    Rule(id="R-6", category=RuleCategory.PERFORMANCE,title="高频接口必须加 Redis 分布式锁",               description="防止缓存击穿与雪崩。", active=False),
    Rule(id="R-7", category=RuleCategory.PERFORMANCE,title="数据库查询必须加 LIMIT 分页",                 description="禁止无限制的全表扫描。", active=True),
    Rule(id="R-8", category=RuleCategory.PERFORMANCE,title="静态资源必须启用 CDN 缓存策略",              description="减少源站压力。", active=True),
    # 规范 (Style)
    Rule(id="R-9", category=RuleCategory.STYLE,      title="严格遵循前后端分离设计标准",                 description="禁止在前端嵌入业务逻辑 SQL。", active=True),
    Rule(id="R-10",category=RuleCategory.STYLE,      title="代码覆盖率硬约束 ≥ 80%",                    description="生成代码的单元测试覆盖率必须超过 80%。", active=False),
    Rule(id="R-11",category=RuleCategory.STYLE,      title="API 必须遵循 OpenAPI 3.0 规范",              description="自动校验接口文档完整性。", active=True),
    Rule(id="R-12",category=RuleCategory.STYLE,      title="前端组件必须使用 TailwindCSS 样式",           description="严禁行内 style 样式。", active=True),
    # 自定义 (预留)
    Rule(id="R-13",category=RuleCategory.CUSTOM,     title="Scope 禁止越权访问",                         description="Agent 只允许访问已授权的文件系统和 API。", active=True),
    Rule(id="R-14",category=RuleCategory.CUSTOM,     title="日志必须脱敏输出",                           description="禁止打印密码/Token/密钥到控制台。", active=True),
    Rule(id="R-15",category=RuleCategory.CUSTOM,     title="每次 Agent 调用必须记录 Token 消耗",         description="用于成本审计与收敛检测。", active=True),
    Rule(id="R-16",category=RuleCategory.CUSTOM,     title="Agent 循环执行超过 5 次无进展自动终止",      description="Convergence 停止条件。", active=True),
]


class PipelineEngine:
    """流水线状态机引擎 — 驱动 Task DAG 的 17 状态流转"""

    @staticmethod
    def create_pipeline(name: str, description: str, language: str = "python") -> Pipeline:
        """创建新流水线，初始化任务 DAG"""
        now = datetime.now()
        pipeline_id = f"pipe_{uuid.uuid4().hex[:12]}"

        # 定义任务 DAG (17 节点拓扑)
        tasks = [
            # REQ 阶段 (PM 角色)
            TaskNode(id=f"{pipeline_id}_t01", name="IDEA 分析",           status=TaskStatus.IDEA_ANALYZING,      agent="pm", depends_on=[]),
            TaskNode(id=f"{pipeline_id}_t02", name="需求规格生成",         status=TaskStatus.PENDING,              agent="pm", depends_on=[f"{pipeline_id}_t01"]),
            TaskNode(id=f"{pipeline_id}_t03", name="Gate1: 需求审查",      status=TaskStatus.PENDING,              agent="pm", depends_on=[f"{pipeline_id}_t02"]),
            # DESIGN 阶段 (Architect 角色)
            TaskNode(id=f"{pipeline_id}_t04", name="架构设计生成",         status=TaskStatus.PENDING,              agent="architect", depends_on=[f"{pipeline_id}_t03"]),
            TaskNode(id=f"{pipeline_id}_t05", name="接口规范定义",         status=TaskStatus.PENDING,              agent="architect", depends_on=[f"{pipeline_id}_t04"]),
            TaskNode(id=f"{pipeline_id}_t06", name="设计审批",             status=TaskStatus.PENDING,              agent="architect", depends_on=[f"{pipeline_id}_t05"]),
            # DEV 阶段 (Developer 角色)
            TaskNode(id=f"{pipeline_id}_t07", name="后端代码生成",         status=TaskStatus.PENDING,              agent="developer", depends_on=[f"{pipeline_id}_t06"]),
            TaskNode(id=f"{pipeline_id}_t08", name="前端代码生成",         status=TaskStatus.PENDING,              agent="developer", depends_on=[f"{pipeline_id}_t07"]),
            TaskNode(id=f"{pipeline_id}_t09", name="Gate2: 代码审查",      status=TaskStatus.PENDING,              agent="developer", depends_on=[f"{pipeline_id}_t08"]),
            # TEST 阶段 (Tester 角色)
            TaskNode(id=f"{pipeline_id}_t10", name="单元测试执行",         status=TaskStatus.PENDING,              agent="tester", depends_on=[f"{pipeline_id}_t09"]),
            TaskNode(id=f"{pipeline_id}_t11", name="E2E 测试执行",         status=TaskStatus.PENDING,              agent="tester", depends_on=[f"{pipeline_id}_t10"]),
            TaskNode(id=f"{pipeline_id}_t12", name="规则合规审查",         status=TaskStatus.PENDING,              agent="tester", depends_on=[f"{pipeline_id}_t11"]),
            # VERIFY 阶段 (Tester 角色)
            TaskNode(id=f"{pipeline_id}_t13", name="VERIFY 验证",          status=TaskStatus.PENDING,              agent="tester", depends_on=[f"{pipeline_id}_t12"]),
            # REVIEW 阶段 (Reviewer 角色)
            TaskNode(id=f"{pipeline_id}_t14", name="Gate3: 发布审查",      status=TaskStatus.PENDING,              agent="reviewer", depends_on=[f"{pipeline_id}_t13"]),
            # DEPLOY 阶段 (DevOps 角色)
            TaskNode(id=f"{pipeline_id}_t15", name="Docker 镜像构建",      status=TaskStatus.PENDING,              agent="devops", depends_on=[f"{pipeline_id}_t14"]),
            TaskNode(id=f"{pipeline_id}_t16", name="K8s 部署发布",         status=TaskStatus.PENDING,              agent="devops", depends_on=[f"{pipeline_id}_t15"]),
            # 知识沉淀
            TaskNode(id=f"{pipeline_id}_t17", name="知识提取与归档",       status=TaskStatus.PENDING,              agent="devops", depends_on=[f"{pipeline_id}_t16"]),
        ]

        gates = [
            Gate(id="Gate1", name="需求→设计审查",     stage=Stage.ANALYSIS),
            Gate(id="Gate2", name="测试→部署审查",     stage=Stage.EXECUTION),
            Gate(id="Gate3", name="发布上线终审",       stage=Stage.RELEASE),
        ]

        pipeline = Pipeline(
            id=pipeline_id,
            name=name,
            description=description,
            status=PipelineStatus.RUNNING,
            current_stage=Stage.ANALYSIS,
            tasks=tasks,
            rules=list(DEFAULT_RULES),
            gates=gates,
            logs=[f"[Engine] 流水线 {pipeline_id} 创建成功 — 启动 REQ 阶段..."],
            progress=5,
            language=language,
            created_at=now,
            updated_at=now,
        )
        return pipeline

    @staticmethod
    def advance(pipeline: Pipeline, task_id: str, new_status: TaskStatus, output: Optional[str] = None, error: Optional[str] = None):
        """推进单个任务节点的状态"""
        for task in pipeline.tasks:
            if task.id == task_id:
                task.status = new_status
                if output:
                    task.output = output
                if error:
                    task.error = error
                if new_status in (TaskStatus.DEPLOYED, TaskStatus.KNOWLEDGE_EXTRACTED):
                    task.completed_at = datetime.now()
                elif new_status in (TaskStatus.IDEA_ANALYZING, TaskStatus.CODE_GENERATING, TaskStatus.TEST_RUNNING, TaskStatus.VERIFY_RUNNING):
                    task.started_at = datetime.now()
                break
        pipeline.updated_at = datetime.now()

    @staticmethod
    def _all_deps_done(pipeline: Pipeline, task: TaskNode) -> bool:
        """检查任务的所有上游依赖是否已完成"""
        for dep_id in task.depends_on:
            dep = next((t for t in pipeline.tasks if t.id == dep_id), None)
            if dep and dep.status not in (TaskStatus.DEPLOYED, TaskStatus.KNOWLEDGE_EXTRACTED,
                                          TaskStatus.DESIGN_APPROVED, TaskStatus.CODE_REVIEW,
                                          TaskStatus.TEST_PASSED, TaskStatus.VERIFY_PASSED,
                                          TaskStatus.TEST_FIXING):
                # 检查该节点是否处于已完成状态
                if dep.status.value.endswith("_DONE") or dep.status.value.endswith("_PASSED") or \
                   dep.status.value.endswith("_APPROVED") or dep.status == TaskStatus.KNOWLEDGE_EXTRACTED:
                    continue
                return False
        return True

    @staticmethod
    def _stage_from_task(task: TaskNode) -> Stage:
        """根据任务节点判断所属阶段"""
        agent_stage = {
            "pm": Stage.ANALYSIS,
            "architect": Stage.ANALYSIS,
            "developer": Stage.EXECUTION,
            "tester": Stage.QA,
            "reviewer": Stage.RELEASE,
            "devops": Stage.RELEASE,
        }
        return agent_stage.get(task.agent, Stage.ANALYSIS)

    @staticmethod
    def get_next_ready_tasks(pipeline: Pipeline) -> list[TaskNode]:
        """获取当前可执行的下一个任务（依赖已满足的）"""
        ready = []
        for task in pipeline.tasks:
            if task.status == TaskStatus.PENDING and PipelineEngine._all_deps_done(pipeline, task):
                ready.append(task)
        return ready

    @staticmethod
    def get_current_task(pipeline: Pipeline) -> Optional[TaskNode]:
        """获取当前正在执行的任务"""
        active_statuses = {
            TaskStatus.IDEA_ANALYZING, TaskStatus.REQUIREMENT_GEN,
            TaskStatus.CODE_GENERATING, TaskStatus.TEST_RUNNING,
            TaskStatus.VERIFY_RUNNING, TaskStatus.DEPLOYING,
            TaskStatus.DESIGN_GEN, TaskStatus.CODE_REVIEW,
            TaskStatus.TEST_FIXING, TaskStatus.KNOWLEDGE_EXTRACTED,
        }
        for task in pipeline.tasks:
            if task.status in active_statuses:
                return task
        return None

    @staticmethod
    def update_progress(pipeline: Pipeline):
        """根据已完成任务数计算进度百分比"""
        total = len(pipeline.tasks)
        done_count = sum(1 for t in pipeline.tasks if t.status in (
            TaskStatus.DEPLOYED, TaskStatus.KNOWLEDGE_EXTRACTED,
            TaskStatus.DESIGN_APPROVED, TaskStatus.CODE_REVIEW,
            TaskStatus.TEST_PASSED, TaskStatus.VERIFY_PASSED,
            TaskStatus.REQUIREMENT_REVIEW,
        ))
        pipeline.progress = min(100, int((done_count / total) * 100))

    @staticmethod
    def auto_advance(pipeline: Pipeline):
        """自动推进流水线 — 检查是否有待推进的任务"""
        next_tasks = PipelineEngine.get_next_ready_tasks(pipeline)
        for task in next_tasks:
            # 根据任务名称设置状态
            if "需求规格" in task.name:
                task.status = TaskStatus.REQUIREMENT_GEN
                task.started_at = datetime.now()
                pipeline.logs.append(f"[Engine] 自动推进: {task.name} → REQUIREMENT_GEN")
            elif "架构设计" in task.name or "接口规范" in task.name:
                task.status = TaskStatus.DESIGN_GEN
                task.started_at = datetime.now()
                pipeline.logs.append(f"[Engine] 自动推进: {task.name} → DESIGN_GEN")
            elif "后端代码" in task.name or "前端代码" in task.name:
                task.status = TaskStatus.CODE_GENERATING
                task.started_at = datetime.now()
                pipeline.logs.append(f"[Engine] 自动推进: {task.name} → CODE_GENERATING")
            elif "单元测试" in task.name or "E2E" in task.name:
                task.status = TaskStatus.TEST_RUNNING
                task.started_at = datetime.now()
                pipeline.logs.append(f"[Engine] 自动推进: {task.name} → TEST_RUNNING")
            elif "合规审查" in task.name:
                task.status = TaskStatus.VERIFY_RUNNING
                task.started_at = datetime.now()
                pipeline.logs.append(f"[Engine] 自动推进: {task.name} → VERIFY_RUNNING")
            elif "Docker" in task.name:
                task.status = TaskStatus.DEPLOYING
                task.started_at = datetime.now()
                pipeline.logs.append(f"[Engine] 自动推进: {task.name} → DEPLOYING")
            elif "知识提取" in task.name:
                task.status = TaskStatus.KNOWLEDGE_EXTRACTED
                task.completed_at = datetime.now()
                pipeline.logs.append(f"[Engine] 自动推进: {task.name} → KNOWLEDGE_EXTRACTED")
                pipeline.status = PipelineStatus.COMPLETED
            elif "Gate1" in task.name:
                task.status = TaskStatus.REQUIREMENT_REVIEW
                for g in pipeline.gates:
                    if g.id == "Gate1":
                        g.status = GateStatus.PENDING
                pipeline.status = PipelineStatus.GATE_WAIT
                pipeline.logs.append(f"[Engine] ⏸ 到达 Gate1 — 等待人工需求审查...")
            elif "Gate2" in task.name:
                task.status = TaskStatus.CODE_REVIEW
                for g in pipeline.gates:
                    if g.id == "Gate2":
                        g.status = GateStatus.PENDING
                pipeline.status = PipelineStatus.GATE_WAIT
                pipeline.logs.append(f"[Engine] ⏸ 到达 Gate2 — 等待人工代码审查...")
            elif "Gate3" in task.name:
                task.status = TaskStatus.REVIEW_PENDING
                for g in pipeline.gates:
                    if g.id == "Gate3":
                        g.status = GateStatus.PENDING
                pipeline.status = PipelineStatus.GATE_WAIT
                pipeline.logs.append(f"[Engine] ⏸ 到达 Gate3 — 等待发布终审...")
            elif "VERIFY" in task.name:
                task.status = TaskStatus.VERIFY_RUNNING
                task.started_at = datetime.now()
                pipeline.logs.append(f"[Engine] 自动推进: {task.name} → VERIFY_RUNNING")

            # 自动完成没有下游依赖的简单节点
            if task.status == TaskStatus.IDEA_ANALYZING:
                # 只有第一个节点是 IDEA_ANALYZING
                pass

        PipelineEngine.update_progress(pipeline)
        pipeline.updated_at = datetime.now()
