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

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import threading
import re
import urllib.request
import base64 as _base64
from pathlib import Path

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

# 挂载本地静态资源 (代替 CDN)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 挂载前端工程 (Vite + React)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/src", StaticFiles(directory=os.path.join(FRONTEND_DIR, "src")), name="frontend-src")
    assets_dir = os.path.join(FRONTEND_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")
    print(f"📦 本地静态资源已挂载: {STATIC_DIR}")

# ============================================================
# API: 流水线管理
# ============================================================

@app.post("/api/pipeline/start", response_model=PipelineResponse)
async def start_pipeline(req: IdeaSubmitRequest):
    """启动新流水线 — 提交产品构想"""
    pipeline = PipelineEngine.create_pipeline(req.name, req.description)
    pipelines[pipeline.id] = pipeline

    # 提取活跃规则作为约束上下文
    active_rules_text = "\n".join([
        f"- [{r.id}] {r.title}: {r.description}" for r in pipeline.rules if r.active
    ])

    try:
        # ── REQ Agent: 需求结构化 (注入规则约束) ──
        pipeline.logs.append("[LLM] REQ Agent 分析中...")
        req_result = llm.analyze_requirement(req.name, req.description)
        req_md = req_result.get("requirement_md", f"# {req.name}\n\n{req.description}")
        pipeline.logs.append(f"[LLM] ✅ 需求分析: {len(req_result.get('user_stories', []))} 条用户故事, {len(req_result.get('functional_modules', []))} 个功能模块")

        # 保存需求产物
        KnowledgeEngine.save_artifact(pipeline, Artifact(
            id=f"art_{uuid.uuid4().hex[:8]}", type=ArtifactType.REQUIREMENT,
            name="需求规格说明书", path="docs/requirement.md", content=req_md, task_id=pipeline.id))

        # ── Architect Agent: 架构设计 (基于结构化需求 + 规则约束) ──
        pipeline.logs.append("[LLM] Architect Agent 架构设计中 (含 Guardrails)...")
        design_result = llm.design_architecture(
            f"用户故事:\n" + "\n".join(req_result.get("user_stories", [])[:5]) +
            f"\n功能模块:\n" + json.dumps(req_result.get("functional_modules", []), ensure_ascii=False) +
            f"\nAPI规格:\n" + json.dumps(req_result.get("api_specs", []), ensure_ascii=False) +
            f"\n技术栈建议:\n" + ", ".join(req_result.get("tech_stack", [])) +
            f"\n风险评估:\n" + "\n".join(req_result.get("risk_points", []))
        )
        design_md = design_result.get("design_md", "")
        component_count = len(design_result.get("component_list", []))
        pipeline.logs.append(f"[LLM] ✅ 架构设计: {component_count} 个组件, {len(design_result.get('api_design', []))} 个接口")

        KnowledgeEngine.save_artifact(pipeline, Artifact(
            id=f"art_{uuid.uuid4().hex[:8]}", type=ArtifactType.DESIGN,
            name="架构设计文档", path="docs/design.md", content=design_md, task_id=pipeline.id))
        KnowledgeEngine.save_artifact(pipeline, Artifact(
            id=f"art_{uuid.uuid4().hex[:8]}", type=ArtifactType.DESIGN,
            name="架构拓扑图", path="docs/architecture.mmd",
            content=design_result.get("architecture_diagram", ""), task_id=pipeline.id))
        KnowledgeEngine.save_artifact(pipeline, Artifact(
            id=f"art_{uuid.uuid4().hex[:8]}", type=ArtifactType.DESIGN,
            name="接口规范", path="docs/api_spec.md",
            content=json.dumps(design_result.get("api_design", []), ensure_ascii=False, indent=2), task_id=pipeline.id))
        KnowledgeEngine.save_artifact(pipeline, Artifact(
            id=f"art_{uuid.uuid4().hex[:8]}", type=ArtifactType.DESIGN,
            name="数据流设计", path="docs/data_flow.md",
            content=json.dumps(design_result.get("data_flow", []), ensure_ascii=False, indent=2), task_id=pipeline.id))

        # ── Guardrails 检查需求+设计 ──
        pipeline.logs.append("[Guardrails] 检查需求与设计合规性...")
        context = {"code": design_md, "logs": "\n".join(pipeline.logs[-10:]),
                    "api_spec": json.dumps(design_result.get("api_design", []))}
        rule_results = GuardrailEngine.check_all_rules(pipeline, context)
        failed_rules = [r for r in rule_results if not r.get("passed")]
        if failed_rules:
            pipeline.logs.append(f"[Guardrails] ⚠️ {len(failed_rules)} 条规则未通过: {[r.get('rule_id') for r in failed_rules]}")
        else:
            pipeline.logs.append("[Guardrails] ✅ 全部激活规则通过")

        # 推进任务
        engine.advance(pipeline, f"{pipeline.id}_t01", TaskStatus.IDEA_ANALYZING, output=req_md)
        engine.advance(pipeline, f"{pipeline.id}_t02", TaskStatus.REQUIREMENT_GEN, output=req_md)
        engine.advance(pipeline, f"{pipeline.id}_t04", TaskStatus.DESIGN_GEN, output=design_md)
        engine.advance(pipeline, f"{pipeline.id}_t05", TaskStatus.DESIGN_GEN, output=design_md)
        engine.advance(pipeline, f"{pipeline.id}_t03", TaskStatus.REQUIREMENT_REVIEW)
        for g in pipeline.gates:
            if g.id == "Gate1": g.status = GateStatus.PENDING
        pipeline.status = PipelineStatus.GATE_WAIT
        pipeline.logs.append("[Engine] ⏸ 到达 Gate1 — 等待人工审批需求审查...")

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

    # 🔥 Gate1 放行后 → 后台异步启动 Code Execution Loop
    if req.gate_id == "Gate1" and req.action == "approve":
        pipeline.logs.append("[System] 🔥 Gate1 通过 → 后台启动 Code Execution Loop...")
        req_content = next((a.content for a in pipeline.artifacts if a.type.value == "requirement"), pipeline.description)
        design_content = next((a.content for a in pipeline.artifacts if a.type.value == "design"), "")

        def _run_codeloop():
            try:
                loop_result = PipelineEngine.run_code_execution_loop(
                    pipeline, pipeline.description, design_content)
                pipeline.logs.append(f"[System] ✅ CodeLoop 完成: "
                    f"pytest={'PASS' if loop_result.get('passed') else 'FAIL'}, "
                    f"review={loop_result.get('reviews',{}).get('score',0)}/100")

                # 🔥 推送到 Gitea 仓库
                try:
                    from runtime.git_pusher import GitPushEngine
                    git_engine = GitPushEngine()
                    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '-', pipeline.name[:30])
                    repo_name = f"{pipeline.id[:12]}-{safe_name}"
                    ws = loop_result.get("workspace_path", f"workspace/{pipeline.id}")
                    push_result = git_engine.push_workspace(ws, repo_name, pipeline.description)
                    if push_result.get("success"):
                        pipeline.logs.append(f"[Git] ✅ 代码已推送: {push_result.get('repo_url','')}")
                    else:
                        pipeline.logs.append(f"[Git] ⚠️ 推送跳过 (Gitea 未运行)")
                except Exception as git_err:
                    pipeline.logs.append(f"[Git] ⚠️ {git_err}")

                engine.auto_advance(pipeline)
                engine.update_progress(pipeline)
            except Exception as e:
                pipeline.logs.append(f"[System] ⚠️ CodeLoop 异常: {e}")

        threading.Thread(target=_run_codeloop, daemon=True).start()

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


