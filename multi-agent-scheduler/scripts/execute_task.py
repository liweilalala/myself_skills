#!/usr/bin/env python3
"""
execute_task.py - 检查并继续执行任务
用法: python3 execute_task.py <task_record_json_path>
"""

import json
import sys
from pathlib import Path


def get_task_record(task_path):
    """读取任务记录"""
    try:
        with open(task_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[错误] 读取任务记录失败: {e}")
        return None


def save_task_record(task_path, record):
    """保存任务记录"""
    try:
        with open(task_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[错误] 保存任务记录失败: {e}")
        return False


def get_next_pending_step(record):
    """获取下一个待执行的步骤"""
    steps = record.get("steps", [])
    for step in steps:
        if step.get("status") == "pending":
            deps = step.get("dependsOn", [])
            if not deps:
                return step
            # 检查依赖是否都完成
            all_done = all(
                next((s for s in steps if s.get("id") == d), {}).get("status") == "completed"
                for d in deps
            )
            if all_done:
                return step
    return None


def check_step_completed(step):
    """检查步骤是否已完成（通过输出文件判断）"""
    for out_path in step.get("output", {}).values():
        if isinstance(out_path, str) and Path(out_path).exists():
            return True
    return False


def main():
    if len(sys.argv) < 2:
        print("用法: python3 execute_task.py <task_record_json_path>")
        sys.exit(1)

    task_path = Path(sys.argv[1])
    record = get_task_record(task_path)
    if not record:
        sys.exit(1)

    task_id = record.get("id")
    print(f"[检查] 任务 {task_id}，状态: {record.get('status')}")

    # 任务已完成，无需处理
    if record.get("status") == "completed":
        print("[完成] 任务已全部完成")
        sys.exit(0)

    # 检查 in_progress 步骤是否实际完成
    for step in record.get("steps", []):
        if step.get("status") == "in_progress":
            if check_step_completed(step):
                step["status"] = "completed"
                print(f"[完成] 步骤 {step['id']}: {step['name']}")

    # 找下一个待执行步骤
    next_step = get_next_pending_step(record)

    if not next_step:
        # 检查是否全部完成
        all_done = all(s.get("status") == "completed" for s in record.get("steps", []))
        if all_done:
            record["status"] = "completed"
            print("[完成] 所有步骤执行完毕")
            save_task_record(task_path, record)
        else:
            print("[等待] 没有可执行的步骤（等待前置依赖）")
        sys.exit(0)

    step_id = next_step["id"]
    step_name = next_step["name"]
    agent = next_step["agent"]

    print(f"[执行] 步骤 {step_id}: {step_name}，Agent: {agent}")

    # 更新状态为 in_progress
    next_step["status"] = "in_progress"
    record["currentStep"] = step_id
    save_task_record(task_path, record)

    # 打印启动信息供主Agent执行
    print(f"\n=== 启动指令 ===")
    print(f"agentId: {agent}")
    print(f"task: 执行步骤 {step_id}: {step_name}")
    print(f"输入: {json.dumps(next_step.get('input', {}), ensure_ascii=False)}")
    print(f"输出: {json.dumps(next_step.get('output', {}), ensure_ascii=False)}")
    print("================")

    sys.exit(0)


if __name__ == "__main__":
    main()