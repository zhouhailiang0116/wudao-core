# -*- coding: utf-8 -*-
"""
悟空智能体 v2：自动导航学习
任务：悟空能自己找到目标，不需要键盘控制

算法：简单策略 - 朝目标方向移动
奖励函数：距离越小奖励越高，到达目标给大奖
"""
import pygame
import random
import math

# ========== 配置 ==========
SCREEN_W, SCREEN_H = 600, 500
FPS = 60
EPISODES = 10
STEPS_PER_EPISODE = 200

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

# 悟空配置
WUKONG_SIZE = 28
WUKONG_SPEED = 4
TARGET_RADIUS = 10
REACH_DIST = WUKONG_SIZE // 2 + TARGET_RADIUS

# ========== 初始化 ==========
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("悟空智能体 v2 - 自动导航学习")
clock = pygame.time.Clock()
font = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 18)
font_small = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 14)
font_big = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 28)

def new_target():
    margin = 60
    return random.randint(margin, SCREEN_W - margin), random.randint(margin + 40, SCREEN_H - margin)

def get_distance(x, y, tx, ty):
    return math.sqrt((x - tx) ** 2 + (y - ty) ** 2)

def get_reward(dist):
    if dist < REACH_DIST:
        return 100
    return -dist / 10

def decide_action(x, y, tx, ty):
    dx, dy = 0, 0
    if x < tx - 2:
        dx = WUKONG_SPEED
    elif x > tx + 2:
        dx = -WUKONG_SPEED
    if y < ty - 2:
        dy = WUKONG_SPEED
    elif y > ty + 2:
        dy = -WUKONG_SPEED
    return dx, dy

episode_rewards = []
episode_steps = []

episode = 0
running = True
auto_mode = True

