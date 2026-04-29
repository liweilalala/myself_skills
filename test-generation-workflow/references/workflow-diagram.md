# Test Workflow Diagram

## 工作流全景图

```
输入：设计文档（.docx 或 .md）
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ 阶段0：初始化                                           │
│  - 生成 taskId（如 task_20260429_101000）              │
│  - 创建任务文件夹                                       │
│  - 文档预处理（word→markdown 或直接使用）               │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ 阶段1：需求分析（requirement_analyst）                   │
│                                                         │
│ 输入：doc.md                                            │
│ Skill：testing-requirement-analysis                     │
│                                                         │
│ 输出：                                                  │
│  - rule_split_analysis.json（规则拆分结果）            │
│  - usecase_with_rule.json（用例+规则）                  │
│                                                         │
│ 监控：持续检查直到任务完成，检查输出文件                 │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ 阶段2.1：特性原子能力测试点生成（test_designer）         │
│                                                         │
│ Step 2.1.1：                                            │
│   输入：doc.md + rule_split_analysis.json               │
│   Skill：atomic-capability-with-ibo-extraction         │
│   输出：atomic-capability.json                         │
│                                                         │
│ Step 2.1.2：                                            │
│   输入：atomic-capability.json                         │
│   Skill：feature-tree-testpoint-generation              │
│   输出：logic_testpoints.json（逻辑测试点）             │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ 阶段2.2：实现原子能力测试点生成（test_designer）         │
│                                                         │
│ 输入：doc.md                                            │
│ Skill：implement-testpoint-generation-workflow          │
│ 输出：interface_testpoints.json（接口测试点）           │
└─────────────────────────────────────────────────────────┘
         │
         ▼
最终产出：<taskId>/ 文件夹下所有测试点文件
```

## 文件说明

### 输入文件

| 文件 | 说明 | 来源 |
|------|------|------|
| 设计文档.docx/.md | 原始设计文档 | 用户提供 |

### 中间文件

| 文件 | 说明 | 阶段 |
|------|------|------|
| doc.md | 预处理后的设计文档 | 阶段0 |
| rule_split_analysis.json | 规则拆分分析结果 | 阶段1 |
| usecase_with_rule.json | 用例与规则关联 | 阶段1 |
| atomic-capability.json | 原子能力清单 | 阶段2.1.1 |
| logic_testpoints.json | 逻辑测试点 | 阶段2.1.2 |
| interface_testpoints.json | 接口测试点 | 阶段2.2 |

## Agent职责

### requirement_analyst

- **职责**：需求分析
- **输入**：doc.md
- **Skill**：testing-requirement-analysis
- **输出**：rule_split_analysis.json, usecase_with_rule.json
- **工作目录**：~/.openclaw/agents/requirement_analyst/workspace/

### test_designer

- **职责**：测试点生成
- **输入**：各种中间产物
- **Skill**：atomic-capability-with-ibo-extraction, feature-tree-testpoint-generation, implement-testpoint-generation-workflow
- **输出**：atomic-capability.json, logic_testpoints.json, interface_testpoints.json
- **工作目录**：~/.openclaw/agents/test_designer/workspace/

## 任务ID命名规范

格式：`task_YYYYMMDD_HHMMSS`

示例：
- task_20260429_101000
- task_20260428_162248

## 关键检查点

| 阶段 | 检查点 | 预期文件 |
|------|--------|---------|
| 阶段1完成 | requirement_analyst任务结束 | rule_split_analysis.json, usecase_with_rule.json |
| 阶段2.1.1完成 | atomic-capability生成结束 | atomic-capability.json |
| 阶段2.1.2完成 | 逻辑测试点生成结束 | logic_testpoints.json |
| 阶段2.2完成 | 接口测试点生成结束 | interface_testpoints.json |
