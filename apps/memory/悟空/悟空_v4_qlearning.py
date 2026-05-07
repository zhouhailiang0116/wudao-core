# -*- coding: utf-8 -*-
"""
悟空智能体 v4：Q-Learning强化学习
任务：悟空通过Q-Learning学会最优路径

核心：
- Q表存储状态-动作价值
- 探索vs利用（epsilon-greedy）
- Q学习更新规则
"""
import pygame
import random
import math
import os

# ========== 配置 ==========
SCREEN_W, SCREEN_H = 700, 550
FPS = 60
EPISODES = 30
STEPS_PER_EPISODE = 400

# 颜色
BLACK = (20, 20, 30)
WHITE = (255, 255, 255)
RED = (230, 60, 50)
GREEN = (30, 180, 100)
BLUE = (50, 100, 230)
GRAY = (120, 120, 135)
YELLOW = (255, 210, 60)
ORANGE = (255, 150, 50)
PURPLE = (160, 80, 220)
CYAN = (50, 200, 200)
PINK = (220, 80, 160)

# 悟空配置
WUKONG_SIZE = 24
WUKONG_SPEED = 5
TARGET_RADIUS = 10
REACH_DIST = WUKONG_SIZE // 2 + TARGET_RADIUS

# Q-Learning配置
ALPHA = 0.1      # 学习率
GAMMA = 0.9      # 折扣因子
EPSILON = 0.3    # 探索率
EPSILON_DECAY = 0.98  # 探索率衰减
MIN_EPSILON = 0.05

# 状态离散化
GRID_SIZE = 50   # 网格大小

# 障碍物
OBSTACLE_COLOR = (70, 70, 90)
OBSTACLE_COUNT = 6

# ========== 初始化 ==========
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("悟空智能体 v4 - Q-Learning")
clock = pygame.time.Clock()
font = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 18)
font_small = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 14)
font_big = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 28)
font_title = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 22)

# ========== Q-Learning 核心 ==========
Q = {}  # Q表

def get_state(x, y, tx, ty, obstacles):
    """离散化状态：将连续坐标转为网格状态"""
    # 相对位置（8方向）
    dx = 1 if x < tx - 20 else (-1 if x > tx + 20 else 0)
    dy = 1 if y < ty - 20 else (-1 if y > ty + 20 else 0)
    
    # 障碍物检测（4方向）
    obs_near = ""
    check_dists = [30, 50]
    for d, name in [((-1,0),"L"), ((1,0),"R"), ((0,-1),"U"), ((0,1),"D")]:
        for dist in check_dists:
            test_x = x + d[0] * dist
            test_y = y + d[1] * dist
            for obs in obstacles:
                if obs["x"] < test_x < obs["x"] + obs["w"] and obs["y"] < test_y < obs["y"] + obs["h"]:
                    obs_near += name
                    break
    
    return (dx, dy, obs_near)

def get_actions():
    """动作空间：4个方向 + 不动"""
    return [(0, -WUKONG_SPEED), (0, WUKONG_SPEED), 
            (-WUKONG_SPEED, 0), (WUKONG_SPEED, 0), (0, 0)]

def choose_action(state, epsilon):
    """epsilon-greedy策略"""
    if random.random() < epsilon:
        return random.choice(get_actions())
    
    q_vals = [Q.get((state, a), 0.0) for a in get_actions()]
    max_q = max(q_vals)
    if q_vals.count(max_q) > 1:
        return random.choice([a for a in get_actions() if Q.get((state, a), 0) == max_q])
    return get_actions()[q_vals.index(max_q)]

def update_q(state, action, reward, next_state):
    """Q学习更新"""
    a_idx = get_actions().index(action)
    max_next_q = max([Q.get((next_state, a), 0.0) for a in get_actions()])
    current_q = Q.get((state, action), 0.0)
    new_q = current_q + ALPHA * (reward + GAMMA * max_next_q - current_q)
    Q[(state, action)] = new_q

