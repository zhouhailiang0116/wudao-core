# -*- coding: utf-8 -*-
import cv2
import numpy as np
import pygame
import math
import random

SCREEN_W = 1000
SCREEN_H = 700
FPS = 30

RED_LOWER1 = np.array([0, 100, 100])
RED_UPPER1 = np.array([10, 255, 255])
RED_LOWER2 = np.array([160, 100, 100])
RED_UPPER2 = np.array([180, 255, 255])

WUKONG_SIZE = 40
WUKONG_SPEED = 5
CATCH_DIST = 50

RED = (230, 60, 50)
GREEN = (30, 180, 100)
BLUE = (50, 100, 230)
YELLOW = (255, 210, 60)
WHITE = (255, 255, 255)
GRAY = (120, 120, 135)
CYAN = (50, 200, 200)

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Wukong v8 - Camera Vision")
clock = pygame.time.Clock()

def make_font(size):
    try:
        return pygame.font.Font('C:/Windows/Fonts/msyh.ttc', size)
    except:
        return pygame.font.SysFont('Arial', size)

font18 = make_font(18)
font14 = make_font(14)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Camera not available!")
    exit()

print("Wukong v8 - Camera test started")

wukong_x = SCREEN_W // 2
wukong_y = SCREEN_H // 2
catches = 0
frame_count = 0
target_visible = False
target_x = 0
target_y = 0
running = True

while running:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = cv2.flip(frame, 1)
    frame_count += 1
    
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv, RED_LOWER1, RED_UPPER1)
    mask2 = cv2.inRange(hsv, RED_LOWER2, RED_UPPER2)
    mask = cv2.bitwise_or(mask1, mask2)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    target_visible = False
    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) > 500:
            x, y, w, h = cv2.boundingRect(largest)
            target_x = x + w // 2
            target_y = y + h // 2
            target_visible = True
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_r:
                wukong_x = SCREEN_W // 2
                wukong_y = SCREEN_H // 2
                catches = 0
    
    if target_visible:
        dx = target_x - wukong_x
        dy = target_y - wukong_y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > CATCH_DIST:
            wukong_x += int(dx / dist * WUKONG_SPEED)
            wukong_y += int(dy / dist * WUKONG_SPEED)
        else:
            catches += 1
    else:
        if random.random() < 0.1:
            wukong_x += random.randint(-5, 5)
            wukong_y += random.randint(-5, 5)
    
    wukong_x = max(20, min(SCREEN_W - 20, wukong_x))
    wukong_y = max(20, min(SCREEN_H - 20, wukong_y))
    
    # Render
    frame_small = cv2.resize(frame, (640, 480))
    frame_rgb = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
    frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
    screen.blit(frame_surface, (0, 0))
    
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 60))
    screen.blit(overlay, (0, 0))
    
    title = font18.render("Wukong v8 - Camera Vision", True, CYAN)
    screen.blit(title, (10, 10))
    
    status = "Target Found!" if target_visible else "Searching..."
    color = GREEN if target_visible else GRAY
    st = font18.render(status, True, color)
    screen.blit(st, (10, 40))
    
    data_text = "Frames: %d | Catches: %d" % (frame_count, catches)
    dt = font14.render(data_text, True, WHITE)
    screen.blit(dt, (10, 65))
    
    # Wukong
    pygame.draw.circle(screen, RED, (wukong_x, wukong_y), WUKONG_SIZE // 2)
    pygame.draw.circle(screen, (255, 130, 120), (wukong_x - 5, wukong_y - 5), 8)
    
    if target_visible:
        tx = int(target_x * 640 / frame.shape[1])
        ty = int(target_y * 480 / frame.shape[0])
        pygame.draw.circle(screen, GREEN, (tx, ty), 15, 3)
        pygame.draw.line(screen, GREEN, (tx-20, ty), (tx+20, ty), 2)
        pygame.draw.line(screen, GREEN, (tx, ty-20), (tx, ty+20), 2)
        pygame.draw.line(screen, YELLOW, (wukong_x, wukong_y), (tx, ty), 2)
    
    # Panel
    panel_x = SCREEN_W - 200
    pygame.draw.rect(screen, (25, 25, 40), (panel_x, 10, 190, SCREEN_H - 20), border_radius=10)
    
    iy = 25
    title2 = font14.render("Vision Info", True, CYAN)
    screen.blit(title2, (panel_x + 15, iy))
    iy += 30
    frame_text = "Frames: %d" % frame_count
    screen.blit(font14.render(frame_text, True, WHITE), (panel_x + 15, iy))
    iy += 22
    catch_text = "Catches: %d" % catches
    screen.blit(font14.render(catch_text, True, GREEN), (panel_x + 15, iy))
    iy += 30
    
    vision_label = font14.render("Vision:", True, GRAY)
    screen.blit(vision_label, (panel_x + 15, iy))
    iy += 22
    if target_visible:
        vis_text = "Red object detected"
    else:
        vis_text = "No target"
    vis_color = GREEN if target_visible else GRAY
    screen.blit(font14.render(vis_text, True, vis_color), (panel_x + 15, iy))
    iy += 25
    
    wukong_label = font14.render("Wukong:", True, GRAY)
    screen.blit(wukong_label, (panel_x + 15, iy))
    iy += 22
    pos_text = "Pos: (%d, %d)" % (wukong_x, wukong_y)
    screen.blit(font14.render(pos_text, True, WHITE), (panel_x + 15, iy))
    iy += 30
    
    tips_label = font14.render("Tips:", True, CYAN)
    screen.blit(tips_label, (panel_x + 15, iy))
    iy += 22
    tips = ["1. Show red object", "2. Move in camera", "3. Wukong follows"]
    for tip in tips:
        screen.blit(font14.render(tip, True, GRAY), (panel_x + 15, iy))
        iy += 18
    
    preview = cv2.resize(frame, (160, 120))
    preview_rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
    preview_surface = pygame.surfarray.make_surface(preview_rgb.swapaxes(0, 1))
    screen.blit(preview_surface, (panel_x + 15, SCREEN_H - 140))
    
    help_t = font14.render("R=Reset | ESC=Exit", True, GRAY)
    screen.blit(help_t, (panel_x + 15, SCREEN_H - 20))
    
    pygame.display.flip()
    clock.tick(FPS)

cap.release()
pygame.quit()
print("Wukong v8 finished - Frames: %d, Catches: %d" % (frame_count, catches))
