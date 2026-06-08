# AgentDev OS — 端到端软件需求 Agent 平台

从**产品想法**到**需求分析、规则约束、Agent 执行、验证、发布、知识沉淀**的端到端系统。

## 🚀 一键启动

```bash
# Windows
双击 AgentDevOS/start.bat

# Linux/macOS
./AgentDevOS/start.sh
```

→ 浏览器打开 **http://localhost:8000**（前后端联动，同源服务）

## 🧭 项目结构

```
AgentDevOS/
├── index.html                  # 前端 (React 18 + Tailwind CSS, 1260 行)
├── start.bat / start.sh        # 一键启动脚本
├── ai-factory / ai-factory.bat # CLI 包装器
│
├── backend/                    # FastAPI 后端 (1427 行 Python)
│   ├── main.py                 # REST API 入口 + 14 端点
│   ├── models/                 # Pipeline/Task/Rule/Gate/Artifact 模型
│   ├── core/                   # 17 状态 FSM + 任务 DAG 编排
│   ├── guardrails/             # 规则引擎 (4类×16条)
│   ├── gates/                  # 闸门系统 (Gate1/2/3)
│   ├── llm/                    # DeepSeek API 驱动
│   ├── knowledge/              # 知识沉淀引擎
│   └── sandbox/                # 代码沙箱执行
│
└── ai-factory-runtime/         # CLI 网关 (793 行 Python)
    ├── cli.py                  # 入口
    ├── config.yaml             # DeepSeek + Gate 配置
    ├── commands/
    │   ├── init.py             # 项目脚手架
    │   ├── submit.py           # 提交需求
    │   ├── status.py           # 查看 DAG 状态
    │   └── gate.py             # 闸门审批
    └── utils/
        ├── config.py           # 配置加载
        └── api.py              # 后端 HTTP 客户端
```

## 📋 CLI 命令

```bash
# 创建项目
ai-factory init <project-name>

# 提交需求 → 启动流水线
ai-factory submit "功能名" -d "需求描述"

# 查看 17 节点 DAG 状态
ai-factory status <task_id>

# 持续监听模式
ai-factory status <task_id> --watch

# 审批闸门
ai-factory gate approve -p <task_id> -g Gate1 -c "通过"
ai-factory gate reject  -p <task_id> -g Gate1 -c "驳回原因"
```

## 🏗 前端看板

| 模块 | 功能 |
|------|------|
| M8 全局框架 | 左侧导航 + 顶部状态流 + 中央工作区 + 底部日志终端 |
| M2 需求孵化 | 输入产品想法 + AI 评估 + 自动轮询推流 |
| M3 智能分析 | req/design 文档 + 拓扑图 + Gate 放行 |
| M4 规则约束 | 16 条规则矩阵 + 自定义规则 + Toggle |
| M5 Agent 执行 | 4 Agent DAG + 实时 Prompt 追踪 |
| M6 验证 QA  | 测试流水线 + Self-Healing |
| M7 发布沉淀 | 部署成功 + 知识资产归档 |

## 🔄 流水线流程

```
用户提交需求
  → REQ Agent (DeepSeek 需求分析)
  → Architect Agent (架构设计)
  → ⏸ Gate1 (人工审批)
  → Developer Agent (代码生成)
  → Tester Agent (pytest + ruff + 规则审查)
  → 🔄 Self-Healing (失败自动修复)
  → ⏸ Gate2 (人工审批)
  → Reviewer Agent (审查)
  → ⏸ Gate3 (不可跳过终审)
  → DevOps Agent (Docker 构建)
  → Knowledge 沉淀 (Prompts + FT 数据 + 知识库)
```

## 🎯 后端 API (14 端点)

| 端点 | 功能 |
|------|------|
| `POST /api/pipeline/start` | 提交需求启动流水线 |
| `GET /api/pipeline/status` | 长轮询状态 |
| `POST /api/pipeline/gate` | 审批闸门 |
| `POST /api/pipeline/rules/toggle` | 开关规则 |
| `POST /api/pipeline/rules/add` | 追加自定义规则 |
| `GET /api/pipeline/knowledge/{id}` | 知识资产 |
| `GET /api/pipeline/history/{id}` | 全链路追溯 |
| `GET /api/pipeline/logs/{id}` | 流水线日志 |
| `GET /api/products/list` | 产物清单 |
| `GET /api/products/file/{path}` | 产物内容 |
| `POST /api/pipeline/save_artifact` | 保存产物 |
| `GET /api/pipeline/rules/{id}` | 规则列表 |
| `POST /api/pipeline/restart` | 重启流水线 |
| `GET /api/health` | 健康检查 |

## 🔧 技术栈

- **前端**: React 18 (CDN) + Tailwind CSS v4 + Babel Standalone
- **后端**: FastAPI + Pydantic + httpx
- **CLI**: argpars + click + PyYAML
- **LLM**: DeepSeek API (Mock 回退)
- **状态管理**: 微型 Zustand (publish/subscribe)
