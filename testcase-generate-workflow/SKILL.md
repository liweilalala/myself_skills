# Testcase Generate Workflow

> 从设计文档（.docx/.md）生成完整测试用例的自动化工作流。  
> 集成 **task-coordinator**（任务追踪 + 超时兜底）和 **trace-query**（历史经验复用）。

---

## 核心概念

| 概念 | 说明 |
|------|------|
| **主Agent** | 当前会话，执行工作流编排、派发、监控、汇总 |
| **task-coordinator** | 每个子任务的追踪器：init → checkpoint → complete/fail/timeout |
| **trace-query** | 启动前查相似成功任务 + 失败模式，避免重复踩坑 |
| **requirement_analyst** | 子Agent，负责 Step 1-7（需求分析阶段） |
| **test_designer** | 子Agent，负责 Step 8-12（测试用例生成阶段） |

---

## 工作流程总览

```
用户请求
    │
    ├── Step 0: trace-query — 查相似成功任务 + 失败模式
    │
    ├── Step 1: 需求格式化 (requirement_analyst)
    │
    ├── Step 2: 客户问题识别 (requirement_analyst)  ←─┐
    │                                                    │
    ├── Step 3: 术语替换-5w2h (requirement_analyst)  ──┼── 并行
    │                                                    │
    ├── Step 4: 术语替换-subprob (requirement_analyst) ──┘
    │
    ├── Step 5: 规则拆分 (requirement_analyst)  ──┐
    │                                              ├──→ Step 7
    ├── Step 6: Usecase提取 (requirement_analyst) ──┘
    │
    ├── Step 7: Usecase规则匹配 (requirement_analyst)
    │                │
    │                ├──→ Step 8-10 (test_designer)  ──→ logic_testcase.json
    │                │           （分支1：逻辑测试用例）
    │                │
    │                └──→ Step 11-12 (test_designer) ──→ interface_testcase.json
    │                            （分支2：接口测试用例）
```

---

## Step 0: 查询历史（必须）

```bash
# 查相似成功任务
python3 ~/.openclaw/workspace/skills/trace-query/scripts/query_api.py similar \
  --goal "从${INPUT_DOC}生成测试用例" --k 3 --status completed

# 查失败模式
python3 ~/.openclaw/workspace/skills/trace-query/scripts/query_api.py failures \
  --step-type testcase_generation
```

将查询结果注入启动 prompt，让子Agent借鉴历史经验。

---

## 步骤定义

| Step | 名称 | Agent | 依赖 | 超时建议 |
|------|------|-------|------|---------|
| 1 | 需求格式化 | requirement_analyst | - | 3min |
| 2 | 客户问题识别 | requirement_analyst | 1 | 3min |
| 3 | 术语替换-5w2h | requirement_analyst | 2 | 2min |
| 4 | 术语替换-subprob | requirement_analyst | 2 | 2min |
| 5 | 规则拆分 | requirement_analyst | 3,4 | 5min |
| 6 | Usecase提取 | requirement_analyst | 3,4 | 5min |
| 7 | Usecase规则匹配 | requirement_analyst | 5,6 | 5min |
| 8 | 原子能力提取 | test_designer | 7 | 5min |
| 9 | 逻辑测试点生成 | test_designer | 8 | 5min |
| 10 | 逻辑测试用例生成 | test_designer | 9 | 5min |
| 11 | 接口测试点生成 | test_designer | 7 | 5min |
| 12 | 接口测试用例生成 | test_designer | 11 | 5min |

---

## spawn subagent 强制 Checklist

**每个 subagent 必须遵循以下流程：**

### □ Step 0: trace-query — 查同类任务历史

```bash
python3 ~/.openclaw/workspace/skills/trace-query/scripts/query_api.py similar \
  --goal "${TASK_GOAL}" --k 3 --status completed
```

目的：借鉴成功经验、避坑失败模式。将结果作为上下文注入 prompt。

### □ Step 1: task-coordinator init — 为每个子任务单独建追踪

