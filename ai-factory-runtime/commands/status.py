"""AI Factory — status 命令: 流水线状态 DAG"""
from __future__ import annotations
import time
import sys
from utils.api import APIClient

# 状态图标映射
STATUS_ICONS = {
    "IDEA_ANALYZING":     "🔄",
    "REQUIREMENT_GEN":    "📝",
    "REQUIREMENT_REVIEW":  "⏸",
    "DESIGN_GEN":         "🎨",
    "DESIGN_APPROVED":    "✅",
    "CODE_GENERATING":    "💻",
    "CODE_GENERATED":     "✅",
    "CODE_REVIEW":        "⏸",
    "TEST_RUNNING":       "🧪",
    "TEST_PASSED":        "✅",
    "TEST_FAILED":        "❌",
    "TEST_FIXING":        "🔄",
    "VERIFY_RUNNING":     "🔍",
    "VERIFY_PASSED":      "✅",
    "VERIFY_FAILED":      "❌",
    "REVIEW_PENDING":     "⏸",
    "DEPLOYING":          "📦",
    "DEPLOYED":           "✅",
    "KNOWLEDGE_EXTRACTED":"📚",
    "PENDING":            "⬜",
    "PROCESSING":         "🔄",
    "SUCCESS":            "✅",
}

STAGE_COLORS = {
    "pm":        "\033[36m",  # 青色
    "architect": "\033[35m",  # 紫色
    "developer": "\033[34m",  # 蓝色
    "tester":    "\033[33m",  # 黄色
    "reviewer":  "\033[31m",  # 红色
    "devops":    "\033[32m",  # 绿色
}
RESET = "\033[0m"


def cmd_status(args, api: APIClient):
    """查看流水线任务 DAG 状态"""
    task_id = args.task_id

    if not task_id:
        # 没有指定 task_id, 列出最近的
        print("📋 查看最近的流水线...")
        products = api.list_products()
        if products:
            for p in products:
                print(f"   {p['id']}: {p['name']} ({p['status']})")
        print("   用法: ai-factory status <task_id>")
        return

    if args.watch:
        _watch_status(api, task_id, args.interval)
    else:
        _print_status(api, task_id)


def _print_status(api: APIClient, task_id: str):
    """打印单次状态"""
    try:
        data = api.get_status(task_id)
    except Exception as e:
        print(f"❌ 获取状态失败: {e}")
        return

    # 摘要
    name = data.get("name", "")
    status = data.get("status", "UNKNOWN")
    progress = data.get("progress", 0)
    stage = data.get("current_stage", "")
    error = data.get("error")

    print(f"╔══ AI Factory Runtime 状态 ═══════════════════╗")
    print(f"║  项目: {name}")
    print(f"║  任务: {task_id}")
    print(f"║  状态: {_color_status(status)} {status}")
    print(f"║  阶段: {stage}")
    print(f"║  进度: {'█' * (progress // 10)}{'░' * (10 - progress // 10)} {progress}%")
    if error:
        print(f"║  ❌ 错误: {error}")
    print(f"╚════════════════════════════════════════════════╝")
    print()

    # 闸门状态
    gates = data.get("gates", [])
    if gates:
        print("🚪 闸门状态:")
        for g in gates:
            g_status = g.get("status", "PENDING")
            icon = "✅" if g_status == "APPROVED" else "❌" if g_status == "REJECTED" else "⏸"
            print(f"   {icon} {g['id']}: {g['name']} — {g_status}")
        print()

    # 任务 DAG
    tasks = data.get("tasks", [])
    if tasks:
        print("📋 任务 DAG (17 节点):")
        print(f"   {'状态':>4} {'Agent':>10} {'任务名称':<20}")
        print(f"   {'────':>4} {'──────':>10} {'────────':<20}")
        for t in tasks:
            t_status = t.get("status", "PENDING")
            agent = t.get("agent", "?")
            name = t.get("name", "?")
            icon = STATUS_ICONS.get(t_status, "⬜")
            color = STAGE_COLORS.get(agent, "")
            agent_label = {"pm": "PM", "architect": "架构", "developer": "开发",
                           "tester": "测试", "reviewer": "审查", "devops": "运维"}.get(agent, agent)
            print(f"   {icon} {color}{agent_label:>10}{RESET} {name:<20}")
        print()

    # 日志
    logs = data.get("logs", [])
    if logs:
        print("📋 最近日志:")
        for log in logs[-8:]:
            print(f"   {log}")
        print()

    # 如果到达 Gate，提示
    if status == "GATE_WAIT":
        pending_gate = next((g for g in gates if g.get("status") == "PENDING"), None)
        if pending_gate:
            print(f"⏸ ⏸ 等待闸门审批: {pending_gate['id']}")
            print(f"   批准: ai-factory gate approve -p {task_id} -g {pending_gate['id']} -c '通过'")

    if status == "COMPLETED":
        print("🎉 流水线已完成!")
        print(f"   查看知识资产: 访问后端 API /api/pipeline/knowledge/{task_id}")


def _watch_status(api: APIClient, task_id: str, interval: int = 3):
    """持续监听模式"""
    print(f"📡 持续监听 (每 {interval}s 刷新) — Ctrl+C 退出")
    print()

    terminal_states = {"COMPLETED", "FAILED"}
    seen_logs = set()

    try:
        while True:
            data = api.get_status(task_id)
            status = data.get("status", "")
            progress = data.get("progress", 0)

            # 增量日志
            logs = data.get("logs", [])
            for log in logs:
                if log not in seen_logs:
                    print(f"  {log}")
                    seen_logs.add(log)

            # 进度条
            bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
            print(f"\r📊 [{bar}] {progress}% — {status}", end="", flush=True)

            if status in terminal_states:
                print()
                print()
                if status == "COMPLETED":
                    print("🎉 流水线已完成!")
                else:
                    print(f"❌ 流水线失败: {data.get('error', '未知错误')}")
                break

            time.sleep(interval)

    except KeyboardInterrupt:
        print()
        print("👋 停止监听")
    except Exception as e:
        print()
        print(f"❌ 监听出错: {e}")


def _color_status(status: str) -> str:
    colors = {
        "RUNNING": "\033[33m",    # 黄
        "GATE_WAIT": "\033[36m",  # 青
        "COMPLETED": "\033[32m",  # 绿
        "FAILED": "\033[31m",     # 红
    }
    color = colors.get(status, "")
    if color:
        return f"{color}{status}{RESET}"
    return status