while running and episode < EPISODES:
    wukong_x = SCREEN_W // 2
    wukong_y = SCREEN_H // 2
    target_x, target_y = new_target()

    episode_reward = 0
    steps = 0
    done = False

    while not done and running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    auto_mode = not auto_mode

        if auto_mode:
            dx, dy = decide_action(wukong_x, wukong_y, target_x, target_y)
        else:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy = -WUKONG_SPEED
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy = WUKONG_SPEED
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -WUKONG_SPEED
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = WUKONG_SPEED

        wukong_x = max(WUKONG_SIZE // 2, min(SCREEN_W - WUKONG_SIZE // 2, wukong_x + dx))
        wukong_y = max(WUKONG_SIZE // 2, min(SCREEN_H - WUKONG_SIZE // 2, wukong_y + dy))
        steps += 1

        dist = get_distance(wukong_x, wukong_y, target_x, target_y)
        reward = get_reward(dist)
        episode_reward += reward

        if dist < REACH_DIST:
            done = True
            target_x, target_y = new_target()

        if steps >= STEPS_PER_EPISODE:
            done = True

        # ========== 渲染 ==========
        screen.fill(BLACK)

        for gx in range(0, SCREEN_W, 40):
            pygame.draw.line(screen, (35, 35, 48), (gx, 0), (gx, SCREEN_H))
        for gy in range(0, SCREEN_H, 40):
            pygame.draw.line(screen, (35, 35, 48), (0, gy), (SCREEN_W, gy))

        pygame.draw.circle(screen, GREEN, (target_x, target_y), TARGET_RADIUS)
        pygame.draw.circle(screen, (80, 220, 150), (target_x, target_y), TARGET_RADIUS, 2)

        if not done:
            for i in range(0, int(dist), 8):
                t = i / dist
                px = int(wukong_x + (target_x - wukong_x) * t)
                py = int(wukong_y + (target_y - wukong_y) * t)
                pygame.draw.circle(screen, (60, 60, 80), (px, py), 1)

        wukong_rect = pygame.Rect(
            wukong_x - WUKONG_SIZE // 2,
            wukong_y - WUKONG_SIZE // 2,
            WUKONG_SIZE, WUKONG_SIZE
        )
        pygame.draw.rect(screen, RED, wukong_rect, border_radius=4)
        pygame.draw.rect(screen, (255, 120, 100),
                         (wukong_rect.x + 3, wukong_rect.y + 3, 8, 8), border_radius=2)

        if done and dist < REACH_DIST:
            text = font.render("到达！", True, YELLOW)
            screen.blit(text, (SCREEN_W // 2 - text.get_width() // 2, 30))
        elif done:
            text = font.render("超时", True, ORANGE)
            screen.blit(text, (SCREEN_W // 2 - text.get_width() // 2, 30))

        mode_color = GREEN if auto_mode else YELLOW
        mode_text = "自动" if auto_mode else "手动"
        title = font.render(f"回合 {episode + 1}/{EPISODES} | {mode_text}", True, mode_color)
        screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 10))

        info_y = SCREEN_H - 110

        if len(episode_rewards) > 1:
            max_r = max(episode_rewards) if episode_rewards else 100
            min_r = min(episode_rewards) if episode_rewards else -100
            range_r = max_r - min_r if max_r != min_r else 1
            for i in range(len(episode_rewards) - 1):
                x1 = 20 + i * (SCREEN_W - 40) // max(1, len(episode_rewards) - 1)
                x2 = 20 + (i + 1) * (SCREEN_W - 40) // max(1, len(episode_rewards) - 1)
                y1 = info_y + 60 - int((episode_rewards[i] - min_r) / range_r * 50)
                y2 = info_y + 60 - int((episode_rewards[i + 1] - min_r) / range_r * 50)
                pygame.draw.line(screen, PURPLE, (x1, y1), (x2, y2), 2)

        info_bg = pygame.Rect(10, info_y, SCREEN_W - 20, 90)
        pygame.draw.rect(screen, (30, 30, 40), info_bg, border_radius=8)

        screen.blit(font_small.render(f"步数: {steps}", True, WHITE), (20, info_y + 8))
        screen.blit(font_small.render(f"奖励: {episode_reward:.1f}", True, WHITE), (20, info_y + 28))
        screen.blit(font_small.render(f"距离: {int(dist)}", True, WHITE), (20, info_y + 48))
        screen.blit(font_small.render(f"回合: {len(episode_rewards)}", True, GRAY), (20, info_y + 68))

        if episode_rewards:
            screen.blit(font_small.render(f"平均: {sum(episode_rewards) / len(episode_rewards):.1f}", True, PURPLE), (200, info_y + 8))
            screen.blit(font_small.render(f"最佳: {max(episode_rewards):.1f}", True, GREEN), (200, info_y + 28))

        help_txt = "SPACE切换 | WASD手动 | ESC退出"
        help_text = font_small.render(help_txt, True, GRAY)
        screen.blit(help_text, (SCREEN_W // 2 - help_text.get_width() // 2, SCREEN_H - 15))

        pygame.display.flip()
        clock.tick(FPS)

    episode_rewards.append(episode_reward)
    episode_steps.append(steps)
    episode += 1

screen.fill(BLACK)
title = font_big.render("学习完成！", True, GREEN)
screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 2 - 60))

for i, (r, s) in enumerate(zip(episode_rewards, episode_steps)):
    screen.blit(font_small.render(f"回合{i + 1}: 奖励={r:.1f}, 步数={s}", True, WHITE),
                 (SCREEN_W // 2 - 120, SCREEN_H // 2 - 20 + i * 22))

avg = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0
screen.blit(font.render(f"平均奖励: {avg:.1f}", True, PURPLE),
            (SCREEN_W // 2 - 80, SCREEN_H // 2 + 50))

pygame.display.flip()
pygame.time.wait(3000)
pygame.quit()

print(f"\n=== 悟空v2学习报告 ===")
print(f"完成回合: {len(episode_rewards)}")
print(f"平均奖励: {avg:.1f}")
print(f"最佳奖励: {max(episode_rewards):.1f}")
print(f"最差奖励: {min(episode_rewards):.1f}")
