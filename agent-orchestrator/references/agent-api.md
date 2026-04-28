# Agent Orchestrator API 参考

## 工具调用

### 1. sessions_spawn - 启动子Agent任务

```python
sessions_spawn(
    task="<任务描述>",
    runtime="subagent",
    agentId="<目标agentId>",
    mode="run",          # run=一次性, session=持续会话
    runTimeoutSeconds=0  # 0=无超时限制
)
```

**返回**：
- 成功：返回包含 `sessionKey` 的结果
- 失败：返回错误信息

### 2. sessions_list - 列出活跃会话

```python
sessions_list(
    kinds=["subagent"],       # 只看子Agent会话
    activeMinutes=30,         # 最近30分钟有活动的
    limit=10,
    messageLimit=5            # 每个会话返回最近5条消息
)
```

**返回格式**：
```json
{
  "sessions": [
    {
      "sessionKey": "xxx",
      "agentId": "scholar_assistant",
      "activeMinutes": 5,
      "lastMessage": "任务已完成：...",
      "status": "completed|active|idle"
    }
  ]
}
```

### 3. sessions_history - 获取会话历史

```python
sessions_history(
    sessionKey="<sessionKey>",
    limit=20,
    includeTools=true
)
```

### 4. subagents - 查看运行中的子任务

```python
subagents(
    action="list",
    recentMinutes=30
)
```

**返回格式**：
```json
{
  "subagents": [
    {
      "task": "调研任务",
      "agentId": "scholar_assistant",
      "status": "running|completed|failed"
    }
  ]
}
```

## 子Agent工作目录结构

每个Agent的工作目录位于：
```
~/.openclaw/agents/<agentId>/workspace/
```

**标准文件**：
- `AGENTS.md` - Agent配置
- `SOUL.md` - Agent定位
- `USER.md` - 用户信息
- `memory/YYYY-MM-DD.md` - 每日执行日志

**任务输出**：
任务产生的文件会保存在工作目录中，具体取决于任务内容。

## 状态监控策略

| 任务类型 | 建议监控频率 | 超时判断 |
|---------|------------|---------|
| 快速任务（<1分钟） | 每10秒 | >3分钟无响应 |
| 中等任务（1-10分钟） | 每30秒 | >15分钟无响应 |
| 长时任务（>10分钟） | 每1分钟 | 根据任务特性判断 |

## 错误处理

- **Agent不存在**：`sessions_spawn` 返回错误，检查agentId是否正确
- **任务超时**：使用 `subagents(action="kill", target="<subagentId>")` 终止
- **工作目录无权限**：检查文件权限，使用 `elevated=true` 提升权限
