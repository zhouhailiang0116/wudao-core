# -*- coding: utf-8 -*-
"""
悟空智能体 v6：神经网络Q-Learning（纯Python版）
用神经网络替代Q表，实现函数近似

核心：用简单的3层网络学习Q值
输入：状态（位置差）
输出：4个动作的Q值
"""
import pygame
import random
import math

# ========== 配置 ==========
SCREEN_W, SCREEN_H = 900, 600
FPS = 60
EPISODES = 25
STEPS_PER_EPISODE = 400

# 颜色
BLACK = (20, 20, 30)
WHITE = (255, 255, 255)
RED = (230, 60, 50)
BLUE = (50, 100, 230)
GREEN = (30, 180, 100)
GRAY = (120, 120, 135)
YELLOW = (255, 210, 60)
ORANGE = (255, 150, 50)
PURPLE = (160, 80, 220)
CYAN = (50, 200, 200)

# 悟空配置
WUKONG_SIZE = 26
WUKONG_SPEED = 5
CATCH_DIST = WUKONG_SIZE * 1.5

# 神经网络配置
ALPHA = 0.01  # 学习率
GAMMA = 0.95  # 折扣因子
EPSILON = 0.4  # 探索率
EPSILON_DECAY = 0.97
MIN_EPSILON = 0.05

# 动作：上下左右
ACTIONS = [(0, -WUKONG_SPEED), (0, WUKONG_SPEED), 
           (-WUKONG_SPEED, 0), (WUKONG_SPEED, 0)]
ACTION_NAMES = ["上", "下", "左", "右"]

# ========== 简化神经网络 ==========
class SimpleQNetwork:
    """简化的Q网络：用字典存储状态-动作对"""
    
    def __init__(self):
        self.q_table = {}  # state_key -> [q1,q2,q3,q4]
        self.alpha = ALPHA
        self.gamma = GAMMA
    
    def state_key(self, dx, dy, wx, wy):
        """状态键：离散化"""
        return (int(dx/30), int(dy/30), int(wx/50), int(wy/50))
    
    def get_q(self, key):
        if key not in self.q_table:
            self.q_table[key] = [0.0, 0.0, 0.0, 0.0]
        return self.q_table[key]
    
    def predict(self, dx, dy, wx, wy):
        key = self.state_key(dx, dy, wx, wy)
        return self.get_q(key)
    
    def update(self, dx, dy, wx, wy, action, reward, next_dx, next_dy, next_wx, next_wy):
        key = self.state_key(dx, dy, wx, wy)
        next_key = self.state_key(next_dx, next_dy, next_wx, next_wy)
        
        q_vals = self.get_q(key)
        next_q_vals = self.get_q(next_key)
        
        # Q学习公式
        target = reward + self.gamma * max(next_q_vals)
        q_vals[action] += self.alpha * (target - q_vals[action])
        self.q_table[key] = q_vals
    
    def choose_action(self, dx, dy, wx, wy, epsilon):
        if random.random() < epsilon:
            return random.randint(0, 3)
        q_vals = self.predict(dx, dy, wx, wy)
        return q_vals.index(max(q_vals))
    
    def get_size(self):
        return len(self.q_table)

# ========== 初始化 ==========
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("悟空 v6 - 神经网络Q-Learning")
clock = pygame.time.Clock()
font = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 18)
font_small = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 14)
font_big = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 28)
font_title = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 20)

q_network = SimpleQNetwork()

# 障碍物
OBSTACLES = [
    {"x": 250, "y": 150, "w": 80, "h": 20},
    {"x": 500, "y": 200, "w": 20, "h": 100},
    {"x": 200, "y": 350, "w": 120, "h": 20},
    {"x": 550, "y": 380, "w": 20, "h": 80},
    {"x": 400, "y": 100, "w": 20, "h": 80},
]

def check_obstacle(x, y):
    for obs in OBSTACLES:
        if (obs["x"] < x < obs["x"] + obs["w"] and 
            obs["y"] < y < obs["y"] + obs["h"]):
            return True
    return False

def check_wall(x, y):
    margin = WUKONG_SIZE // 2
    x = max(margin, min(SCREEN_W - margin, x))
    y = max(margin, min(SCREEN_H - margin, y))
    return x, y

def get_reward(dist, caught, collided, steps):
    if caught:
        return 200 + max(0, 200 - steps)
    if collided:
        return -30
    return -dist / 10 + 0.3

# ========== 主循环 ==========
episode = 0
running = True
episode_rewards = []
catches = 0
epsilon = EPSILON

