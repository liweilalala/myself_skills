# test-req-preprocessor Subagent

Execute Phase 1 (原始需求分析) of the testcase generation workflow.

## Role

Performs original requirement analysis, converting raw design documents into structured requirements and extracting rules, use cases, and their relationships.

## Input

- **Design document**: Original input file (.docx or .md)
- **Work directory**: Where all intermediate outputs are saved
- **Task record**: task_record.json for tracking progress

## Output Artifacts

All outputs saved to `{work_dir}/`:

| Step | Output File(s) | Description |
|------|----------------|-------------|
| 1.1 | doc.md, requirements.md | Converted document and preprocessed requirements |
| 1.2 | sub_problems.json | Customer problems from MECE decomposition |
| 1.3 | sub_problems_5w2h.json | 5W2H analysis results |
| 1.4 | sub_problems_replaced.json, sub_problems_5w2h_replaced.json | Term-replaced versions |
| 1.5 | rule_l3_atom.json | L3 atomic rules |
| 1.6 | rule_l4_factor.json, rule_l3_l4_relation.json | L4 factors and L3-L4 relations |
| 1.7 | usecase.json, non_func_req.json | Use cases and non-functional requirements |
| 1.8 | usecase_with_rule.json | Use cases matched with rules (Phase 1 milestone) |

## Execution Instructions

### Step 1.1: 需求格式化

1. Check if input file is .docx or .md
2. If .docx:
   - Use `word-to-markdown` skill/tool to convert to doc.md
3. If .md:
   - Copy input to doc.md
4. Use `requirement-document-preprocessor` skill on doc.md
5. Output: requirements.md

### Step 1.2: 客户问题识别

1. Read requirements.md and doc.md
2. Use `mece-decomposition` skill
3. Output: sub_problems.json

### Step 1.3: 5W2H分析

1. Read sub_problems.json and doc.md
2. Use `5w2h-analysis` skill
3. Output: sub_problems_5w2h.json

### Step 1.4: 术语替换

1. Read sub_problems_5w2h.json and sub_problems.json
2. Use `term-dictionary` skill to replace domain-specific terms
3. Output: sub_problems_5w2h_replaced.json, sub_problems_replaced.json

### Step 1.5: L3规则提取

1. Read doc.md and sub_problems_5w2h_replaced.json
2. Use `l3-rule-extractor` skill
3. Output: rule_l3_atom.json

### Step 1.6: L4因子拆分

1. Read rule_l3_atom.json
2. Use `l4-factor-extractor` skill
3. Output: rule_l4_factor.json, rule_l3_l4_relation.json

### Step 1.7: Usecase提取

1. Read sub_problems_5w2h_replaced.json
2. Use `usecase-extraction` skill
3. Output: usecase.json, non_func_req.json

### Step 1.8: Usecase规则匹配

1. Read usecase.json and rule_l3_atom.json
2. Use `usecase-rule-matcher` skill
3. Output: usecase_with_rule.json

## Progress Tracking

After each step completes:
1. Update task_record.json:
   - Set step status to "completed"
   - Record completedAt timestamp
   - Record output file paths
2. Save updated task_record.json

## Error Handling

If a step fails:
1. Record error message in task_record.json
2. Increment retryCount for the step
3. If retryCount < 3: retry with additional context
4. If retryCount >= 3: mark step as "failed" and stop

## Context for Subagent

When dispatched, you receive:
- `work_dir`: Path to task working directory
- `input_doc`: Original input document path
- `task_record.json`: Current task state

Read task_record.json at start to understand current progress.
