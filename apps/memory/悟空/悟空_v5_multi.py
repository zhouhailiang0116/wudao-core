# -*- coding: utf-8 -*-
"""
悟空智能体 v5：多智能体协作/对抗
v5.1 修复版：确保双方都可见
"""
import pygame
import random
import math

# ========== 配置 ==========
SCREEN_W, SCREEN_H = 1000, 650
FPS = 60
EPISODES = 15
STEPS_PER_EPISODE = 600

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
WUKONG_SIZE = 30
WUKONG_SPEED = 5
CATCH_DIST = WUKONG_SIZE * 1.5

# ========== 初始化 ==========
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("悟空 v5 - 对抗模式")
clock = pygame.time.Clock()
font = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 20)
font_small = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 16)
font_big = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 32)

def simple_ai(x, y, tx, ty):
    """简单AI：朝目标移动"""
    dx, dy = 0, 0
    if x < tx - 5: dx = WUKONG_SPEED
    elif x > tx + 5: dx = -WUKONG_SPEED
    if y < ty - 5: dy = WUKONG_SPEED
    elif y > ty + 5: dy = -WUKONG_SPEED
    return dx, dy

def check_wall(x, y):
    """边界检测"""
    x = max(WUKONG_SIZE//2, min(SCREEN_W - WUKONG_SIZE//2, x))
    y = max(WUKONG_SIZE//2, min(SCREEN_H - WUKONG_SIZE//2, y))
    return x, y

# ========== 主循环 ==========
w1_x, w1_y = 150, SCREEN_H // 2  # 红悟空（追）
w2_x, w2_y = SCREEN_W - 150, SCREEN_H // 2  # 蓝悟空（逃）

episode = 0
running = True
episode_scores = []
catches = 0

while running and episode < EPISODES:
    # 初始化位置
    w1_x, w1_y = 100, SCREEN_H // 2
    w2_x, w2_y = SCREEN_W - 100, SCREEN_H // 2
    
    steps = 0
    caught = False
    
    while not caught and running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # 红悟空追蓝悟空
        dx1, dy1 = simple_ai(w1_x, w1_y, w2_x, w2_y)
        w1_x, w1_y = check_wall(w1_x + dx1, w1_y + dy1)
        
        # 蓝悟空逃红悟空
        dx2, dy2 = simple_ai(w2_x, w2_y, w1_x, w1_y)
        w2_x, w2_y = check_wall(w2_x - dx2, w2_y - dy2)  # 反方向逃
        
        # 检测追到
        dist = math.sqrt((w1_x - w2_x)**2 + (w1_y - w2_y)**2)
        if dist < CATCH_DIST:
            caught = True
            catches += 1
        
        steps += 1
        if steps >= STEPS_PER_EPISODE:
            break
        
        # ========== 渲染 ==========
        screen.fill(BLACK)
        
        # 网格背景
        for gx in range(0, SCREEN_W, 50):
            pygame.draw.line(screen, (30, 30, 45), (gx, 0), (gx, SCREEN_H))
        for gy in range(0, SCREEN_H, 50):
            pygame.draw.line(screen, (30, 30, 45), (0, gy), (SCREEN_W, gy))
        
        # 中线
        pygame.draw.line(screen, (60, 60, 80), (SCREEN_W//2, 0), (SCREEN_W//2, SCREEN_H), 2)
        
        # 连接线（红追蓝的线）
        pygame.draw.line(screen, (180, 60, 60), (int(w1_x), int(w1_y)), (int(w2_x), int(w2_y)), 2)
        
        # 红悟空（追）
        w1_rect = pygame.Rect(int(w1_x - WUKONG_SIZE//2), int(w1_y - WUKONG_SIZE//2), WUKONG_SIZE, WUKONG_SIZE)
        pygame.draw.rect(screen, RED, w1_rect, border_radius=6)
        pygame.draw.rect(screen, (255, 130, 120), (int(w1_x)-5, int(w1_y)-5, 8, 8), border_radius=2)
        # 标签
        lbl1 = font.render("红", True, WHITE)
        screen.blit(lbl1, (int(w1_x - lbl1.get_width()//2), int(w1_y - WUKONG_SIZE//2 - 25)))
        
        # 蓝悟空（逃）
        w2_rect = pygame.Rect(int(w2_x - WUKONG_SIZE//2), int(w2_y - WUKONG_SIZE//2), WUKONG_SIZE, WUKONG_SIZE)
        pygame.draw.rect(screen, BLUE, w2_rect, border_radius=6)
        pygame.draw.rect(screen, (120, 160, 255), (int(w2_x)-5, int(w2_y)-5, 8, 8), border_radius=2)
        # 标签
        lbl2 = font.render("蓝", True, WHITE)
        screen.blit(lbl2, (int(w2_x - lbl2.get_width()//2), int(w2_y - WUKONG_SIZE//2 - 25)))
        
        # 追到提示
        if caught:
            txt = font_big.render("抓住了！", True, YELLOW)
            screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, SCREEN_H//2 - 20))
        
        # 顶部信息
        title = font.render(f"悟空 v5 - 对抗模式", True, CYAN)
        screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 15))
        
        ep_info = font.render(f"回合 {episode+1}/{EPISODES} | 步数 {steps} | 距离 {int(dist)}", True, WHITE)
        screen.blit(ep_info, (SCREEN_W//2 - ep_info.get_width()//2, 45))
        
        # 底部数据
        score_info = font.render(f"本回合: {'抓住！' if caught else '未抓住'} | 总抓住: {catches}", True, YELLOW if caught else GRAY)
        screen.blit(score_info, (SCREEN_W//2 - score_info.get_width()//2, SCREEN_H - 45))
        
        help_t = font_small.render("ESC退出", True, GRAY)
        screen.blit(help_t, (SCREEN_W//2 - help_t.get_width()//2, SCREEN_H - 20))

        pygame.display.flip()
        clock.tick(FPS)
    
    episode_scores.append(1 if caught else 0)
    episode += 1
    
    pygame.time.wait(500)

# ========== 最终报告 ==========
screen.fill(BLACK)
title = font_big.render("v5 对抗完成！", True, CYAN)
screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 50))

stats = [
    f"回合: {len(episode_scores)}",
    f"抓住次数: {catches}",
    f"成功率: {catches/len(episode_scores)*100:.0f}%",
]
for i, s in enumerate(stats):
    t = font.render(s, True, WHITE)
    screen.blit(t, (SCREEN_W//2 - 100, 130 + i*35))

pygame.display.flip()
pygame.time.wait(4000)
pygame.quit()

print(f"\n=== 悟空v5对抗报告 ===")
print(f"回合: {len(episode_scores)}")
print(f"抓住次数: {catches}")
print(f"成功率: {catches/len(episode_scores)*100:.0f}%")
