# -*- coding: utf-8 -*-
"""
悟空智能体 v3：障碍物环境
任务：悟空能绕过障碍物到达目标

改进：
- 增加障碍物（固定+随机）
- 碰撞检测：碰到障碍物扣分
- 学习曲线可视化
"""
import pygame
import random
import math

# ========== 配置 ==========
SCREEN_W, SCREEN_H = 700, 550
FPS = 60
EPISODES = 15
STEPS_PER_EPISODE = 300

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

# 悟空配置
WUKONG_SIZE = 26
WUKONG_SPEED = 5
TARGET_RADIUS = 10
REACH_DIST = WUKONG_SIZE // 2 + TARGET_RADIUS

# 障碍物配置
OBSTACLE_COLOR = (70, 70, 90)
OBSTACLE_COUNT = 5  # 每回合障碍物数量

# ========== 初始化 ==========
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("悟空智能体 v3 - 障碍物环境")
clock = pygame.time.Clock()
font = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 18)
font_small = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 14)
font_big = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 28)
font_title = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 22)

def new_target(obstacles, wk_x, wk_y):
    """生成新目标，确保不和障碍物重叠"""
    for _ in range(100):
        margin = 50
        tx = random.randint(margin, SCREEN_W - margin)
        ty = random.randint(margin + 50, SCREEN_H - margin)
        
        # 检查和悟空距离
        if math.sqrt((tx-wk_x)**2 + (ty-wk_y)**2) < 80:
            continue
        
        # 检查和障碍物不重叠
        valid = True
        for obs in obstacles:
            if obs["x"] - 20 < tx < obs["x"] + obs["w"] + 20 and \
               obs["y"] - 20 < ty < obs["y"] + obs["h"] + 20:
                valid = False
                break
        if valid:
            return tx, ty
    return SCREEN_W - 80, SCREEN_H - 80

def generate_obstacles():
    """生成障碍物布局"""
    obstacles = []
    for _ in range(OBSTACLE_COUNT):
        w = random.randint(40, 120)
        h = random.randint(15, 40)
        x = random.randint(60, SCREEN_W - 60 - w)
        y = random.randint(80, SCREEN_H - 80 - h)
        obstacles.append({"x": x, "y": y, "w": w, "h": h})
    return obstacles

