#!/usr/bin/env python3
"""
创建测试用例生成任务记录
在 task_records 下创建以任务ID命名的文件夹，所有中间文件都存放在此文件夹中
"""
import json
import sys
import os
from datetime import datetime

TASK_TEMPLATE = {
    "id": "",
    "name": "测试用例生成工作流",
    "status": "pending",
    "currentStep": 0,
    "context": {
        "workspace": "",
        "inputDoc": "",
        "workDir": "",
        "outputDir": ""
    },
    "steps": [
        {
            "id": 1,
            "name": "需求格式化",
            "agent": "requirement_analyst",
            "skill": "word-to-markdown + requirement-document-preprocessor",
            "dependsOn": [],
            "inputFiles": [],
            "outputFiles": [],
            "status": "pending",
            "task": "将设计文档转换为标准化需求文档"
        },
        {
            "id": 2,
            "name": "客户问题识别",
            "agent": "requirement_analyst",
            "skill": "requirement-analysis-decomposition",
            "dependsOn": [1],
            "inputFiles": [],
            "outputFiles": [],
            "status": "pending",
            "task": "从需求文档中识别客户子问题"
        },
        {
            "id": 3,
            "name": "术语替换-5w2h",
            "agent": "requirement_analyst",
            "skill": "term-dictionary",
            "dependsOn": [2],
            "inputFiles": [],
            "outputFiles": [],
            "status": "pending",
            "task": "替换sub_problems_5w2h.json中的术语"
        },
        {
            "id": 4,
            "name": "术语替换-subprob",
            "agent": "requirement_analyst",
            "skill": "term-dictionary",
            "dependsOn": [2],
            "inputFiles": [],
            "outputFiles": [],
            "status": "pending",
            "task": "替换sub_problems.json中的术语"
        },
        {
            "id": 5,
            "name": "规则拆分",
            "agent": "requirement_analyst",
            "skill": "rule-split",
            "dependsOn": [3, 4],
            "inputFiles": [],
            "outputFiles": [],
            "status": "pending",
            "task": "从sub_problems_5w2h_replaced.json抽取出规则"
        },
        {
            "id": 6,
            "name": "Usecase提取",
            "agent": "requirement_analyst",
            "skill": "usecase-extraction",
            "dependsOn": [3, 4],
            "inputFiles": [],
            "outputFiles": [],
            "status": "pending",
            "task": "从sub_problems_5w2h_replaced.json中抽取usecase"
        },
        {
            "id": 7,
            "name": "Usecase规则匹配",
            "agent": "requirement_analyst",
            "skill": "usecase-rule-matcher",
            "dependsOn": [5, 6],
            "inputFiles": [],
            "outputFiles": [],
            "status": "pending",
            "task": "将usecase与规则进行匹配"
        },
        {
            "id": 8,
            "name": "原子能力提取",
            "agent": "test_designer",
            "skill": "atomic-capability-with-ibo-extraction",
            "dependsOn": [7],
            "inputFiles": [],
            "outputFiles": [],
            "status": "pending",
            "task": "从doc.md和rules.json提取原子能力",
            "branch": 1
        },
        {
            "id": 9,
            "name": "逻辑测试点生成",
            "agent": "test_designer",
            "skill": "feature-tree-testpoint-generation",
            "dependsOn": [8],
            "inputFiles": [],
            "outputFiles": [],
            "status": "pending",
            "task": "从atomic_capability.json生成逻辑测试点",
            "branch": 1
        },
        {
            "id": 10,
            "name": "逻辑测试用例生成",
            "agent": "test_designer",
            "skill": "testpoint-to-testcase",
            "dependsOn": [9],
            "inputFiles": [],
            "outputFiles": [],
            "status": "pending",
            "task": "将logic_testpoint.json转换为logic_testcase.json",
            "branch": 1
        },
        {
            "id": 11,
            "name": "接口测试点生成",
            "agent": "test_designer",
            "skill": "implement-testpoint-generation-workflow",
            "dependsOn": [7],
            "inputFiles": [],
            "outputFiles": [],
            "status": "pending",
            "task": "从doc.md生成interface_testpoint.json",
            "branch": 2
        },
        {
            "id": 12,
            "name": "接口测试用例生成",
            "agent": "test_designer",
            "skill": "testpoint-to-testcase",
            "dependsOn": [11],
            "inputFiles": [],
            "outputFiles": [],
            "status": "pending",
            "task": "将interface_testpoint.json转换为interface_testcase.json",
            "branch": 2
        }
    ]
}

# 文件路径映射
FILE_MAPPING = {
    1: {"inputs": ["{inputDoc}"], "outputs": ["doc.md", "requirements.md"]},
    2: {"inputs": ["requirements.md"], "outputs": ["sub_problems_5w2h.json", "sub_problems.json"]},
    3: {"inputs": ["sub_problems_5w2h.json"], "outputs": ["sub_problems_5w2h_replaced.json"]},
    4: {"inputs": ["sub_problems.json"], "outputs": ["sub_problems_replaced.json"]},
    5: {"inputs": ["sub_problems_5w2h_replaced.json"], "outputs": ["rules.json"]},
    6: {"inputs": ["sub_problems_5w2h_replaced.json"], "outputs": ["usecase.json"]},
    7: {"inputs": ["usecase.json", "rules.json"], "outputs": ["usecase_with_rule.json"]},
    8: {"inputs": ["doc.md", "rules.json"], "outputs": ["atomic_capability.json"]},
    9: {"inputs": ["atomic_capability.json"], "outputs": ["logic_testpoint.json"]},
    10: {"inputs": ["logic_testpoint.json"], "outputs": ["logic_testcase.json"]},
    11: {"inputs": ["doc.md"], "outputs": ["interface_testpoint.json"]},
    12: {"inputs": ["interface_testpoint.json"], "outputs": ["interface_testcase.json"]}
}


