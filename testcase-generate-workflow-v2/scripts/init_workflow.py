#!/usr/bin/env python3
"""
init_workflow.py - Initialize testcase-generate-workflow

Creates the task folder and initializes task_record.json.

Usage:
    python3 init_workflow.py <input_doc> [--workspace <workspace_path>] [--task-id <task_id>]

Examples:
    python3 init_workflow.py "/path/to/design.docx"
    python3 init_workflow.py "/path/to/design.md" --workspace ~/.openclaw/workspace
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def generate_task_id() -> str:
    """Generate a task ID with format: task_tcg_YYYYMMDD_HHMMSS"""
    return f"task_tcg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def get_default_workspace() -> str:
    """Get the default workspace path"""
    home = os.path.expanduser("~")
    return os.path.join(home, ".openclaw", "workspace")


def create_task_record(task_id: str, input_doc: str, workspace: str) -> dict:
    """Create the initial task record structure"""
    work_dir = os.path.join(workspace, "task_records", task_id)

    now = datetime.now().isoformat()

    task_record = {
        "id": task_id,
        "name": "测试用例生成工作流",
        "version": "1.0",
        "createdAt": now,
        "updatedAt": now,
        "status": "pending",
        "context": {
            "workspace": workspace,
            "inputDoc": input_doc,
            "workDir": work_dir
        },
        "steps": [
            # Phase 1: Sequential steps
            {"id": "1.1", "name": "需求格式化", "agent": "test-req-preprocessor", "skill": "word-to-markdown + requirement-document-preprocessor", "dependsOn": [], "branch": None, "status": "pending", "task": "将设计文档转换为标准化需求文档", "inputFiles": [input_doc], "outputFiles": [f"{work_dir}/doc.md", f"{work_dir}/requirements.md"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
            {"id": "1.2", "name": "客户问题识别", "agent": "test-req-preprocessor", "skill": "mece-decomposition", "dependsOn": ["1.1"], "branch": None, "status": "pending", "task": "使用mece-decomposition识别客户问题", "inputFiles": [f"{work_dir}/requirements.md", f"{work_dir}/doc.md"], "outputFiles": [f"{work_dir}/sub_problems.json"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
            {"id": "1.3", "name": "5W2H分析", "agent": "test-req-preprocessor", "skill": "5w2h-analysis", "dependsOn": ["1.2"], "branch": None, "status": "pending", "task": "使用5w2h-analysis进行5W2H分析", "inputFiles": [f"{work_dir}/sub_problems.json", f"{work_dir}/doc.md"], "outputFiles": [f"{work_dir}/sub_problems_5w2h.json"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
            {"id": "1.4", "name": "术语替换", "agent": "test-req-preprocessor", "skill": "term-dictionary", "dependsOn": ["1.3"], "branch": None, "status": "pending", "task": "使用term-dictionary进行术语替换", "inputFiles": [f"{work_dir}/sub_problems_5w2h.json", f"{work_dir}/sub_problems.json"], "outputFiles": [f"{work_dir}/sub_problems_5w2h_replaced.json", f"{work_dir}/sub_problems_replaced.json"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
            {"id": "1.5", "name": "L3规则提取", "agent": "test-req-preprocessor", "skill": "l3-rule-extractor", "dependsOn": ["1.4"], "branch": None, "status": "pending", "task": "使用l3-rule-extractor提取L3规则", "inputFiles": [f"{work_dir}/doc.md", f"{work_dir}/sub_problems_5w2h_replaced.json"], "outputFiles": [f"{work_dir}/rule_l3_atom.json"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
            {"id": "1.6", "name": "L4因子拆分", "agent": "test-req-preprocessor", "skill": "l4-factor-extractor", "dependsOn": ["1.5"], "branch": None, "status": "pending", "task": "使用l4-factor-extractor进行L4因子拆分", "inputFiles": [f"{work_dir}/rule_l3_atom.json"], "outputFiles": [f"{work_dir}/rule_l4_factor.json", f"{work_dir}/rule_l3_l4_relation.json"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
            {"id": "1.7", "name": "Usecase提取", "agent": "test-req-preprocessor", "skill": "usecase-extraction", "dependsOn": ["1.6"], "branch": None, "status": "pending", "task": "使用usecase-extraction提取用例", "inputFiles": [f"{work_dir}/sub_problems_5w2h_replaced.json"], "outputFiles": [f"{work_dir}/usecase.json", f"{work_dir}/non_func_req.json"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
            {"id": "1.8", "name": "Usecase规则匹配", "agent": "test-req-preprocessor", "skill": "usecase-rule-matcher", "dependsOn": ["1.7"], "branch": None, "status": "pending", "task": "使用usecase-rule-matcher匹配用例和规则", "inputFiles": [f"{work_dir}/usecase.json", f"{work_dir}/rule_l3_atom.json"], "outputFiles": [f"{work_dir}/usecase_with_rule.json"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
            # Phase 2: Parallel branches
            {"id": "2.1.1", "name": "Feature原子能力提取", "agent": "test-requirement-analyst", "skill": "feature-tree-atomic-extraction", "dependsOn": ["1.8"], "branch": 1, "status": "pending", "task": "使用feature-tree-atomic-extraction提取特性原子能力", "inputFiles": [f"{work_dir}/doc.md"], "outputFiles": [f"{work_dir}/feature_atomic.json"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
            {"id": "2.1.2", "name": "Feature原子IBO填充", "agent": "test-requirement-analyst", "skill": "feature-atomic-ibo-filler", "dependsOn": ["2.1.1"], "branch": 1, "status": "pending", "task": "使用feature-atomic-ibo-filler填充IBO", "inputFiles": [f"{work_dir}/feature_atomic.json", f"{work_dir}/doc.md", f"{work_dir}/rule_l3_atom.json"], "outputFiles": [f"{work_dir}/feature_atomic_ibo.json"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
            {"id": "2.2.1", "name": "实现原子能力提取", "agent": "test-requirement-analyst", "skill": "implementation-atomic-capability-extractor", "dependsOn": ["1.8"], "branch": 2, "status": "pending", "task": "使用implementation-atomic-capability-extractor提取实现原子能力", "inputFiles": [f"{work_dir}/doc.md"], "outputFiles": [f"{work_dir}/implementation_atomic.json"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
            {"id": "2.2.2", "name": "接口IBO填充", "agent": "test-requirement-analyst", "skill": "interface-ibo-filler", "dependsOn": ["2.2.1"], "branch": 2, "status": "pending", "task": "使用interface-ibo-filler填充IBO", "inputFiles": [f"{work_dir}/doc.md", f"{work_dir}/implementation_atomic.json"], "outputFiles": [f"{work_dir}/implementation_atomic_ibo.json"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
            # Phase 3: Parallel branches
            {"id": "3.1.1", "name": "逻辑测试点生成", "agent": "test-design-expert", "skill": "feature-atomic-capability-testpoint-generation", "dependsOn": ["2.1.2"], "branch": 1, "status": "pending", "task": "使用feature-atomic-capability-testpoint-generation生成逻辑测试点", "inputFiles": [f"{work_dir}/feature_atomic_ibo.json"], "outputFiles": [f"{work_dir}/logic_testpoint.json"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
            {"id": "3.1.2", "name": "逻辑测试用例生成", "agent": "test-design-expert", "skill": "testpoint-to-testcase", "dependsOn": ["3.1.1"], "branch": 1, "status": "pending", "task": "使用testpoint-to-testcase生成逻辑测试用例", "inputFiles": [f"{work_dir}/logic_testpoint.json"], "outputFiles": [f"{work_dir}/logic_testcase.json"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
            {"id": "3.1.3", "name": "逻辑测试用例导出", "agent": "test-design-expert", "skill": "logic-testcase-to-excel", "dependsOn": ["3.1.2"], "branch": 1, "status": "pending", "task": "使用logic-testcase-to-excel导出Excel", "inputFiles": [f"{work_dir}/logic_testpoint.json", f"{work_dir}/logic_testcase.json"], "outputFiles": [f"{work_dir}/logic_testcase_export.xlsx"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
            {"id": "3.2.1", "name": "接口测试点生成", "agent": "test-design-expert", "skill": "interface-testpoint-generation", "dependsOn": ["2.2.2"], "branch": 2, "status": "pending", "task": "使用interface-testpoint-generation生成接口测试点", "inputFiles": [f"{work_dir}/implementation_atomic_ibo.json", f"{work_dir}/rule_l3_atom.json"], "outputFiles": [f"{work_dir}/interface_testpoint.json"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
            {"id": "3.2.2", "name": "接口测试用例生成", "agent": "test-design-expert", "skill": "testpoint-to-testcase", "dependsOn": ["3.2.1"], "branch": 2, "status": "pending", "task": "使用testpoint-to-testcase生成接口测试用例", "inputFiles": [f"{work_dir}/interface_testpoint.json"], "outputFiles": [f"{work_dir}/interface_testcase.json"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
            {"id": "3.2.3", "name": "接口测试用例导出", "agent": "test-design-expert", "skill": "interface-testcase-to-excel", "dependsOn": ["3.2.2"], "branch": 2, "status": "pending", "task": "使用interface-testcase-to-excel导出Excel", "inputFiles": [f"{work_dir}/interface_testpoint.json", f"{work_dir}/interface_testcase.json"], "outputFiles": [f"{work_dir}/interface_testcase_export.xlsx"], "completedAt": None, "startedAt": None, "error": None, "retryCount": 0, "notes": None},
        ],
        "completionCriteria": {
            "finalOutputs": [f"{work_dir}/logic_testcase_export.xlsx", f"{work_dir}/interface_testcase_export.xlsx"]
        }
    }

    return task_record


def init_workflow(input_doc: str, workspace: str = None, task_id: str = None) -> dict:
    """Initialize the workflow - create directories and task record"""

    if workspace is None:
        workspace = get_default_workspace()

    if task_id is None:
        task_id = generate_task_id()

    work_dir = os.path.join(workspace, "task_records", task_id)

    # Create directories
    os.makedirs(work_dir, exist_ok=True)

    # Create task record
    task_record = create_task_record(task_id, input_doc, workspace)

    # Write task record
    task_record_path = os.path.join(work_dir, "task_record.json")
    with open(task_record_path, 'w', encoding='utf-8') as f:
        json.dump(task_record, f, ensure_ascii=False, indent=2)

    return {
        "taskId": task_id,
        "workDir": work_dir,
        "taskRecordPath": task_record_path,
        "status": "initialized"
    }


def main():
    parser = argparse.ArgumentParser(description="Initialize testcase-generate-workflow")
    parser.add_argument("input_doc", help="Path to input design document (.docx or .md)")
    parser.add_argument("--workspace", help="Workspace path (default: ~/.openclaw/workspace)")
    parser.add_argument("--task-id", help="Custom task ID (default: auto-generated)")

    args = parser.parse_args()

    # Validate input file exists
    if not os.path.exists(args.input_doc):
        print(f"Error: Input file not found: {args.input_doc}", file=sys.stderr)
        sys.exit(1)

    result = init_workflow(args.input_doc, args.workspace, args.task_id)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
