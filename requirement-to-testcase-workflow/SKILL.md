---
name: requirement-to-testcase-workflow
description: 从需求分析到测试用例生成的完整工作流。输入设计文档（.docx或.md），依次执行：1）word-to-markdown预处理；2）requirement_analyst使用testing-requirement-analysis skill进行需求分析，生成rule_split_analysis.json和usecase_with_rule.json；3）test_designer使用testcase-generate-workflow skill生成logic_testcase.json和interface_testcase.json。触发条件：用户要求"执行需求到测试用例工作流"、"从需求生成测试用例"、"需求分析到测试用例"。
---

# Requirement to Testcase Workflow

## 概述

编排从**设计文档**到**测试用例**的完整工作流，涉及requirement_analyst和test_designer两个Agent协作。

**输入**：设计文档（`.docx` 或 `.md`）

**输出**：
- `rule_split_analysis.json` — 规则拆分结果
- `usecase_with_rule.json` — Usecase结果
- `logic_testcase.json` — 逻辑测试用例
- `interface_testcase.json` — 接口测试用例

## 工作流程

```
设计文档
    ↓
Step 0: 文档预处理
  .docx → word-to-markdown → doc.md
  .md → 直接作为 doc.md
    ↓
Step 1: 需求分析 (requirement_analyst)
  testing-requirement-analysis skill
    ↓ 产出: rule_split_analysis.json, usecase_with_rule.json
    ↓
Step 2: 测试点生成 (test_designer)
  testcase-generate-workflow skill
    ↓ 产出: logic_testcase.json, interface_testcase.json
```

## 执行步骤

### Step 0: 文档预处理

**判断文档类型**：
- `.docx` → 启动sub-agent使用`word-to-markdown`转换为`doc.md`
- `.md` → 直接复制为`doc.md`

**创建任务文件夹**：
```
~/.openclaw/workspace/<taskId>/
```
任务ID格式：`task_YYYYMMDD_HHMM`，例如 `task_20260429_1717`

### Step 1: 需求分析

**启动 requirement_analyst**：

使用 `sessions_spawn` 派发任务：

```
agentId: requirement_analyst
task: |
  请处理设计文档 doc.md，执行需求分析。
  使用 testing-requirement-analysis skill 进行处理。
  处理完成后，汇报任务ID（即创建的文件夹名称）。
```

**监控任务状态**：
- 每10-30秒检查 `sessions_list(kinds=["subagent"])` 
- 确认任务完成后，检查产出文件：
  ```bash
  ls -la ~/.openclaw/agents/requirement_analyst/workspace/<taskId>/
  ```

**产出检查**：
确认以下文件存在：
- `rule_split_analysis.json`
- `usecase_with_rule.json`

**错误处理**：
- 如果任务长时间阻塞 → 对requirement_analyst发送指令 `/compact` 压缩上下文，然后重试

### Step 2: 测试点生成

**启动 test_designer**：

使用 `sessions_spawn` 派发任务：

```
agentId: test_designer
task: |
  请基于以下文件执行测试用例生成工作流：
  - 输入：doc.md 和 rule_split_analysis.json（在任务文件夹中）
  - 执行：testcase-generate-workflow skill
  - 任务ID：<taskId>
  - 输出：logic_testcase.json 和 interface_testcase.json
  保存到 ~/.openclaw/workspace/<taskId>/
```

**监控任务状态**：
- 定期检查 `sessions_list(kinds=["subagent"])`
- 任务完成后检查产出：
  ```bash
  ls -la ~/.openclaw/workspace/<taskId>/
  ```

**错误处理**：
- 如果任务长时间阻塞 → 对test_designer发送指令 `/compact` 压缩上下文，然后重试

## Agent通信协议

### 派发任务
使用 `sessions_spawn(runtime="subagent", agentId=<agentId>, task=<task>, mode="run")`

### 监控状态
- `sessions_list(kinds=["subagent"], activeMinutes=5)` — 查看活跃子Agent
- `sessions_history(sessionKey, limit=20)` — 查看任务输出

### 上下文压缩
当Agent阻塞时，使用 `sessions_send(sessionKey, "/compact")` 压缩上下文

## 任务文件夹结构

```
~/.openclaw/workspace/<taskId>/
├── doc.md                      # 预处理后的设计文档
├── rule_split_analysis.json    # Step 1产出
├── usecase_with_rule.json      # Step 1产出
├── logic_testcase.json         # Step 2产出
└── interface_testcase.json     # Step 2产出
```

## 使用方式

触发后按以下步骤执行：

1. 解析输入的设计文档路径
2. 生成任务ID，创建任务文件夹
3. 预处理文档（docx→md或直接复制）
4. 启动requirement_analyst进行需求分析，监控直到完成
5. 检查Step 1产出文件
6. 启动test_designer进行测试点生成，监控直到完成
7. 汇总报告所有产出文件位置