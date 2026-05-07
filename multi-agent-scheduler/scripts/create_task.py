#!/usr/bin/env python3
"""
create_task.py - 创建任务记录
用法: python3 create_task.py <task_json_path>

输入JSON格式:
{
  "name": "任务名称",
  "sourceDoc": "来源文档",
  "steps": [
    {
      "name": "步骤1",
      "agent": "agent_id",
      "skill": "skill_name",
      "dependsOn": [],
      "input": {"key": "value"},
      "output": {"key": "value"},
      "task": "详细的执行任务描述（必填）"
    }
  ]
}

修复记录:
  - 2026-05-07: 确保每个step都有task字段，避免派发时缺失
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta


SKILL_DIR = Path(__file__).parent.parent.resolve()
SCRIPT_DIR = SKILL_DIR / "scripts"
REFERENCES_DIR = SKILL_DIR / "references"
REGISTRY_FILE = REFERENCES_DIR / "agent-registry.json"
WORKSPACE = Path.home() / ".openclaw" / "workspace"
TASK_RECORDS_DIR = WORKSPACE / "task_records"


def gmt8_now():
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M GMT+8")


def generate_task_id():
    now = datetime.now(timezone(timedelta(hours=8)))
    return f"task_{now.strftime('%Y%m%d_%H%M%S')}_{now.microsecond // 10000:04d}"


def validate_task_desc(task_desc):
    """验证任务描述的必填字段"""
    errors = []

    if not task_desc.get("name"):
        errors.append("缺少任务名称 (name)")

    steps = task_desc.get("steps", [])
    if not steps:
        errors.append("缺少步骤定义 (steps)")

    for i, step in enumerate(steps):
        step_name = step.get("name", f"步骤{i+1}")
        if not step.get("agent"):
            errors.append(f"步骤 {i+1} ({step_name}) 缺少 agent")
        if not step.get("task"):
            errors.append(f"步骤 {i+1} ({step_name}) 缺少 task 字段（详细的执行描述）")

    return errors


def create_task_record(task_desc):
    task_id = generate_task_id()
    now = gmt8_now()

    record = {
        "id": task_id,
        "name": task_desc.get("name", "未命名任务"),
        "version": "1.0",
        "createdAt": now,
        "updatedAt": now,
        "status": "pending",
        "currentStep": 0,
        "context": {
            "workspace": str(WORKSPACE),
            "sourceDoc": task_desc.get("sourceDoc", "")
        },
        "steps": [],
        "heartbeatAgents": [],
        "dispatches": []
    }

    for i, step_desc in enumerate(task_desc.get("steps", [])):
        step_name = step_desc.get("name", f"步骤{i+1}")

        # 确保 task 字段存在
        task_text = step_desc.get("task")
        if not task_text:
            # 从 input/output 构建默认 task
            input_str = json.dumps(step_desc.get("input", {}), ensure_ascii=False)
            output_str = json.dumps(step_desc.get("output", {}), ensure_ascii=False)
            task_text = f"执行 {step_name}。输入: {input_str}，输出: {output_str}"

        step = {
            "id": i + 1,
            "name": step_name,
            "agent": step_desc.get("agent"),
            "skill": step_desc.get("skill"),
            "dependsOn": step_desc.get("dependsOn", []),
            "status": "pending",
            "input": step_desc.get("input", {}),
            "output": step_desc.get("output", {}),
            "task": task_text,
            "watchFiles": step_desc.get("watchFiles", []),
            "completedAt": None,
            "notes": step_desc.get("notes")
        }
        record["steps"].append(step)

        # 记录需要心跳的 agent
        agent = step_desc.get("agent")
        if agent and agent not in record["heartbeatAgents"]:
            record["heartbeatAgents"].append(agent)

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
        print("\n输入JSON格式:")
        print('{"name": "任务名称", "steps": [{"name": "步骤1", "agent": "xxx", "task": "详细描述", ...}]}')
        sys.exit(1)

    task_desc_path = Path(sys.argv[1])
    if not task_desc_path.exists():
        print(f"[错误] 文件不存在: {task_desc_path}")
        sys.exit(1)

    try:
        with open(task_desc_path, "r", encoding="utf-8") as f:
            task_desc = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[错误] JSON格式错误: {e}")
        sys.exit(1)

    # 验证必填字段
    errors = validate_task_desc(task_desc)
    if errors:
        print("[错误] 任务描述验证失败:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    record = create_task_record(task_desc)
    task_path = save_task_record(record)

    print(f"[创建] 任务 {record['id']}")
    print(f"[名称] {record['name']}")
    print(f"[步骤] {len(record['steps'])} 个:")
    for step in record['steps']:
        print(f"  - #{step['id']} {step['name']} (agent={step['agent']})")
        print(f"    task: {step['task'][:60]}...")
    print(f"[Agent] {record['heartbeatAgents']}")
    print(f"[路径] {task_path}")

    return True


if __name__ == "__main__":
    main()