```bash
# 生成唯一 task_id
TASK_ID="task-$(date +%Y%m%d-%H%M%S)-${AGENT}-${STEP_NAME}"

# 初始化追踪
python3 ~/.openclaw/workspace/skills/task-coordinator/scripts/task_tracker.py init \
  "$TASK_ID" \
  "目标描述" \
  "${AGENT}" \
  --steps "步骤1,步骤2"
```

⚠️ **常见错误**：只建一个总任务追踪，不给每个 subagent 单独建 → 中间某步超时无法定位。

### □ Step 2: sessions_spawn

```python
sessions_spawn(
  runtime="subagent",
  agentId="${AGENT}",
  task="任务描述（包含 trace-query 查询结果作为上下文）",
  label=TASK_ID,   # 用 task_id 作为 label，方便追踪
  runTimeoutSeconds=300
)
```

### □ Step 3: 等待结果 → complete / fail / timeout

```bash
# SubAgent 成功返回
python3 ~/.openclaw/workspace/skills/task-coordinator/scripts/task_tracker.py complete \
  "$TASK_ID" --output "结果摘要" --duration ${DURATION_MS}

# SubAgent 报告了错误 → 3-Strike 协议重试
python3 ~/.openclaw/workspace/skills/task-coordinator/scripts/task_tracker.py checkpoint \
  "$TASK_ID" "strike-1" "failed" --note "失败原因和下次策略"

# 超时兜底（没有收到返回）
python3 ~/.openclaw/workspace/skills/task-coordinator/scripts/task_tracker.py timeout \
  "$TASK_ID" --last-step "最后步骤" --duration ${ELAPSED_MS}
```

---

## 3-Strike 协议

```
SubAgent 失败
│
├── Strike 1: 同一 Agent 重试（补充上下文，包含 trace-query 结果）
│   └── 失败 ↓
├── Strike 2: 换 Agent 或换方法（requirement_analyst → test_designer）
│   └── 失败 ↓
└── Strike 3: 输出结构化失败报告给用户
    ├── 包含：做了什么、到哪了、为什么失败
    ├── 包含：建议用户怎么做
    └── 标记 result.json status=failed
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
├── workflow.json          # 工作流元数据
├── doc.md                  # Step1 输出
├── requirements.md         # Step1 输出
├── sub_problems_5w2h.json  # Step2 输出
├── sub_problems.json       # Step2 输出
├── sub_problems_5w2h_replaced.json  # Step3 输出
├── sub_problems_replaced.json       # Step4 输出
├── rules.json              # Step5 输出
├── usecase.json            # Step6 输出
├── usecase_with_rule.json  # Step7 输出
├── atomic_capability.json   # Step8 输出
├── logic_testpoint.json    # Step9 输出
├── logic_testcase.json     # Step10 输出
├── interface_testpoint.json # Step11 输出
└── interface_testcase.json  # Step12 输出
```

---

## 完整执行示例

