#!/usr/bin/env python3
"""
execute_task.py - 检查并继续执行任务
用法: python3 execute_task.py <task_record_json_path> [--spawn]

此脚本由主Agent的心跳调用，用于检查任务状态并决定是否需要派发下一个步骤。
派发由主Agent通过 sessions_spawn 工具直接执行。
"""

import json
import sys
import os
import platform
from pathlib import Path


def get_home_dir():
    """获取用户主目录"""
    if platform.system() == "Windows":
        home = os.environ.get("USERPROFILE")
        if not home:
            home = os.environ.get("HOMEDRIVE", "") + os.environ.get("HOMEPATH", "")
    else:
        home = os.environ.get("HOME")
        if not home:
            try:
                import pwd
                home = pwd.getpwuid(os.getuid()).pw_dir
            except Exception:
                home = os.path.expanduser("~")
    return home


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
    """获取下一个待执行的步骤（依赖已满足的）"""
    steps = record.get("steps", [])
    for step in steps:
        if step.get("status") == "pending":
            deps = step.get("dependsOn", [])
            if not deps:
                return step
            # 检查依赖是否都完成
            all_done = True
            for d in deps:
                dep_step = next((s for s in steps if s.get("id") == d), None)
                if not dep_step or dep_step.get("status") != "completed":
                    all_done = False
                    break
            if all_done:
                return step
    return None


def check_step_completed(step):
    """检查步骤是否已完成（通过输出文件判断）"""
    for out_path in step.get("output", {}).values():
        if isinstance(out_path, str) and out_path:
            expanded = os.path.expanduser(os.path.expandvars(out_path))
            if Path(expanded).exists():
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
    print(f"[检查] 任务 {task_id}，状态: {record.get('status')}", flush=True)

    # 任务已完成，无需处理
    if record.get("status") == "completed":
        print("[完成] 任务已全部完成", flush=True)
        sys.exit(0)

    # 检查 in_progress 步骤是否实际完成
    updated = False
    for step in record.get("steps", []):
        if step.get("status") == "in_progress":
            if check_step_completed(step):
                step["status"] = "completed"
                step["completedAt"] = record.get("updatedAt", "")
                print(f"[完成] 步骤 {step['id']}: {step['name']}", flush=True)
                updated = True

    # 如果有更新，保存记录
    if updated:
        record["updatedAt"] = record.get("updatedAt", "")
        save_task_record(task_path, record)

    # 找下一个待执行步骤
    next_step = get_next_pending_step(record)

    if not next_step:
        # 检查是否全部完成
        all_done = all(s.get("status") == "completed" for s in record.get("steps", []))
        if all_done:
            record["status"] = "completed"
            print("[完成] 所有步骤执行完毕", flush=True)
            save_task_record(task_path, record)
        else:
            print("[等待] 没有可执行的步骤（等待前置依赖）", flush=True)
        sys.exit(0)

    step_id = next_step["id"]
    step_name = next_step["name"]
    agent = next_step["agent"]
    task_msg = next_step.get("task", f"执行步骤 {step_id}: {step_name}")

    print(f"[执行] 步骤 {step_id}: {step_name}，Agent: {agent}", flush=True)

    # 更新状态为 in_progress
    next_step["status"] = "in_progress"
    record["currentStep"] = step_id
    save_task_record(task_path, record)

    # 打印 JSON 格式的派发信息供主Agent解析
    # 使用特殊标记让主Agent能够识别并提取
    print(f"\n=== AGENT_DISPATCH ===", flush=True)
    dispatch_info = {
        "agentId": agent,
        "task": task_msg,
        "stepId": step_id,
        "stepName": step_name,
        "input": next_step.get("input", {}),
        "output": next_step.get("output", {}),
        "taskRecord": str(task_path)
    }
    print(json.dumps(dispatch_info, ensure_ascii=False), flush=True)
    print(f"=== END_DISPATCH ===", flush=True)

    sys.exit(0)


if __name__ == "__main__":
    main()
