# 测试用例生成工作流 - 目录结构

## 工作目录

```
~/.openclaw/workspace/task_records/<task_id>/
├── task_record.json              # 任务记录
├── doc.md                        # Step1 输出
├── requirements.md               # Step1 输出
├── sub_problems_5w2h.json        # Step2 输出
├── sub_problems.json             # Step2 输出
├── sub_problems_5w2h_replaced.json   # Step3 输出
├── sub_problems_replaced.json    # Step4 输出
├── rules.json                    # Step5 输出
├── usecase.json                  # Step6 输出
├── usecase_with_rule.json        # Step7 输出
├── atomic_capability.json        # Step8 输出
├── logic_testpoint.json          # Step9 输出
├── logic_testcase.json           # Step10 输出
├── interface_testpoint.json      # Step11 输出
└── interface_testcase.json       # Step12 输出
```

## 文件传递依赖

```
[Step1] doc.md, requirements.md
  ↓
[Step2] sub_problems_5w2h.json, sub_problems.json
  ↓
┌───────────────────────────────────┐
│ Step3 (→ sub_problems_5w2h_replaced.json)  │
│ Step4 (→ sub_problems_replaced.json)      │
└───────────────────────────────────┘
  ↓
┌───────────────────────────────────┐
│ Step5 (rules.json)                │
│ Step6 (usecase.json)             │
└───────────────────────────────────┘
  ↓
[Step7] usecase_with_rule.json
  ↓
┌───────────────────────────────────┐
│ 分支1:                             │
│ Step8  → atomic_capability.json   │
│ Step9  → logic_testpoint.json     │
│ Step10 → logic_testcase.json      │
│                                    │
│ 分支2:                             │
│ Step11 → interface_testpoint.json  │
│ Step12 → interface_testcase.json  │
└───────────────────────────────────┘
```

## 绝对路径示例

假设 task_id = `task_tcg_20260506_170000`，work_dir 如下：

```
/home/admin/.openclaw/workspace/task_records/task_tcg_20260506_170000/
├── doc.md
├── requirements.md
├── sub_problems_5w2h.json
├── sub_problems.json
├── sub_problems_5w2h_replaced.json
├── sub_problems_replaced.json
├── rules.json
├── usecase.json
├── usecase_with_rule.json
├── atomic_capability.json
├── logic_testpoint.json
├── logic_testcase.json
├── interface_testpoint.json
└── interface_testcase.json
```

## 派发信息示例

```json
{
  "agentId": "requirement_analyst",
  "stepId": 1,
  "stepName": "需求格式化",
  "skill": "word-to-markdown + requirement-document-preprocessor",
  "inputFiles": ["/path/to/input.docx"],
  "outputFiles": [
    "/home/admin/.openclaw/workspace/task_records/task_tcg_20260506_170000/doc.md",
    "/home/admin/.openclaw/workspace/task_records/task_tcg_20260506_170000/requirements.md"
  ],
  "workDir": "/home/admin/.openclaw/workspace/task_records/task_tcg_20260506_170000",
  "taskRecordPath": "/home/admin/.openclaw/workspace/task_records/task_tcg_20260506_170000/task_record.json"
}
```