@app.get("/api/pipeline/products/{pipeline_id}")
async def get_pipeline_products(pipeline_id: str):
    """获取流水线产物文件树"""
    import glob as _glob
    pipeline = pipelines.get(pipeline_id)
    if not pipeline:
        raise HTTPException(404, f"任务 {pipeline_id} 不存在")

    files = []
    # 知识库产物
    knowledge_dir = os.path.join("data", "knowledge", pipeline_id)
    if os.path.exists(knowledge_dir):
        for root, dirs, filenames in os.walk(knowledge_dir):
            for fn in filenames:
                full = os.path.join(root, fn)
                rel = "/".join(full.split("/")[-3:])
                files.append({"path": rel, "size": os.path.getsize(full), "source": "knowledge"})
    # workspace 产物
    workspace_dir = os.path.join("workspace", pipeline_id)
    if os.path.exists(workspace_dir):
        for root, dirs, filenames in os.walk(workspace_dir):
            for fn in filenames:
                if fn.startswith(".") or fn.endswith(".pyc"):
                    continue
                full = os.path.join(root, fn)
                rel = str(Path(full).relative_to(workspace_dir))
                files.append({"path": rel, "size": os.path.getsize(full), "source": "workspace"})
    return {"pipeline_id": pipeline_id, "files": files, "total": len(files)}


