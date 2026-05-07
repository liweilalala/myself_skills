#!/usr/bin/env python3
"""
execute_task.py - 检查并更新任务状态
用法: python3 execute_task.py <task_record_json_path> [--check-only]

此脚本由主Agent的心跳调用（或手动），用于检查任务状态。
派发逻辑由主Agent根据任务记录中的信息直接执行。

修复记录:
  - 2026-05-07: 移除错误的派发输出设计
  - 改用状态文件模式：更新任务记录中的 dispatches 数组
  - 主Agent心跳时读取 dispatches 数组并执行派发
"""

import json
import sys
import os
import platform
from pathlib import Path
from datetime import datetime, timezone, timedelta

SKILL_DIR = Path(__file__).parent.parent.resolve()
REFERENCES_DIR = SKILL_DIR / "references"
REGISTRY_FILE = REFERENCES_DIR / "agent-registry.json"
WORKSPACE = Path.home() / ".openclaw" / "workspace"
TASK_RECORDS_DIR = WORKSPACE / "task_records"


def gmt8_now():
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M GMT+8")


def expand_path(path_str):
    """展开路径中的~和环境变量"""
    if not path_str:
        return path_str
    path_str = os.path.expanduser(path_str)
    path_str = os.path.expandvars(path_str)
    return path_str


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


def check_step_completed(step):
    """检查步骤是否已完成（通过输出文件判断）"""
    for out_path in step.get("output", {}).values():
        if isinstance(out_path, str) and out_path:
            expanded = expand_path(out_path)
            if Path(expanded).exists():
                return True
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


def scan_pending_tasks():
    """扫描所有待处理的任务（用于断点续跑）"""
    if not TASK_RECORDS_DIR.exists():
        return []

    pending = []
    for task_file in TASK_RECORDS_DIR.glob("*.json"):
        record = get_task_record(task_file)
        if not record:
            continue

        status = record.get("status", "unknown")
        if status in ["in_progress", "pending"]:
            # 检查是否有可执行的步骤
            next_step = get_next_pending_step(record)
            if next_step:
                pending.append({
                    "task_id": record.get("id"),
                    "task_name": record.get("name"),
                    "task_path": str(task_file),
                    "status": status,
                    "next_step": next_step
                })
            elif status == "in_progress":
                # in_progress 但没有可执行步骤，可能是等待中
                pending.append({
                    "task_id": record.get("id"),
                    "task_name": record.get("name"),
                    "task_path": str(task_file),
                    "status": "waiting",
                    "next_step": None
                })

    return pending


def main():
    # 如果没有参数，扫描所有待处理任务（用于断点续跑）
    if len(sys.argv) < 2:
        print("[扫描] 检查所有待处理任务...", flush=True)
        pending = scan_pending_tasks()
        if not pending:
            print("[完成] 没有待处理的任务", flush=True)
            sys.exit(0)

        print(f"[发现] {len(pending)} 个待处理任务:", flush=True)
        for p in pending:
            step_info = f"步骤 {p['next_step']['id']}: {p['next_step']['name']}" if p['next_step'] else "等待中"
            print(f"  - {p['task_id']} ({p['task_name']}) [{p['status']}] - {step_info}", flush=True)
        sys.exit(0)

    task_path = Path(sys.argv[1])
    check_only = "--check-only" in sys.argv

    record = get_task_record(task_path)
    if not record:
        sys.exit(1)

    task_id = record.get("id")
    task_name = record.get("name", task_id)

    if check_only:
        print(f"[检查] 任务 {task_id}，状态: {record.get('status')}", flush=True)
        print(f"[步骤] {len(record.get('steps', []))} 个", flush=True)
        print(f"[心跳] Agent: {record.get('heartbeatAgents', [])}", flush=True)
        sys.exit(0)

    print(f"[检查] 任务 {task_id} ({task_name})，状态: {record.get('status')}", flush=True)

    # 任务已完成
    if record.get("status") == "completed":
        print("[完成] 任务已全部完成", flush=True)
        sys.exit(0)

    # 初始化 dispatches 数组（如果不存在）
    if "dispatches" not in record:
        record["dispatches"] = []

    # 检查 in_progress 步骤是否实际完成
    updated = False
    for step in record.get("steps", []):
        if step.get("status") == "in_progress":
            if check_step_completed(step):
                step["status"] = "completed"
                step["completedAt"] = gmt8_now()
                record["updatedAt"] = gmt8_now()
                print(f"[完成] 步骤 {step['id']}: {step['name']}", flush=True)
                updated = True

                # 从 dispatches 中移除该步骤的待派发记录
                record["dispatches"] = [
                    d for d in record["dispatches"]
                    if d.get("stepId") != step["id"]
                ]

    # 找下一个待执行步骤
    next_step = get_next_pending_step(record)

    if not next_step:
        # 检查是否全部完成
        all_done = all(s.get("status") == "completed" for s in record.get("steps", []))
        if all_done:
            record["status"] = "completed"
            record["completedAt"] = gmt8_now()
            record["updatedAt"] = gmt8_now()
            print("[完成] 所有步骤执行完毕", flush=True)
            # 清理 dispatches
            record["dispatches"] = []
            updated = True
        else:
            print("[等待] 没有可执行的步骤（等待前置依赖）", flush=True)
    else:
        # 有可执行的步骤，添加到 dispatches 数组
        step_id = next_step["id"]
        step_name = next_step["name"]
        agent = next_step.get("agent", "")

        # 检查是否已经在 dispatches 中
        existing = any(d.get("stepId") == step_id for d in record["dispatches"])
        if not existing:
            dispatch_info = {
                "stepId": step_id,
                "stepName": step_name,
                "agent": agent,
                "task": next_step.get("task", f"执行步骤 {step_id}: {step_name}"),
                "input": next_step.get("input", {}),
                "output": next_step.get("output", {}),
                "addedAt": gmt8_now()
            }
            record["dispatches"].append(dispatch_info)
            print(f"[待派发] 步骤 {step_id}: {step_name}，Agent: {agent}", flush=True)
            updated = True

        # 更新当前步骤
        record["currentStep"] = step_id
        record["status"] = "in_progress"
        record["updatedAt"] = gmt8_now()

    if updated:
        save_task_record(task_path, record)

    # 输出 dispatches 信息供主Agent解析
    if record.get("dispatches"):
        print(f"\n[派发] 待执行步骤数: {len(record['dispatches'])}", flush=True)
        for d in record["dispatches"]:
            print(f"  - stepId={d['stepId']}, agent={d['agent']}, task={d['task'][:50]}...", flush=True)

    sys.exit(0)


if __name__ == "__main__":
    main()