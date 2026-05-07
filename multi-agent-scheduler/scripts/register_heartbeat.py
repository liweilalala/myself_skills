#!/usr/bin/env python3
"""
register_heartbeat.py - 注册心跳监控
用法: python3 register_heartbeat.py <task_record_json_path>

此脚本通过 OpenClaw cron tool 注册心跳任务（由主Agent调用）。
注册成功后，心跳每30秒触发 execute_task.py 检查任务状态。
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

SKILL_DIR = Path(__file__).parent.parent.resolve()
SCRIPT_PATH = SKILL_DIR / "scripts" / "execute_task.py"
WORKSPACE = Path.home() / ".openclaw" / "workspace"
TASK_RECORDS_DIR = WORKSPACE / "task_records"


def gmt8_now():
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M GMT+8")


def get_task_record(path):
    """加载任务记录"""
    if not path.exists():
        print(f"[错误] 任务记录不存在: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[错误] 读取任务记录失败: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print("用法: python3 register_heartbeat.py <task_record_json_path>")
        sys.exit(1)

    task_path = Path(sys.argv[1])
    record = get_task_record(task_path)
    if not record:
        sys.exit(1)

    task_id = record.get("id")
    task_name = record.get("name", task_id)

    print(f"[注册] 任务: {task_name} ({task_id})")
    print(f"[信息] 心跳间隔: 30秒")
    print(f"[脚本] {SCRIPT_PATH}")
    print(f"[任务] {task_path}")

    # 输出 JSON 格式的配置信息，供主Agent使用 cron tool 注册
    cron_config = {
        "name": f"heartbeat_{task_id}",
        "everyMs": 30000,
        "script_path": str(SCRIPT_PATH),
        "task_path": str(task_path),
        "task_name": task_name
    }

    print(f"\n=== CRON_CONFIG ===")
    print(json.dumps(cron_config, ensure_ascii=False, indent=2))
    print(f"=== END_CRON_CONFIG ===")

    print(f"\n[完成] 请使用 cron tool (action=add) 注册心跳任务")
    print(f"提示: 主Agent应读取 === CRON_CONFIG === 块并调用 cron(tool)")

    sys.exit(0)


if __name__ == "__main__":
    main()