def check_collision(x, y, size, obstacles):
    """检测碰撞"""
    rect = pygame.Rect(x - size//2, y - size//2, size, size)
    for obs in obstacles:
        obs_rect = pygame.Rect(obs["x"], obs["y"], obs["w"], obs["h"])
        if rect.colliderect(obs_rect):
            return True
    return False

def get_reward(dist, collided, arrived):
    """奖励函数"""
    if arrived:
        return 150
    if collided:
        return -80  # 撞墙扣分
    return -dist / 10 + 1  # 距离奖励+存活奖励

def decide_action(x, y, tx, ty, obstacles):
    """决策：绕路策略"""
    dx, dy = 0, 0
    
    # 简单绕路：如果正前方有障碍，尝试绕行
    next_x = x + (WUKONG_SPEED if x < tx else -WUKONG_SPEED if x > tx else 0)
    next_y = y + (WUKONG_SPEED if y < ty else -WUKONG_SPEED if y > ty else 0)
    
    # 检测移动方向是否有障碍
    if check_collision(next_x, next_y, WUKONG_SIZE, obstacles):
        # 绕行：先上下再左右，或先左右再上下
        if random.random() < 0.5:
            # 尝试垂直移动
            dy = WUKONG_SPEED if y < ty else -WUKONG_SPEED if y > ty else 0
            if check_collision(x, y + dy * 3, WUKONG_SIZE, obstacles):
                dy = 0
                dx = WUKONG_SPEED if x < tx else -WUKONG_SPEED if x > tx else 0
        else:
            dx = WUKONG_SPEED if x < tx else -WUKONG_SPEED if x > tx else 0
            if check_collision(x + dx * 3, y, WUKONG_SIZE, obstacles):
                dx = 0
                dy = WUKONG_SPEED if y < ty else -WUKONG_SPEED if y > ty else 0
    else:
        # 正常移动
        if x < tx - 2:
            dx = WUKONG_SPEED
        elif x > tx + 2:
            dx = -WUKONG_SPEED
        if y < ty - 2:
            dy = WUKONG_SPEED
        elif y > ty + 2:
            dy = -WUKONG_SPEED
    
    return dx, dy

# ========== 学习记录 ==========
episode_rewards = []
episode_steps = []
collision_count = []

episode = 0
running = True
show_path = True  # 显示路径

while running and episode < EPISODES:
    # 生成障碍物（每回合新布局）
    obstacles = generate_obstacles()
    
    # 初始化
    wukong_x = 60
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
                elif event.key == pygame.K_p:
                    show_path = not show_path

        # 悟空决策
        dx, dy = decide_action(wukong_x, wukong_y, target_x, target_y, obstacles)
        
        # 移动
        new_x = max(WUKONG_SIZE//2, min(SCREEN_W - WUKONG_SIZE//2, wukong_x + dx))
        new_y = max(WUKONG_SIZE//2, min(SCREEN_H - WUKONG_SIZE//2, wukong_y + dy))
        
        # 碰撞检测
        collided = check_collision(new_x, new_y, WUKONG_SIZE, obstacles)
        if collided:
            collisions += 1
            # 反弹
            new_x = wukong_x
            new_y = wukong_y
        
        wukong_x, wukong_y = new_x, new_y
        if dx != 0 or dy != 0:
            steps += 1
            path_points.append((wukong_x, wukong_y))
            if len(path_points) > 500:
                path_points = path_points[-500:]
        
        # 距离和奖励
        dist = math.sqrt((wukong_x - target_x)**2 + (wukong_y - target_y)**2)
        reward = get_reward(dist, collided, dist < REACH_DIST)
        episode_reward += reward
        
        # 到达检测
        if dist < REACH_DIST:
            done = True
            target_x, target_y = new_target(obstacles, wukong_x, wukong_y)
            path_points = [(wukong_x, wukong_y)]
        
        if steps >= STEPS_PER_EPISODE:
            done = True
        
        # ========== 渲染 ==========
        screen.fill(BLACK)
        
        # 网格背景
        for gx in range(0, SCREEN_W, 40):
            pygame.draw.line(screen, (30, 30, 42), (gx, 0), (gx, SCREEN_H))
        for gy in range(0, SCREEN_H, 40):
            pygame.draw.line(screen, (30, 30, 42), (0, gy), (SCREEN_W, gy))
        
        # 障碍物
        for obs in obstacles:
            pygame.draw.rect(screen, OBSTACLE_COLOR, (obs["x"], obs["y"], obs["w"], obs["h"]), border_radius=4)
            pygame.draw.rect(screen, (100, 100, 130), (obs["x"], obs["y"], obs["w"], obs["h"]), 2, border_radius=4)
        
        # 目标
        pygame.draw.circle(screen, GREEN, (target_x, target_y), TARGET_RADIUS + 4)
        pygame.draw.circle(screen, (80, 230, 140), (target_x, target_y), TARGET_RADIUS)
        
        # 路径轨迹
        if show_path and len(path_points) > 1:
            for i in range(len(path_points) - 1):
                alpha = 255 * i // len(path_points)
                color = (min(255, 100 + alpha//3), min(255, 150 + alpha//4), min(255, 200 + alpha//5))
                pygame.draw.line(screen, color, path_points[i], path_points[i+1], 2)
        
        # 悟空
        wk_rect = pygame.Rect(
            wukong_x - WUKONG_SIZE//2,
            wukong_y - WUKONG_SIZE//2,
            WUKONG_SIZE, WUKONG_SIZE
        )
        pygame.draw.rect(screen, RED, wk_rect, border_radius=5)
        pygame.draw.rect(screen, (255, 120, 100),
                         (wk_rect.x + 3, wk_rect.y + 3, 7, 7), border_radius=2)
        # 碰撞闪烁
        if collided:
            pygame.draw.rect(screen, YELLOW, wk_rect, 2, border_radius=5)
        
        # 顶部信息
        title = font_title.render(f"悟空 v3 - 障碍物环境", True, CYAN)
        screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 10))
        
        ep_info = font.render(f"回合 {episode+1}/{EPISODES} | 步数 {steps}", True, WHITE)
        screen.blit(ep_info, (SCREEN_W//2 - ep_info.get_width()//2, 38))
        
        # 状态提示
        if done and dist < REACH_DIST:
            txt = font.render("✓ 到达！", True, YELLOW)
            screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, SCREEN_H - 80))
        elif done:
            txt = font.render("超时", True, ORANGE)
            screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, SCREEN_H - 80))
        elif collisions > 0:
            txt = font_small.render(f"碰撞 {collisions} 次", True, ORANGE)
            screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, SCREEN_H - 80))
        
        # 右侧数据面板
        panel_x = SCREEN_W - 210
        panel_bg = pygame.Rect(panel_x, 65, 200, SCREEN_H - 150)
        pygame.draw.rect(screen, (25, 25, 35), panel_bg, border_radius=8)
        
        # 学习曲线
        if len(episode_rewards) > 1:
            pygame.draw.rect(screen, (40, 40, 55), (panel_x + 10, 80, 180, 100), border_radius=4)
            max_r = max(episode_rewards) if episode_rewards else 100
            min_r = min(episode_rewards) if episode_rewards else -100
            range_r = max_r - min_r if max_r != min_r else 1
            
            for i in range(len(episode_rewards) - 1):
                x1 = panel_x + 15 + i * 180 // max(1, len(episode_rewards) - 1)
                x2 = panel_x + 15 + (i+1) * 180 // max(1, len(episode_rewards) - 1)
                y1 = 175 - int((episode_rewards[i] - min_r) / range_r * 90)
                y2 = 175 - int((episode_rewards[i+1] - min_r) / range_r * 90)
                color = GREEN if episode_rewards[i+1] > episode_rewards[i] else ORANGE
                pygame.draw.line(screen, color, (x1, y1), (x2, y2), 2)
        
        # 数据
        data_y = 190
        screen.blit(font_small.render(f"当前奖励: {episode_reward:.0f}", True, WHITE), (panel_x + 15, data_y))
        data_y += 22
        screen.blit(font_small.render(f"碰撞次数: {collisions}", True, ORANGE if collisions > 0 else WHITE), (panel_x + 15, data_y))
        data_y += 22
        
        if episode_rewards:
            avg = sum(episode_rewards) / len(episode_rewards)
            screen.blit(font_small.render(f"平均奖励: {avg:.0f}", True, PURPLE), (panel_x + 15, data_y))
            data_y += 22
            best = max(episode_rewards)
            screen.blit(font_small.render(f"最佳奖励: {best:.0f}", True, GREEN), (panel_x + 15, data_y))
            data_y += 22
        
        # 操作提示
        help_txt = "P显示路径 | ESC退出"
        help_t = font_small.render(help_txt, True, GRAY)
        screen.blit(help_t, (SCREEN_W//2 - help_t.get_width()//2, SCREEN_H - 18))

        pygame.display.flip()
        clock.tick(FPS)
    
    # 回合结束
    episode_rewards.append(episode_reward)
    episode_steps.append(steps)
    collision_count.append(collisions)
    episode += 1

# ========== 学习报告 ==========
screen.fill(BLACK)
title = font_big.render("v3 学习完成！", True, CYAN)
screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 50))

# 统计数据
stats = [
    f"完成回合: {len(episode_rewards)}",
    f"平均奖励: {sum(episode_rewards)/len(episode_rewards):.1f}",
    f"最佳奖励: {max(episode_rewards):.1f}",
    f"总碰撞: {sum(collision_count)}次",
]
for i, stat in enumerate(stats):
    t = font.render(stat, True, WHITE)
    screen.blit(t, (SCREEN_W//2 - 100, 120 + i*28))

# 详细记录
for i, (r, s, c) in enumerate(zip(episode_rewards, episode_steps, collision_count)):
    t = font_small.render(f"回合{i+1}: 奖励={r:.0f} 步={s} 碰={c}", True, 
                          GREEN if r > 0 else WHITE)
    screen.blit(t, (SCREEN_W//2 - 130, 260 + i*22))

pygame.display.flip()
pygame.time.wait(5000)
pygame.quit()

print(f"\n=== 悟空v3学习报告 ===")
print(f"完成回合: {len(episode_rewards)}")
print(f"平均奖励: {sum(episode_rewards)/len(episode_rewards):.1f}")
print(f"最佳奖励: {max(episode_rewards):.1f}")
print(f"总碰撞次数: {sum(collision_count)}")
