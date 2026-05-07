# -*- coding: utf-8 -*-
"""
悟空物理世界 - 验证版
测试：悟空是否真的在学物理，还是只是碰运气
"""
import pygame
import random
import math

SCREEN_W, SCREEN_H = 900, 650
FPS = 60
EPISODES = 30

GRAVITY = 0.5       # 增强重力，更难学
FRICTION = 0.95
BOUNCE = 0.6
WUKONG_SIZE = 28
CATCH_DIST = WUKONG_SIZE * 1.5

BLACK = (20, 20, 30)
RED = (230, 60, 50)
BLUE = (50, 100, 230)
GREEN = (30, 180, 100)
GRAY = (120, 120, 135)
YELLOW = (255, 210, 60)
CYAN = (50, 200, 200)
WHITE = (255, 255, 255)

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
clock = pygame.time.Clock()
font = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 18)
font_small = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 14)
font_big = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 28)

class PhysicsBody:
    def __init__(self, x, y, vx=0, vy=0):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.radius = WUKONG_SIZE // 2
    
    def apply_force(self, fx, fy):
        self.vx += fx
        self.vy += fy
    
    def update(self):
        self.vy += GRAVITY
        self.vx *= FRICTION
        self.vy *= FRICTION
        
        speed = math.sqrt(self.vx**2 + self.vy**2)
        max_speed = 12
        if speed > max_speed:
            self.vx = self.vx / speed * max_speed
            self.vy = self.vy / speed * max_speed
        
        self.x += self.vx
        self.y += self.vy
        
        if self.x < self.radius: self.x = self.radius; self.vx *= -BOUNCE
        if self.x > SCREEN_W - self.radius: self.x = SCREEN_W - self.radius; self.vx *= -BOUNCE
        if self.y < self.radius: self.y = self.radius; self.vy *= -BOUNCE
        if self.y > SCREEN_H - self.radius: self.y = SCREEN_H - self.radius; self.vy *= -BOUNCE

# 智能体：学会预测物理
class LearningAgent:
    def __init__(self):
        self.knowledge = {}  # 状态 -> 最佳动作
        self.alpha = 0.1
        self.epsilon = 0.3
    
    def get_state(self, body, target):
        # 简化状态：相对位置 + 身体速度方向
        dx = target.x - body.x
        dy = target.y - body.y
        dist = math.sqrt(dx**2 + dy**2)
        dvx = body.vx
        dvy = body.vy
        
        # 离散化
        angle = math.atan2(dy, dx) if dist > 0 else 0
        key = (
            "up" if dvy < -1 else "down" if dvy > 1 else "mid",
            "left" if dvx < -1 else "right" if dvx > 1 else "mid",
            "close" if dist < 100 else "far"
        )
        return key
    
    def decide(self, body, target):
        state = self.get_state(body, target)
        
        # 探索
        if random.random() < self.epsilon:
            forces = [(0,-0.8), (0,0.8), (-0.5,0), (0.5,0)]
            return random.choice(forces)
        
        # 利用经验
        if state in self.knowledge:
            return self.knowledge[state]
        
        # 默认：朝目标
        dx = target.x - body.x
        dy = target.y - body.y
        dist = math.sqrt(dx**2 + dy**2) if dx != 0 or dy != 0 else 1
        return (dx/dist * 0.8, dy/dist * 0.8)
    
    def learn(self, state, action, reward):
        if state not in self.knowledge:
            self.knowledge[state] = action
        else:
            # 简单更新
            ox, oy = self.knowledge[state]
            self.knowledge[state] = (ox * (1-self.alpha) + action[0] * self.alpha,
                                    oy * (1-self.alpha) + action[1] * self.alpha)

agent = LearningAgent()
episode = 0
running = True
catches = 0
episode_rewards = []

