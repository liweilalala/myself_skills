---
name: multi-agent-scheduler
description: 多Agent任务调度框架。当需要创建、管理、或监控多Agent任务执行时使用此skill。核心功能：1) 初始化Agent列表；2) 创建任务并派发；3) 监控执行状态；4) 断点续跑。触发场景：初始化Agent列表、创建任务、执行任务、查看任务状态。
---

# Multi-Agent Scheduler

## 核心概念

- **任务记录 (Task Record)**：JSON文件，描述完整工作流的步骤、依赖、状态
- **主Agent**：当前执行此skill的Agent，负责调度和监控
- **子Agent**：通过 `sessions_spawn(runtime="subagent")` 启动，拥有独立session
- **心跳**：通过 `cron` 注册，每30秒触发任务状态检查

## 工作流程

```
[初始化] → [创建任务] → [派发执行] → [心跳监控] → [任务完成]
```

**关键原则**：派发任务时，主Agent直接调用 `sessions_spawn` 工具启动子Agent，而不是依赖外部脚本。

---

## Step 1: 初始化 Agent 列表

**触发时机**：
- 注册表不存在或过期（>24小时）
- 用户明确要求「初始化」

**执行**：
```bash
python3 ~/.openclaw/workspace/skills/multi-agent-scheduler/scripts/init_agents.py
```

**Agent注册表**保存在 `references/agent-registry.json`

---

## Step 2: 创建任务

**触发时机**：用户要求「创建任务」并提供任务描述

**输入**：用户提供的任务描述（自然语言或JSON）

**主Agent动作**：
1. 解析任务描述，识别涉及的 agent 和步骤
2. 生成标准任务记录 JSON
3. 保存到 `~/.openclaw/workspace/task_records/<task_id>.json`

**任务记录格式**：
```json
{
  "id": "task_20260506_111500_0001",
  "name": "多步骤数据处理工作流",
  "status": "pending",
  "currentStep": 0,
  "context": {
    "workspace": "/home/admin/.openclaw/workspace"
  },
  "steps": [
    {
      "id": 1,
      "name": "数据清洗",
      "agent": "data_agent",
      "skill": "data-processing",
      "dependsOn": [],
      "status": "pending",
      "input": {"source": "/data/raw.csv"},
      "output": {"cleaned": "/data/cleaned.csv"},
      "task": "执行数据清洗步骤..."
    },
    {
      "id": 2,
      "name": "数据分析",
      "agent": "analysis_agent",
      "skill": "analytics",
      "dependsOn": [1],
      "status": "pending",
      "input": {"source": "/data/cleaned.csv"},
      "output": {"report": "/data/report.json"},
      "task": "执行数据分析步骤..."
    }
  ],
  "heartbeatAgents": ["data_agent", "analysis_agent"]
}
```

---

## Step 3: 派发任务

**执行方式**：主Agent直接调用 `sessions_spawn` 工具派发任务

**步骤**：
1. 读取任务记录
2. 找到 `status=pending` 且依赖已满足的步骤
3. 直接调用 `sessions_spawn` 启动对应 agent：

```
sessions_spawn(
  task="<step.task>",
  runtime="subagent",
  agentId="<step.agent>",
  runTimeoutSeconds=300,
  attachments=[
    {"name": "task_record.json", "content": "<task_record_json>"}
  ]
)
```

4. 更新步骤状态为 `in_progress`
5. 保存任务记录

**示例派发**：
```
sessions_spawn(
  task="执行数据清洗步骤。输入文件：/data/raw.csv，输出文件：/data/cleaned.csv",
  runtime="subagent",
  agentId="data_agent",
  runTimeoutSeconds=300
)
```

---

## Step 4: 心跳监控

**心跳触发**：每30秒由cron调用 `execute_task.py` 检查状态

**心跳逻辑** (`execute_task.py`)：
1. 读取任务记录
2. 检查 `in_progress` 步骤是否完成（输出文件存在）
3. 找到下一个可执行的 pending 步骤
4. **输出派发信息**（JSON格式），由主Agent解析

**派发信息格式**：
```
=== AGENT_DISPATCH ===
{"agentId": "data_agent", "task": "执行数据清洗...", "stepId": 1, ...}
=== END_DISPATCH ===
```

**主Agent收到心跳后的动作**：
1. 检查派发信息
2. 如果有待执行步骤 → 调用 `sessions_spawn` 派发
3. 如果所有步骤完成 → 更新任务状态为 `completed`

---

## Step 5: 断点续跑

**触发**：主Agent重启后检查未完成任务

**逻辑**：
1. 扫描 `~/.openclaw/workspace/task_records/` 下的任务记录
2. 对 `status=in_progress` 的步骤：检查输出文件
   - 存在 → 标记为 `completed`
   - 超时 → 重新派发
3. 对 `status=pending` 且依赖已满足的步骤 → 继续派发

---

## 执行脚本说明

| 脚本 | 功能 |
|------|------|
| `init_agents.py` | 初始化Agent注册表 |
| `create_task.py` | 创建任务记录 |
| `execute_task.py` | 心跳检查，输出派发信息 |
| `register_heartbeat.py` | 注册cron心跳任务 |

---

## 路径约定

| 用途 | 路径 |
|------|------|
| Workspace | `~/.openclaw/workspace` |
| Task Records | `~/.openclaw/workspace/task_records/` |
| Agent Workspaces | `~/.openclaw/agents/<agentId>/workspace/` |
| Scripts | `~/.openclaw/workspace/skills/multi-agent-scheduler/scripts/` |

---

## 完整示例

### 1. 初始化Agent列表
```
python3 ~/.openclaw/workspace/skills/multi-agent-scheduler/scripts/init_agents.py
```

### 2. 创建任务
用户说：「创建一个数据处理任务，包含数据清洗和数据分析两个步骤」

主Agent执行：
- 调用 `create_task.py` 或直接创建任务记录 JSON
- 保存到 `~/.openclaw/workspace/task_records/task_xxx.json`

### 3. 派发第一个步骤
主Agent直接调用 `sessions_spawn` 启动 `data_agent`

### 4. 心跳监控
注册cron job：
```
cron(action=add, job={
  "name": "heartbeat_<task_id>",
  "schedule": {"kind": "every", "everyMs": 30000},
  "payload": {"kind": "agentTurn", "message": "python3 ~/.openclaw/workspace/skills/multi-agent-scheduler/scripts/execute_task.py ~/.openclaw/workspace/task_records/<task_id>.json"},
  "sessionTarget": "isolated"
})
```

### 5. 任务完成
所有步骤完成后，`execute_task.py` 输出 `[完成] 所有步骤执行完毕`
