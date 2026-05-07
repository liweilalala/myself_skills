#!/usr/bin/env python3
"""
spawn_and_track - 测试用例生成工作流的子任务派发封装

整合了：
1. trace-query 查询相似成功任务 + 失败模式
2. task-coordinator init 初始化追踪
3. sessions_spawn 派发子Agent
4. 返回 task_id 供后续 complete/fail/timeout 使用

用法（通常由主Agent在会话中调用，不是命令行）：
"""

import argparse
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

TRACE_QUERY = "~/.openclaw/workspace/skills/trace-query/scripts/query_api.py"
TRACKER = "~/.openclaw/workspace/skills/task-coordinator/scripts/task_tracker.py"


def query_similar(goal: str, k: int = 3):
    """查询相似成功任务"""
    script = os.path.expanduser(TRACE_QUERY)
    if not os.path.exists(script):
        return []
    try:
        result = subprocess.run(
            ["python3", script, "similar", "--goal", goal, "--k", str(k), "--status", "completed"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return []


def query_failures(step_type: str = ""):
    """查询失败模式"""
    script = os.path.expanduser(TRACE_QUERY)
    if not os.path.exists(script):
        return {}
    try:
        cmd = ["python3", script, "failures"]
        if step_type:
            cmd += ["--step-type", step_type]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return {}


def init_tracker(task_id: str, goal: str, agent: str, steps: str = "") -> bool:
    """初始化任务追踪"""
    script = os.path.expanduser(TRACKER)
    cmd = ["python3", script, "init", task_id, goal, agent]
    if steps:
        cmd += ["--steps", steps]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception:
        return False


def complete_tracker(task_id: str, output: str = "", duration_ms: int = 0):
    """标记任务完成"""
    script = os.path.expanduser(TRACKER)
    cmd = ["python3", script, "complete", task_id]
    if output:
        cmd += ["--output", output]
    if duration_ms > 0:
        cmd += ["--duration", str(duration_ms)]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except Exception:
        pass


def checkpoint_tracker(task_id: str, step: str, status: str, note: str = ""):
    """记录检查点"""
    script = os.path.expanduser(TRACKER)
    cmd = ["python3", script, "checkpoint", task_id, step, status]
    if note:
        cmd += ["--note", note]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except Exception:
        pass


def fail_tracker(task_id: str, reason: str, last_step: str = "", duration_ms: int = 0):
    """标记任务失败"""
    script = os.path.expanduser(TRACKER)
    cmd = ["python3", script, "fail", task_id, reason]
    if last_step:
        cmd += ["--last-step", last_step]
    if duration_ms > 0:
        cmd += ["--duration", str(duration_ms)]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except Exception:
        pass


def timeout_tracker(task_id: str, last_step: str = "", duration_ms: int = 0):
    """标记任务超时"""
    script = os.path.expanduser(TRACKER)
    cmd = ["python3", script, "timeout", task_id]
    if last_step:
        cmd += ["--last-step", last_step]
    if duration_ms > 0:
        cmd += ["--duration", str(duration_ms)]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except Exception:
        pass


def build_context_prompt(goal: str, similar: list, failures: dict) -> str:
    """构建包含历史经验的上下文 prompt"""
    lines = []
    if similar:
        lines.append("【参考相似成功任务】")
        for t in similar[:3]:
            lines.append(f"  - {t.get('task_id')}: {t.get('goal', 'N/A')}")
            if t.get('result'):
                lines.append(f"    结果：{t['result'][:200]}")
        lines.append("")
    if failures and failures.get("patterns"):
        lines.append("【常见失败模式】")
        for p in failures["patterns"][:3]:
            lines.append(f"  - {p.get('pattern', 'N/A')}: {p.get('count', 0)}次")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="spawn_and_track 封装脚本")
    parser.add_argument("--task-id", help="任务ID，默认自动生成")
    parser.add_argument("--goal", required=True, help="任务目标描述")
    parser.add_argument("--agent", required=True, help="Agent ID")
    parser.add_argument("--steps", default="", help="步骤列表，逗号分隔")
    parser.add_argument("--step-type", default="", help="trace-query step类型")
    parser.add_argument("--similar-k", type=int, default=3, help="查询相似任务数量")
    parser.add_argument("--no-trace", action="store_true", help="跳过trace-query查询")
    args = parser.parse_args()

    # 生成 task_id
    task_id = args.task_id
    if not task_id:
        step_tag = args.goal[:20].replace(" ", "_").replace("/", "-")
        task_id = f"task-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{step_tag}"

    print(f"task_id: {task_id}", file=sys.stderr)

    # Step 0: trace-query（除非跳过）
    similar = []
    failures = {}
    context = ""
    if not args.no_trace:
        similar = query_similar(args.goal, k=args.similar_k)
        failures = query_failures(args.step_type)
        context = build_context_prompt(args.goal, similar, failures)
        if context:
            print(f"【历史经验上下文】\n{context}", file=sys.stderr)

    # Step 1: init tracker
    ok = init_tracker(task_id, args.goal, args.agent, args.steps)
    if not ok:
        print("WARNING: task-tracker init 失败", file=sys.stderr)

    # 输出 JSON 供主Agent解析
    output = {
        "task_id": task_id,
        "goal": args.goal,
        "agent": args.agent,
        "steps": args.steps.split(",") if args.steps else [],
        "similar_count": len(similar),
        "failures_count": len(failures.get("patterns", [])) if failures else 0,
        "context": context,
        "tracker_init_ok": ok
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()