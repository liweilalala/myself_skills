#!/usr/bin/env python3
"""
workflow_monitor.py - 监控测试生成工作流任务状态和产出文件
用法: python3 workflow_monitor.py <taskId> [workspace_path]
"""
import sys
import json
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("用法: workflow_monitor.py <taskId> [workspace_path]")
        sys.exit(1)

    task_id = sys.argv[1]
    workspace_root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.home() / ".openclaw" / "workspace"
    workspace = workspace_root / task_id

    if not workspace.exists():
        print(f"[错误] 任务文件夹不存在: {workspace}")
        sys.exit(1)

    # 列出所有文件
    print(f"=== 任务文件夹内容: {task_id} ===")
    for f in sorted(workspace.rglob("*")):
        if f.is_file():
            size = f.stat().st_size
            print(f"  {f.relative_to(workspace)} ({size} bytes)")

    # 检查关键产出文件
    key_files = [
        "doc.md",
        "rule_split_analysis.json",
        "atomic-capability.json",
        "logic_testpoint.json",
        "interface_testpoint.json",
        "logic_testcase.json",
        "interface_testcase.json"
    ]

    print(f"\n=== 关键产出文件检查 ===")
    all_exist = True
    for fname in key_files:
        fpath = workspace / fname
        if fpath.exists() and fpath.stat().st_size > 0:
            print(f"  ✓ {fname}")
        else:
            print(f"  ✗ {fname} (缺失或为空)")
            all_exist = False

    if all_exist:
        print(f"\n[完成] 所有产出文件已生成")
    else:
        print(f"\n[进行中] 工作流尚未完成")


if __name__ == "__main__":
    main()