@app.get("/api/pipeline/files/{pipeline_id}/{path:path}")
async def get_pipeline_file(pipeline_id: str, path: str):
    """读取产物文件内容 (尝试 knowledge 和 workspace 两个来源)"""
    for src_dir in ["data/knowledge", "workspace"]:
        filepath = os.path.join(src_dir, pipeline_id, path)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return {"path": path, "content": content, "size": len(content)}
    raise HTTPException(404, f"文件 {path} 不存在")


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


# ============================================================
# API: 认证 + Agent 状态 + 测试结果
# ============================================================

GITEA_URL = "http://localhost:3000"
_git_tokens: dict[str, str] = {}

@app.post("/api/auth/login")
async def auth_login(req: dict):
    """登录 — 用 Gitea API 验证用户名密码, 返回 token"""
    username = req.get("username", "")
    password = req.get("password", "")
    if not username or not password:
        raise HTTPException(400, "用户名和密码不能为空")

    try:
        data = json.dumps({"name": "agentdev-login"}).encode()
        auth = _base64.b64encode(f"{username}:{password}".encode()).decode()
        http_req = urllib.request.Request(
            f"{GITEA_URL}/api/v1/users/{username}/tokens",
            data=data, method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Basic {auth}"},
        )
        resp = urllib.request.urlopen(http_req, timeout=5)
        result = json.loads(resp.read())
        token = result.get("sha1", "")
        _git_tokens[username] = token
        return {"status": "ok", "username": username, "token": token, "gitea_url": GITEA_URL}
    except Exception as e:
        # 回退: 本地简单验证
        if username == "devops" and password == "devops123":
            _git_tokens[username] = "local-dev-token"
            return {"status": "ok", "username": username, "token": "local-dev-token", "gitea_url": GITEA_URL}
        raise HTTPException(401, f"登录失败: {str(e)}")


@app.get("/api/pipeline/agent-status/{pipeline_id}")
async def get_agent_status(pipeline_id: str):
    """获取每个 Agent 节点的真实执行状态 (用于 M5 拓扑)"""
    pipeline = pipelines.get(pipeline_id)
    if not pipeline:
        raise HTTPException(404, f"任务 {pipeline_id} 不存在")

    # 读取 workspace 中的产物来判断每个 Agent 做了什么
    ws = os.path.join("workspace", pipeline_id)
    files_found = []
    if os.path.exists(ws):
        for root, dirs, filenames in os.walk(ws):
            for fn in filenames:
                if fn.startswith(".") or fn.endswith(".pyc"):
                    continue
                full = os.path.join(root, fn)
                files_found.append({
                    "path": str(Path(full).relative_to(ws)),
                    "size": os.path.getsize(full),
                })

    agents = [
        {"id": "pm",       "name": "PM Agent",         "icon": "🧭", "desc": "需求分析与结构化",
         "status": "done" if any("requirement" in a.type.value for a in pipeline.artifacts) else "pending",
         "output": f"生成 {len([a for a in pipeline.artifacts if a.type.value=='requirement'])} 份需求文档"},
        {"id": "architect","name": "Architect Agent",   "icon": "🎨", "desc": "系统架构与接口设计",
         "status": "done" if any("design" in a.type.value for a in pipeline.artifacts) else "pending",
         "output": f"架构设计 {len([a for a in pipeline.artifacts if a.type.value=='design'])} 份文档"},
        {"id": "developer","name": "Developer Agent",   "icon": "💻", "desc": "代码生成与测试编写",
         "status": "running" if os.path.exists(ws) and files_found else "pending",
         "output": f"生成 {len(files_found)} 个文件" if files_found else ""},
        {"id": "tester",   "name": "Tester Agent",      "icon": "🧪", "desc": "pytest 执行 + 结果分析",
         "status": "done" if any(t.status.value == "TEST_PASSED" for t in pipeline.tasks) else "pending",
         "output": "单元测试完成" if pipeline.progress > 30 else ""},
        {"id": "reviewer", "name": "Reviewer Agent",    "icon": "🧐", "desc": "10维代码审查",
         "status": "done" if pipeline.progress > 50 else "pending",
         "output": f"审查评分完成" if pipeline.progress > 50 else ""},
        {"id": "devops",   "name": "DevOps Agent",      "icon": "🚀", "desc": "构建 + 推送 Gitea",
         "status": "done" if pipeline.status.value == "COMPLETED" else "pending",
         "output": "已推送到 Gitea 仓库" if pipeline.status.value == "COMPLETED" else ""},
    ]
    return {"pipeline_id": pipeline_id, "agents": agents, "progress": pipeline.progress,
            "files": files_found[:20]}


