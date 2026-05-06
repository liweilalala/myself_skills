---
name: testcase-generate-workflow
description: 从设计文档生成完整测试用例的工作流编排skill。输入设计文档（Word .docx 或 Markdown .md），依次执行：1）atomic-capability-with-ibo-extraction生成atomic-capability.json；2）feature-tree-testpoint-generation生成logic_testpoint.json；3）implement-testpoint-generation-workflow生成interface_testpoint.json；4）testpoint-to-testcase分别生成logic_testcase.json和interface_testcase.json。触发条件：用户要求"执行测试工作流"、"从设计文档生成测试用例"、"测试用例生成"。
---

# Testcase Generate Workflow

> 本skill基于 `multi-agent-scheduler` 框架，负责**任务编排**，具体执行委托给 `multi-agent-scheduler`。

## 核心概念

| 概念 | 说明 |
|------|------|
| **主Agent** | 当前执行此skill，向用户解释进度 |
| **multi-agent-scheduler** | 执行引擎：任务创建、派发、监控 |
| **子Agent** | `requirement_analyst`（Step 1-7）、`test_designer`（Step 8-12） |

---

## 工作流程

```
用户请求 → 解析输入 → 创建任务（委托multi-agent-scheduler）→ 监控 → 汇总结果
```

---

## Step 1: 解析用户请求

用户可能说：
- 「执行测试工作流，输入文档是 xxx.docx」
- 「从设计文档生成测试用例 xxx.md」

提取：
- **设计文档路径**（.docx 或 .md）

---

## Step 2: 创建任务

调用 `multi-agent-scheduler` 的 `create_task.py`：

```bash
python3 ~/.openclaw/workspace/skills/multi-agent-scheduler/scripts/create_task.py \
  --name "测试用例生成工作流" \
  --agent testcase_workflow \
  --task "从{inputDoc}生成完整测试用例"
```

然后**手动构建工作流步骤**（因为测试用例生成有特殊的12步流程）：

```bash
# 创建工作目录
mkdir -p ~/.openclaw/workspace/task_records/<task_id>/

# 构建 task_record.json（含12个步骤）
# 详见下方「步骤定义」
```

---

## 步骤定义

| Step | 名称 | Agent | 依赖 | 输入 | 输出 |
|------|------|-------|------|------|------|
| 1 | 需求格式化 | requirement_analyst | - | `{inputDoc}` | `doc.md`, `requirements.md` |
| 2 | 客户问题识别 | requirement_analyst | 1 | `requirements.md` | `sub_problems_5w2h.json`, `sub_problems.json` |
| 3 | 术语替换-5w2h | requirement_analyst | 2 | `sub_problems_5w2h.json` | `sub_problems_5w2h_replaced.json` |
| 4 | 术语替换-subprob | requirement_analyst | 2 | `sub_problems.json` | `sub_problems_replaced.json` |
| 5 | 规则拆分 | requirement_analyst | 3,4 | `sub_problems_5w2h_replaced.json` | `rules.json` |
| 6 | Usecase提取 | requirement_analyst | 3,4 | `sub_problems_5w2h_replaced.json` | `usecase.json` |
| 7 | Usecase规则匹配 | requirement_analyst | 5,6 | `usecase.json`, `rules.json` | `usecase_with_rule.json` |
| 8 | 原子能力提取 | test_designer | 7 | `doc.md`, `rules.json` | `atomic_capability.json` |
| 9 | 逻辑测试点生成 | test_designer | 8 | `atomic_capability.json` | `logic_testpoint.json` |
| 10 | 逻辑测试用例生成 | test_designer | 9 | `logic_testpoint.json` | `logic_testcase.json` |
| 11 | 接口测试点生成 | test_designer | 7 | `doc.md` | `interface_testpoint.json` |
| 12 | 接口测试用例生成 | test_designer | 11 | `interface_testpoint.json` | `interface_testcase.json` |

---

## Step 3: 派发任务

使用 `sessions_spawn` 派发第一步：

```python
sessions_spawn(
  runtime="subagent",
  agentId="requirement_analyst",
  task="执行Step1: 需求格式化...",
  runTimeoutSeconds=300
)
```

---

## Step 4: 注册监控

使用 `multi-agent-scheduler` 的 `register_heartbeat.py`：

```bash
python3 ~/.openclaw/workspace/skills/multi-agent-scheduler/scripts/register_heartbeat.py <task_id>
```

---

## Step 5: 汇总结果

任务完成后，读取输出文件汇总给用户：

```
~/.openclaw/workspace/task_records/<task_id>/
├── logic_testcase.json      # 分支1最终产物
└── interface_testcase.json  # 分支2最终产物
```

---

## 工作目录结构

```
~/.openclaw/workspace/task_records/<task_id>/
├── task_record.json          # 任务记录（12个步骤）
├── doc.md                    # Step1输出
├── requirements.md           # Step1输出
├── sub_problems_5w2h.json   # Step2输出
├── sub_problems.json        # Step2输出
├── sub_problems_5w2h_replaced.json  # Step3输出
├── sub_problems_replaced.json       # Step4输出
├── rules.json               # Step5输出
├── usecase.json             # Step6输出
├── usecase_with_rule.json   # Step7输出
├── atomic_capability.json    # Step8输出
├── logic_testpoint.json     # Step9输出
├── logic_testcase.json      # Step10输出
├── interface_testpoint.json  # Step11输出
└── interface_testcase.json  # Step12输出
```

---

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
- Step3, Step4 并行（依赖Step2）
- Step5, Step6 并行（依赖Step3, Step4）
- 分支1（Step8-10）和分支2（Step11-12）并行（都依赖Step7）

---

## 分支并行执行

Step 8-10（逻辑测试用例）和 Step 11-12（接口测试用例）可以并行执行：

```python
# 并行派发两个分支
sessions_spawn(agentId="test_designer", task="执行Step8-10...")
sessions_spawn(agentId="test_designer", task="执行Step11-12...")
```

---

## scripts/

本skill的scripts仅做**特定用途**，通用功能委托 `multi-agent-scheduler`：

| 脚本 | 功能 | 委托自 |
|------|------|--------|
| `init_workflow.py` | 初始化工作流环境 | -（本skill专用） |
| - | 任务创建 | → `multi-agent-scheduler/scripts/create_task.py` |
| - | 心跳注册 | → `multi-agent-scheduler/scripts/register_heartbeat.py` |
| - | 状态检查 | → `multi-agent-scheduler/scripts/execute_task.py` |

---

## 与 multi-agent-scheduler 的分工

| 功能 | testcase-generate-workflow | multi-agent-scheduler |
|------|---------------------------|----------------------|
| 工作流编排 | ✅ | - |
| 步骤定义 | ✅ (12步) | - |
| 派发子Agent | ✅ | 提供sessions_spawn |
| 任务创建 | - | ✅ |
| 心跳监控 | - | ✅ |