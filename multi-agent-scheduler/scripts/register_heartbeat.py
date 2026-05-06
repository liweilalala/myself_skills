#!/usr/bin/env python3
"""
register_heartbeat.py - 通过 OpenClaw cron 注册心跳监控
用法: python3 register_heartbeat.py <task_record_json_path>
"""

import json
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime, timezone


SKILL_DIR = Path(__file__).parent.parent.resolve()
SCRIPT_PATH = SKILL_DIR / "scripts" / "execute_task.py"
WORKSPACE = Path.home() / ".openclaw" / "workspace"
TASK_RECORDS_DIR = WORKSPACE / "task_records"


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


def get_openclaw_cmd():
    """查找 openclaw 命令"""
    cmd = shutil.which("openclaw")
    if cmd:
        return cmd
    # Windows 变体
    for name in ["openclaw.exe", "openclaw.cmd", "openclaw.bat"]:
        cmd = shutil.which(name)
        if cmd:
            return cmd
    return "openclaw"


def register_cron_job(name, task_path, interval_ms=30000):
    """通过 openclaw cron add 注册心跳任务"""
    openclaw = get_openclaw_cmd()
    
    # 构建 cron job 配置
    job_name = f"heartbeat_{name}"
    
    # 使用 agentTurn 模式，定时执行 execute_task.py
    message = f"python3 {SCRIPT_PATH} {task_path}"
    
    # 调用 openclaw cron add
    cmd = [
        openclaw, "cron", "add",
        "--name", job_name,
        "--every", str(interval_ms),
        "--message", message
    ]
    
    print(f"[注册] 执行命令: {' '.join(cmd)}", flush=True)
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        shell=False
    )
    
    if result.returncode == 0:
        print(f"[成功] 心跳任务已注册: {job_name}", flush=True)
        print(result.stdout, flush=True)
        return True
    else:
        print(f"[失败] 注册心跳任务失败", flush=True)
        print(f"stdout: {result.stdout}", flush=True)
        print(f"stderr: {result.stderr}", flush=True)
        return False


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
    
    print(f"[注册] 任务: {task_name} ({task_id})", flush=True)
    print(f"[信息] 使用 OpenClaw cron 定时任务（每30秒心跳检查）", flush=True)

    # 注册心跳 cron job
    success = register_cron_job(task_id, task_path)
    
    if success:
        print(f"\n[完成] 心跳监控已启动", flush=True)
        print(f"提示: 使用 'openclaw cron list' 查看所有定时任务", flush=True)
        print(f"      使用 'openclaw cron rm <job_id>' 停止心跳监控", flush=True)
    else:
        print(f"\n[错误] 心跳监控注册失败，请检查 openclaw cron 配置", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()