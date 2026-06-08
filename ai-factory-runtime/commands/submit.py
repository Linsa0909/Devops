"""AI Factory — submit 命令: 提交需求到流水线"""
from __future__ import annotations
import sys
import time
from utils.api import APIClient
from utils.config import AIConfig


def cmd_submit(args, config: AIConfig, api: APIClient):
    """提交需求 → 启动 Agent 流水线"""
    # 获取需求描述
    description = args.description
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                description = f.read()
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            sys.exit(1)

    feature_name = args.feature_name or "未命名需求"
    if not description:
        print("📝 请输入需求描述 (Ctrl+D 结束):")
        try:
            description = sys.stdin.read().strip()
        except EOFError:
            description = ""

    if not description:
        print("❌ 需求描述不能为空")
        sys.exit(1)

    # 检查后端是否就绪
    try:
        health = api.health()
        print(f"✅ 后端连接成功: {health.get('status', 'ok')}")
    except Exception as e:
        print(f"❌ 无法连接后端 ({api.base_url}): {e}")
        print("   请确认后端已启动: uvicorn main:app --port 8000")
        sys.exit(1)

    print()
    print(f"🚀 提交需求: {feature_name}")
    print(f"   描述: {description[:80]}{'...' if len(description) > 80 else ''}")
    print()

    # 调用后端
    try:
        result = api.start_pipeline(feature_name, description)
        task_id = result.get("id", "")
        status = result.get("status", "UNKNOWN")
        progress = result.get("progress", 0)
        print(f"📋 任务 ID: {task_id}")
        print(f"📊 状态: {status}")
        print(f"📈 进度: {progress}%")
        print(f"🔧 任务数: {len(result.get('tasks', []))}")
        print(f"🚪 闸门数: {len(result.get('gates', []))}")
        print()

        # 检查是否到达 Gate1
        if status == "GATE_WAIT":
            print("⏸  ⏸ 流水线已到达 Gate1 (需求审查)")
            print("   使用以下命令审批:")
            print(f"   ai-factory gate approve -p {task_id} -g Gate1 -c '通过'")

        # 打印最近日志
        logs = result.get("logs", [])
        if logs:
            print("📋 最近日志:")
            for log in logs[-5:]:
                print(f"   {log}")

        print()
        print(f"💡 查看状态: ai-factory status {task_id}")
        print(f"💡 持续监控: ai-factory status {task_id} --watch")

    except Exception as e:
        print(f"❌ 提交失败: {e}")
        sys.exit(1)