while running and episode < EPISODES:
    w1 = PhysicsBody(100, SCREEN_H // 2)
    w2 = PhysicsBody(SCREEN_W - 100, SCREEN_H // 2, 
                    vx=random.uniform(-3, 3), vy=random.uniform(-3, 3))
    
    episode_reward = 0
    steps = 0
    caught = False
    
    while not caught and running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
        
        # 决策
        state = agent.get_state(w1, w2)
        fx, fy = agent.decide(w1, w2)
        w1.apply_force(fx, fy)
        
        # 蓝随机
        if random.random() < 0.03:
            w2.apply_force(random.uniform(-1, 1), random.uniform(-1, 1))
        
        w1.update()
        w2.update()
        steps += 1
        
        # 奖励
        dist = math.sqrt((w1.x - w2.x)**2 + (w1.y - w2.y)**2)
        
        if dist < CATCH_DIST:
            caught = True
            reward = 100
            agent.learn(state, (fx, fy), reward)
            catches += 1
        elif steps > 400:
            reward = -10
        else:
            reward = -dist / 50
        
        episode_reward += reward
        
        if not caught and steps % 10 == 0:
            agent.learn(state, (fx, fy), reward)
        
        if steps > 500:
            break
        
        # 渲染
        screen.fill(BLACK)
        
        for gx in range(0, SCREEN_W, 40):
            pygame.draw.line(screen, (28, 28, 42), (gx, 0), (gx, SCREEN_H))
        for gy in range(0, SCREEN_H, 40):
            pygame.draw.line(screen, (28, 28, 42), (0, gy), (SCREEN_W, gy))
        
        # 物理指示
        pygame.draw.circle(screen, GREEN, (50, 25), 6)
        screen.blit(font_small.render(f"重力:{GRAVITY}", True, GREEN), (60, 17))
        pygame.draw.circle(screen, YELLOW, (170, 25), 6)
        screen.blit(font_small.render(f"摩擦:{FRICTION}", True, YELLOW), (180, 17))
        
        # 速度向量
        if abs(w1.vy) > 0.5:
            pygame.draw.line(screen, RED, (int(w1.x), int(w1.y)),
                           (int(w1.x + w1.vx*4), int(w1.y + w1.vy*4)), 3)
        
        pygame.draw.circle(screen, RED, (int(w1.x), int(w1.y)), w1.radius)
        pygame.draw.circle(screen, (255,130,120), (int(w1.x)+4, int(w1.y)-4), 4)
        
        pygame.draw.circle(screen, BLUE, (int(w2.x), int(w2.y)), w1.radius)
        pygame.draw.line(screen, (150,50,50), (int(w1.x), int(w1.y)),
                        (int(w2.x), int(w2.y)), 2)
        
        if caught:
            txt = font_big.render("抓住！", True, YELLOW)
            screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, SCREEN_H//2))
        
        title = font.render(f"回合 {episode+1}/{EPISODES} | 重力学习", True, CYAN)
        screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 10))
        
        data = font_small.render(f"步数:{steps} 距离:{int(dist)} 速度:{math.sqrt(w1.vx**2+w1.vy**2):.1f}", True, WHITE)
        screen.blit(data, (SCREEN_W//2 - data.get_width()//2, 40))
        
        panel_x = SCREEN_W - 180
        pygame.draw.rect(screen, (25,25,35), (panel_x, 60, 170, SCREEN_H-120), border_radius=8)
        screen.blit(font_small.render(f"回合:{episode+1}", True, WHITE), (panel_x+15, 75))
        screen.blit(font_small.render(f"抓住:{catches}", True, GREEN), (panel_x+15, 95))
        if episode_rewards:
            avg = sum(episode_rewards)/len(episode_rewards)
            screen.blit(font_small.render(f"平均奖励:{avg:.0f}", True, CYAN), (panel_x+15, 115))
        
        pygame.display.flip()
        clock.tick(FPS)
    
    episode_rewards.append(episode_reward)
    episode += 1
    agent.epsilon = max(0.05, agent.epsilon * 0.98)
    pygame.time.wait(200)

screen.fill(BLACK)
title = font_big.render("物理世界学习完成！", True, CYAN)
screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 50))

results = [
    f"回合: {EPISODES}",
    f"抓住: {catches}",
    f"成功率: {catches/EPISODES*100:.0f}%",
    f"学到的状态数: {len(agent.knowledge)}",
]

for i, r in enumerate(results):
    t = font.render(r, True, WHITE)
    screen.blit(t, (SCREEN_W//2 - 80, 130 + i*30))

pygame.display.flip()
pygame.time.wait(5000)
pygame.quit()

print(f"\n=== 物理世界验证结果 ===")
print(f"回合: {EPISODES}")
print(f"抓住: {catches} ({catches/EPISODES*100:.0f}%)")
print(f"学到的状态: {len(agent.knowledge)}")
print(f"重力: {GRAVITY}, 摩擦: {FRICTION}, 反弹: {BOUNCE}")
