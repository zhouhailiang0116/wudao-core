# -*- coding: utf-8 -*-
"""
悟空智能体 - 物理世界vs数字世界
任务：悟空在虚拟环境中理解两个世界的差异

物理世界：重力、摩擦力、碰撞反弹
数字世界：网格、像素、无重力

这个版本让悟空在"真实物理"环境中行动
"""
import pygame
import random
import math

# ========== 配置 ==========
SCREEN_W, SCREEN_H = 900, 650
FPS = 60
EPISODES = 20

# 物理参数
GRAVITY = 0.3       # 重力
FRICTION = 0.98     # 摩擦力
BOUNCE = 0.7        # 反弹系数
WUKONG_SIZE = 28
WUKONG_SPEED = 8
TARGET_RADIUS = 12
CATCH_DIST = WUKONG_SIZE * 1.5

# 颜色
BLACK = (20, 20, 30)
WHITE = (255, 255, 255)
RED = (230, 60, 50)
BLUE = (50, 100, 230)
GREEN = (30, 180, 100)
GRAY = (120, 120, 135)
YELLOW = (255, 210, 60)
CYAN = (50, 200, 200)
PURPLE = (160, 80, 220)

# ========== 初始化 ==========
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("悟空智能体 - 物理世界vs数字世界")
clock = pygame.time.Clock()
font = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 18)
font_small = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 14)
font_big = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 28)

