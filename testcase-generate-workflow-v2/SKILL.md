---
name: testcase-generate-workflow
description: Use when the user wants to generate test cases from a design document (.docx/.md). This is a multi-phase workflow that orchestrates 3 specialized subagents across 3 phases with parallel branch execution and checkpoint/resume support.
---

# Testcase Generate Workflow

Orchestrates multi-phase test case generation from design documents using 3 specialized subagents across 3 phases with parallel branch execution and checkpoint/resume support.

## When to Use

- User provides a design document (.docx or .md) and wants complete test cases generated
- Complex multi-phase workflow requiring specialized agents for requirement analysis and test design
- Need for checkpoint/resume capability to handle interruptions
- Parallel execution of logic test case and interface test case branches

## Input

- **Design document**: `.docx` or `.md` file containing product requirements
- **Task ID** (optional for resume): If resuming, provide the existing task ID

## Output

```
logic_testcase_export.xlsx    # Logic test cases (from feature atomic capability)
interface_testcase_export.xlsx # Interface test cases (from implementation atomic capability)
```

## Process Overview

```
INPUT: design_document.docx/.md
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: 原始需求分析 (test-req-preprocessor)                   │
│ Steps 1.1 → 1.2 → 1.3 → 1.4 → 1.5 → 1.6 → 1.7 → 1.8         │
│                                                              │
│ Output: usecase_with_rule.json                               │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2: 测试需求分析 (test-requirement-analyst)               │
│                                                              │
│ Branch 1 (parallel with Branch 2)  │  Branch 2               │
│ 2.1.1 → 2.1.2                     │  2.2.1 → 2.2.2           │
│ Output: feature_atomic_ibo.json   │  Output: implementation_ │
│                                  │  atomic_ibo.json         │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3: 测试设计 (test-design-expert)                         │
│                                                              │
│ Branch 1 (parallel with Branch 2)  │  Branch 2               │
│ 3.1.1 → 3.1.2 → 3.1.3             │  3.2.1 → 3.2.2 → 3.2.3   │
│ Output: logic_testcase_export.xlsx │  Output: interface_     │
│                                  │  testcase_export.xlsx   │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
OUTPUT: logic_testcase_export.xlsx + interface_testcase_export.xlsx
```

---

## Directory Structure

```
~/.openclaw/workspace/task_records/<task_id>/
├── task_record.json              # Master task tracking file
│
├── doc.md                       # Step 1.1: converted from input
├── requirements.md               # Step 1.1: preprocessed requirements
│
├── sub_problems.json            # Step 1.2: customer problems
├── sub_problems_5w2h.json       # Step 1.3: 5W2H analysis
│
├── sub_problems_replaced.json    # Step 1.4: term replaced
├── sub_problems_5w2h_replaced.json # Step 1.4: term replaced
│
├── rule_l3_atom.json            # Step 1.5: L3 rules
├── rule_l4_factor.json          # Step 1.6: L4 factors
├── rule_l3_l4_relation.json     # Step 1.6: L3-L4 relations
│
├── usecase.json                 # Step 1.7: use cases
├── non_func_req.json            # Step 1.7: non-functional requirements
│
├── usecase_with_rule.json       # Step 1.8: use cases with rules (Phase 1 milestone)
│
├── feature_atomic.json          # Step 2.1.1: feature atomic capability
├── feature_atomic_ibo.json       # Step 2.1.2: feature atomic with IBO
│
├── implementation_atomic.json   # Step 2.2.1: implementation atomic capability
├── implementation_atomic_ibo.json # Step 2.2.2: implementation atomic with IBO
│
├── logic_testpoint.json         # Step 3.1.1: logic test points
├── logic_testcase.json          # Step 3.1.2: logic test cases
├── logic_testcase_export.xlsx   # Step 3.1.3: final output
│
├── interface_testpoint.json     # Step 3.2.1: interface test points
├── interface_testcase.json      # Step 3.2.2: interface test cases
└── interface_testcase_export.xlsx # Step 3.2.3: final output
```

---

## Step Definitions

### Phase 1: 原始需求分析 (Sequential)

