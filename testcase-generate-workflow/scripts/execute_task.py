#!/usr/bin/env python3
"""
测试用例生成工作流 - 心跳检查脚本
检查任务状态，输出待执行的派发信息（包含绝对路径）
"""
import json
import sys
import os


def load_task_record(task_file: str) -> dict:
    """加载任务记录"""
    with open(task_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_step_by_id(task_record: dict, step_id: int) -> dict:
    """根据ID获取步骤"""
    for step in task_record["steps"]:
        if step["id"] == step_id:
            return step
    return None


def can_execute(step: dict, task_record: dict) -> bool:
    """检查步骤依赖是否满足"""
    if step["status"] != "pending":
        return False
    
    for dep_id in step.get("dependsOn", []):
        dep_step = get_step_by_id(task_record, dep_id)
        if dep_step is None or dep_step["status"] != "completed":
            return False
    return True


def get_pending_steps(task_record: dict) -> list:
    """获取所有可执行的pending步骤"""
    pending = []
    for step in task_record["steps"]:
        if can_execute(step, task_record):
            pending.append(step)
    return pending


def check_parallel_branches(pending_steps: list) -> list:
    """
    检查并行分支，返回需要派发的步骤
    分支1: 8,9,10 (atomic_capability → logic_testpoint → logic_testcase)
    分支2: 11,12 (interface_testpoint → interface_testcase)
    这两个分支在步骤7之后可以并行
    """
    if not pending_steps:
        return []
    
    if len(pending_steps) > 1:
        branch_1_steps = [s for s in pending_steps if s.get("branch") == 1]
        branch_2_steps = [s for s in pending_steps if s.get("branch") == 2]
        
        if branch_1_steps and branch_2_steps:
            return pending_steps
    
    return pending_steps


def format_dispatch_info(step: dict, task_record: dict) -> str:
    """格式化派发信息，包含绝对路径"""
    context = task_record["context"]
    
    dispatch = {
        "agentId": step["agent"],
        "stepId": step["id"],
        "stepName": step["name"],
        "skill": step["skill"],
        "task": step["task"],
        "inputFiles": step.get("inputFiles", []),
        "outputFiles": step.get("outputFiles", []),
        "workDir": context["workDir"],
        "context": context,
        "taskRecordPath": task_record.get("_filePath", "")
    }
    
    return json.dumps(dispatch, ensure_ascii=False)


def main():
    if len(sys.argv) < 2:
        print("[ERROR] 用法: python3 execute_task.py <任务记录文件路径>")
        sys.exit(1)
    
    task_file = sys.argv[1]
    
    if not os.path.exists(task_file):
        print(f"[ERROR] 任务记录文件不存在: {task_file}")
        sys.exit(1)
    
    # 加载任务记录
    task_record = load_task_record(task_file)
    task_record["_filePath"] = task_file
    
    # 检查是否已完成
    if task_record["status"] == "completed":
        print("[完成] 所有步骤执行完毕")
        print(f"工作目录: {task_record['context']['workDir']}")
        print(f"logic_testcase.json: {os.path.join(task_record['context']['workDir'], 'logic_testcase.json')}")
        print(f"interface_testcase.json: {os.path.join(task_record['context']['workDir'], 'interface_testcase.json')}")
        return
    
    # 获取可执行的步骤
    pending_steps = get_pending_steps(task_record)
    pending_steps = check_parallel_branches(pending_steps)
    
    if not pending_steps:
        in_progress = [s for s in task_record["steps"] if s["status"] == "in_progress"]
        if in_progress:
            print("[INFO] 等待进行中的步骤完成...")
            for step in in_progress:
                print(f"  - Step {step['id']}: {step['name']} ({step['agent']})")
        else:
            failed = [s for s in task_record["steps"] if s["status"] == "failed"]
            if failed:
                print("[WARNING] 以下步骤执行失败:")
                for step in failed:
                    print(f"  - Step {step['id']}: {step['name']}")
        return
    
    # 输出派发信息
    print("=== AGENT_DISPATCH ===")
    for step in pending_steps:
        dispatch_info = format_dispatch_info(step, task_record)
        print(dispatch_info)
    print("=== END_DISPATCH ===")
    
    # 标记为in_progress
    for step in pending_steps:
        step["status"] = "in_progress"
    
    # 保存更新后的任务记录
    with open(task_file, "w", encoding="utf-8") as f:
        save_record = {k: v for k, v in task_record.items() if not k.startswith("_")}
        json.dump(save_record, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()