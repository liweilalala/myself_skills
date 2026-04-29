---
name: testcase-generate-workflow
description: 从设计文档生成完整测试用例的工作流编排skill。输入设计文档（Word .docx 或 Markdown .md）和规则拆分结果（rule_split_analysis.json），依次执行：1）atomic-capability-with-ibo-extraction生成atomic-capability.json；2）feature-tree-testpoint-generation生成logic_testpoint.json；3）implement-testpoint-generation-workflow生成interface_testpoint.json；4）testpoint-to-testcase分别生成logic_testcase.json和interface_testcase.json。触发条件：用户要求"执行测试工作流"、"从设计文档生成测试用例"、"测试用例生成"。
---

# Test Generation Workflow Orchestrator

## 概述

编排从**设计文档**到**测试用例**的完整工作流。

**输入**：
- 设计文档（`.docx` → 转换为 `doc.md`；`.md` → 直接作为 `doc.md`）
- `rule_split_analysis.json` — 格式化的规则拆分结果

**输出**：`logic_testcase.json`、`interface_testcase.json`

## 工作流程

```
输入预处理
    ↓
Step 1: atomic-capability-with-ibo-extraction → atomic-capability.json
    ↓
Step 2: feature-tree-testpoint-generation → logic_testpoint.json
    ↓
Step 3: implement-testpoint-generation-workflow → interface_testpoint.json
    ↓
Step 4: testpoint-to-testcase → logic_testcase.json + interface_testcase.json
```

## 执行步骤

### Step 0: 初始化

**生成任务ID**：
```bash
date +%Y%m%d_%H%M
# 例如：task_20260429_1629
```

**创建任务文件夹**：
```
~/.openclaw/workspace/<taskId>/
```

**文档预处理**：
- `.docx` → 启动sub-agent用word-to-markdown转换为`doc.md`
- `.md` → 直接复制为`doc.md`
- 将`rule_split_analysis.json`复制到任务文件夹

### Step 1: 生成 atomic-capability.json

启动sub-agent执行`atomic-capability-with-ibo-extraction` skill：

```
输入：doc.md + rule_split_analysis.json
输出：atomic-capability.json
```

### Step 2: 生成 logic_testpoint.json

启动sub-agent执行`feature-tree-testpoint-generation` skill：

```
输入：atomic-capability.json
输出：logic_testpoint.json
```

### Step 3: 生成 interface_testpoint.json

启动sub-agent执行`implement-testpoint-generation-workflow` skill：

```
输入：doc.md
输出：interface_testpoint.json
```

### Step 4: 生成测试用例

**4a.** 启动sub-agent执行`testpoint-to-testcase` skill处理logic_testpoint.json：

```
输入：logic_testpoint.json
输出：logic_testcase.json
```

**4b.** 启动sub-agent执行`testpoint-to-testcase` skill处理interface_testpoint.json：

```
输入：interface_testpoint.json
输出：interface_testcase.json
```

## 任务执行策略

**逐个执行**：每个step启动一个sub-agent，等待完成后检查输出文件，再启动下一个。

**检查点**：每个step完成后验证输出文件存在且非空（大小>0）。检查命令：
```bash
ls -la ~/.openclaw/workspace/<taskId>/
```

**错误处理**：
- sub-agent执行失败 → 记录错误，询问用户重试或跳过
- 文件缺失 → 终止并报告

**任务文件夹结构**：
```
~/.openclaw/workspace/<taskId>/
├── doc.md                      # 预处理后的设计文档
├── rule_split_analysis.json    # 输入的规则拆分结果
├── atomic-capability.json      # Step 1产出
├── logic_testpoint.json        # Step 2产出
├── interface_testpoint.json    # Step 3产出
├── logic_testcase.json         # Step 4a产出
└── interface_testcase.json     # Step 4b产出
```