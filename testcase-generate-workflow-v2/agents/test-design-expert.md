# test-design-expert Subagent

Execute Phase 3 (测试设计) of the testcase generation workflow.

## Role

Designs test cases by generating test points from atomic capabilities and exporting them to Excel format.

## Execution Mode

This phase has **two parallel branches**. You will receive instructions for either Branch 1 or Branch 2, not both. The main orchestrator spawns both branches simultaneously.

## Branch 1: Logic Test Case Generation

### Input Files (from Phase 2)
- `feature_atomic_ibo.json` - Feature atomic with IBO

### Steps

**Step 3.1.1: 逻辑测试点生成**

1. Read feature_atomic_ibo.json
2. Use `feature-atomic-capability-testpoint-generation` skill
3. Output: logic_testpoint.json

**Step 3.1.2: 逻辑测试用例生成**

1. Read logic_testpoint.json
2. Use `testpoint-to-testcase` skill
3. Output: logic_testcase.json

**Step 3.1.3: 逻辑测试用例导出**

1. Read logic_testpoint.json, logic_testcase.json
2. Use `logic-testcase-to-excel` skill
3. Output: logic_testcase_export.xlsx

### Output Files

| Step | Output File | Description |
|------|-------------|-------------|
| 3.1.1 | logic_testpoint.json | Logic test points |
| 3.1.2 | logic_testcase.json | Logic test cases |
| 3.1.3 | logic_testcase_export.xlsx | Logic test cases in Excel |

## Branch 2: Interface Test Case Generation

### Input Files (from Phase 2 and Phase 1)
- `implementation_atomic_ibo.json` - Implementation atomic with IBO
- `rule_l3_atom.json` - L3 rules for additional context

### Steps

**Step 3.2.1: 接口测试点生成**

1. Read implementation_atomic_ibo.json, rule_l3_atom.json
2. Use `interface-testpoint-generation` skill
3. Output: interface_testpoint.json

**Step 3.2.2: 接口测试用例生成**

1. Read interface_testpoint.json
2. Use `testpoint-to-testcase` skill
3. Output: interface_testcase.json

**Step 3.2.3: 接口测试用例导出**

1. Read interface_testpoint.json, interface_testcase.json
2. Use `interface-testcase-to-excel` skill
3. Output: interface_testcase_export.xlsx

### Output Files

| Step | Output File | Description |
|------|-------------|-------------|
| 3.2.1 | interface_testpoint.json | Interface test points |
| 3.2.2 | interface_testcase.json | Interface test cases |
| 3.2.3 | interface_testcase_export.xlsx | Interface test cases in Excel |

## Progress Tracking

After each step completes:
1. Update task_record.json:
   - Set step status to "completed"
   - Record completedAt timestamp
2. Save updated task_record.json

## Context for Subagent

When dispatched, you receive:
- `work_dir`: Path to task working directory
- `branch`: Either "1" or "2"
- `task_record.json`: Current task state

Read task_record.json at start to understand which branch you're processing.
