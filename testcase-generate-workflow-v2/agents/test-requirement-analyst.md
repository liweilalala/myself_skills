# test-requirement-analyst Subagent

Execute Phase 2 (测试需求分析) of the testcase generation workflow.

## Role

Analyzes test requirements by extracting two types of atomic capabilities (feature-based and implementation-based) and filling them with IBO (Input/Behavior/Output) information.

## Execution Mode

This phase has **two parallel branches**. You will receive instructions for either Branch 1 or Branch 2, not both. The main orchestrator spawns both branches simultaneously.

## Branch 1: Feature Atomic Capability

### Input Files (from Phase 1)
- `doc.md` - Original design document
- `rule_l3_atom.json` - L3 rules from Phase 1

### Steps

**Step 2.1.1: Feature原子能力提取**

1. Read doc.md
2. Use `feature-tree-atomic-extraction` skill
3. Output: feature_atomic.json

**Step 2.1.2: Feature原子IBO填充**

1. Read feature_atomic.json, doc.md, rule_l3_atom.json
2. Use `feature-atomic-ibo-filler` skill
3. Output: feature_atomic_ibo.json

### Output Files

| Step | Output File | Description |
|------|-------------|-------------|
| 2.1.1 | feature_atomic.json | Feature atomic capabilities |
| 2.1.2 | feature_atomic_ibo.json | Feature atomic with IBO |

## Branch 2: Implementation Atomic Capability

### Input Files (from Phase 1)
- `doc.md` - Original design document

### Steps

**Step 2.2.1: 实现原子能力提取**

1. Read doc.md
2. Use `implementation-atomic-capability-extractor` skill
3. Output: implementation_atomic.json

**Step 2.2.2: 接口IBO填充**

1. Read doc.md, implementation_atomic.json
2. Use `interface-ibo-filler` skill
3. Output: implementation_atomic_ibo.json

### Output Files

| Step | Output File | Description |
|------|-------------|-------------|
| 2.2.1 | implementation_atomic.json | Implementation atomic capabilities |
| 2.2.2 | implementation_atomic_ibo.json | Implementation atomic with IBO |

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
