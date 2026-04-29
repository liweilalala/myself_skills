# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

This is a skills repository containing skill modules for task orchestration. Each skill is self-contained with its own `SKILL.md`, `scripts/`, and `references/` directories.

### Skills

- **agent-orchestrator/**: Multi-agent task scheduling and monitoring. Uses `sessions_spawn` to dispatch tasks to sub-agents, monitors via `sessions_list` and `subagents`.
- **test-generation-workflow/**: Test workflow orchestration from design documents to test point generation. Three-phase pipeline: requirement analysis → feature atomic capability test points → implementation atomic capability test points.

### Key Files

| Path | Purpose |
|------|---------|
| `agent-orchestrator/SKILL.md` | Main agent orchestrator documentation |
| `agent-orchestrator/scripts/monitor_agent.py` | Sub-agent status monitoring script |
| `agent-orchestrator/references/agent-api.md` | Sessions tool API reference |
| `test-generation-workflow/SKILL.md` | Test workflow documentation |
| `test-generation-workflow/references/workflow-diagram.md` | Workflow phase diagram and file specifications |

## Core Concepts

### Sub-agent Workspace Structure

```
~/.openclaw/agents/<agentId>/workspace/
├── AGENTS.md         # Agent config
├── SOUL.md           # Agent identity
├── USER.md           # User info
└── memory/
    └── YYYY-MM-DD.md  # Daily execution logs
```

### Task Execution Pattern

1. **Spawn**: `sessions_spawn(runtime="subagent", agentId="<id>", task="<desc>", mode="run")`
2. **Monitor**: `sessions_list(kinds=["subagent"], activeMinutes=<N>)` or `subagents(action="list")`
3. **Collect**: Check workspace directory for output files

### Test Workflow Phases

1. **Phase 1**: `requirement_analyst` → `rule_split_analysis.json`, `usecase_with_rule.json`
2. **Phase 2.1**: `test_designer` → `atomic-capability.json`, `logic_testpoints.json`
3. **Phase 2.2**: `test_designer` → `interface_testpoints.json`

Task IDs use format `task_YYYYMMDD_HHMMSS`.

## Commands

### Monitor Sub-agent Status

```bash
python3 agent-orchestrator/scripts/monitor_agent.py <agentId>
```

### Monitor Workflow Task

```bash
python3 test-generation-workflow/scripts/workflow_monitor.py <taskId> [agentId]
```

### List Available Agents

```bash
openclaw agents list
```

### Git Operations (pre-approved)

- `git add *`
- `git commit -m '...'`
- `git push`
- `ssh-keygen *`
- `git remote *`