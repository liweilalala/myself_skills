---
name: test-generation-workflow
description: 测试工作流编排：从需求分析到测试点生成的完整流程。输入设计文档（Word或Markdown），依次执行需求分析、特性原子能力测试点生成、实现原子能力测试点生成三个阶段。触发条件：用户要求"执行测试工作流"、"从设计文档生成测试点"、"需求到测试点"。
---

# Test Workflow Orchestrator

## 概述

此skill用于编排从**设计文档**到**测试点生成**的完整测试工作流。

**输入**：设计文档（.docx 或 .md）
**输出**：包含各类测试点的完整文件夹

## 核心概念

- **任务ID**：每次工作流执行生成唯一ID，格式 `task_YYYYMMDD_HHMMSS`
- **工作目录**：`~/.openclaw/agents/<agentId>/workspace/<taskId>/`
- **阶段Agent**：
  - `requirement_analyst` → 需求分析
  - `test_designer` → 测试点生成

## 工作流阶段

```
┌─────────────────────────────────────────────────────────────────┐
│ 阶段1：需求分析（requirement_analyst）                            │
│   └→ rule_split_analysis.json                                   │
│   └→ usecase_with_rule.json                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 阶段2.1：特性原子能力测试点生成（test_designer）                  │
│   ├→ atomic-capability.json（从 doc.md + rule_split_analysis.json）│
│   └→ 逻辑测试点（从 atomic-capability.json）                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 阶段2.2：实现原子能力测试点生成（test_designer）                   │
│   └→ 接口测试点（从 doc.md）                                      │
└─────────────────────────────────────────────────────────────────┘
```

## 工作流程

### 阶段0：初始化

**生成任务ID**：
```bash
date +%Y%m%d_%H%M%S  # 例如：task_20260429_101000
```

**创建任务文件夹**：
```bash
mkdir -p ~/.openclaw/agents/requirement_analyst/workspace/<taskId>/
mkdir -p ~/.openclaw/agents/test_designer/workspace/<taskId>/
```

**文档预处理**：
- 如果输入是 `.docx` 文件：使用 `word-to-markdown` 转换为 `doc.md`
- 如果输入是 `.md` 文件：直接作为 `doc.md`
- 将预处理后的 `doc.md` 放入 `<taskId>/` 文件夹

### 阶段1：需求分析

**启动 `requirement_analyst`**：

使用 `sessions_spawn` 或 `openclaw agent` 派发任务：

```
agentId: requirement_analyst
task: |
  请处理设计文档 doc.md，执行需求分析。
  使用 testing-requirement-analysis skill 进行处理。
  处理完成后，在工作目录下创建一个以任务ID命名的文件夹，例如 task_20260428_162248_5605。
  完成后汇报。
```

**监控任务状态**：
- 每10-30秒检查 `sessions_list` 或 `subagents`
- 等待任务完成（可监控文件夹内容变化）

**产出检查**：
确认以下文件存在：
- `rule_split_analysis.json` — 规则拆分结果
- `usecase_with_rule.json` — 生成的usecase结果

### 阶段2.1：特性原子能力测试点生成

**Step 2.1.1：生成 atomic-capability.json**

启动 `test_designer` 执行 `atomic-capability-with-ibo-extraction` skill：

```
agentId: test_designer
task: |
  请处理以下文件，生成原子能力清单：
  - 输入：doc.md 和 rule_split_analysis.json
  - 执行：atomic-capability-with-ibo-extraction skill
  - 输出：atomic-capability.json
  保存到 <taskId>/atomic-capability.json
```

**Step 2.1.2：生成逻辑测试点**

启动 `test_designer` 执行 `feature-tree-testpoint-generation` skill：

```
agentId: test_designer
task: |
  请基于 atomic-capability.json 生成逻辑测试点：
  - 输入：atomic-capability.json
  - 执行：feature-tree-testpoint-generation skill
  - 输出：logic_testpoints.json 或类似文件
  保存到 <taskId>/
```

### 阶段2.2：实现原子能力测试点生成

**Step 2.2.1：生成接口测试点**

启动 `test_designer` 执行 `implement-testpoint-generation-workflow` skill：

```
agentId: test_designer
task: |
  请基于设计文档生成接口测试点：
  - 输入：doc.md
  - 执行：implement-testpoint-generation-workflow skill
  - 输出：interface_testpoints.json 或类似文件
  保存到 <taskId>/
```

## 任务执行策略

### 逐个执行原则

由于任务复杂、上下文有限，采用**逐个执行**策略：

1. **启动一个sub-agent** → 等待完成 → 检查输出文件
2. **有输出文件** → 启动下一个sub-agent
3. **无输出文件** → 诊断错误，记录日志，重新尝试或跳过

### 检查点机制

每个阶段完成后检查：
- 输出文件是否存在？
- 文件内容是否完整（大小 > 0）？
- 格式是否符合预期（JSON可解析）？

### 错误处理

- **Agent执行失败**：记录错误信息，询问用户是跳过还是重试
- **文件缺失**：终止当前阶段，向用户报告缺失文件和预期输入
- **部分完成**：返回已完成的部分结果，说明未完成阶段

## SKILL.md 使用方式

此skill被触发后，按以下步骤执行：

1. **解析输入**：确认设计文档路径
2. **初始化**：生成taskId，创建文件夹，预处理文档
3. **执行阶段1**：启动 requirement_analyst，监控直到完成
4. **检查产出**：确认 rule_split_analysis.json 和 usecase_with_rule.json
5. **执行阶段2.1**：依次执行 atomic-capability 和逻辑测试点生成
6. **执行阶段2.2**：执行接口测试点生成
7. **汇总报告**：向用户报告所有输出文件位置

## scripts/

### workflow_monitor.py

工作流监控脚本，用于检查任务状态和产出文件：

```python
#!/usr/bin/env python3
"""
workflow_monitor.py - 监控工作流任务状态和产出文件
用法: python3 workflow_monitor.py <taskId> [agentId]
"""
import sys
import json
from pathlib import Path
from datetime import datetime

def main():
    if len(sys.argv) < 2:
        print("用法: workflow_monitor.py <taskId> [agentId]")
        sys.exit(1)
    
    task_id = sys.argv[1]
    agent_id = sys.argv[2] if len(sys.argv) > 2 else "test_designer"
    
    workspace = Path.home() / ".openclaw" / "agents" / agent_id / "workspace" / task_id
    
    if not workspace.exists():
        print(f"[错误] 任务文件夹不存在: {workspace}")
        sys.exit(1)
    
    # 列出所有文件
    print(f"=== 任务文件夹内容: {task_id} ===")
    for f in sorted(workspace.rglob("*")):
        if f.is_file():
            size = f.stat().st_size
            print(f"  {f.relative_to(workspace)} ({size} bytes)")
    
    # 检查关键产出文件
    key_files = [
        "rule_split_analysis.json",
        "usecase_with_rule.json",
        "atomic-capability.json",
        "logic_testpoints.json",
        "interface_testpoints.json"
    ]
    
    print(f"\n=== 关键产出文件检查 ===")
    for fname in key_files:
        fpath = workspace / fname
        if fpath.exists():
            print(f"  ✓ {fname}")
        else:
            print(f"  ✗ {fname} (缺失)")

if __name__ == "__main__":
    main()
```

## references/

### workflow-diagram.md

工作流阶段详细说明和文件格式规范。
