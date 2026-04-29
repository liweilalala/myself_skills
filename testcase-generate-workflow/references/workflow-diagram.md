# Test Generation Workflow - 工作流详细说明

## 工作流阶段

```
Step 0: 初始化
  - 生成任务ID: task_YYYYMMDD_HHMM
  - 创建文件夹: ~/.openclaw/workspace/<taskId>/
  - 文档预处理: docx → doc.md 或 直接复制md
  - 复制 rule_split_analysis.json 到任务文件夹

Step 1: atomic-capability-with-ibo-extraction
  输入: doc.md + rule_split_analysis.json
  输出: atomic-capability.json

Step 2: feature-tree-testpoint-generation
  输入: atomic-capability.json
  输出: logic_testpoint.json

Step 3: implement-testpoint-generation-workflow
  输入: doc.md
  输出: interface_testpoint.json

Step 4a: testpoint-to-testcase (logic)
  输入: logic_testpoint.json
  输出: logic_testcase.json

Step 4b: testpoint-to-testcase (interface)
  输入: interface_testpoint.json
  输出: interface_testcase.json
```

## 文件格式规范

### atomic-capability.json
```json
{
  "capabilities": [
    {
      "id": "CAP-001",
      "name": "能力名称",
      "description": "能力描述",
      "ibo": "独立构建块",
      "testable": true
    }
  ]
}
```

### logic_testpoint.json
```json
{
  "testpoints": [
    {
      "id": "TP-001",
      "capability_id": "CAP-001",
      "scenario": "测试场景",
      "steps": ["步骤1", "步骤2"],
      "expected": "预期结果"
    }
  ]
}
```

### interface_testpoint.json
```json
{
  "testpoints": [
    {
      "id": "ITP-001",
      "interface": "接口名称",
      "method": "GET/POST/PUT/DELETE",
      "params": {},
      "expected_response": {}
    }
  ]
}
```

### logic_testcase.json / interface_testcase.json
```json
{
  "testcases": [
    {
      "id": "TC-001",
      "testpoint_id": "TP-001",
      "title": "用例标题",
      "preconditions": [],
      "test_steps": ["步骤1", "步骤2"],
      "expected_results": ["结果1", "结果2"],
      "priority": "high/medium/low"
    }
  ]
}
```

## Agent配置

| Step | Agent | Skill |
|------|-------|-------|
| Step 0 | main (self) | word-to-markdown (if needed) |
| Step 1 | test_designer | atomic-capability-with-ibo-extraction |
| Step 2 | test_designer | feature-tree-testpoint-generation |
| Step 3 | test_designer | implement-testpoint-generation-workflow |
| Step 4 | test_designer | testpoint-to-testcase |

## 监控任务状态

```bash
ls -la ~/.openclaw/workspace/<taskId>/
```