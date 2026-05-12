#!/usr/bin/env python3
"""
check_resume.py - Check if a task can resume and find the next steps to execute

Usage:
    python3 check_resume.py <task_id> [--workspace <workspace_path>]

Output:
    JSON with:
    - canResume: boolean
    - nextSteps: list of step IDs that can be executed next
    - completedSteps: list of completed step IDs
    - failedSteps: list of failed step IDs
    - pendingSteps: list of pending step IDs
    - currentPhase: current phase number (1, 2, or 3)
    - taskStatus: overall task status

Examples:
    python3 check_resume.py task_tcg_20260512_143000
"""

import argparse
import json
import os
import sys
from pathlib import Path


def get_default_workspace() -> str:
    """Get the default workspace path"""
    home = os.path.expanduser("~")
    return os.path.join(home, ".openclaw", "workspace")


def can_resume_step(step: dict, completed_steps: set) -> bool:
    """Check if a step can resume:
    1. Its status is 'pending' or 'failed'
    2. All steps in its dependsOn list are 'completed'
    3. retryCount < 3
    """
    if step["status"] not in ["pending", "failed"]:
        return False

    if step.get("retryCount", 0) >= 3:
        return False

    for dep in step.get("dependsOn", []):
        if dep not in completed_steps:
            return False

    return True


def check_resume(task_id: str, workspace: str = None) -> dict:
    """Check if task can resume and find next steps"""

    if workspace is None:
        workspace = get_default_workspace()

    task_record_path = os.path.join(workspace, "task_records", task_id, "task_record.json")

    if not os.path.exists(task_record_path):
        raise FileNotFoundError(f"Task record not found: {task_record_path}")

    with open(task_record_path, 'r', encoding='utf-8') as f:
        task_record = json.load(f)

    completed_steps = set()
    failed_steps = set()
    pending_steps = set()
    in_progress_steps = set()

    for step in task_record["steps"]:
        step_id = step["id"]
        status = step["status"]

        if status == "completed":
            completed_steps.add(step_id)
        elif status == "failed":
            failed_steps.add(step_id)
        elif status == "pending":
            pending_steps.add(step_id)
        elif status == "in_progress":
            in_progress_steps.add(step_id)

    # Find next executable steps
    next_steps = []
    for step in task_record["steps"]:
        if can_resume_step(step, completed_steps):
            next_steps.append(step["id"])

    # Determine current phase
    current_phase = 1
    if "1.1" in completed_steps:
        current_phase = 1
    if "1.8" in completed_steps:
        current_phase = 2
    if any(s in completed_steps for s in ["2.1.2", "2.2.2"]):
        current_phase = 3

    # Determine if can resume
    # Can resume if:
    # 1. Task status is not 'completed' or 'failed'
    # 2. There are steps that can be executed
    can_resume = (
        task_record["status"] not in ["completed", "failed"] and
        len(next_steps) > 0
    )

    return {
        "canResume": can_resume,
        "nextSteps": sorted(next_steps, key=lambda x: (len(x.split('.')), x)),
        "completedSteps": sorted(list(completed_steps)),
        "failedSteps": sorted(list(failed_steps)),
        "pendingSteps": sorted(list(pending_steps)),
        "inProgressSteps": sorted(list(in_progress_steps)),
        "currentPhase": current_phase,
        "taskStatus": task_record["status"],
        "taskId": task_id,
        "workDir": task_record["context"]["workDir"]
    }


def main():
    parser = argparse.ArgumentParser(description="Check if task can resume")
    parser.add_argument("task_id", help="Task ID (e.g., task_tcg_20260512_143000)")
    parser.add_argument("--workspace", help="Workspace path (default: ~/.openclaw/workspace)")

    args = parser.parse_args()

    try:
        result = check_resume(args.task_id, args.workspace)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