| Step | Name | Agent | Input | Output | Skill |
|------|------|-------|-------|--------|-------|
| 1.1 | 需求格式化 | test-req-preprocessor | input.docx/.md | doc.md, requirements.md | word-to-markdown + requirement-document-preprocessor |
| 1.2 | 客户问题识别 | test-req-preprocessor | requirements.md, doc.md | sub_problems.json | mece-decomposition |
| 1.3 | 5W2H分析 | test-req-preprocessor | sub_problems.json, doc.md | sub_problems_5w2h.json | 5w2h-analysis |
| 1.4 | 术语替换 | test-req-preprocessor | sub_problems_5w2h.json, sub_problems.json | sub_problems_5w2h_replaced.json, sub_problems_replaced.json | term-dictionary |
| 1.5 | L3规则提取 | test-req-preprocessor | doc.md, sub_problems_5w2h_replaced.json | rule_l3_atom.json | l3-rule-extractor |
| 1.6 | L4因子拆分 | test-req-preprocessor | rule_l3_atom.json | rule_l4_factor.json, rule_l3_l4_relation.json | l4-factor-extractor |
| 1.7 | Usecase提取 | test-req-preprocessor | sub_problems_5w2h_replaced.json | usecase.json, non_func_req.json | usecase-extraction |
| 1.8 | Usecase规则匹配 | test-req-preprocessor | usecase.json, rule_l3_atom.json | usecase_with_rule.json | usecase-rule-matcher |

### Phase 2: 测试需求分析 (Parallel Branches)

| Step | Name | Agent | Branch | Input | Output | Skill |
|------|------|-------|--------|-------|--------|-------|
| 2.1.1 | Feature原子能力提取 | test-requirement-analyst | 1 | doc.md | feature_atomic.json | feature-tree-atomic-extraction |
| 2.1.2 | Feature原子IBO填充 | test-requirement-analyst | 1 | feature_atomic.json, doc.md, rule_l3_atom.json | feature_atomic_ibo.json | feature-atomic-ibo-filler |
| 2.2.1 | 实现原子能力提取 | test-requirement-analyst | 2 | doc.md | implementation_atomic.json | implementation-atomic-capability-extractor |
| 2.2.2 | 接口IBO填充 | test-requirement-analyst | 2 | doc.md, implementation_atomic.json | implementation_atomic_ibo.json | interface-ibo-filler |

### Phase 3: 测试设计 (Parallel Branches)

| Step | Name | Agent | Branch | Input | Output | Skill |
|------|------|-------|--------|-------|--------|-------|
| 3.1.1 | 逻辑测试点生成 | test-design-expert | 1 | feature_atomic_ibo.json | logic_testpoint.json | feature-atomic-capability-testpoint-generation |
| 3.1.2 | 逻辑测试用例生成 | test-design-expert | 1 | logic_testpoint.json | logic_testcase.json | testpoint-to-testcase |
| 3.1.3 | 逻辑测试用例导出 | test-design-expert | 1 | logic_testpoint.json, logic_testcase.json | logic_testcase_export.xlsx | logic-testcase-to-excel |
| 3.2.1 | 接口测试点生成 | test-design-expert | 2 | implementation_atomic_ibo.json, rule_l3_atom.json | interface_testpoint.json | interface-testpoint-generation |
| 3.2.2 | 接口测试用例生成 | test-design-expert | 2 | interface_testpoint.json | interface_testcase.json | testpoint-to-testcase |
| 3.2.3 | 接口测试用例导出 | test-design-expert | 2 | interface_testpoint.json, interface_testcase.json | interface_testcase_export.xlsx | interface-testcase-to-excel |

---

## Orchestration Process

### Step 1: Initialize Task

If **new task**:
1. Generate task ID: `task_tcg_{datetime.now().strftime('%Y%m%d_%H%M%S')}`
2. Create work directory: `~/.openclaw/workspace/task_records/{task_id}/`
3. Run `init_workflow.py` to create task_record.json

If **resume task**:
1. Receive task_id from user
2. Run `check_resume.py {task_id}` to find next steps
3. Load existing task_record.json

### Step 2: Execute Phase 1 (Sequential)

Spawn `test-req-preprocessor` subagent with steps 1.1-1.8:

```
Task tool:
  description: "Phase 1: 原始需求分析"
  prompt: |
    Execute the following steps in order:

    Step 1.1: 需求格式化
    - If input is .docx, use word-to-markdown to convert to doc.md
    - If input is already .md, copy it to doc.md
    - Use requirement-document-preprocessor skill on doc.md to produce requirements.md

    Step 1.2: 客户问题识别
    - Use mece-decomposition skill on requirements.md and doc.md
    - Output: sub_problems.json

    Step 1.3: 5W2H分析
    - Use 5w2h-analysis skill on sub_problems.json and doc.md
    - Output: sub_problems_5w2h.json

    Step 1.4: 术语替换
    - Use term-dictionary skill on sub_problems_5w2h.json and sub_problems.json
    - Output: sub_problems_5w2h_replaced.json, sub_problems_replaced.json

    Step 1.5: L3规则提取
    - Use l3-rule-extractor skill on doc.md and sub_problems_5w2h_replaced.json
    - Output: rule_l3_atom.json

    Step 1.6: L4因子拆分
    - Use l4-factor-extractor skill on rule_l3_atom.json
    - Output: rule_l4_factor.json, rule_l3_l4_relation.json

    Step 1.7: Usecase提取
    - Use usecase-extraction skill on sub_problems_5w2h_replaced.json
    - Output: usecase.json, non_func_req.json

    Step 1.8: Usecase规则匹配
    - Use usecase-rule-matcher skill on usecase.json and rule_l3_atom.json
    - Output: usecase_with_rule.json

    After each step:
    - Update task_record.json with step status = "completed"
    - Save intermediate outputs to the work directory

    Work directory: {work_dir}
    Input document: {input_doc}
```

### Step 3: Execute Phase 2 (Parallel Branches)

Spawn **two** `test-requirement-analyst` subagents **in parallel**:

**Branch 1** (test-req-preprocessor for feature atomic):
```
Task tool:
  description: "Phase 2 Branch 1: Feature Atomic IBO"
  prompt: |
    Execute the following steps for Branch 1:

    Step 2.1.1: Feature原子能力提取
    - Use feature-tree-atomic-extraction skill on doc.md
    - Output: feature_atomic.json

    Step 2.1.2: Feature原子IBO填充
    - Use feature-atomic-ibo-filler skill on feature_atomic.json, doc.md, rule_l3_atom.json
    - Output: feature_atomic_ibo.json

    After each step:
    - Update task_record.json with step status = "completed"

    Work directory: {work_dir}
```

**Branch 2** (test-requirement-analyst for implementation atomic):
```
Task tool:
  description: "Phase 2 Branch 2: Implementation Atomic IBO"
  prompt: |
    Execute the following steps for Branch 2:

    Step 2.2.1: 实现原子能力提取
    - Use implementation-atomic-capability-extractor skill on doc.md
    - Output: implementation_atomic.json

    Step 2.2.2: 接口IBO填充
    - Use interface-ibo-filler skill on doc.md and implementation_atomic.json
    - Output: implementation_atomic_ibo.json

    After each step:
    - Update task_record.json with step status = "completed"

    Work directory: {work_dir}
```

Launch both branches **simultaneously** in the same turn.

### Step 4: Execute Phase 3 (Parallel Branches)

Wait for Phase 2 to complete, then spawn **two** `test-design-expert` subagents **in parallel**:

**Branch 1** (test-design-expert for logic test cases):
```
Task tool:
  description: "Phase 3 Branch 1: Logic Test Case Generation"
  prompt: |
    Execute the following steps for Branch 1:

    Step 3.1.1: 逻辑测试点生成
    - Use feature-atomic-capability-testpoint-generation skill on feature_atomic_ibo.json
    - Output: logic_testpoint.json

    Step 3.1.2: 逻辑测试用例生成
    - Use testpoint-to-testcase skill on logic_testpoint.json
    - Output: logic_testcase.json

    Step 3.1.3: 逻辑测试用例导出
    - Use logic-testcase-to-excel skill on logic_testpoint.json and logic_testcase.json
    - Output: logic_testcase_export.xlsx

    After each step:
    - Update task_record.json with step status = "completed"

    Work directory: {work_dir}
```