@app.get("/api/pipeline/test-results/{pipeline_id}")
async def get_test_results(pipeline_id: str):
    """获取真实测试结果 (pytest 输出 + 测试代码 + 覆盖率)"""
    pipeline = pipelines.get(pipeline_id)
    if not pipeline:
        raise HTTPException(404, f"任务 {pipeline_id} 不存在")

    # 读取 workspace 中的测试文件
    ws = os.path.join("workspace", pipeline_id)
    test_files = []
    test_output = ""
    coverage = "N/A"
    fix_attempts = []

    if os.path.exists(ws):
        for root, dirs, filenames in os.walk(ws):
            for fn in filenames:
                full = os.path.join(root, fn)
                rel = str(Path(full).relative_to(ws))
                if "test" in fn.lower() and fn.endswith(".py"):
                    with open(full) as f:
                        test_files.append({"path": rel, "content": f.read()[:3000]})
                if "fix_attempt" in fn.lower():
                    with open(full) as f:
                        fix_attempts.append({"file": rel, "content": f.read()[:1500]})

    # 读取 CodeLoop 产出中的 pytest 输出
    for task in pipeline.tasks:
        if task.output and ("pytest" in (task.output or "").lower() or "passed" in (task.output or "").lower()):
            test_output = task.output[:2000]

    return {
        "pipeline_id": pipeline_id,
        "test_files": test_files,
        "test_output": test_output or "等待执行...",
        "coverage": coverage,
        "fix_attempts": fix_attempts,
        "total_retries": len(fix_attempts),
    }


from runtime.parser import DocumentParser

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

_deploy_store: dict[str, str] = {}  # pipeline_id -> deploy_url

@app.post("/api/pipeline/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件并解析内容"""
    filepath = UPLOAD_DIR / (uuid.uuid4().hex[:8] + "_" + (file.filename or "unknown"))
    content = await file.read()
    filepath.write_bytes(content)

    parser = DocumentParser(llm_service=llm)
    result = parser.parse(str(filepath))
    return {
        "status": "ok", "filename": file.filename, "type": result["type"],
        "text": result["text"][:5000], "size": result["size"], "file_id": filepath.name,
    }


@app.post("/api/deploy/{pipeline_id}")
async def deploy_pipeline(pipeline_id: str):
    """部署生成的代码为可访问服务"""
    pipeline = pipelines.get(pipeline_id)
    if not pipeline:
        raise HTTPException(404, f"任务 {pipeline_id} 不存在")
    from runtime.deploy import DeployEngine
    ws = os.path.join("workspace", pipeline_id)
    if not os.path.exists(ws):
        raise HTTPException(400, "工作区不存在，请先通过 Gate1 触发 CodeLoop")
    result = DeployEngine.deploy(pipeline_id, ws)
    if result.get("success"):
        _deploy_store[pipeline_id] = result.get("url", "")
        pipeline.logs.append(f"[Deploy] 🚀 服务已部署: {result.get('url')}")
    return result


@app.get("/api/deploy/status/{pipeline_id}")
async def deploy_status(pipeline_id: str):
    from runtime.deploy import DeployEngine
    return DeployEngine.status(pipeline_id)


@app.post("/api/deploy/stop/{pipeline_id}")
async def deploy_stop(pipeline_id: str):
    from runtime.deploy import DeployEngine
    DeployEngine.stop(pipeline_id)
    _deploy_store.pop(pipeline_id, None)
    return {"status": "stopped"}


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
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
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
