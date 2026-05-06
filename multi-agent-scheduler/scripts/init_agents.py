#!/usr/bin/env python3
"""
init_agents.py - 初始化Agent列表
用法: python3 init_agents.py
功能:
  1. 调用 openclaw agents list 获取所有可用Agent
  2. 解析输出，生成结构化注册表
  3. 保存到 references/agent-registry.json
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

SKILL_DIR = Path(__file__).parent.parent.resolve()
REFERENCES_DIR = SKILL_DIR / "references"
REGISTRY_FILE = REFERENCES_DIR / "agent-registry.json"


def get_gmt8_time():
    """获取GMT+8时区的当前时间"""
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M GMT+8")


def init_agents():
    """初始化Agent列表"""
    print("[初始化] 开始获取Agent列表...")
    
    # 调用 openclaw agents list
    try:
        result = subprocess.run(
            ["openclaw", "agents", "list"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            print(f"[错误] openclaw agents list 执行失败: {result.stderr}")
            return False
        
        output = result.stdout
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
    # 假设输出格式为表格形式，解析每行获取Agent信息
    agents = []
    lines = output.strip().split("\n")
    
    for line in lines:
        line = line.strip()
        # 跳过空行、标题行、分隔线
        if not line or line.startswith("-") or line.startswith("Agent") or line.startswith("ID"):
            continue
        
        # 解析格式: "agent_id    name    description"
        parts = line.split()
        if len(parts) >= 1:
            agent_id = parts[0]
            name = parts[1] if len(parts) > 1 else agent_id
            workspace = f"/home/admin/.openclaw/agents/{agent_id}/workspace"
            
            agents.append({
                "agentId": agent_id,
                "name": name,
                "workspace": workspace,
                "status": "available",
                "registeredAt": get_gmt8_time()
            })
    
    # 构建注册表
    registry = {
        "version": "1.0",
        "updatedAt": get_gmt8_time(),
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
        print(f"  - {agent['agentId']}: {agent['name']} (workspace: {agent['workspace']})")
    
    return True


def main():
    success = init_agents()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()