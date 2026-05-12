#!/usr/bin/env python3
"""
create_task.py - Create a new task record

Simplified interface for creating task records. For full initialization,
use init_workflow.py instead.

Usage:
    python3 create_task.py <input_doc> [--workspace <workspace_path>]

Output:
    JSON with task_id and paths
"""

import argparse
import json
import os
import sys
from datetime import datetime


def generate_task_id() -> str:
    """Generate a task ID with format: task_tcg_YYYYMMDD_HHMMSS"""
    return f"task_tcg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def get_default_workspace() -> str:
    """Get the default workspace path"""
    home = os.path.expanduser("~")
    return os.path.join(home, ".openclaw", "workspace")


def create_task(input_doc: str, workspace: str = None) -> dict:
    """Create a new task"""

    if workspace is None:
        workspace = get_default_workspace()

    task_id = generate_task_id()
    work_dir = os.path.join(workspace, "task_records", task_id)

    # Create work directory
    os.makedirs(work_dir, exist_ok=True)

    # Create task record
    task_record = {
        "id": task_id,
        "name": "测试用例生成工作流",
        "version": "1.0",
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
        "status": "pending",
        "context": {
            "workspace": workspace,
            "inputDoc": os.path.abspath(input_doc),
            "workDir": work_dir
        },
        "taskRecordPath": os.path.join(work_dir, "task_record.json")
    }

    # Write task record
    task_record_path = os.path.join(work_dir, "task_record.json")
    with open(task_record_path, 'w', encoding='utf-8') as f:
        json.dump(task_record, f, ensure_ascii=False, indent=2)

    return {
        "taskId": task_id,
        "workDir": work_dir,
        "taskRecordPath": task_record_path
    }


def main():
    parser = argparse.ArgumentParser(description="Create a new task record")
    parser.add_argument("input_doc", help="Path to input design document (.docx or .md)")
    parser.add_argument("--workspace", help="Workspace path (default: ~/.openclaw/workspace)")

    args = parser.parse_args()

    if not os.path.exists(args.input_doc):
        print(f"Error: Input file not found: {args.input_doc}", file=sys.stderr)
        sys.exit(1)

    result = create_task(args.input_doc, args.workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
