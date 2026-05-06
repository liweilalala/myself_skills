#!/usr/bin/env python3
"""
注册测试用例生成工作流的心跳任务
"""
import sys
import json


def main():
    if len(sys.argv) < 2:
        print("用法: python3 register_heartbeat.py <任务ID>")
        sys.exit(1)
    
    task_id = sys.argv[1]
    
    # 构建cron任务配置
    cron_config = {
        "name": f"heartbeat_{task_id}",
        "schedule": {
            "kind": "every",
            "everyMs": 90000  # 每90秒
        },
        "payload": {
            "kind": "agentTurn",
            "message": f"python3 ~/.openclaw/workspace/skills/testcase-generate-workflow/scripts/execute_task.py ~/.openclaw/workspace/task_records/{task_id}.json"
        },
        "sessionTarget": "isolated",
        "enabled": True
    }
    
    print("心跳任务配置:")
    print(json.dumps(cron_config, ensure_ascii=False, indent=2))
    print()
    print("请使用以下命令注册心跳:")
    print(f"cron(action='add', job={json.dumps(cron_config, ensure_ascii=False)})")


if __name__ == "__main__":
    main()
