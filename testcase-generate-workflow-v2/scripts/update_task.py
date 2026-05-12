#!/usr/bin/env python3
"""
update_task.py - Update task_record.json after step completion

Usage:
    python3 update_task.py <task_id> <step_id> <status> [--error <error_message>] [--notes <notes>]

Examples:
    python3 update_task.py task_tcg_20260512_143000 1.1 completed
    python3 update_task.py task_tcg_20260512_143000 2.1.1 failed --error "Skill not found"
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def get_default_workspace() -> str:
    """Get the default workspace path"""
    home = os.path.expanduser("~")
    return os.path.join(home, ".openclaw", "workspace")


def update_step_status(task_id: str, step_id: str, status: str,
                       error: str = None, notes: str = None,
                       workspace: str = None) -> dict:
    """Update the status of a specific step in task_record.json"""

    if workspace is None:
        workspace = get_default_workspace()

    task_record_path = os.path.join(workspace, "task_records", task_id, "task_record.json")

    if not os.path.exists(task_record_path):
        raise FileNotFoundError(f"Task record not found: {task_record_path}")

    with open(task_record_path, 'r', encoding='utf-8') as f:
        task_record = json.load(f)

    # Find and update the step
    step_found = False
    for step in task_record["steps"]:
        if step["id"] == step_id:
            step["status"] = status
            step["updatedAt"] = datetime.now().isoformat()

            if status == "in_progress":
                step["startedAt"] = datetime.now().isoformat()
            elif status == "completed":
                step["completedAt"] = datetime.now().isoformat()
            elif status == "failed":
                step["error"] = error
                step["retryCount"] = step.get("retryCount", 0) + 1

            if notes:
                step["notes"] = notes

            step_found = True
            break

    if not step_found:
        raise ValueError(f"Step {step_id} not found in task record")

    # Update task status if needed
    if status == "completed":
        # Check if all steps are completed
        all_completed = all(s["status"] == "completed" for s in task_record["steps"])
        if all_completed:
            task_record["status"] = "completed"
    elif status == "failed":
        task_record["status"] = "failed"
    elif status == "in_progress" and task_record["status"] == "pending":
        task_record["status"] = "in_progress"

    task_record["updatedAt"] = datetime.now().isoformat()

    # Write updated task record
    with open(task_record_path, 'w', encoding='utf-8') as f:
        json.dump(task_record, f, ensure_ascii=False, indent=2)

    return {
        "taskId": task_id,
        "stepId": step_id,
        "status": status,
        "taskRecordPath": task_record_path
    }


def main():
    parser = argparse.ArgumentParser(description="Update task step status")
    parser.add_argument("task_id", help="Task ID (e.g., task_tcg_20260512_143000)")
    parser.add_argument("step_id", help="Step ID (e.g., 1.1, 2.1.1)")
    parser.add_argument("status", choices=["pending", "in_progress", "completed", "failed", "skipped"],
                        help="New status for the step")
    parser.add_argument("--workspace", help="Workspace path (default: ~/.openclaw/workspace)")
    parser.add_argument("--error", help="Error message if step failed")
    parser.add_argument("--notes", help="Additional notes")

    args = parser.parse_args()

    try:
        result = update_step_status(
            args.task_id,
            args.step_id,
            args.status,
            args.error,
            args.notes,
            args.workspace
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