**Branch 2** (test-design-expert for interface test cases):
```
Task tool:
  description: "Phase 3 Branch 2: Interface Test Case Generation"
  prompt: |
    Execute the following steps for Branch 2:

    Step 3.2.1: 接口测试点生成
    - Use interface-testpoint-generation skill on implementation_atomic_ibo.json and rule_l3_atom.json
    - Output: interface_testpoint.json

    Step 3.2.2: 接口测试用例生成
    - Use testpoint-to-testcase skill on interface_testpoint.json
    - Output: interface_testcase.json

    Step 3.2.3: 接口测试用例导出
    - Use interface-testcase-to-excel skill on interface_testpoint.json and interface_testcase.json
    - Output: interface_testcase_export.xlsx

    After each step:
    - Update task_record.json with step status = "completed"

    Work directory: {work_dir}
```

### Step 5: Complete Workflow

1. Update task_record.json with status = "completed"
2. Report final output locations to user:
   - `logic_testcase_export.xlsx`
   - `interface_testcase_export.xlsx`

---

## Checkpoint/Resume Logic

### How Checkpointing Works

1. **After each step completes**: Update `task_record.json` with:
   - Step status = "completed"
   - `completedAt` timestamp
   - Output file paths

2. **On interruption**: The task record persists in the work directory

3. **Resume process**:
   ```
   User: "Resume task task_tcg_20260512_143000"
   →
   Run check_resume.py to find pending steps
   →
   Find steps where: status="pending" AND all dependsOn are "completed"
   →
   Resume from the first such step
   ```

### Resume Decision Logic (from check_resume.py)

```python
def can_resume_step(step, completed_steps):
    """A step can resume if:
    1. Its status is 'pending' or 'failed'
    2. All steps in its dependsOn list are 'completed'
    """
    if step['status'] not in ['pending', 'failed']:
        return False
    for dep in step['dependsOn']:
        if dep not in completed_steps:
            return False
    return True
```

---

## 3-Strike Retry Protocol

```
Step fails
  │
  ├── Strike 1: Same agent retry with additional context
  │         └── Fail → Strike 2
  ├── Strike 2: Different agent or method
  │         └── Fail → Strike 3
  └── Strike 3: Structured failure report
                 - What was attempted
                 - Where it failed
                 - Why it failed
                 → Mark step status = "failed"
                 → Mark task status = "failed"
```

---

## Handling Subagent Questions

Subagents may ask clarifying questions during execution. Handle as follows:

1. **Context questions** (before starting): Answer and let them proceed
2. **Ambiguity questions**: Provide guidance based on the skill's best practices
3. **Blocked questions** (cannot proceed): Note the blocker, attempt to resolve or escalate

If a subagent returns `BLOCKED` status:
1. Assess the blocker
2. Provide more context or break the task into smaller pieces
3. Re-dispatch with the same or more capable model

---

## Integration with Other Skills

This workflow **requires** the following skills to be available (but does not implement them):

**Phase 1 Skills:**
- word-to-markdown
- requirement-document-preprocessor
- mece-decomposition
- 5w2h-analysis
- term-dictionary
- l3-rule-extractor
- l4-factor-extractor
- usecase-extraction
- usecase-rule-matcher

**Phase 2 Skills:**
- feature-tree-atomic-extraction
- feature-atomic-ibo-filler
- implementation-atomic-capability-extractor
- interface-ibo-filler

**Phase 3 Skills:**
- feature-atomic-capability-testpoint-generation
- testpoint-to-testcase
- logic-testcase-to-excel
- interface-testpoint-generation
- interface-testcase-to-excel

---

## Task Record Schema

See `references/task-record-schema.json` for the complete JSON Schema definition.

Key fields:
- `id`: Task ID (format: `task_tcg_YYYYMMDD_HHMMSS`)
- `status`: pending | in_progress | completed | failed | paused
- `steps[].status`: pending | in_progress | completed | failed | skipped
- `steps[].retryCount`: 0-3 (maximum 3 retries per step)

---

## Files

- `agents/test-req-preprocessor.md` - Phase 1 subagent definition
- `agents/test-requirement-analyst.md` - Phase 2 subagent definition
- `agents/test-design-expert.md` - Phase 3 subagent definition
- `scripts/init_workflow.py` - Initialize workflow and create task folder
- `scripts/create_task.py` - Create task_record.json
- `scripts/update_task.py` - Update task status after step completion
- `scripts/check_resume.py` - Check if task can resume and find next steps
- `scripts/spawn_and_track.py` - Spawn subagent with tracking
- `references/task-record-schema.json` - JSON Schema for task_record.json
- `references/step-dependencies.json` - Step dependency definitions
