"""
AgentDev OS — 主入口
FastAPI 应用 + 所有 REST API 端点
"""
from __future__ import annotations
import os
import uuid
import json
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from core import PipelineEngine
from guardrails import GuardrailEngine
from gates import GateEngine
from llm import LLMService
from knowledge import KnowledgeEngine
from sandbox import SandboxEngine
from models import *

# ============================================================
# 全局状态 (内存存储 — 生产环境替换为 Redis/PostgreSQL)
# ============================================================
pipelines: dict[str, Pipeline] = {}
llm = LLMService()
engine = PipelineEngine()

# ============================================================
# 生命周期
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 AgentDev OS Backend 启动成功")
    print(f"   DeepSeek API: {'✅ 已配置' if os.getenv('DEEPSEEK_API_KEY') else '⚠️ 未配置 (Mock 模式)'}")
    # 确保数据目录
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/knowledge", exist_ok=True)
    os.makedirs("data/products", exist_ok=True)
    yield
    print("🛑 AgentDev OS Backend 关闭")


app = FastAPI(
    title="AgentDev OS — AI Factory Runtime",
    description="端到端软件需求 Agent 平台后端",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# API: 流水线管理
# ============================================================

@app.post("/api/pipeline/start", response_model=PipelineResponse)
async def start_pipeline(req: IdeaSubmitRequest):
    """启动新流水线 — 提交产品构想"""
    pipeline = PipelineEngine.create_pipeline(req.name, req.description)
    pipelines[pipeline.id] = pipeline

    # 异步触发 REQ 分析
    try:
        req_result = llm.analyze_requirement(req.name, req.description)
        req_md = req_result.get("requirement_md", f"# {req.name}\n\n{req.description}")
        pipeline.logs.append(f"[LLM] ✅ 需求分析完成 — 生成 {len(req_result.get('user_stories', []))} 条用户故事")

        # 保存需求产物
        artifact = Artifact(
            id=f"art_{uuid.uuid4().hex[:8]}",
            type=ArtifactType.REQUIREMENT,
            name="需求规格说明书",
            path=f"docs/requirement.md",
            content=req_md,
            task_id=pipeline.id,
        )
        KnowledgeEngine.save_artifact(pipeline, artifact)

        # 架构设计
        design_result = llm.design_architecture(req_md)
        design_md = design_result.get("design_md", "")
        pipeline.logs.append(f"[LLM] ✅ 架构设计完成 — {len(design_result.get('component_list', []))} 个组件")

        design_artifact = Artifact(
            id=f"art_{uuid.uuid4().hex[:8]}",
            type=ArtifactType.DESIGN,
            name="架构设计文档",
            path=f"docs/design.md",
            content=design_md,
            task_id=pipeline.id,
        )
        KnowledgeEngine.save_artifact(pipeline, design_artifact)

        # 保存架构图
        mermaid = design_result.get("architecture_diagram", "")
        mermaid_artifact = Artifact(
            id=f"art_{uuid.uuid4().hex[:8]}",
            type=ArtifactType.DESIGN,
            name="架构拓扑图",
            path=f"docs/architecture.mmd",
            content=mermaid,
            task_id=pipeline.id,
        )
        KnowledgeEngine.save_artifact(pipeline, mermaid_artifact)

        # 推进任务状态
        engine.advance(pipeline, f"{pipeline.id}_t01", TaskStatus.IDEA_ANALYZING, output=req_md)
        engine.advance(pipeline, f"{pipeline.id}_t02", TaskStatus.REQUIREMENT_GEN, output=req_md)
        engine.advance(pipeline, f"{pipeline.id}_t04", TaskStatus.DESIGN_GEN, output=design_md)
        engine.advance(pipeline, f"{pipeline.id}_t05", TaskStatus.DESIGN_GEN, output=design_md)

        # 到达 Gate1
        engine.advance(pipeline, f"{pipeline.id}_t03", TaskStatus.REQUIREMENT_REVIEW)
        for g in pipeline.gates:
            if g.id == "Gate1":
                g.status = GateStatus.PENDING
        pipeline.status = PipelineStatus.GATE_WAIT
        pipeline.logs.append(f"[Engine] ⏸ 到达 Gate1 — 等待人工审批需求审查...")

    except Exception as e:
        pipeline.logs.append(f"[ERROR] 分析阶段出错: {str(e)}")
        pipeline.error = str(e)

    engine.update_progress(pipeline)
    pipeline.updated_at = datetime.now()
    return _to_response(pipeline)


@app.get("/api/pipeline/status", response_model=PipelineResponse)
async def get_pipeline_status(task_id: str):
    """获取流水线状态 (长轮询接口)"""
    pipeline = pipelines.get(task_id)
    if not pipeline:
        raise HTTPException(404, f"任务 {task_id} 不存在")
    return _to_response(pipeline)


@app.post("/api/pipeline/gate")
async def gate_action(req: GateActionRequest):
    """处理闸门审批"""
    pipeline = pipelines.get(req.pipeline_id)
    if not pipeline:
        raise HTTPException(404, f"任务 {req.pipeline_id} 不存在")

    if req.action == "approve":
        success = GateEngine.approve(pipeline, req.gate_id, comment=req.comment or "")
    elif req.action == "reject":
        success = GateEngine.reject(pipeline, req.gate_id, reason=req.comment or "驳回")
    else:
        raise HTTPException(400, "action 必须是 approve 或 reject")

    if not success:
        raise HTTPException(400, f"闸门 {req.gate_id} 不在待审批状态")

    # 放行后自动推进
    engine.auto_advance(pipeline)
    engine.update_progress(pipeline)

    return _to_response(pipeline)


@app.post("/api/pipeline/restart")
async def restart_pipeline(task_id: str):
    """重新启动流水线 (重新生成)"""
    pipeline = pipelines.get(task_id)
    if not pipeline:
        raise HTTPException(404, f"任务 {task_id} 不存在")

    # 重置任务状态 (保留已有产物)
    for task in pipeline.tasks:
        if task.status not in (TaskStatus.DEPLOYED, TaskStatus.KNOWLEDGE_EXTRACTED):
            task.status = TaskStatus.PENDING
            task.started_at = None
            task.completed_at = None
            task.error = None

    pipeline.status = PipelineStatus.RUNNING
    pipeline.current_stage = Stage.ANALYSIS
    pipeline.error = None
    pipeline.logs.append(f"[Engine] 🔄 流水线重新启动...")

    # 重置 Gates
    for g in pipeline.gates:
        g.status = GateStatus.PENDING
        g.decided_at = None

    engine.auto_advance(pipeline)
    pipeline.updated_at = datetime.now()
    return _to_response(pipeline)

# ============================================================
# API: 规则管理
# ============================================================

@app.post("/api/pipeline/rules/toggle")
async def toggle_rule(req: RuleToggleRequest):
    """开关规则"""
    for pid, pipeline in pipelines.items():
        GuardrailEngine.toggle_rule(pipeline, req.rule_id, req.active)
        return {"status": "ok", "rule_id": req.rule_id, "active": req.active}
    raise HTTPException(404, "没有流水线")


@app.post("/api/pipeline/rules/add")
async def add_rule(req: AddRuleRequest):
    """添加自定义规则"""
    pipeline = pipelines.get(req.pipeline_id)
    if not pipeline:
        raise HTTPException(404, f"任务 {req.pipeline_id} 不存在")
    rule = GuardrailEngine.add_custom_rule(pipeline, req.title, req.category, req.description)
    return {"status": "ok", "rule": rule.model_dump()}


@app.get("/api/pipeline/rules/{pipeline_id}")
async def get_rules(pipeline_id: str):
    """获取流水线规则列表"""
    pipeline = pipelines.get(pipeline_id)
    if not pipeline:
        raise HTTPException(404, f"任务 {pipeline_id} 不存在")
    return {"rules": [r.model_dump() for r in pipeline.rules]}

# ============================================================
# API: 产物与知识
# ============================================================

@app.get("/api/products/list")
async def list_products():
    """列出所有已部署产物"""
    products = []
    for pid, pipeline in pipelines.items():
        if pipeline.status == PipelineStatus.COMPLETED:
            products.append({
                "id": pid,
                "name": pipeline.name,
                "version": f"v1.0.0-build.{pid[-4:]}",
                "status": "deployed",
                "artifacts": len(pipeline.artifacts),
                "created_at": str(pipeline.created_at),
            })
    return {"products": products}


@app.get("/api/products/file/{path:path}")
async def get_product_file(path: str):
    """获取产物文件内容"""
    filepath = os.path.join("data", path)
    if not os.path.exists(filepath):
        raise HTTPException(404, f"文件 {path} 不存在")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return {"path": path, "content": content}


@app.post("/api/pipeline/save_artifact")
async def save_artifact(req: dict):
    pipeline_id = req.get("pipeline_id", "")
    name = req.get("name", "")
    content = req.get("content", "")
    art_type = req.get("type", "code")
    """保存产物"""
    pipeline = pipelines.get(pipeline_id)
    if not pipeline:
        raise HTTPException(404, f"任务 {pipeline_id} 不存在")

    artifact = Artifact(
        id=f"art_{uuid.uuid4().hex[:8]}",
        type=ArtifactType(art_type),
        name=name,
        path=f"artifacts/{name}",
        content=content,
        task_id=pipeline_id,
    )
    filepath = KnowledgeEngine.save_artifact(pipeline, artifact)
    return {"status": "ok", "path": filepath}


@app.get("/api/pipeline/knowledge/{pipeline_id}")
async def get_knowledge(pipeline_id: str):
    """获取知识资产"""
    pipeline = pipelines.get(pipeline_id)
    if not pipeline:
        raise HTTPException(404, f"任务 {pipeline_id} 不存在")
    return KnowledgeEngine.get_knowledge_assets(pipeline)


@app.get("/api/pipeline/history/{pipeline_id}")
async def get_history(pipeline_id: str):
    """获取全链路追溯"""
    pipeline = pipelines.get(pipeline_id)
    if not pipeline:
        raise HTTPException(404, f"任务 {pipeline_id} 不存在")
    return {"trace": KnowledgeEngine.get_history(pipeline)}


@app.get("/api/pipeline/logs/{pipeline_id}")
async def get_logs(pipeline_id: str):
    """获取日志"""
    pipeline = pipelines.get(pipeline_id)
    if not pipeline:
        raise HTTPException(404, f"任务 {pipeline_id} 不存在")
    return {"logs": pipeline.logs[-100:]}


@app.get("/api/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "pipelines": len(pipelines),
        "deepseek_configured": bool(os.getenv("DEEPSEEK_API_KEY")),
    }

# ============================================================
# 辅助
# ============================================================
def _to_response(p: Pipeline) -> dict:
    d = p.model_dump()
    d["logs"] = p.logs[-50:]
    return d


# ============================================================
# 前端页面服务 (兜底路由 — 必须在所有 API 路由之后)
# ============================================================
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..")
INDEX_HTML = os.path.join(FRONTEND_DIR, "index.html")


@app.get("/")
async def serve_frontend():
    """服务前端 index.html"""
    if os.path.exists(INDEX_HTML):
        return FileResponse(INDEX_HTML, media_type="text/html")
    return HTMLResponse("<h1>AgentDev OS Backend</h1><p>前端文件未找到</p>")


@app.get("/index.html")
async def serve_index():
    if os.path.exists(INDEX_HTML):
        return FileResponse(INDEX_HTML, media_type="text/html")
    return HTMLResponse("<h1>AgentDev OS Backend</h1>")
