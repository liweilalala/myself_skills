#!/usr/bin/env python3
"""
create_task.py - 创建任务记录并派发第一个步骤
用法: python3 create_task.py <task_json_path>
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta


WORKSPACE = Path.home() / ".openclaw" / "workspace"
TASK_RECORDS_DIR = WORKSPACE / "task_records"


def gmt8_now():
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M GMT+8")


def generate_task_id():
    now = datetime.now(timezone(timedelta(hours=8)))
    return f"task_{now.strftime('%Y%m%d_%H%M%S')}_{now.microsecond // 10000:04d}"


def create_task_record(task_desc):
    task_id = generate_task_id()

    record = {
        "id": task_id,
        "name": task_desc.get("name", "未命名任务"),
        "version": "1.0",
        "createdAt": gmt8_now(),
        "updatedAt": gmt8_now(),
        "status": "pending",
        "currentStep": 0,
        "context": {
            "workspace": str(WORKSPACE),
            "sourceDoc": task_desc.get("sourceDoc", "")
        },
        "steps": [],
        "heartbeatAgents": []
    }

    for i, step_desc in enumerate(task_desc.get("steps", [])):
        step = {
            "id": i + 1,
            "name": step_desc.get("name", f"步骤{i+1}"),
            "agent": step_desc.get("agent"),
            "skill": step_desc.get("skill"),
            "dependsOn": step_desc.get("dependsOn", []),
            "status": "pending",
            "input": step_desc.get("input", {}),
            "output": step_desc.get("output", {}),
            "watchFiles": step_desc.get("watchFiles", []),
            "completedAt": None,
            "notes": None
        }
        record["steps"].append(step)

        if step_desc.get("agent") and step_desc["agent"] not in record["heartbeatAgents"]:
            record["heartbeatAgents"].append(step_desc["agent"])

    return record


def save_task_record(record):
    TASK_RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    task_path = TASK_RECORDS_DIR / f"{record['id']}.json"
    with open(task_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    return task_path


def main():
    if len(sys.argv) < 2:
        print("用法: python3 create_task.py <task_json_path>")
        sys.exit(1)

    task_desc_path = Path(sys.argv[1])
    if not task_desc_path.exists():
        print(f"[错误] 文件不存在: {task_desc_path}")
        sys.exit(1)

    with open(task_desc_path, "r", encoding="utf-8") as f:
        task_desc = json.load(f)

    record = create_task_record(task_desc)
    task_path = save_task_record(record)

    print(f"[创建] 任务 {record['id']}")
    print(f"[名称] {record['name']}")
    print(f"[步骤] {len(record['steps'])} 个")
    print(f"[Agent] {record['heartbeatAgents']}")
    print(f"[路径] {task_path}")

    return True


if __name__ == "__main__":
    main()