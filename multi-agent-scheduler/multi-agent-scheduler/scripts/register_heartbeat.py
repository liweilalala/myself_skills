#!/usr/bin/env python3
"""
register_heartbeat.py - 注册心跳检测
用法: python3 register_heartbeat.py <task_record_json_path>
说明: 为任务涉及的 agent 注册 cron job，每 30 秒检查任务状态
"""

import json
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).parent.parent.resolve()
SCRIPT_PATH = f"{SKILL_DIR}/scripts/execute_task.py"
WORKSPACE = Path.home() / ".openclaw" / "workspace"


def get_task_record(task_path):
    """读取任务记录"""
    try:
        with open(task_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[错误] 读取任务记录失败: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print("用法: python3 register_heartbeat.py <task_record_json_path>")
        sys.exit(1)

    task_path = Path(sys.argv[1]).resolve()
    record = get_task_record(task_path)
    if not record:
        sys.exit(1)

    task_id = record.get("id", "unknown")
    heartbeat_agents = record.get("heartbeatAgents", [])

    if not heartbeat_agents:
        print("[信息] 没有需要心跳检测的 Agent")
        sys.exit(0)

    print(f"[任务] {task_id}")
    print(f"[Agent] {heartbeat_agents}")
    print(f"\n请使用 cron tool 添加心跳 job：")
    print(f"- 名称: heartbeat_{task_id}")
    print(f"- 间隔: every 30 秒")
    print(f"- 执行: python3 {SCRIPT_PATH} {task_path}")
    print(f"\nCron 配置示例：")
    print(f"""{{
  "name": "heartbeat_{task_id}",
  "schedule": {{"kind": "every", "everyMs": 30000}},
  "payload": {{"kind": "agentTurn", "message": "python3 {SCRIPT_PATH} {task_path}"}},
  "enabled": true
}}""")

    sys.exit(0)


if __name__ == "__main__":
    main()