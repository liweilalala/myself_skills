#!/usr/bin/env python3
"""
monitor_agent.py - 监控指定Agent的活跃会话状态

用法:
    python3 monitor_agent.py <agentId>          # 查看基本信息
    python3 monitor_agent.py <agentId> --log    # 显示完整日志
    python3 monitor_agent.py <agentId> --files  # 列出所有文件
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime


def get_workspace_path(agent_id: str) -> Path:
    """获取Agent工作目录路径"""
    return Path.home() / ".openclaw" / "agents" / agent_id / "workspace"


def show_basic_info(workspace: Path, agent_id: str):
    """显示基本信息"""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = workspace / "memory" / f"{today}.md"

    print(f"=== Agent: {agent_id} ===")
    print(f"工作目录: {workspace}")
    print()

    if log_file.exists():
        content = log_file.read_text()
        # 只显示前30行
        lines = content.split("\n")
        print(f"=== 今日日志 ({today}) - 共{len(lines)}行 ===")
        for line in lines[:30]:
            print(line)
        if len(lines) > 30:
            print(f"... (还有{len(lines)-30}行)")
    else:
        print("[信息] 今日暂无执行日志")


def show_full_log(workspace: Path):
    """显示完整日志"""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = workspace / "memory" / f"{today}.md"

    if log_file.exists():
        print(f"=== 完整日志内容 ({today}) ===")
        print(log_file.read_text())
    else:
        print("[信息] 今日暂无执行日志")


def list_files(workspace: Path):
    """列出工作目录所有文件"""
    print(f"=== 工作目录文件列表 ===")
    print(f"路径: {workspace}")
    print()

    if not workspace.exists():
        print("[错误] 工作目录不存在")
        return

    for item in sorted(workspace.iterdir()):
        if item.is_dir():
            print(f"  📁 {item.name}/")
            # 显示子目录内容（最多3层）
            try:
                for sub in sorted(item.iterdir())[:5]:
                    if sub.is_dir():
                        print(f"      📁 {sub.name}/")
                    else:
                        size = sub.stat().st_size
                        print(f"      📄 {sub.name} ({size} bytes)")
                if len(list(item.iterdir())) > 5:
                    print(f"      ... 还有{len(list(item.iterdir()))-5}项")
            except PermissionError:
                print(f"      [无权限访问]")
        else:
            size = item.stat().st_size
            print(f"  📄 {item.name} ({size} bytes)")


def main():
    parser = argparse.ArgumentParser(description="监控Agent状态和日志")
    parser.add_argument("agent_id", help="Agent ID")
    parser.add_argument("--log", action="store_true", help="显示完整日志")
    parser.add_argument("--files", action="store_true", help="列出所有文件")

    args = parser.parse_args()

    workspace = get_workspace_path(args.agent_id)

    if not workspace.exists():
        print(f"[错误] Agent工作目录不存在: {workspace}")
        sys.exit(1)

    if args.files:
        list_files(workspace)
    elif args.log:
        show_full_log(workspace)
    else:
        show_basic_info(workspace, args.agent_id)


if __name__ == "__main__":
    main()
