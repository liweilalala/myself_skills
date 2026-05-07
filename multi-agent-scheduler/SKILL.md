---
name: multi-agent-scheduler
description: 多Agent任务调度框架。当需要创建、管理、或监控多Agent任务执行时使用此skill。核心功能：1) 初始化Agent列表；2) 创建任务并派发；3) 监控执行状态；4) 断点续跑。触发场景：初始化Agent列表、创建任务、执行任务、查看任务状态。
---

# Multi-Agent Scheduler

## 核心概念

- **任务记录 (Task Record)**：JSON文件，描述完整工作流的步骤、依赖、状态
- **主Agent**：当前执行此skill的Agent，负责调度和监控
- **子Agent**：通过 `sessions_spawn(runtime="subagent")` 启动，拥有独立session
- **心跳**：通过 `cron` 注册，每30秒触发 `execute_task.py` 检查任务状态
- **dispatches数组**：任务记录中的待派发步骤队列，主Agent心跳时读取并执行派发

## 工作流程

```
[初始化] → [创建任务] → [派发执行] → [心跳监控] → [任务完成]
              ↑
         [断点续跑] ←── 主Agent重启时自动恢复
```

**关键原则**：
- 派发任务时，主Agent调用 `sessions_spawn` 工具启动子Agent
- 心跳脚本 (`execute_task.py`) 只更新状态，不直接派发
- 派发信息通过任务记录的 `dispatches` 数组传递

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

**输入**：用户提供的任务描述（JSON格式）

**主Agent动作**：
1. 解析任务描述，识别涉及的 agent 和步骤
2. 验证必填字段（name, steps, 每个step的 agent/task）
3. 生成标准任务记录 JSON
4. 保存到 `~/.openclaw/workspace/task_records/<task_id>.json`

**任务记录格式**：
```json
{
  "id": "task_20260507_120000_0001",
  "name": "多步骤数据处理工作流",
  "status": "pending",
  "currentStep": 0,
  "dispatches": [],
  "context": {
    "workspace": "/home/admin/.openclaw/workspace"
  },
  "steps": [
    {
      "id": 1,
      "name": "数据清洗",
      "agent": "scholar_assistant",
      "skill": "data-processing",
      "dependsOn": [],
      "status": "pending",
      "input": {"source": "/data/raw.csv"},
      "output": {"cleaned": "/data/cleaned.csv"},
      "task": "执行数据清洗步骤，从 raw.csv 读取数据，清洗后保存到 cleaned.csv"
    }
  ],
  "heartbeatAgents": ["scholar_assistant"]
}
```

---

## Step 3: 派发任务

**执行方式**：主Agent调用 `sessions_spawn` 工具派发任务

**触发时机**：
1. 用户手动触发
2. 主Agent心跳时读取 `dispatches` 数组

**步骤**：
1. 读取任务记录
2. 检查 `dispatches` 数组是否有待派发步骤
3. 调用 `sessions_spawn` 启动对应 agent：

```python
sessions_spawn(
  task="<dispatch.task>",
  runtime="subagent",
  agentId="<dispatch.agent>",
  runTimeoutSeconds=300,
  attachments=[
    {"name": "task_record.json", "content": "<task_record_json>"}
  ]
)
```

4. 更新步骤状态为 `in_progress`
5. **不要**从 `dispatches` 立即移除（等步骤实际完成后才移除）

---

## Step 4: 心跳监控

**心跳触发**：每30秒由cron调用 `execute_task.py`

**心跳逻辑** (`execute_task.py`)：
1. 读取任务记录
2. 检查 `in_progress` 步骤是否完成（输出文件存在）
3. 找到下一个可执行的 `pending` 步骤
4. 将派发信息**追加**到 `dispatches` 数组
5. 更新任务状态为 `in_progress`

**主Agent心跳检查流程**：
1. 调用 `execute_task.py` 或读取任务记录
2. 检查 `dispatches` 数组
3. 对每个待派发步骤调用 `sessions_spawn`
4. 步骤完成后，从 `dispatches` 移除

---

## Step 5: 断点续跑

**触发**：主Agent重启后检查未完成任务

**逻辑**：
1. 扫描 `~/.openclaw/workspace/task_records/` 下的任务记录
2. 对 `status=in_progress` 的步骤：检查输出文件
   - 存在 → 标记为 `completed`
   - 不存在但超时 → 可选择重新派发
3. 对 `status=pending` 且依赖已满足的步骤 → 继续派发

**命令**：
```bash
# 扫描所有待处理任务
python3 ~/.openclaw/workspace/skills/multi-agent-scheduler/scripts/execute_task.py

# 检查指定任务
python3 ~/.openclaw/workspace/skills/multi-agent-scheduler/scripts/execute_task.py <task_path> --check-only
```

---

## 执行脚本说明

| 脚本 | 功能 |
|------|------|
| `init_agents.py` | 初始化Agent注册表 |
| `create_task.py` | 创建任务记录（验证必填字段） |
| `execute_task.py` | 心跳检查，更新 dispatches 数组 |
| `register_heartbeat.py` | 输出 cron 配置信息（供主Agent使用 cron tool） |

---

## 路径约定

| 用途 | 路径 |
|------|------|
| Workspace | `~/.openclaw/workspace` |
| Task Records | `~/.openclaw/workspace/task_records/` |
| Agent Workspaces | `~/.openclaw/agents/<agentId>/workspace/` |
| Scripts | `~/.openclaw/workspace/skills/multi-agent-scheduler/scripts/` |
| Registry | `~/.openclaw/workspace/skills/multi-agent-scheduler/references/agent-registry.json` |

---

## 完整示例

### 1. 初始化Agent列表
```bash
python3 ~/.openclaw/workspace/skills/multi-agent-scheduler/scripts/init_agents.py
```

### 2. 创建任务
用户说：「创建一个数据处理任务，包含数据清洗和数据分析两个步骤」

主Agent执行：
- 调用 `create_task.py` 或直接创建任务记录 JSON
- 保存到 `~/.openclaw/workspace/task_records/task_xxx.json`

### 3. 派发第一个步骤
主Agent直接调用 `sessions_spawn` 启动 `scholar_assistant`

### 4. 注册心跳监控
使用 cron tool 注册：
```python
cron(action=add, job={
  "name": "heartbeat_<task_id>",
  "schedule": {"kind": "every", "everyMs": 30000},
  "payload": {"kind": "agentTurn", "message": "python3 ~/.openclaw/workspace/skills/multi-agent-scheduler/scripts/execute_task.py <task_path>"},
  "sessionTarget": "isolated"
})
```

### 5. 任务完成
所有步骤完成后，`execute_task.py` 更新状态为 `completed`

---

## 修复记录 (2026-05-07)

1. **init_agents.py**: 简化代码，修复 workspace 解析逻辑
2. **execute_task.py**: 重构派发机制，改用 `dispatches` 数组替代直接输出
3. **register_heartbeat.py**: 改用 JSON 格式输出配置，供主Agent使用 cron tool
4. **create_task.py**: 添加必填字段验证，确保 `task` 字段存在
5. **SKILL.md**: 同步更新文档，反映实际实现