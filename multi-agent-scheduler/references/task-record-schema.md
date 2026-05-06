# Task Record Schema

任务记录完整JSON格式说明。

## 完整结构

```json
{
  "id": "task_20260430_192600_001",
  "name": "需求到测试用例完整工作流",
  "version": "1.0",
  "createdAt": "2026-04-30T19:26:00+08:00",
  "updatedAt": "2026-04-30T19:26:00+08:00",
  "status": "in_progress",
  "currentStep": 1,
  "context": {
    "sourceDoc": "doc.md",
    "workspace": "/home/admin/.openclaw/workspace"
  },
  "steps": [
    {
      "id": 1,
      "name": "需求分析",
      "agent": "requirement_analyst",
      "skill": "testing-requirement-analysis",
      "status": "pending",
      "input": {
        "doc": "/home/admin/.openclaw/workspace/doc.md",
        "description": "待分析的需求文档"
      },
      "output": {
        "ruleSplitAnalysis": "/home/admin/.openclaw/agents/requirement_analyst/workspace/task_YYYYMMDD_HHMMSS_XXXX/rule_split_analysis.json",
        "usecaseWithRule": "/home/admin/.openclaw/agents/requirement_analyst/workspace/task_YYYYMMDD_HHMMSS_XXXX/usecase_with_rule.json"
      },
      "watchFiles": [
        "/home/admin/.openclaw/agents/requirement_analyst/workspace/task_YYYYMMDD_HHMMSS_XXXX/rule_split_analysis.json",
        "/home/admin/.openclaw/agents/requirement_analyst/workspace/task_YYYYMMDD_HHMMSS_XXXX/usecase_with_rule.json"
      ],
      "completedAt": null,
      "notes": null
    },
    {
      "id": 2,
      "name": "特性原子能力生成逻辑测试点",
      "agent": "test_designer",
      "skill": "atomic-capability-with-ibo-extraction",
      "dependsOn": [1],
      "status": "pending",
      "input": {
        "doc": "/home/admin/.openclaw/workspace/doc.md",
        "ruleSplitAnalysis": "/home/admin/.openclaw/agents/requirement_analyst/workspace/task_YYYYMMDD_HHMMSS_XXXX/rule_split_analysis.json"
      },
      "output": {
        "atomicCapability": "/home/admin/.openclaw/agents/test_designer/workspace/atomic-capability.json"
      },
      "completedAt": null,
      "notes": null
    },
    {
      "id": 3,
      "name": "生成逻辑测试点",
      "agent": "test_designer",
      "skill": "feature-tree-testpoint-generation",
      "dependsOn": [2],
      "status": "pending",
      "input": {
        "atomicCapability": "/home/admin/.openclaw/agents/test_designer/workspace/atomic-capability.json"
      },
      "output": {
        "logicTestpoint": "/home/admin/.openclaw/agents/test_designer/workspace/logic_testpoint.json"
      },
      "completedAt": null,
      "notes": null
    },
    {
      "id": 4,
      "name": "实现原子能力生成接口测试点",
      "agent": "test_designer",
      "skill": "implement-testpoint-generation-workflow",
      "dependsOn": [1],
      "status": "pending",
      "input": {
        "doc": "/home/admin/.openclaw/workspace/doc.md"
      },
      "output": {
        "interfaceTestpoint": "/home/admin/.openclaw/agents/test_designer/workspace/interface_testpoint.json"
      },
      "completedAt": null,
      "notes": null
    }
  ],
  "heartbeatAgents": ["requirement_analyst", "test_designer"],
  "completionCriteria": {
    "finalOutputs": [
      "rule_split_analysis.json",
      "usecase_with_rule.json",
      "atomic-capability.json",
      "logic_testpoint.json",
      "interface_testpoint.json"
    ]
  }
}
```

## 字段说明

### 顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 任务唯一标识，格式：`task_YYYYMMDD_HHMMSS_XXXX` |
| `name` | string | 任务名称 |
| `version` | string | 格式版本，当前为 `1.0` |
| `createdAt` | string | ISO 8601 时间戳 |
| `updatedAt` | string | ISO 8601 时间戳 |
| `status` | string | 任务状态：`pending`/`in_progress`/`completed`/`failed` |
| `currentStep` | integer | 当前应执行的步骤编号 |
| `context` | object | 全局上下文，包含源文档和工作区路径 |
| `steps` | array | 步骤列表 |
| `heartbeatAgents` | array | 需要心跳检测的Agent列表 |
| `completionCriteria` | object | 完成标准 |

### Step对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | integer | 步骤编号 |
| `name` | string | 步骤名称 |
| `agent` | string | 负责执行的Agent ID |
| `skill` | string | 使用的skill名称 |
| `dependsOn` | array | 依赖的步骤ID列表 |
| `status` | string | 步骤状态：`pending`/`in_progress`/`completed`/`failed`/`waiting` |
| `input` | object | 输入文件路径映射 |
| `output` | object | 输出文件路径映射 |
| `watchFiles` | array | 需要监控的文件路径（用于判断完成） |
| `completedAt` | string | 完成时间戳 |
| `notes` | string | 备注信息 |

### 状态流转

```
pending → in_progress → completed
                     ↘ failed
                     ↘ waiting (等待依赖)
```

- `status: "waiting"` 表示等待前置步骤完成
- `currentStep` 自动更新为第一个 `pending` 且依赖已满足的步骤

## 路径约定

所有路径必须使用绝对路径：
- Workspace: `/home/admin/.openclaw/workspace`
- Task Records: `/home/admin/.openclaw/workspace/task_records/`
- Agent Workspaces: `/home/admin/.openclaw/agents/<agentId>/workspace/`

## 完成判断

当所有步骤状态为 `completed` 时，任务状态更新为 `completed`。

## 心跳检测

创建任务时，根据 `heartbeatAgents` 列表为每个Agent注册心跳检测：
- 频率：每30秒
- 执行内容：调用 `execute_task.py` 处理同一任务记录
- 退出条件：任务已全部完成或失败