```python
# ============================================================
# 测试用例生成工作流 - 主Agent执行脚本
# ============================================================

INPUT_DOC = "设计文档.docx"  # 用户输入
WORKFLOW_TASK_ID = f"workflow-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
WORK_DIR = f"~/.openclaw/workspace/task_records/{WORKFLOW_TASK_ID}"
os.makedirs(os.path.expanduser(WORK_DIR), exist_ok=True)

# ----------------------------------------------------------
# Step 0: trace-query 查询历史
# ----------------------------------------------------------
similar = query_trace_similar(f"从{INPUT_DOC}生成测试用例", k=3)
failures = query_trace_failures("testcase_generation")

# ----------------------------------------------------------
# Step 1: 需求格式化
# ----------------------------------------------------------
TASK1 = f"task-{WORKFLOW_TASK_ID}-step1"
spawn_and_track(
  task_id=TASK1,
  agent="requirement_analyst",
  goal=f"将{INPUT_DOC}格式化为需求文档",
  similar=similar,
  failures=failures,
  timeout=180
)

# ----------------------------------------------------------
# Step 2: 客户问题识别（依赖Step1）
# ----------------------------------------------------------
TASK2 = f"task-{WORKFLOW_TASK_ID}-step2"
spawn_and_track(
  task_id=TASK2,
  agent="requirement_analyst",
  goal="从requirements.md识别客户问题",
  depends_on=[TASK1],
  timeout=180
)

# ----------------------------------------------------------
# Step 3 & 4: 并行术语替换（依赖Step2）
# ----------------------------------------------------------
TASK3 = f"task-{WORKFLOW_TASK_ID}-step3"
TASK4 = f"task-{WORKFLOW_TASK_ID}-step4"
# 并行派发
spawn_and_track(TASK3, "requirement_analyst", "术语替换-5w2h", depends_on=[TASK2])
spawn_and_track(TASK4, "requirement_analyst", "术语替换-subprob", depends_on=[TASK2])

# ----------------------------------------------------------
# Step 5 & 6: 并行规则拆分和Usecase提取（依赖Step3,4）
# ----------------------------------------------------------
TASK5 = f"task-{WORKFLOW_TASK_ID}-step5"
TASK6 = f"task-{WORKFLOW_TASK_ID}-step6"
spawn_and_track(TASK5, "requirement_analyst", "规则拆分", depends_on=[TASK3, TASK4])
spawn_and_track(TASK6, "requirement_analyst", "Usecase提取", depends_on=[TASK3, TASK4])

# ----------------------------------------------------------
# Step 7: Usecase规则匹配（依赖Step5,6）
# ----------------------------------------------------------
TASK7 = f"task-{WORKFLOW_TASK_ID}-step7"
spawn_and_track(TASK7, "requirement_analyst", "Usecase规则匹配", depends_on=[TASK5, TASK6])

# ----------------------------------------------------------
# Step 8-10: 分支1 - 逻辑测试用例（依赖Step7）
# ----------------------------------------------------------
TASK8 = f"task-{WORKFLOW_TASK_ID}-step8"
TASK9 = f"task-{WORKFLOW_TASK_ID}-step9"
TASK10 = f"task-{WORKFLOW_TASK_ID}-step10"
spawn_and_track(TASK8, "test_designer", "原子能力提取", depends_on=[TASK7])
spawn_and_track(TASK9, "test_designer", "逻辑测试点生成", depends_on=[TASK8])
spawn_and_track(TASK10, "test_designer", "逻辑测试用例生成", depends_on=[TASK9])

# ----------------------------------------------------------
# Step 11-12: 分支2 - 接口测试用例（依赖Step7，并行）
# ----------------------------------------------------------
TASK11 = f"task-{WORKFLOW_TASK_ID}-step11"
TASK12 = f"task-{WORKFLOW_TASK_ID}-step12"
spawn_and_track(TASK11, "test_designer", "接口测试点生成", depends_on=[TASK7])
spawn_and_track(TASK12, "test_designer", "接口测试用例生成", depends_on=[TASK11])

# ----------------------------------------------------------
# 汇总结果
# ----------------------------------------------------------
logic_testcase = read_file(f"{WORK_DIR}/logic_testcase.json")
interface_testcase = read_file(f"{WORK_DIR}/interface_testcase.json")
send_to_user(f"✅ 测试用例生成完成\n\n逻辑测试用例：{logic_testcase}\n接口测试用例：{interface_testcase}")
```

---

## 与旧版 multi-agent-scheduler 的区别

| 维度 | 旧版 | 新版（task-coordinator集成） |
|------|------|--------------------------|
| 任务追踪 | 多步骤混在一个task | 每个子任务独立追踪 |
| 超时处理 | 无 | watchdog 自动标记 + 通知 |
| 失败重试 | 无 | 3-Strike 协议 |
| 历史经验 | 无 | trace-query 借鉴成功/失败 |
| 粒度 | 粗 | 细（精确到每步） |
| 进度可见性 | 低 | 高（progress.json 每步记录） |