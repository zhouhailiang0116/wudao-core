# -*- coding: utf-8 -*-
"""
悟空智能体 - 经验日志
记录每次学习的关键洞察
"""
from datetime import datetime
import os

LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "wukong_log.txt")

def log(text):
    """写入日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"[{timestamp}] {text}\n"
    
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)
    print(line.strip())

def get_log():
    """读取日志"""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# ========== 初始经验 ==========
INITIAL_INSIGHTS = """
=== 悟空智能体 v1-v4 经验总结 ===

v1 键盘控制：
- 学会了pygame环境搭建
- 事件循环、按键检测

v2 自动导航：
- 简单的"朝目标移动"策略
- 奖励函数：距离越小奖励越高
- 问题：不会绕路，直线撞墙

v3 障碍物：
- 学会了碰撞检测
- 绕路策略：遇到障碍换方向
- 问题：策略固定，不够智能

v4 Q-Learning：
- 学会了强化学习核心概念
- 探索vs利用（epsilon-greedy）
- Q表记录状态-动作价值
- 下一步：让Q表越来越精确

关键教训：
1. 强化学习需要大量试错
2. 状态离散化要合理（太细=太多状态，太粗=学不到）
3. 奖励函数设计决定学习方向
4. epsilon衰减让悟空从探索到利用

文件：
- Q表：Desktop/training/wukong_q_table.txt
- 代码：workspace/scripts/悟空/
"""

if __name__ == "__main__":
    log("=== 悟空经验系统启动 ===")
    log("v1-v4 全部完成")
    print("\n" + INITIAL_INSIGHTS)
    print("\n日志：")
    print(get_log())
