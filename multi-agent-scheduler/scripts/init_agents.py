#!/usr/bin/env python3
"""
init_agents.py - 初始化Agent列表
用法: python3 init_agents.py
功能:
  1. 调用 openclaw agents list 获取所有可用Agent
  2. 扫描每个Agent工作目录下的skills文件夹，记录可用技能
  3. 生成结构化注册表，保存到 references/agent-registry.json

修复记录:
  - 2026-05-07: 移除冗余的平台判断，直接使用 Path 处理跨平台路径
  - 修复workspace解析，确保从openclaw agents list输出中正确提取
"""

import json
import os
import re
import subprocess
import sys
import platform
from pathlib import Path
from datetime import datetime, timezone, timedelta

SKILL_DIR = Path(__file__).parent.parent.resolve()
REFERENCES_DIR = SKILL_DIR / "references"
REGISTRY_FILE = REFERENCES_DIR / "agent-registry.json"
WORKSPACE = Path.home() / ".openclaw" / "workspace"


def get_gmt8_time():
    """获取GMT+8时区的当前时间"""
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M GMT+8")


def expand_path(path_str):
    """展开路径中的~和环境变量"""
    if not path_str:
        return path_str
    path_str = os.path.expanduser(path_str)
    path_str = os.path.expandvars(path_str)
    return path_str


def scan_agent_skills(workspace_path):
    """扫描指定Agent工作目录下的skills文件夹，返回技能列表"""
    workspace_path = expand_path(workspace_path)
    skills_dir = Path(workspace_path) / "skills"

    skills = []
    if skills_dir.exists() and skills_dir.is_dir():
        for skill_entry in skills_dir.iterdir():
            if skill_entry.is_dir():
                skill_id = skill_entry.name
                skill_md = skill_entry / "SKILL.md"

                description = ""
                if skill_md.exists():
                    try:
                        content = skill_md.read_text(encoding="utf-8")
                        for line in content.split("\n"):
                            line_stripped = line.strip()
                            if line_stripped.startswith("description:"):
                                description = line.split("description:", 1)[1].strip().strip('"').strip("'")
                                break
                    except Exception:
                        pass

                skills.append({
                    "skillId": skill_id,
                    "description": description,
                    "path": str(skill_entry)
                })

    return skills


def find_openclaw_cmd():
    """查找openclaw命令路径"""
    import shutil
    for name in ["openclaw"] + ([f"openclaw.{ext}" for ext in ["exe", "cmd", "bat"]] if platform.system() == "Windows" else []):
        cmd_path = shutil.which(name)
        if cmd_path:
            return cmd_path
    return "openclaw"


def run_openclaw_agents_list():
    """执行openclaw agents list命令"""
    cmd = find_openclaw_cmd()
    result = subprocess.run(
        [cmd, "agents", "list"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        shell=(platform.system() == "Windows")
    )

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
        print(f"[错误] openclaw agents list 执行失败: {stderr}")
        return None

    return result.stdout.decode("utf-8", errors="replace")


def init_agents():
    """初始化Agent列表"""
    print("[初始化] 开始获取Agent列表...")

    try:
        output = run_openclaw_agents_list()
        if output is None:
            return False
        print(f"[信息] openclaw agents list 输出:\n{output}")
    except FileNotFoundError:
        print("[错误] 未找到 openclaw 命令，请确保已安装并配置好PATH")
        return False
    except subprocess.TimeoutExpired:
        print("[错误] openclaw agents list 执行超时")
        return False
    except Exception as e:
        print(f"[错误] 执行 openclaw agents list 时发生异常: {e}")
        return False

    agents = []
    current_agent = None

    lines = output.strip().split("\n")
    for line in lines:
        stripped = line.strip()

        # 新Agent开始: "- agent_id (default)" 或 "- agent_id"
        if stripped.startswith("- "):
            # 保存上一个Agent
            if current_agent and current_agent.get("agentId"):
                skills = scan_agent_skills(current_agent["workspace"])
                current_agent["skills"] = skills
                current_agent["skillCount"] = len(skills)
                agents.append(current_agent)
                print(f"[扫描] {current_agent['agentId']} 发现 {len(skills)} 个技能: {[s['skillId'] for s in skills]}")

            # 解析新的Agent ID
            agent_line = stripped[2:]
            parts = agent_line.split()
            agent_id = parts[0] if parts else ""

            # 默认路径仅作为 fallback，实际 workspace 从 openclaw agents list 获取
            default_workspace = str(Path.home() / ".openclaw" / "agents" / agent_id / "workspace")

            current_agent = {
                "agentId": agent_id,
                "name": agent_id,
                "workspace": default_workspace,
                "status": "available",
                "registeredAt": get_gmt8_time(),
                "skills": [],
                "skillCount": 0
            }

        elif current_agent is not None:
            if stripped.startswith("Workspace:"):
                workspace = stripped.split("Workspace:", 1)[1].strip()
                workspace = expand_path(workspace)
                current_agent["workspace"] = workspace

            elif stripped.startswith("Identity:"):
                identity = stripped.split("Identity:", 1)[1].strip()
                if " (" in identity:
                    name_part = identity.split(" (")[0].strip()
                    # 去除emoji
                    try:
                        name_part = re.sub(r'[\U00010000-\U0010ffff]', '', name_part).strip()
                    except Exception:
                        name_part = ''.join(c for c in name_part if ord(c) < 0x10000)
                    if name_part:
                        current_agent["name"] = name_part

    # 保存最后一个Agent
    if current_agent and current_agent.get("agentId"):
        skills = scan_agent_skills(current_agent["workspace"])
        current_agent["skills"] = skills
        current_agent["skillCount"] = len(skills)
        agents.append(current_agent)
        print(f"[扫描] {current_agent['agentId']} 发现 {len(skills)} 个技能: {[s['skillId'] for s in skills]}")

    # 构建注册表
    registry = {
        "version": "1.1",
        "updatedAt": get_gmt8_time(),
        "platform": platform.system(),
        "agents": agents,
        "totalCount": len(agents)
    }

    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)

    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

    print(f"[成功] Agent注册表已保存到: {REGISTRY_FILE}")
    print(f"[信息] 共检测到 {len(agents)} 个Agent:")
    for agent in agents:
        skills_summary = f" ({len(agent['skills'])}个技能: {', '.join([s['skillId'] for s in agent['skills']])})" if agent['skills'] else ""
        print(f"  - {agent['agentId']}: {agent['name']}{skills_summary}")

    return True


def main():
    success = init_agents()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()