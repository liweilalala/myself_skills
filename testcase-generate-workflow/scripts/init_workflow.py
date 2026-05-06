#!/usr/bin/env python3
"""
初始化测试用例生成工作流所需的Agent注册表
直接操作 agent_registry.json，不嵌套调用
"""
import json
import os

def main():
    registry_path = os.path.expanduser("~/.openclaw/workspace/agent_registry.json")
    
    # 确保目录存在
    os.makedirs(os.path.dirname(registry_path), exist_ok=True)
    
    # 构建测试用例生成工作流专用的Agent注册表
    registry_template = {
        "agents": [
            {
                "id": "requirement_analyst",
                "name": "需求分析师",
                "description": "负责需求分析阶段的各项工作，包括需求格式化、客户问题识别、术语替换、规则拆分、usecase提取和匹配",
                "capabilities": [
                    "word-to-markdown",
                    "requirement-document-preprocessor",
                    "requirement-analysis-decomposition",
                    "term-dictionary",
                    "rule-split",
                    "usecase-extraction",
                    "usecase-rule-matcher"
                ],
                "workspace": "~/.openclaw/agents/requirement_analyst/workspace"
            },
            {
                "id": "test_designer",
                "name": "测试设计师",
                "description": "负责测试用例生成阶段的工作，包括原子能力提取、逻辑测试点生成、接口测试点生成、测试用例生成",
                "capabilities": [
                    "atomic-capability-with-ibo-extraction",
                    "feature-tree-testpoint-generation",
                    "implement-testpoint-generation-workflow",
                    "testpoint-to-testcase"
                ],
                "workspace": "~/.openclaw/agents/test_designer/workspace"
            }
        ],
        "registry_version": "1.0"
    }
    
    # 写入注册表
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry_template, f, ensure_ascii=False, indent=2)
    
    print(f"Agent注册表已写入: {registry_path}")


if __name__ == "__main__":
    main()