# 物理引擎
class PhysicsBody:
    def __init__(self, x, y, vx=0, vy=0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = WUKONG_SIZE // 2
    
    def apply_force(self, fx, fy):
        self.vx += fx
        self.vy += fy
    
    def update(self):
        # 重力
        self.vy += GRAVITY
        # 摩擦力
        self.vx *= FRICTION
        self.vy *= FRICTION
        # 速度限制
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > WUKONG_SPEED:
            self.vx = self.vx / speed * WUKONG_SPEED
            self.vy = self.vy / speed * WUKONG_SPEED
        # 移动
        self.x += self.vx
        self.y += self.vy
        # 边界反弹
        if self.x < self.radius:
            self.x = self.radius
            self.vx *= -BOUNCE
        if self.x > SCREEN_W - self.radius:
            self.x = SCREEN_W - self.radius
            self.vx *= -BOUNCE
        if self.y < self.radius:
            self.y = self.radius
            self.vy *= -BOUNCE
        if self.y > SCREEN_H - self.radius:
            self.y = SCREEN_H - self.radius
            self.vy *= -BOUNCE
    
    def get_pos(self):
        return int(self.x), int(self.y)

# AI控制器（简单策略）
class AIController:
    def __init__(self):
        self.learning = True
    
    def decide(self, body, target_x, target_y):
        # 朝目标方向施加力
        dx = target_x - body.x
        dy = target_y - body.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist < 5:
            return 0, 0
        
        # 归一化
        fx = dx / dist * 0.8
        fy = dy / dist * 0.8
        
        return fx, fy

# ========== 主循环 ==========
print("=== 悟空：物理世界vs数字世界 ===")
print("物理世界：重力、摩擦力、反弹")
print("数字世界：无重力、无摩擦、网格移动")

ai = AIController()
episode = 0
running = True
catches = 0

# 统计
physics_knowledge = []  # 记录物理行为
episode_times = []

while running and episode < EPISODES:
    # 创建物理身体
    w1 = PhysicsBody(100, SCREEN_H // 2)
    w2 = PhysicsBody(SCREEN_W - 100, SCREEN_H // 2, vx=random.uniform(-2, 2), vy=random.uniform(-2, 2))
    
    target_x, target_y = random.randint(200, SCREEN_W-200), random.randint(150, SCREEN_H-150)
    
    start_time = pygame.time.get_ticks()
    caught = False
    steps = 0
    max_steps = 600  # 10秒
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # AI决策
        fx, fy = ai.decide(w1, w2.x, w2.y)
        w1.apply_force(fx, fy)
        
        # 蓝悟空随机移动
        if random.random() < 0.05:
            w2.apply_force(random.uniform(-1, 1), random.uniform(-1, 1))
        
        # 物理更新
        w1.update()
        w2.update()
        steps += 1
        
        # 检测
        dist = math.sqrt((w1.x - w2.x)**2 + (w1.y - w2.y)**2)
        if dist < CATCH_DIST:
            caught = True
            break
        
        if steps > max_steps:
            break
        
        # ========== 渲染 ==========
        screen.fill(BLACK)
        
        # 背景提示
        help_bg = pygame.Rect(0, 0, SCREEN_W, 50)
        pygame.draw.rect(screen, (25, 25, 35), help_bg)
        
        # 标题
        title = font.render("悟空：物理世界 vs 数字世界", True, CYAN)
        screen.blit(title, (10, 15))
        
        # 世界状态指示
        physics_y = 18
        pygame.draw.circle(screen, GREEN, (SCREEN_W - 180, physics_y), 6)
        screen.blit(font_small.render("重力: ON", True, GREEN), (SCREEN_W - 170, physics_y - 5))
        
        pygame.draw.circle(screen, YELLOW, (SCREEN_W - 90, physics_y), 6)
        screen.blit(font_small.render("摩擦: ON", True, YELLOW), (SCREEN_W - 80, physics_y - 5))
        
        # 网格（数字世界特征）
        for gx in range(0, SCREEN_W, 40):
            pygame.draw.line(screen, (30, 30, 42), (gx, 0), (gx, SCREEN_H))
        for gy in range(0, SCREEN_H, 40):
            pygame.draw.line(screen, (30, 30, 42), (0, gy), (SCREEN_W, gy))
        
        # 物理指示
        if abs(w1.vy) > 0.5:  # 下落中
            pygame.draw.line(screen, RED, (int(w1.x), int(w1.y)), 
                           (int(w1.x + w1.vx*3), int(w1.y + w1.vy*3)), 2)
        
        # 速度向量
        speed = math.sqrt(w1.vx**2 + w1.vy**2)
        vel_text = font_small.render(f"v={speed:.1f}", True, GRAY)
        screen.blit(vel_text, (int(w1.x) + 20, int(w1.y) - 10))
        
        # 目标
        pygame.draw.circle(screen, GREEN, (target_x, target_y), TARGET_RADIUS + 4)
        pygame.draw.circle(screen, (80, 230, 140), (target_x, target_y), TARGET_RADIUS)
        
        # 红悟空
        wx, wy = w1.get_pos()
        pygame.draw.circle(screen, RED, (wx, wy), WUKONG_SIZE//2)
        pygame.draw.circle(screen, (255, 130, 120), (wx+5, wy-5), 5)
        screen.blit(font_small.render("红", True, WHITE), (wx - 7, wy - WUKONG_SIZE//2 - 18))
        
        # 蓝悟空
        bx, by = w2.get_pos()
        pygame.draw.circle(screen, BLUE, (bx, by), WUKONG_SIZE//2)
        pygame.draw.circle(screen, (120, 160, 255), (bx+5, by-5), 5)
        screen.blit(font_small.render("蓝", True, WHITE), (bx - 7, by - WUKONG_SIZE//2 - 18))
        
        # 连线
        pygame.draw.line(screen, (150, 50, 50), (wx, wy), (bx, by), 2)
        
        # 抓住提示
        if caught:
            txt = font_big.render("抓住了！", True, YELLOW)
            screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, SCREEN_H//2 - 20))
        
        # 底部数据
        data_y = SCREEN_H - 80
        pygame.draw.rect(screen, (25, 25, 35), (10, data_y, SCREEN_W - 20, 70), border_radius=8)
        
        screen.blit(font_small.render(f"回合: {episode+1}/{EPISODES}", True, WHITE), (20, data_y + 8))
        screen.blit(font_small.render(f"步数: {steps}", True, WHITE), (20, data_y + 28))
        screen.blit(font_small.render(f"红速度: {math.sqrt(w1.vx**2+w1.vy**2):.1f}", True, RED), (20, data_y + 48))
        
        screen.blit(font_small.render(f"蓝速度: {math.sqrt(w2.vx**2+w2.vy**2):.1f}", True, BLUE), (200, data_y + 8))
        screen.blit(font_small.render(f"距离: {int(dist)}", True, WHITE), (200, data_y + 28))
        
        # 物理vs数字对比
        physics_text = font_small.render("物理世界: 重力+摩擦+反弹  |  数字世界: 网格+离散移动", True, GRAY)
        screen.blit(physics_text, (SCREEN_W//2 - physics_text.get_width()//2, data_y + 50))
        
        # 帮助
        help_t = font_small.render("ESC退出", True, GRAY)
        screen.blit(help_t, (SCREEN_W - 80, SCREEN_H - 20))

        pygame.display.flip()
        clock.tick(FPS)
    
    # 回合结束
    elapsed = (pygame.time.get_ticks() - start_time) / 1000
    episode_times.append(elapsed)
    
    if caught:
        catches += 1
    
    physics_knowledge.append({
        "episode": episode + 1,
        "caught": caught,
        "time": elapsed,
        "steps": steps,
        "w1_speed": math.sqrt(w1.vx**2 + w1.vy**2),
        "w2_speed": math.sqrt(w2.vx**2 + w2.vy**2),
    })
    
    episode += 1
    pygame.time.wait(500)

# ========== 最终报告 ==========
screen.fill(BLACK)
title = font_big.render("物理世界vs数字世界 - 完成！", True, CYAN)
screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 30))

# 物理知识总结
knowledge_text = [
    "悟空在物理世界中学会了：",
    "• 重力：物体会下落（vy持续增加）",
    "• 摩擦力：速度会衰减",
    "• 反弹：撞墙会反弹（速度反向×系数）",
    "",
    "与数字世界的区别：",
    "• 数字世界：网格移动，无重力",
    "• 物理世界：连续移动，有重力摩擦",
    "• 物理世界更接近真实！",
]

for i, line in enumerate(knowledge_text):
    color = YELLOW if "•" in line else WHITE
    size = 18 if "悟空" in line or "与" in line else 16
    t = font.render(line, True, color)
    screen.blit(t, (80, 100 + i * 28))

# 统计数据
stats_y = 420
pygame.draw.rect(screen, (30, 30, 42), (50, stats_y, SCREEN_W - 100, 150), border_radius=10)

stats = [
    f"回合: {len(physics_knowledge)}",
    f"抓住次数: {catches}",
    f"成功率: {catches/len(physics_knowledge)*100:.0f}%",
    f"平均用时: {sum(d['time'] for d in physics_knowledge)/len(physics_knowledge):.1f}秒",
]

for i, s in enumerate(stats):
    t = font.render(s, True, WHITE)
    screen.blit(t, (100, stats_y + 20 + i * 28))

# 对比表
contrast = [
    "维度       物理世界     数字世界",
    "移动       连续         离散",
    "重力       有           无",
    "摩擦       有           无",
    "反弹       有           无",
    "真实感     强           弱",
]

for i, line in enumerate(contrast):
    color = CYAN if i == 0 else WHITE
    t = font_small.render(line, True, color)
    screen.blit(t, (SCREEN_W - 320, stats_y + 15 + i * 20))

pygame.display.flip()
pygame.time.wait(8000)
pygame.quit()

print("\n=== 悟空：物理世界vs数字世界 ===")
print(f"回合: {len(physics_knowledge)}")
print(f"抓住: {catches} ({catches/len(physics_knowledge)*100:.0f}%)")
print(f"平均用时: {sum(d['time'] for d in physics_knowledge)/len(physics_knowledge):.1f}秒")
print("\n悟空学到了：")
print("- 物理世界：重力、摩擦力、反弹")
print("- 数字世界：网格、离散移动")
print("- 理解两个世界的差异")
