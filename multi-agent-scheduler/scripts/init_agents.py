#!/usr/bin/env python3
"""
init_agents.py - 初始化Agent列表（跨平台版本）
用法: python3 init_agents.py
功能:
  1. 调用 openclaw agents list 获取所有可用Agent
  2. 扫描每个Agent工作目录下的skills文件夹，记录可用技能
  3. 生成结构化注册表，保存到 references/agent-registry.json
"""

import json
import os
import re
import subprocess
import sys
import platform
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 跨平台路径处理
def get_home_dir():
    """获取用户主目录，兼容Windows和Unix"""
    if platform.system() == "Windows":
        # Windows:优先用USERPROFILE，其次HOMEDRIVE+HOMEPATH
        home = os.environ.get("USERPROFILE")
        if not home:
            home = os.environ.get("HOMEDRIVE", "") + os.environ.get("HOMEPATH", "")
    else:
        # Unix/Linux: 先尝试环境变量HOME，其次使用getpwuid
        home = os.environ.get("HOME")
        if not home:
            try:
                import pwd
                home = pwd.getpwuid(os.getuid()).pw_dir
            except Exception:
                home = os.path.expanduser("~")
    return home


def get_openclaw_base():
    """获取OpenClaw基础目录，兼容不同操作系统"""
    home = get_home_dir()
    if platform.system() == "Windows":
        # Windows: %USERPROFILE%\.openclaw
        return Path(home) / ".openclaw"
    else:
        # Unix/Linux/macOS: ~/.openclaw
        return Path(home) / ".openclaw"


def expand_path(path_str):
    """展开路径中的~和环境变量"""
    if not path_str:
        return path_str
    # 使用os.path.expanduser展开~（跨平台兼容）
    path_str = os.path.expanduser(path_str)
    # 展开环境变量
    path_str = os.path.expandvars(path_str)
    return path_str


SKILL_DIR = Path(__file__).parent.parent.resolve()
REFERENCES_DIR = SKILL_DIR / "references"
REGISTRY_FILE = REFERENCES_DIR / "agent-registry.json"
AGENTS_BASE_DIR = get_openclaw_base() / "agents"


def get_gmt8_time():
    """获取GMT+8时区的当前时间"""
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M GMT+8")


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
                
                # 读取技能描述（如果有SKILL.md）
                description = ""
                if skill_md.exists():
                    try:
                        content = skill_md.read_text(encoding="utf-8")
                        # 获取description字段
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
    # 首先尝试直接调用（可能在PATH中）
    cmd_name = "openclaw.exe" if platform.system() == "Windows" else "openclaw"
    
    # 使用shutil.which查找
    import shutil
    cmd_path = shutil.which(cmd_name)
    if cmd_path:
        return cmd_path
    
    # Windows上可能叫openclaw.cmd或openclaw.bat
    if platform.system() == "Windows":
        for name in ["openclaw.cmd", "openclaw.bat"]:
            cmd_path = shutil.which(name)
            if cmd_path:
                return cmd_path
    
    # 返回命令名，让subprocess自己找
    return "openclaw"


def run_openclaw_agents_list():
    """执行openclaw agents list命令"""
    cmd = find_openclaw_cmd()
    
    # 根据系统选择shell参数
    if platform.system() == "Windows":
        # Windows: 使用cmd执行
        result = subprocess.run(
            [cmd, "agents", "list"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            shell=True  # 使用shell确保.cmd/.bat可以找到
        )
    else:
        # Unix/Linux/macOS
        result = subprocess.run(
            [cmd, "agents", "list"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )
    
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
        print(f"[错误] openclaw agents list 执行失败: {stderr}")
        return None
    
    return result.stdout.decode("utf-8", errors="replace")


def init_agents():
    """初始化Agent列表"""
    print("[初始化] 开始获取Agent列表...")
    
    # 调用 openclaw agents list
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
    
    # 解析Agent列表
    # openclaw agents list 输出是多行格式，需要解析每个Agent块
    agents = []
    current_agent = None
    
    lines = output.strip().split("\n")
    for line in lines:
        # 检测新Agent开始: "- agent_id (default)" 或 "- agent_id"
        if line.strip().startswith("- "):
            # 保存上一个Agent
            if current_agent and current_agent.get("agentId"):
                # 扫描该Agent的skills文件夹
                skills = scan_agent_skills(current_agent["workspace"])
                current_agent["skills"] = skills
                current_agent["skillCount"] = len(skills)
                agents.append(current_agent)
                print(f"[扫描] {current_agent['agentId']} 发现 {len(skills)} 个技能: {[s['skillId'] for s in skills]}")
            
            # 解析新的Agent ID和名称
            agent_line = line.strip()[2:]  # 去掉 "- "
            agent_id = agent_line.split()[0] if agent_line else ""
            name = agent_id
            
            # 构建工作目录路径（跨平台）
            if platform.system() == "Windows":
                workspace = str(get_openclaw_base() / "agents" / agent_id / "workspace")
            else:
                workspace = str(get_openclaw_base() / "agents" / agent_id / "workspace")
            
            current_agent = {
                "agentId": agent_id,
                "name": name,
                "workspace": workspace,
                "status": "available",
                "registeredAt": get_gmt8_time(),
                "skills": [],
                "skillCount": 0
            }
        
        # 解析Agent的属性行
        elif current_agent is not None:
            line_stripped = line.strip()
            
            if line_stripped.startswith("Workspace:"):
                workspace = line.split("Workspace:", 1)[1].strip()
                workspace = expand_path(workspace)
                current_agent["workspace"] = workspace
            
            elif line_stripped.startswith("Identity:"):
                identity = line.split("Identity:", 1)[1].strip()
                # 尝试提取名称（格式如 "✨ 小V (Xiao V)"）
                if " (" in identity:
                    name_part = identity.split(" (")[0].strip()
                    # 去除emoji（兼容不同Python版本）
                    try:
                        name_part = re.sub(r'[\U00010000-\U0010ffff]', '', name_part).strip()
                    except Exception:
                        # Python < 3.7 不支持高级Unicode范围，简单处理
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
    
    # 确保references目录存在
    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
    
    # 保存到JSON文件
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
