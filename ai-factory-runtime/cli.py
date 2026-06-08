"""AI Factory — CLI 入口

Usage:
    ai-factory init <project-name>
    ai-factory submit <feature-name>
    ai-factory status
    ai-factory gate approve|reject <reason>
"""
from __future__ import annotations
import sys
import os
import argparse
from pathlib import Path

# 让 Python 能找到 ai-factory-runtime 包
_RUNTIME_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(_RUNTIME_DIR.parent))

from utils.config import AIConfig, DEFAULT_CONFIG_PATH
from utils.api import APIClient, DEFAULT_BACKEND_URL
from commands.init import cmd_init
from commands.submit import cmd_submit
from commands.status import cmd_status
from commands.gate import cmd_gate


def main():
    parser = argparse.ArgumentParser(
        prog="ai-factory",
        description="🤖 AI Factory — Enterprise Full-Stack Development Runtime",
        epilog="端到端软件需求 Agent 平台 CLI 网关",
    )
    parser.add_argument("--backend", default=DEFAULT_BACKEND_URL, help="后端地址 (默认: http://localhost:8000)")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="配置文件路径")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # === init ===
    init_p = subparsers.add_parser("init", help="创建项目脚手架")
    init_p.add_argument("project_name", help="项目名称")

    # === submit ===
    submit_p = subparsers.add_parser("submit", help="提交需求到流水线")
    submit_p.add_argument("feature_name", nargs="?", help="需求/功能名称")
    submit_p.add_argument("--description", "-d", default="", help="需求描述")
    submit_p.add_argument("--file", "-f", help="从文件读取需求描述")

    # === status ===
    status_p = subparsers.add_parser("status", help="查看流水线状态")
    status_p.add_argument("task_id", nargs="?", help="任务 ID (不指定则显示最近的)")
    status_p.add_argument("--watch", "-w", action="store_true", help="持续监听模式")
    status_p.add_argument("--interval", "-i", type=int, default=3, help="轮询间隔(秒)")

    # === gate ===
    gate_p = subparsers.add_parser("gate", help="闸门审批")
    gate_p.add_argument("action", choices=["approve", "reject"], help="审批动作")
    gate_p.add_argument("--pipeline", "-p", required=True, help="流水线 ID")
    gate_p.add_argument("--gate", "-g", required=True, choices=["Gate1", "Gate2", "Gate3"], help="闸门 ID")
    gate_p.add_argument("--comment", "-c", default="", help="审批备注")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 加载配置 + 创建 API 客户端
    config = AIConfig(Path(args.config))
    api = APIClient(args.backend)

    # 路由到对应命令
    if args.command == "init":
        cmd_init(args.project_name, config)
    elif args.command == "submit":
        cmd_submit(args, config, api)
    elif args.command == "status":
        cmd_status(args, api)
    elif args.command == "gate":
        cmd_gate(args, api)


if __name__ == "__main__":
    main()
