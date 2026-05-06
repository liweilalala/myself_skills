---
name: testcase-generate-workflow
description: 从设计文档生成完整测试用例的工作流编排skill。输入设计文档（Word .docx 或 Markdown .md），依次执行：1）atomic-capability-with-ibo-extraction生成atomic-capability.json；2）feature-tree-testpoint-generation生成logic_testpoint.json；3）implement-testpoint-generation-workflow生成interface_testpoint.json；4）testpoint-to-testcase分别生成logic_testcase.json和interface_testcase.json。触发条件：用户要求"执行测试工作流"、"从设计文档生成测试用例"、"测试用例生成"。
---

# Testcase Generate Workflow

## 概述

本skill基于 multi-agent-scheduler 框架，实现从设计文档到测试用例的完整自动化生成流程。

## 输入

- 设计文档路径：Word文档(.docx)或Markdown文件(.md)
- 示例：`D:\Project\AI\test_AI\Suite_AI_Assisted_Testing\test_code\task0425\SmartCare Suite 8.0.0 功能设计说明书.docx`

## 工作目录结构

```
~/.openclaw/workspace/task_records/<task_id>/
├── task_record.json              # 任务记录
├── doc.md                        # Step1: word转markdown
├── requirements.md               # Step1: 需求预处理
├── sub_problems_5w2h.json        # Step2: 客户问题识别(5w2h)
├── sub_problems.json             # Step2: 客户问题识别
├── sub_problems_5w2h_replaced.json   # Step3: 术语替换
├── sub_problems_replaced.json    # Step4: 术语替换
├── rules.json                    # Step5: 规则拆分
├── usecase.json                  # Step6: usecase提取
├── usecase_with_rule.json        # Step7: usecase规则匹配
├── atomic_capability.json        # Step8: 原子能力提取
├── logic_testpoint.json          # Step9: 逻辑测试点
├── logic_testcase.json           # Step10: 逻辑测试用例
├── interface_testpoint.json      # Step11: 接口测试点
└── interface_testcase.json       # Step12: 接口测试用例
```

## 执行角色

| 角色 | 职责 |
|------|------|
| requirement_analyst | 执行Step 1-7（需求分析）所有步骤 |
| test_designer | 执行Step 8-12（测试用例生成）所有步骤 |

## 步骤定义与文件传递

| Step | 名称 | Agent | 输入文件 | 输出文件 |
|------|------|-------|----------|----------|
| 1 | 需求格式化 | requirement_analyst | `{inputDoc}` | `doc.md`, `requirements.md` |
| 2 | 客户问题识别 | requirement_analyst | `requirements.md` | `sub_problems_5w2h.json`, `sub_problems.json` |
| 3 | 术语替换-5w2h | requirement_analyst | `sub_problems_5w2h.json` | `sub_problems_5w2h_replaced.json` |
| 4 | 术语替换-subprob | requirement_analyst | `sub_problems.json` | `sub_problems_replaced.json` |
| 5 | 规则拆分 | requirement_analyst | `sub_problems_5w2h_replaced.json` | `rules.json` |
| 6 | Usecase提取 | requirement_analyst | `sub_problems_5w2h_replaced.json` | `usecase.json` |
| 7 | Usecase规则匹配 | requirement_analyst | `usecase.json`, `rules.json` | `usecase_with_rule.json` |
| 8 | 原子能力提取 | test_designer | `doc.md`, `rules.json` | `atomic_capability.json` |
| 9 | 逻辑测试点生成 | test_designer | `atomic_capability.json` | `logic_testpoint.json` |
| 10 | 逻辑测试用例生成 | test_designer | `logic_testpoint.json` | `logic_testcase.json` |
| 11 | 接口测试点生成 | test_designer | `doc.md` | `interface_testpoint.json` |
| 12 | 接口测试用例生成 | test_designer | `interface_testpoint.json` | `interface_testcase.json` |

## 依赖关系图

```
Step1 → Step2 → Step3 ──┐
                        ├──→ Step5 ─┐
                        │          ├──→ Step7 → Step8 → Step9 → Step10 (分支1)
Step4 ← Step2           │          │
                        ├──→ Step6 ─┘
                        │
                        └──→ Step11 → Step12 (分支2)
```

**说明**：
- Step3, Step4 并行执行（都依赖Step2）
- Step5, Step6 并行执行（都依赖Step3, Step4）
- 分支1（Step8-10）和分支2（Step11-12）并行执行（都依赖Step7）

## 执行流程

### 1. 创建任务

主Agent收到用户请求后：
1. 调用 `create_task.py <设计文档路径>` 创建任务
2. 系统在 `~/.openclaw/workspace/task_records/<task_id>/` 创建工作目录
3. 保存任务记录 `task_record.json`

### 2. 派发执行

主Agent通过 `sessions_spawn` 派发任务：
- 解析派发信息中的 `inputFiles` 和 `outputFiles` 获取绝对路径
- 调用对应skill进行处理
- 完成后通过heartbeat汇报结果

### 3. 心跳监控

注册cron job每90秒检查任务状态，输出待执行的派发信息。

## 派发信息格式

```json
{
  "agentId": "requirement_analyst",
  "stepId": 1,
  "stepName": "需求格式化",
  "skill": "word-to-markdown + requirement-document-preprocessor",
  "inputFiles": ["/path/to/input.docx"],
  "outputFiles": ["/path/to/doc.md", "/path/to/requirements.md"],
  "workDir": "/home/admin/.openclaw/workspace/task_records/task_tcg_20260506_170000/doc.md",
  "taskRecordPath": "/home/admin/.openclaw/workspace/task_records/task_tcg_20260506_170000/task_record.json"
}
```

## 执行脚本

| 脚本 | 功能 |
|------|------|
| `create_task.py` | 创建任务记录和工作目录 |
| `execute_task.py` | 心跳检查，输出派发信息（带绝对路径） |
| `register_heartbeat.py` | 注册cron心跳任务 |

## 使用示例

用户：「执行测试工作流，输入文档是 D:\Project\AI\test_AI\test.docx」

主Agent执行：
```python
# 1. 创建任务
task_id = create_task("D:\\Project\\AI\\test.docx")
# 生成: task_tcg_20260506_170000

# 2. 派发第一步
sessions_spawn(
    runtime="subagent",
    agentId="requirement_analyst",
    task="执行Step1: 需求格式化..."
)

# 3. 注册心跳
cron(action='add', job={
    "name": f"heartbeat_{task_id}",
    "schedule": {"kind": "every", "everyMs": 30000},
    "payload": {"kind": "agentTurn", "message": f"python3 execute_task.py <task_record_path>"}
})
```