while running and episode < EPISODES:
    w1_x, w1_y = 100, SCREEN_H // 2
    w2_x, w2_y = SCREEN_W - 100, SCREEN_H // 2
    
    episode_reward = 0
    steps = 0
    caught = False
    path_w1 = [(w1_x, w1_y)]
    
    while not caught and running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    q_network = SimpleQNetwork()
                    epsilon = EPSILON
        
        # 状态
        dx = w2_x - w1_x
        dy = w2_y - w1_y
        wx = 1 if w1_x < 60 else (-1 if w1_x > SCREEN_W - 60 else 0)
        wy = 1 if w1_y < 80 else (-1 if w1_y > SCREEN_H - 60 else 0)
        
        # 红悟空：神经网络决策
        action = q_network.choose_action(dx, dy, wx, wy, epsilon)
        adx, ady = ACTIONS[action]
        
        new_x = w1_x + adx
        new_y = w1_y + ady
        if not check_obstacle(new_x, new_y):
            w1_x, w1_y = check_wall(new_x, new_y)
        
        if adx != 0 or ady != 0:
            steps += 1
            path_w1.append((w1_x, w1_y))
            if len(path_w1) > 500:
                path_w1 = path_w1[-500:]
        
        # 蓝悟空：逃跑
        dx2 = -1 if w1_x < w2_x else (1 if w1_x > w2_x else 0)
        dy2 = -1 if w1_y < w2_y else (1 if w1_y > w2_y else 0)
        new_x2 = w2_x + dx2 * WUKONG_SPEED
        new_y2 = w2_y + dy2 * WUKONG_SPEED
        if not check_obstacle(new_x2, new_y2):
            w2_x, w2_y = check_wall(new_x2, new_y2)
        
        # 奖励
        dist = math.sqrt((w1_x - w2_x)**2 + (w1_y - w2_y)**2)
        collided = check_obstacle(w1_x, w1_y)
        caught = dist < CATCH_DIST
        reward = get_reward(dist, caught, collided, steps)
        
        # 下一状态
        next_dx = w2_x - w1_x
        next_dy = w2_y - w1_y
        next_wx = 1 if w1_x < 60 else (-1 if w1_x > SCREEN_W - 60 else 0)
        next_wy = 1 if w1_y < 80 else (-1 if w1_y > SCREEN_H - 60 else 0)
        
        # 更新网络
        if not caught:
            q_network.update(dx, dy, wx, wy, action, reward, next_dx, next_dy, next_wx, next_wy)
        
        episode_reward += reward
        
        # ========== 渲染 ==========
        screen.fill(BLACK)
        
        for gx in range(0, SCREEN_W, 50):
            pygame.draw.line(screen, (28, 28, 42), (gx, 0), (gx, SCREEN_H))
        for gy in range(0, SCREEN_H, 50):
            pygame.draw.line(screen, (28, 28, 42), (0, gy), (SCREEN_W, gy))
        
        for obs in OBSTACLES:
            pygame.draw.rect(screen, (70, 70, 90), (obs["x"], obs["y"], obs["w"], obs["h"]), border_radius=4)
            pygame.draw.rect(screen, (100, 100, 120), (obs["x"], obs["y"], obs["w"], obs["h"]), 2, border_radius=4)
        
        if len(path_w1) > 1:
            for i in range(len(path_w1) - 1):
                alpha = 200 * i // len(path_w1)
                color = (min(255, 180+alpha//2), min(255, 60+alpha//3), min(255, 60+alpha//4))
                pygame.draw.line(screen, color, path_w1[i], path_w1[i+1], 2)
        
        pygame.draw.line(screen, (150, 50, 50), (int(w1_x), int(w1_y)), (int(w2_x), int(w2_y)), 2)
        
        w1_rect = pygame.Rect(int(w1_x - WUKONG_SIZE//2), int(w1_y - WUKONG_SIZE//2), WUKONG_SIZE, WUKONG_SIZE)
        wk_color = PURPLE if epsilon > 0.1 else RED
        pygame.draw.rect(screen, wk_color, w1_rect, border_radius=5)
        pygame.draw.rect(screen, (255, 120, 100), (int(w1_x)-4, int(w1_y)-4, 6, 6), border_radius=2)
        lbl = font_small.render("AI", True, WHITE)
        screen.blit(lbl, (int(w1_x - lbl.get_width()//2), int(w1_y - WUKONG_SIZE//2 - 20)))
        
        w2_rect = pygame.Rect(int(w2_x - WUKONG_SIZE//2), int(w2_y - WUKONG_SIZE//2), WUKONG_SIZE, WUKONG_SIZE)
        pygame.draw.rect(screen, BLUE, w2_rect, border_radius=5)
        pygame.draw.rect(screen, (120, 160, 255), (int(w2_x)-4, int(w2_y)-4, 6, 6), border_radius=2)
        
        if caught:
            txt = font_big.render("抓住！", True, YELLOW)
            screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, SCREEN_H//2 - 20))
        
        title = font_title.render(f"悟空 v6 - 神经网络Q-Learning", True, PURPLE)
        screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 10))
        
        ep_info = font.render(f"回合 {episode+1}/{EPISODES} | ε={epsilon:.2f} | 距离 {int(dist)}", True, WHITE)
        screen.blit(ep_info, (SCREEN_W//2 - ep_info.get_width()//2, 38))
        
        # 右侧面板
        panel_x = SCREEN_W - 200
        pygame.draw.rect(screen, (22, 22, 32), (panel_x, 60, 190, SCREEN_H - 120), border_radius=8)
        
        q_vals = q_network.predict(dx, dy, wx, wy)
        data_y = 75
        screen.blit(font_small.render("Q值（当前状态）：", True, WHITE), (panel_x + 15, data_y))
        data_y += 22
        for i, (name, q) in enumerate(zip(ACTION_NAMES, q_vals)):
            color = YELLOW if i == action else WHITE
            screen.blit(font_small.render(f"{name}: {q:.1f}", True, color), (panel_x + 15, data_y))
            data_y += 18
        
        data_y += 15
        if len(episode_rewards) > 1:
            screen.blit(font_small.render("奖励曲线：", True, GRAY), (panel_x + 15, data_y))
            data_y += 20
            
            pygame.draw.rect(screen, (35, 35, 48), (panel_x + 10, data_y, 170, 80), border_radius=4)
            
            max_r = max(episode_rewards) + 1
            min_r = min(episode_rewards) - 1
            range_r = max_r - min_r if max_r != min_r else 1
            
            for i in range(len(episode_rewards) - 1):
                x1 = panel_x + 15 + i * 170 // max(1, len(episode_rewards) - 1)
                x2 = panel_x + 15 + (i+1) * 170 // max(1, len(episode_rewards) - 1)
                y1 = data_y + 75 - int((episode_rewards[i] - min_r) / range_r * 70)
                y2 = data_y + 75 - int((episode_rewards[i+1] - min_r) / range_r * 70)
                col = GREEN if episode_rewards[i+1] > episode_rewards[i] else ORANGE
                pygame.draw.line(screen, col, (x1, y1), (x2, y2), 2)
            data_y += 85
        
        data_y += 10
        screen.blit(font_small.render(f"网络状态: {q_network.get_size()}个", True, CYAN), (panel_x + 15, data_y))
        data_y += 20
        
        if episode_rewards:
            avg = sum(episode_rewards) / len(episode_rewards)
            screen.blit(font_small.render(f"平均: {avg:.0f}", True, PURPLE), (panel_x + 15, data_y))
            data_y += 20
            best = max(episode_rewards)
            screen.blit(font_small.render(f"最佳: {best:.0f}", True, GREEN), (panel_x + 15, data_y))
        
        legend_y = SCREEN_H - 55
        pygame.draw.rect(screen, PURPLE, (panel_x + 10, legend_y, 12, 12), border_radius=2)
        screen.blit(font_small.render("探索中", True, PURPLE), (panel_x + 28, legend_y - 1))
        pygame.draw.rect(screen, RED, (panel_x + 100, legend_y, 12, 12), border_radius=2)
        screen.blit(font_small.render("已学习", True, RED), (panel_x + 118, legend_y - 1))
        
        help_t = font_small.render("R重置 | ESC退出", True, GRAY)
        screen.blit(help_t, (SCREEN_W//2 - help_t.get_width()//2, SCREEN_H - 15))

        pygame.display.flip()
        clock.tick(FPS)
    
    episode_rewards.append(episode_reward)
    if caught:
        catches += 1
    epsilon = max(MIN_EPSILON, epsilon * EPSILON_DECAY)
    episode += 1

screen.fill(BLACK)
title = font_big.render("v6 神经网络完成！", True, PURPLE)
screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 50))

stats = [
    f"回合: {len(episode_rewards)}",
    f"抓住: {catches}",
    f"成功率: {catches/len(episode_rewards)*100:.0f}%",
    f"ε最终: {epsilon:.3f}",
    f"网络状态: {q_network.get_size()}个",
]
for i, s in enumerate(stats):
    t = font.render(s, True, WHITE)
    screen.blit(t, (SCREEN_W//2 - 120, 130 + i*30))

avg = sum(episode_rewards) / len(episode_rewards)
t = font.render(f"平均奖励: {avg:.0f}", True, PURPLE)
screen.blit(t, (SCREEN_W//2 - 120, 130 + len(stats)*30))

pygame.display.flip()
pygame.time.wait(5000)
pygame.quit()

print(f"\n=== 悟空v6神经网络报告 ===")
print(f"回合: {len(episode_rewards)}")
print(f"抓住次数: {catches}")
print(f"成功率: {catches/len(episode_rewards)*100:.0f}%")
print(f"平均奖励: {avg:.0f}")
print(f"ε最终: {epsilon:.3f}")
print(f"网络状态数: {q_network.get_size()}")