def build_file_paths(work_dir: str, input_doc: str) -> dict:
    """根据工作目录构建所有步骤的文件绝对路径"""
    paths = {}
    
    # Step 1: 需求格式化
    paths[1] = {
        "inputFiles": [os.path.abspath(input_doc)],
        "outputFiles": [os.path.join(work_dir, "doc.md"), os.path.join(work_dir, "requirements.md")]
    }
    
    # Step 2: 客户问题识别
    paths[2] = {
        "inputFiles": [os.path.join(work_dir, "requirements.md")],
        "outputFiles": [os.path.join(work_dir, "sub_problems_5w2h.json"), os.path.join(work_dir, "sub_problems.json")]
    }
    
    # Step 3: 术语替换-5w2h
    paths[3] = {
        "inputFiles": [os.path.join(work_dir, "sub_problems_5w2h.json")],
        "outputFiles": [os.path.join(work_dir, "sub_problems_5w2h_replaced.json")]
    }
    
    # Step 4: 术语替换-subprob
    paths[4] = {
        "inputFiles": [os.path.join(work_dir, "sub_problems.json")],
        "outputFiles": [os.path.join(work_dir, "sub_problems_replaced.json")]
    }
    
    # Step 5: 规则拆分
    paths[5] = {
        "inputFiles": [os.path.join(work_dir, "sub_problems_5w2h_replaced.json")],
        "outputFiles": [os.path.join(work_dir, "rules.json")]
    }
    
    # Step 6: Usecase提取
    paths[6] = {
        "inputFiles": [os.path.join(work_dir, "sub_problems_5w2h_replaced.json")],
        "outputFiles": [os.path.join(work_dir, "usecase.json")]
    }
    
    # Step 7: Usecase规则匹配
    paths[7] = {
        "inputFiles": [os.path.join(work_dir, "usecase.json"), os.path.join(work_dir, "rules.json")],
        "outputFiles": [os.path.join(work_dir, "usecase_with_rule.json")]
    }
    
    # Step 8: 原子能力提取
    paths[8] = {
        "inputFiles": [os.path.join(work_dir, "doc.md"), os.path.join(work_dir, "rules.json")],
        "outputFiles": [os.path.join(work_dir, "atomic_capability.json")]
    }
    
    # Step 9: 逻辑测试点生成
    paths[9] = {
        "inputFiles": [os.path.join(work_dir, "atomic_capability.json")],
        "outputFiles": [os.path.join(work_dir, "logic_testpoint.json")]
    }
    
    # Step 10: 逻辑测试用例生成
    paths[10] = {
        "inputFiles": [os.path.join(work_dir, "logic_testpoint.json")],
        "outputFiles": [os.path.join(work_dir, "logic_testcase.json")]
    }
    
    # Step 11: 接口测试点生成
    paths[11] = {
        "inputFiles": [os.path.join(work_dir, "doc.md")],
        "outputFiles": [os.path.join(work_dir, "interface_testpoint.json")]
    }
    
    # Step 12: 接口测试用例生成
    paths[12] = {
        "inputFiles": [os.path.join(work_dir, "interface_testpoint.json")],
        "outputFiles": [os.path.join(work_dir, "interface_testcase.json")]
    }
    
    return paths


def create_task(input_doc_path: str, workspace: str = None) -> str:
    """创建测试用例生成任务"""
    if workspace is None:
        workspace = os.path.expanduser("~/.openclaw/workspace")
    
    # 生成任务ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_id = f"task_tcg_{timestamp}"
    
    # 构建任务记录
    task_record = json.loads(json.dumps(TASK_TEMPLATE))  # 深拷贝
    task_record["id"] = task_id
    task_record["context"]["workspace"] = workspace
    task_record["context"]["inputDoc"] = os.path.abspath(input_doc_path)
    
    # 工作目录：task_records/<task_id>/
    work_dir = os.path.join(workspace, "task_records", task_id)
    task_record["context"]["workDir"] = work_dir
    task_record["context"]["outputDir"] = work_dir  # 输出目录也指向工作目录
    
    # 创建工作目录
    os.makedirs(work_dir, exist_ok=True)
    
    # 构建文件路径并填充到步骤中
    file_paths = build_file_paths(work_dir, input_doc_path)
    for step in task_record["steps"]:
        step_id = step["id"]
        if step_id in file_paths:
            step["inputFiles"] = file_paths[step_id]["inputFiles"]
            step["outputFiles"] = file_paths[step_id]["outputFiles"]
    
    # 保存任务记录
    task_file = os.path.join(work_dir, "task_record.json")
    with open(task_file, "w", encoding="utf-8") as f:
        json.dump(task_record, f, ensure_ascii=False, indent=2)
    
    print(f"任务已创建: {task_id}")
    print(f"工作目录: {work_dir}")
    print(f"任务记录: {task_file}")
    
    return task_id


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 create_task.py <设计文档路径> [workspace]")
        sys.exit(1)
    
    input_doc = sys.argv[1]
    workspace = sys.argv[2] if len(sys.argv) > 2 else None
    
    task_id = create_task(input_doc, workspace)
    print(task_id)