#!/usr/bin/env python3
"""
注册测试用例生成工作流的心跳任务
生成配置供主Agent调用cron工具注册
"""
import sys
import json
import os

def main():
    if len(sys.argv) < 2:
        print("用法: python3 register_heartbeat.py <任务ID>")
        sys.exit(1)
    
    task_id = sys.argv[1]
    task_record_path = f"~/.openclaw/workspace/task_records/{task_id}/task_record.json"
    
    # 生成cron任务配置（供主Agent调用cron工具）
    cron_config = {
        "name": f"heartbeat_{task_id}",
        "schedule": {
            "kind": "every",
            "everyMs": 90000  # 每90秒
        },
        "payload": {
            "kind": "agentTurn",
            "message": f"python3 ~/.openclaw/workspace/skills/testcase-generate-workflow/scripts/execute_task.py {task_record_path}"
        },
        "sessionTarget": "isolated",
        "enabled": True
    }
    
    print("=== CRON_JOB_CONFIG ===")
    print(json.dumps(cron_config, ensure_ascii=False, indent=2))
    print("=== END_CRON_CONFIG ===")
    print()
    print("请使用以下命令注册心跳:")
    print(f"cron(action='add', job={json.dumps(cron_config, ensure_ascii=False)})")


if __name__ == "__main__":
    main()
