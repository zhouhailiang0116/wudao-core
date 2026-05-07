# -*- coding: utf-8 -*-
"""
悟空智能体 v1：pygame环境 + 键盘控制
任务：悟空能用键盘控制，在屏幕里移动到目标

验收标准：能用方向键/WASD控制悟空移动
"""
import pygame
import sys

# ========== 配置 ==========
SCREEN_W, SCREEN_H = 600, 500
FPS = 60

# 颜色
BLACK = (20, 20, 30)
WHITE = (255, 255, 255)
RED = (230, 60, 50)
GREEN = (30, 180, 100)
BLUE = (50, 100, 230)
GRAY = (120, 120, 135)
YELLOW = (255, 210, 60)

# 悟空配置
WUKONG_SIZE = 28
WUKONG_SPEED = 5

# 目标配置
TARGET_RADIUS = 10

# ========== 初始化 ==========
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("悟空智能体 v1 - 键盘控制")
clock = pygame.time.Clock()
font = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 18)
font_small = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 14)

# ========== 悟空状态 ==========
wukong_x = SCREEN_W // 2
wukong_y = SCREEN_H // 2

# 目标随机位置
import random
def new_target():
    margin = 50
    return random.randint(margin, SCREEN_W-margin), random.randint(margin+40, SCREEN_H-margin)

target_x, target_y = new_target()

# ========== 游戏循环 ==========
running = True
steps = 0
arrived = False

while running:
    # 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                # 重置目标
                target_x, target_y = new_target()
                arrived = False

    # 键盘控制
    keys = pygame.key.get_pressed()
    dx, dy = 0, 0
    
    if keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_W]:
        dy = -WUKONG_SPEED
    if keys[pygame.K_DOWN] or keys[pygame.K_s] or keys[pygame.K_S]:
        dy = WUKONG_SPEED
    if keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_A]:
        dx = -WUKONG_SPEED
    if keys[pygame.K_RIGHT] or keys[pygame.K_d] or keys[pygame.K_D]:
        dx = WUKONG_SPEED
    
    # 移动
    wukong_x = max(WUKONG_SIZE//2, min(SCREEN_W - WUKONG_SIZE//2, wukong_x + dx))
    wukong_y = max(WUKONG_SIZE//2, min(SCREEN_H - WUKONG_SIZE//2, wukong_y + dy))
    
    if dx != 0 or dy != 0:
        steps += 1
    
    # 检测到达目标
    dist = ((wukong_x - target_x)**2 + (wukong_y - target_y)**2)**0.5
    if dist < WUKONG_SIZE//2 + TARGET_RADIUS:
        if not arrived:
            arrived = True
            target_x, target_y = new_target()  # 立刻生成新目标

    # ========== 渲染 ==========
    screen.fill(BLACK)
    
    # 背景网格
    for gx in range(0, SCREEN_W, 40):
        pygame.draw.line(screen, (35, 35, 48), (gx, 0), (gx, SCREEN_H))
    for gy in range(0, SCREEN_H, 40):
        pygame.draw.line(screen, (35, 35, 48), (0, gy), (SCREEN_W, gy))
    
    # 目标（绿色圆点）
    pygame.draw.circle(screen, GREEN, (target_x, target_y), TARGET_RADIUS)
    pygame.draw.circle(screen, (80, 220, 150), (target_x, target_y), TARGET_RADIUS, 2)
    
    # 距离线（悟空到目标）
    if not arrived:
        alpha_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        alpha_surf.set_alpha(40)
        pygame.draw.line(alpha_surf, GREEN, (wukong_x, wukong_y), (target_x, target_y), 1)
        screen.blit(alpha_surf, (0, 0))
    
    # 悟空（红色方块）
    wukong_rect = pygame.Rect(
        wukong_x - WUKONG_SIZE//2,
        wukong_y - WUKONG_SIZE//2,
        WUKONG_SIZE, WUKONG_SIZE
    )
    pygame.draw.rect(screen, RED, wukong_rect, border_radius=4)
    # 高光
    pygame.draw.rect(screen, (255, 120, 100), 
                     (wukong_rect.x+3, wukong_rect.y+3, 8, 8), border_radius=2)
    
    # 到达提示
    if arrived:
        text = font.render("到达！新目标已生成", True, YELLOW)
        screen.blit(text, (SCREEN_W//2 - text.get_width()//2, 30))
    
    # 信息面板
    info_bg = pygame.Rect(10, SCREEN_H - 70, 200, 60)
    pygame.draw.rect(screen, (30, 30, 40), info_bg, border_radius=8)
    
    dist_val = int(dist)
    screen.blit(font_small.render(f"步数: {steps}", True, WHITE), (20, SCREEN_H - 58))
    screen.blit(font_small.render(f"距离: {dist_val}px", True, WHITE), (20, SCREEN_H - 38))
    screen.blit(font_small.render(f"速度: {WUKONG_SPEED}px/帧", True, GRAY), (20, SCREEN_H - 18))
    
    # 操作说明
    help_text = font_small.render("↑↓←→/WASD 移动  |  SPACE 重置目标  |  ESC 退出", True, GRAY)
    screen.blit(help_text, (SCREEN_W//2 - help_text.get_width()//2, SCREEN_H - 20))
    
    # 标题
    title = font.render("悟空 v1 - 键盘控制", True, BLUE)
    screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 10))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
print(f"游戏结束。总步数: {steps}")