# ========== 环境 ==========
def generate_obstacles():
    obstacles = []
    positions = [
        (150, 120, 100, 25),
        (350, 200, 25, 100),
        (500, 100, 80, 25),
        (200, 350, 120, 25),
        (450, 380, 25, 80),
        (100, 250, 25, 100),
    ]
    for x, y, w, h in positions:
        obstacles.append({"x": x, "y": y, "w": w, "h": h})
    return obstacles

def new_target(obstacles, wk_x, wk_y):
    for _ in range(100):
        tx = random.randint(60, SCREEN_W - 60)
        ty = random.randint(80, SCREEN_H - 60)
        if math.sqrt((tx-wk_x)**2 + (ty-wk_y)**2) < 100:
            continue
        valid = True
        for obs in obstacles:
            if (obs["x"]-15 < tx < obs["x"]+obs["w"]+15 and 
                obs["y"]-15 < ty < obs["y"]+obs["h"]+15):
                valid = False
                break
        if valid:
            return tx, ty
    return SCREEN_W - 60, SCREEN_H - 60

def check_collision(x, y, obstacles):
    rect = pygame.Rect(x - WUKONG_SIZE//2, y - WUKONG_SIZE//2, WUKONG_SIZE, WUKONG_SIZE)
    for obs in obstacles:
        if rect.colliderect(pygame.Rect(obs["x"], obs["y"], obs["w"], obs["h"])):
            return True
    return False

def get_reward(dist, collided, arrived, steps):
    if arrived:
        return 200 + max(0, 100 - steps)  # 到达+效率奖励
    if collided:
        return -50
    return -dist / 15 + 0.5  # 存活+距离奖励

# ========== 学习 ==========
episode_rewards = []
episode_steps = []
collision_count = []

obstacles = generate_obstacles()
epsilon = EPSILON
episode = 0
running = True
best_reward = float('-inf')

while running and episode < EPISODES:
    wukong_x = 50
    wukong_y = SCREEN_H // 2
    target_x, target_y = new_target(obstacles, wukong_x, wukong_y)
    
    episode_reward = 0
    steps = 0
    collisions = 0
    done = False
    path_points = [(wukong_x, wukong_y)]
    
    while not done and running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    # 重置Q表
                    Q.clear()
                    epsilon = EPSILON

        # 获取状态
        state = get_state(wukong_x, wukong_y, target_x, target_y, obstacles)
        
        # 选择动作
        action = choose_action(state, epsilon)
        
        # 执行
        new_x = max(WUKONG_SIZE//2, min(SCREEN_W - WUKONG_SIZE//2, wukong_x + action[0]))
        new_y = max(WUKONG_SIZE//2, min(SCREEN_H - WUKONG_SIZE//2, wukong_y + action[1]))
        
        collided = check_collision(new_x, new_y, obstacles)
        if collided:
            collisions += 1
            new_x, new_y = wukong_x, wukong_y
        
        wukong_x, wukong_y = new_x, new_y
        if action != (0, 0):
            steps += 1
            path_points.append((wukong_x, wukong_y))
            if len(path_points) > 800:
                path_points = path_points[-800:]
        
        # 奖励
        dist = math.sqrt((wukong_x - target_x)**2 + (wukong_y - target_y)**2)
        arrived = dist < REACH_DIST
        reward = get_reward(dist, collided, arrived, steps)
        
        # Q更新
        next_state = get_state(wukong_x, wukong_y, target_x, target_y, obstacles)
        update_q(state, action, reward, next_state)
        
        episode_reward += reward
        
        # 到达
        if arrived:
            done = True
            target_x, target_y = new_target(obstacles, wukong_x, wukong_y)
            path_points = [(wukong_x, wukong_y)]
        
        if steps >= STEPS_PER_EPISODE:
            done = True
        
        # ========== 渲染 ==========
        screen.fill(BLACK)
        
        # 网格
        for gx in range(0, SCREEN_W, GRID_SIZE):
            pygame.draw.line(screen, (28, 28, 40), (gx, 0), (gx, SCREEN_H))
        for gy in range(0, SCREEN_H, GRID_SIZE):
            pygame.draw.line(screen, (28, 28, 40), (0, gy), (SCREEN_W, gy))
        
        # 障碍物
        for obs in obstacles:
            pygame.draw.rect(screen, OBSTACLE_COLOR, (obs["x"], obs["y"], obs["w"], obs["h"]), border_radius=4)
            pygame.draw.rect(screen, (100, 100, 125), (obs["x"], obs["y"], obs["w"], obs["h"]), 2, border_radius=4)
        
        # 目标
        pygame.draw.circle(screen, GREEN, (target_x, target_y), TARGET_RADIUS + 3)
        pygame.draw.circle(screen, (80, 230, 140), (target_x, target_y), TARGET_RADIUS)
        
        # 路径
        if len(path_points) > 1:
            for i in range(len(path_points) - 1):
                alpha = 255 * i // len(path_points)
                r = min(255, 80 + alpha//2)
                g = min(255, 120 + alpha//3)
                b = min(255, 200 + alpha//4)
                pygame.draw.line(screen, (r, g, b), path_points[i], path_points[i+1], 2)
        
        # 悟空
        wk_rect = pygame.Rect(
            wukong_x - WUKONG_SIZE//2,
            wukong_y - WUKONG_SIZE//2,
            WUKONG_SIZE, WUKONG_SIZE
        )
        # 根据epsilon显示颜色
        wk_color = PINK if epsilon > 0.15 else RED
        pygame.draw.rect(screen, wk_color, wk_rect, border_radius=4)
        pygame.draw.rect(screen, (255, 130, 110),
                         (wk_rect.x + 2, wk_rect.y + 2, 6, 6), border_radius=2)
        
        # 碰撞提示
        if collided:
            pygame.draw.rect(screen, YELLOW, wk_rect, 2, border_radius=4)
        
        # 标题
        title = font_title.render(f"悟空 v4 - Q-Learning", True, PURPLE)
        screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 8))
        
        ep_info = font.render(f"回合 {episode+1}/{EPISODES} | ε={epsilon:.2f}", True, WHITE)
        screen.blit(ep_info, (SCREEN_W//2 - ep_info.get_width()//2, 36))
        
        # 到达/超时提示
        if done and dist < REACH_DIST:
            txt = font.render("✓ 到达！", True, YELLOW)
            screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, SCREEN_H - 75))
        elif done:
            txt = font.render("超时", True, ORANGE)
            screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, SCREEN_H - 75))
        
        # 右侧面板
        panel_x = SCREEN_W - 220
        pygame.draw.rect(screen, (22, 22, 32), (panel_x, 60, 210, SCREEN_H - 130), border_radius=8)
        
        # 学习曲线
        if len(episode_rewards) > 1:
            pygame.draw.rect(screen, (35, 35, 48), (panel_x + 10, 75, 190, 100), border_radius=4)
            max_r = max(episode_rewards) + 1
            min_r = min(episode_rewards) - 1
            range_r = max_r - min_r if max_r != min_r else 1
            
            for i in range(len(episode_rewards) - 1):
                x1 = panel_x + 15 + i * 190 // max(1, len(episode_rewards) - 1)
                x2 = panel_x + 15 + (i+1) * 190 // max(1, len(episode_rewards) - 1)
                y1 = 170 - int((episode_rewards[i] - min_r) / range_r * 90)
                y2 = 170 - int((episode_rewards[i+1] - min_r) / range_r * 90)
                color = GREEN if episode_rewards[i+1] > episode_rewards[i] else ORANGE
                pygame.draw.line(screen, color, (x1, y1), (x2, y2), 2)
        
        # 数据
        data_y = 185
        screen.blit(font_small.render(f"奖励: {episode_reward:.0f}", True, WHITE), (panel_x + 15, data_y))
        data_y += 20
        screen.blit(font_small.render(f"步数: {steps}", True, WHITE), (panel_x + 15, data_y))
        data_y += 20
        screen.blit(font_small.render(f"碰撞: {collisions}", True, ORANGE if collisions > 0 else GRAY), (panel_x + 15, data_y))
        data_y += 25
        
        if episode_rewards:
            avg = sum(episode_rewards) / len(episode_rewards)
            screen.blit(font_small.render(f"平均: {avg:.0f}", True, PURPLE), (panel_x + 15, data_y))
            data_y += 20
            best = max(episode_rewards)
            screen.blit(font_small.render(f"最佳: {best:.0f}", True, GREEN), (panel_x + 15, data_y))
            data_y += 20
        
        # Q表大小
        screen.blit(font_small.render(f"Q表: {len(Q)}状态", True, CYAN), (panel_x + 15, data_y))
        data_y += 20
        screen.blit(font_small.render(f"ε: {epsilon:.3f}", True, PINK), (panel_x + 15, data_y))
        
        # 图例
        legend_y = SCREEN_H - 60
        pygame.draw.rect(screen, PINK, (panel_x + 10, legend_y, 12, 12), border_radius=2)
        screen.blit(font_small.render("探索中", True, PINK), (panel_x + 28, legend_y))
        pygame.draw.rect(screen, RED, (panel_x + 110, legend_y, 12, 12), border_radius=2)
        screen.blit(font_small.render("已学习", True, RED), (panel_x + 128, legend_y))
        
        # 操作
        help_t = font_small.render("R重置Q表 | ESC退出", True, GRAY)
        screen.blit(help_t, (SCREEN_W//2 - help_t.get_width()//2, SCREEN_H - 15))

        pygame.display.flip()
        clock.tick(FPS)
    
    # 回合结束
    episode_rewards.append(episode_reward)
    episode_steps.append(steps)
    collision_count.append(collisions)
    epsilon = max(MIN_EPSILON, epsilon * EPSILON_DECAY)
    episode += 1

# ========== 保存Q表 ==========
q_file = os.path.join(os.path.expanduser('~'), 'Desktop', 'training', 'wukong_q_table.txt')
try:
    with open(q_file, 'w') as f:
        for (state, action), q_val in sorted(Q.items()):
            f.write(f"{state},{action},{q_val}\n")
    print(f"Q表已保存: {q_file}")
except:
    pass

# ========== 最终报告 ==========
screen.fill(BLACK)
title = font_big.render("v4 Q-Learning 完成！", True, PURPLE)
screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 40))

# 图
if len(episode_rewards) > 1:
    max_r = max(episode_rewards)
    min_r = min(episode_rewards)
    range_r = max_r - min_r if max_r != min_r else 1
    for i in range(len(episode_rewards) - 1):
        x1 = 50 + i * (SCREEN_W - 100) // max(1, len(episode_rewards) - 1)
        x2 = 50 + (i+1) * (SCREEN_W - 100) // max(1, len(episode_rewards) - 1)
        y1 = 300 - int((episode_rewards[i] - min_r) / range_r * 150)
        y2 = 300 - int((episode_rewards[i+1] - min_r) / range_r * 150)
        color = GREEN if episode_rewards[i+1] > episode_rewards[i] else ORANGE
        pygame.draw.line(screen, color, (x1, y1), (x2, y2), 3)

stats = [
    f"回合: {len(episode_rewards)}",
    f"平均: {sum(episode_rewards)/len(episode_rewards):.1f}",
    f"最佳: {max(episode_rewards):.1f}",
    f"碰撞: {sum(collision_count)}",
    f"Q表: {len(Q)}状态",
]
for i, s in enumerate(stats):
    t = font.render(s, True, WHITE)
    screen.blit(t, (SCREEN_W//2 - 80, 120 + i*28))

pygame.display.flip()
pygame.time.wait(5000)
pygame.quit()

print(f"\n=== 悟空v4 Q-Learning报告 ===")
print(f"回合: {len(episode_rewards)}")
print(f"平均奖励: {sum(episode_rewards)/len(episode_rewards):.1f}")
print(f"最佳奖励: {max(episode_rewards):.1f}")
print(f"Q表大小: {len(Q)}状态-动作对")
print(f"Q表已保存: {q_file}")
