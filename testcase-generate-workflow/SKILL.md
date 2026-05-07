# Testcase Generate Workflow

> 从设计文档（.docx/.md）生成完整测试用例的自动化工作流。  
> 集成 **task-coordinator**（任务追踪 + 超时兜底）和 **trace-query**（历史经验复用）。

---

## 使用方式

```
输入文件：设计文档.docx / 设计文档.md
输出文件：logic_testcase.json + interface_testcase.json
执行Skill：requirement_analyst → test_designer
```

用户只需指定 **输入文件**、**输出文件**、**使用哪个 skill**，工作流自动编排执行。

---

## 工作流程

```
用户请求
    │
    ├── 解析输入输出
    │
    ├── trace-query — 查相似成功任务 + 失败模式
    │
    ├── requirement_analyst 执行（需求分析）
    │       输入：{INPUT_DOC}
    │       输出：usecase_with_rule.json
    │
    └── test_designer 执行（测试用例生成）
            输入：usecase_with_rule.json
            输出：logic_testcase.json, interface_testcase.json
```

---

## 追踪文件结构

```
~/.openclaw/workspace/data/task-traces/<task_id>/
├── task_plan.json    # 目标、步骤、状态
├── progress.json     # 事件流（每步记录）
└── result.json       # 最终结果（completed/failed/timeout）
```

---

## 工作目录结构

```
~/.openclaw/workspace/task_records/<workflow_task_id>/
├── workflow.json              # 工作流元数据
├── doc.md                     # 需求格式化输出
├── requirements.md            # 需求格式化输出
├── sub_problems_5w2h.json     # 客户问题识别输出
├── sub_problems.json          # 客户问题识别输出
├── sub_problems_5w2h_replaced.json  # 术语替换输出
├── sub_problems_replaced.json       # 术语替换输出
├── rules.json                  # 规则拆分输出
├── usecase.json                # Usecase提取输出
├── usecase_with_rule.json      # Usecase规则匹配输出
├── atomic_capability.json       # 原子能力提取输出
├── logic_testpoint.json        # 逻辑测试点输出
├── logic_testcase.json         # 逻辑测试用例最终输出
├── interface_testpoint.json    # 接口测试点输出
└── interface_testcase.json     # 接口测试用例最终输出
```

---

## spawn subagent 强制 Checklist

### □ Step 0: trace-query — 查同类任务历史

```bash
python3 ~/.openclaw/workspace/skills/trace-query/scripts/query_api.py similar \
  --goal "${TASK_GOAL}" --k 3 --status completed

python3 ~/.openclaw/workspace/skills/trace-query/scripts/query_api.py failures \
  --step-type testcase_generation
```

### □ Step 1: task-coordinator init — 为每个子任务单独建追踪

```bash
TASK_ID="task-$(date +%Y%m%d-%H%M%S)-${AGENT}-${STEP_NAME}"

python3 ~/.openclaw/workspace/skills/task-coordinator/scripts/task_tracker.py init \
  "$TASK_ID" "目标描述" "${AGENT}" --steps "步骤1,步骤2"
```

### □ Step 2: sessions_spawn

```python
sessions_spawn(
  runtime="subagent",
  agentId="${AGENT}",
  task="任务描述 (含trace-query结果)",
  label=TASK_ID,
  runTimeoutSeconds=300
)
```

### □ Step 3: 结果处理 — complete / fail / timeout

```bash
# 成功
python3 ~/.openclaw/workspace/skills/task-coordinator/scripts/task_tracker.py complete \
  "$TASK_ID" --output "结果摘要" --duration ${DURATION_MS}

# 失败 → 3-Strike 协议
python3 ~/.openclaw/workspace/skills/task-coordinator/scripts/task_tracker.py checkpoint \
  "$TASK_ID" "strike-1" "failed" --note "失败原因"

# 超时兜底
python3 ~/.openclaw/workspace/skills/task-coordinator/scripts/task_tracker.py timeout \
  "$TASK_ID" --last-step "最后步骤" --duration ${ELAPSED_MS}
```

---

## 3-Strike 协议

```
SubAgent 失败
│
├── Strike 1: 同一 Agent 重试（补充上下文）
│   └── 失败 ↓
├── Strike 2: 换 Agent 或换方法
│   └── 失败 ↓
└── Strike 3: 输出结构化失败报告
    ├── 包含：做了什么、到哪了、为什么失败
    └── 标记 result.json status=failed
```

---

## 简化调用示例

```python
# 只需指定：输入、输出、skill
INPUT_DOC = "设计文档.docx"
WORKFLOW_TASK_ID = f"workflow-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
WORK_DIR = f"~/.openclaw/workspace/task_records/{WORKFLOW_TASK_ID}"

# Step 1: requirement_analyst
TASK1 = f"task-{WORKFLOW_TASK_ID}-requirement_analyst"
spawn_and_track(
  task_id=TASK1,
  agent="requirement_analyst",
  input=INPUT_DOC,
  output=f"{WORK_DIR}/usecase_with_rule.json",
  trace_goal=f"从{INPUT_DOC}生成测试用例"
)

# Step 2: test_designer
TASK2 = f"task-{WORKFLOW_TASK_ID}-test_designer"
spawn_and_track(
  task_id=TASK2,
  agent="test_designer",
  input=f"{WORK_DIR}/usecase_with_rule.json",
  output=f"{WORK_DIR}/logic_testcase.json",
  output2=f"{WORK_DIR}/interface_testcase.json",
  depends_on=[TASK1]
)
```
