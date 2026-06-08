"""AI Factory — gate 命令: 闸门审批"""
from __future__ import annotations
import sys
import time
from utils.api import APIClient


def cmd_gate(args, api: APIClient):
    """审批人工闸门 (Gate1/Gate2/Gate3)"""
    pipeline_id = args.pipeline
    gate_id = args.gate
    action = args.action
    comment = args.comment or f"通过 {gate_id}"

    # 先查看当前状态确认闸门待审批
    try:
        data = api.get_status(pipeline_id)
    except Exception as e:
        print(f"❌ 获取流水线状态失败: {e}")
        sys.exit(1)

    # 找到对应的闸门
    gates = data.get("gates", [])
    target_gate = next((g for g in gates if g["id"] == gate_id), None)

    if not target_gate:
        print(f"❌ 未找到闸门 {gate_id}")
        sys.exit(1)

    current_status = target_gate.get("status", "UNKNOWN")

    if current_status == "APPROVED":
        print(f"⏭  闸门 {gate_id} 已批准，无需重复操作")
        return

    if current_status == "REJECTED":
        print(f"⏭  闸门 {gate_id} 已被驳回，如需重新提交请重启流水线")
        return

    if current_status != "PENDING":
        print(f"⏭  闸门 {gate_id} 当前状态: {current_status}，不可操作")
        return

    # 执行审批
    gate_name = {"Gate1": "需求→设计审查", "Gate2": "测试→部署审查", "Gate3": "发布上线终审"}.get(gate_id, gate_id)
    action_label = "批准" if action == "approve" else "驳回"

    print(f"🚪 闸门: {gate_id} ({gate_name})")
    print(f"  动作: {action_label}")
    print(f"  备注: {comment}")
    print()

    # Gate3 不可跳过确认
    if gate_id == "Gate3" and action == "approve":
        print("⚠️  Gate3 是发布终审，不可跳过。确认放行? (y/N): ", end="", flush=True)
        try:
            confirm = sys.stdin.readline().strip().lower()
            if confirm != "y":
                print("❌ 已取消")
                return
        except:
            pass

    try:
        result = api.gate_action(pipeline_id, gate_id, action, comment)
        print(f"✅ {gate_id} {action_label}成功!")
        print()

        # 显示审批后的状态
        new_status = result.get("status", "")
        new_progress = result.get("progress", 0)
        print(f"📊 流水线状态: {new_status}")
        print(f"📈 进度: {new_progress}%")

        # 显示推进后的日志
        logs = result.get("logs", [])
        if logs:
            print()
            print("📋 最新日志:")
            for log in logs[-3:]:
                print(f"   {log}")

        # 如果到了下一个 Gate 或完成
        if result.get("status") == "GATE_WAIT":
            next_gate = next((g for g in result.get("gates", [])
                             if g.get("status") == "PENDING"), None)
            if next_gate:
                print()
                print(f"⏸ 到达下一个闸门: {next_gate['id']}")
                print(f"   审批: ai-factory gate approve -p {pipeline_id} -g {next_gate['id']}")

        elif result.get("status") == "COMPLETED":
            print()
            print("🎉 流水线全部完成!")

    except Exception as e:
        print(f"❌ 审批失败: {e}")
        sys.exit(1)
