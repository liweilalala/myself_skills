# Agent Registry

> ⚠️ 此文件由初始化命令自动生成，请勿手动修改

## 可用子Agent

| Agent ID | 名称 | 工作目录 |
|----------|------|---------|
| requirement_analyst | 需求分析Agent | ~/.openclaw/agents/requirement_analyst/workspace |
| test_designer | 测试设计Agent | ~/.openclaw/agents/test_designer/workspace |

## Agent职责说明

### requirement_analyst
- **职责**：需求分析
- **使用skill**：testing-requirement-analysis
- **产出**：rule_split_analysis.json, usecase_with_rule.json

### test_designer
- **职责**：测试点/测试用例生成
- **使用skill**：testcase-generate-workflow
- **产出**：logic_testcase.json, interface_testcase.json

## 最后更新

- 更新时间：2026-04-29 17:17 GMT+8
- 更新原因：用户请求创建requirement-to-testpoint-workflow skill