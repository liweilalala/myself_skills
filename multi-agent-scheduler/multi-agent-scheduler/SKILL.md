---
name: multi-agent-scheduler
description: 多Agent任务调度框架。当需要创建、管理、或监控多Agent任务执行时使用此skill。核心功能：1) 初始化Agent列表；2) 创建任务并派发；3) 监控执行状态；4) 断点续跑。触发场景：初始化Agent列表、创建任务、执行任务、查看任务状态。
---

# Multi-Agent Scheduler

## 核心概念

- **任务记录 (Task Record)**：JSON文件，描述完整工作流的步骤、依赖、状态
- **主Agent**：当前执行此skill的Agent，负责调度和监控
- **子Agent**：通过 `sessions_spawn(runtime="subagent")` 启动，拥有独立session
- **心跳**：通过 `cron` 注册，每30秒触发任务检查

## 工作流程

```
[初始化] → [创建任务] → [派发执行] → [心跳监控] → [任务完成]
```

---

## Step 1: 初始化 Agent 列表

**触发时机**：
- 注册表不存在或过期（>24小时）
- 用户明确要求「初始化」

**执行**：
1. 调用 `openclaw agents list` 获取所有可用 agent
2. 扫描每个 agent 工作目录下的 `skills/` 文件夹，记录可用技能
3. 保存到 `references/agent-registry.json`

**Agent注册表格式**：
```json
{
  "version": "1.1",
  "updatedAt": "2026-05-06 10:01 GMT+8",
  "agents": [
    {
      "agentId": "scholar_assistant",
      "name": "学术助手",
      "workspace": "/home/admin/.openclaw/agents/scholar_assistant/workspace",
      "status": "available",
      "registeredAt": "2026-05-06 10:01 GMT+8",
      "skills": [
        {
          "skillId": "self-improvement-agent",
          "description": "持续改进智能体",
          "path": "/home/admin/.openclaw/agents/scholar_assistant/workspace/skills/self-improvement-agent"
        }
      ],
      "skillCount": 1
    }
  ],
  "totalCount": 1
}
```

**技能扫描逻辑**：
- 遍历 `~/.openclaw/agents/<agentId>/workspace/skills/` 目录
- 读取每个技能文件夹中的 `SKILL.md`，提取 `description` 字段
- 记录技能ID、描述、路径到注册表

---

## Step 2: 创建任务

**输入**：用户提供的任务描述（可以是自然语言或JSON）

**主Agent动作**：
1. 解析任务描述，识别涉及的 agent 和步骤
2. 生成标准任务记录 JSON（见 `references/task-record-schema.md`）
3. 保存到 `/home/admin/.openclaw/workspace/task_records/<task_id>.json`
4. 调用 `cron` 为每个涉及 agent 注册心跳

**任务记录示例**：
```json
{
  "id": "task_20260430_194700_0001",
  "name": "需求到测试用例工作流",
  "status": "in_progress",
  "currentStep": 1,
  "context": {
    "workspace": "/home/admin/.openclaw/workspace",
    "sourceDoc": "/home/admin/.openclaw/workspace/doc.md"
  },
  "steps": [
    {
      "id": 1,
      "name": "需求分析",
      "agent": "requirement_analyst",
      "skill": "testing-requirement-analysis",
      "status": "pending",
      "input": {"doc": "/home/admin/.openclaw/workspace/doc.md"},
      "output": {
        "ruleSplitAnalysis": "/home/admin/.openclaw/workspace/agents/requirement_analyst/rule_split_analysis.json",
        "usecaseWithRule": "/home/admin/.openclaw/workspace/agents/requirement_analyst/usecase_with_rule.json"
      }
    }
  ],
  "heartbeatAgents": ["requirement_analyst"]
}
```

---

## Step 3: 派发任务

**原则**：创建任务后立即启动第一个可执行的步骤

**执行**：
1. 读取任务记录，找到 `status=pending` 且依赖已满足的步骤
2. 调用 `sessions_spawn` 启动对应 agent：

```
sessions_spawn(
  runtime="subagent",
  agentId="<step.agent>",
  task="执行步骤：<step.name>\n任务记录：<task_record_path>\n输入：<step.input>\n输出：<step.output>",
  mode="run",
  runTimeoutSeconds=300
)
```

3. 更新步骤状态为 `in_progress`
4. 保存任务记录

---

## Step 4: 心跳监控

**心跳注册**（创建任务时）：
```bash
# 为每个 heartbeatAgent 注册 cron job
# 每 30 秒触发一次，执行 execute_task.py 检查状态
```

**心跳触发时**：
1. `execute_task.py` 读取任务记录
2. 检查当前步骤状态：
   - `completed`：更新 `currentStep` 为下一个 pending 步骤，启动对应 agent
   - `in_progress`：检查是否中断（超时或无心跳 >60s），如果中断则重新派发
   - `pending` 且依赖已满足：直接启动
   - 无待执行步骤：任务完成，移除心跳
3. 更新任务记录

---

## Step 5: 断点续跑

**触发**：主Agent重启、或心跳检测到执行中断

**逻辑**：
1. 读取任务记录
2. 遍历步骤，对每个 `status=in_progress` 的步骤检查：
   - 输出文件是否存在 → 标记为 `completed`
   - 超时无相应 → 重新派发
3. 对 `status=pending` 且依赖已满足的步骤 → 继续执行

---

## 执行脚本说明

### init_agents.py
- 调用 `agents_list` 获取 agent
- 保存到 `references/agent-registry.json`
- 覆盖式写入

### execute_task.py
- 读取任务记录
- 检查/更新每个步骤状态
- 启动待执行的 agent
- 更新任务记录

### register_heartbeat.py
- 为任务注册 cron job
- 每 30 秒调用一次 `execute_task.py`
- 任务完成后自动移除

---

## 路径约定

所有路径使用绝对路径：
- Workspace: `/home/admin/.openclaw/workspace`
- Task Records: `/home/admin/.openclaw/workspace/task_records/`
- Agent Workspaces: `/home/admin/.openclaw/agents/<agentId>/workspace/`
- Scripts: `/home/admin/.openclaw/workspace/skills/multi-agent-scheduler/scripts/`