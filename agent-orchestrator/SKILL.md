---
name: agent-orchestrator
description: 多Agent任务调度与监控。当需要将任务分配给拥有独立工作目录的子Agent执行，并定时监控执行状态、获取工作目录、任务日志、输出文件时使用此skill。
---

# Agent Orchestrator

## 概述

此skill用于主Agent调度子Agent执行任务，并持续监控任务状态、获取执行结果。

## 核心概念

- **主Agent**：当前执行此skill的Agent，负责调度和监控
- **子Agent**：拥有独立工作目录的Agent（如 `scholar_assistant`），通过 `agentId` 标识
- **任务**：发送给子Agent执行的具体内容
- **会话**：每个任务执行对应一个session，可通过 `sessions_list` 和 `sessions_history` 查询

## 工作流程

### 1. 任务调度

使用 `sessions_spawn` 启动子Agent任务：

```
runtime: "subagent"
agentId: <目标agentId>
task: <任务内容>
mode: "run"  (一次性任务)
```

示例：
- agentId: `scholar_assistant`
- task: "帮我调研Transformer架构在CV领域的发展现状"

### 2. 状态监控

调度后使用以下工具监控任务：

- **sessions_list** (`kinds=["subagent"]`, `activeMinutes=<N>`): 列出最近活跃的子Agent会话
- **sessions_history** (`sessionKey`, `limit=20`): 查看任务执行历史和输出
- **subagents** (`action="list"`): 查看当前运行中的子任务

监控频率建议：每10-30秒检查一次（根据任务预计耗时调整）

### 3. 获取执行产物

子Agent的工作目录结构：

```
~/.openclaw/agents/<agentId>/workspace/
├── AGENTS.md
├── SOUL.md
├── USER.md
├── memory/
│   └── YYYY-MM-DD.md  (每日执行日志)
└── [任务产生的文件]
```

获取文件列表：
```bash
ls -la ~/.openclaw/agents/<agentId>/workspace/
```

读取执行日志：
```bash
cat ~/.openclaw/agents/<agentId>/workspace/memory/YYYY-MM-DD.md
```

### 4. 执行状态判断

根据 `sessions_list` 的 `activeMinutes` 判断：
- `activeMinutes < 1`：任务刚启动或正在运行
- `activeMinutes` 持续增长：任务执行中
- 会话消失或 `activeMinutes` 很长时间未更新：任务可能已完成或卡住

## SKILL.md 使用方式

此skill被触发后，AI按以下步骤执行：

1. **解析输入**：确认 `agentId` 和 `task`
2. **启动任务**：调用 `sessions_spawn` 派发任务
3. **建立监控循环**：定期检查 `sessions_list` 和 `subagents`
4. **反馈状态**：向用户报告任务启动、进度、完成情况
5. **返回结果**：任务完成后，返回工作目录路径、日志摘要、输出文件列表

## scripts/

### monitor_agent.py

定时监控子Agent任务状态脚本：

```python
#!/usr/bin/env python3
"""
monitor_agent.py - 监控指定Agent的活跃会话状态
用法: python3 monitor_agent.py <agentId>
"""
import sys
import json
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("用法: monitor_agent.py <agentId>")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    workspace = Path.home() / ".openclaw" / "agents" / agent_id / "workspace"
    
    if not workspace.exists():
        print(f"[错误] Agent工作目录不存在: {workspace}")
        sys.exit(1)
    
    # 读取今日日志
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = workspace / "memory" / f"{today}.md"
    
    if log_file.exists():
        print(f"=== 今日执行日志 ({today}) ===")
        print(log_file.read_text())
    else:
        print("[信息] 今日暂无执行日志")
    
    # 列出工作目录文件
    print(f"\n=== 工作目录文件 ===")
    for f in sorted(workspace.iterdir()):
        print(f"  {f.name}")

if __name__ == "__main__":
    main()
```

## references/

### agent-api.md

子Agent API参考，包含sessions工具的使用说明和返回值格式。
