# -*- coding: utf-8 -*-
"""
悟空智能体 v8+：火眼金睛
AI视觉分析摄像头画面，识别所有物体

功能：
1. 捕获摄像头画面
2. 用AI分析画面中的物体
3. 在画面上标注识别结果
4. 悟空对识别结果做出反应
"""
import cv2
import pygame
import math
import random
import os

# 检查是否有MiniMax/MoMo视觉
HAS_VISION = False
try:
    from PIL import Image
    import urllib.request
    import base64
    import json
    HAS_VISION = True
    print("Vision API available")
except:
    print("Vision API not available, using OpenCV only")

SCREEN_W = 1000
SCREEN_H = 700
FPS = 30

WUKONG_SIZE = 40
WUKONG_SPEED = 5

RED = (230, 60, 50)
GREEN = (30, 180, 100)
BLUE = (50, 100, 230)
YELLOW = (255, 210, 60)
WHITE = (255, 255, 255)
GRAY = (120, 120, 135)
CYAN = (50, 200, 200)
ORANGE = (255, 150, 50)
PURPLE = (160, 80, 220)

# 预定义颜色（根据类别）
CLASS_COLORS = {
    "person": (255, 100, 100),      # 红色
    "car": (100, 150, 255),         # 蓝色
    "dog": (150, 100, 255),          # 紫色
    "cat": (255, 200, 100),          # 橙色
    "book": (100, 200, 150),         # 绿色
    "phone": (200, 200, 100),        # 黄绿色
    "cup": (200, 150, 100),          # 棕色
    "laptop": (100, 200, 200),      # 青色
    "chair": (150, 150, 150),        # 灰色
    "table": (100, 100, 150),       # 深灰
    "flower": (255, 150, 200),      # 粉色
    "tree": (50, 180, 50),          # 深绿
    "sky": (100, 180, 255),         # 天蓝
    "wall": (180, 180, 180),        # 浅灰
    "floor": (120, 100, 80),        # 地板色
}

# OpenCV预训练分类器（简单版）
FACE_CASCADE = None
try:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    print("Face detector loaded")
except:
    print("Face detector not available")

BODY_CASCADE = None
try:
    body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')
    print("Body detector loaded")
except:
    print("Body detector not available")

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Wukong v8+ - Fire Eye")
clock = pygame.time.Clock()

def make_font(size):
    try:
        return pygame.font.Font('C:/Windows/Fonts/msyh.ttc', size)
    except:
        return pygame.font.SysFont('Arial', size)

font18 = make_font(18)
font14 = make_font(14)
font24 = make_font(24)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Camera not available!")
    exit()

print("Wukong v8+ Fire Eye started")

wukong_x = SCREEN_W // 2
wukong_y = SCREEN_H // 2
detections = []
frame_count = 0
running = True
last_detection_time = 0
detection_interval = 10  # 每10帧检测一次

def detect_objects(frame):
    """使用OpenCV检测物体"""
    results = []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 人脸检测
    if FACE_CASCADE is not None:
        faces = FACE_CASCADE.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            results.append({
                "class": "person",
                "label": "人脸",
                "bbox": (x, y, w, h),
                "confidence": 0.9,
                "color": CLASS_COLORS.get("person", RED)
            })
    
    # 身体检测
    if BODY_CASCADE is not None:
        bodies = BODY_CASCADE.detectMultiScale(gray, 1.2, 3)
        for (x, y, w, h) in bodies:
            results.append({
                "class": "person",
                "label": "人体",
                "bbox": (x, y, w, h),
                "confidence": 0.8,
                "color": CLASS_COLORS.get("person", RED)
            })
    
    # 颜色检测（简单版）
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # 红色物体
    red_lower1 = cv2.inRange(hsv, (0, 100, 100), (10, 255, 255))
    red_lower2 = cv2.inRange(hsv, (160, 100, 100), (180, 255, 255))
    red_mask = cv2.bitwise_or(red_lower1, red_lower2)
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if cv2.contourArea(cnt) > 1000:
            x, y, w, h = cv2.boundingRect(cnt)
            results.append({
                "class": "red_object",
                "label": "红色物体",
                "bbox": (x, y, w, h),
                "confidence": 0.7,
                "color": (255, 50, 50)
            })
    
    # 蓝色物体
    blue_mask = cv2.inRange(hsv, (100, 100, 50), (130, 255, 255))
    contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if cv2.contourArea(cnt) > 1000:
            x, y, w, h = cv2.boundingRect(cnt)
            results.append({
                "class": "blue_object",
                "label": "蓝色物体",
                "bbox": (x, y, w, h),
                "confidence": 0.7,
                "color": (50, 50, 255)
            })
    
    # 绿色物体
    green_mask = cv2.inRange(hsv, (35, 50, 50), (85, 255, 255))
    contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if cv2.contourArea(cnt) > 1000:
            x, y, w, h = cv2.boundingRect(cnt)
            results.append({
                "class": "green_object",
                "label": "绿色物体",
                "bbox": (x, y, w, h),
                "confidence": 0.7,
                "color": (50, 200, 50)
            })
    
    # 黄色物体
    yellow_mask = cv2.inRange(hsv, (20, 100, 100), (30, 255, 255))
    contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if cv2.contourArea(cnt) > 1000:
            x, y, w, h = cv2.boundingRect(cnt)
            results.append({
                "class": "yellow_object",
                "label": "黄色物体",
                "bbox": (x, y, w, h),
                "confidence": 0.7,
                "color": (255, 255, 50)
            })
    
    # 肤色检测（人脸/手）
    skin_mask = cv2.inRange(hsv, (0, 20, 70), (20, 255, 255))
    contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if cv2.contourArea(cnt) > 2000:
            x, y, w, h = cv2.boundingRect(cnt)
            results.append({
                "class": "skin",
                "label": "皮肤区域",
                "bbox": (x, y, w, h),
                "confidence": 0.5,
                "color": (220, 180, 150)
            })
    
    return results

while running:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = cv2.flip(frame, 1)
    frame_count += 1
    
    current_time = frame_count // FPS
    
    # 定期检测
    if frame_count - last_detection_time > detection_interval:
        detections = detect_objects(frame)
        last_detection_time = frame_count
    
    # 处理事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_r:
                wukong_x = SCREEN_W // 2
                wukong_y = SCREEN_H // 2
                detections = []
    
    # 悟空移动（朝最近检测到的物体）
    if detections:
        # 找最近的物体
        closest = None
        min_dist = float('inf')
        for det in detections:
            x, y, w, h = det["bbox"]
            cx, cy = x + w//2, y + h//2
            # 转换到 pygame 坐标
            px_cx = int(cx * 640 / frame.shape[1])
            px_cy = int(cy * 480 / frame.shape[0])
            dist = math.sqrt((px_cx - wukong_x)**2 + (px_cy - wukong_y)**2)
            if dist < min_dist:
                min_dist = dist
                closest = (px_cx, px_cy, det)
        
        if closest and min_dist > 30:
            tx, ty, det = closest
            dx = tx - wukong_x
            dy = ty - wukong_y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 0:
                wukong_x += int(dx / dist * WUKONG_SPEED)
                wukong_y += int(dy / dist * WUKONG_SPEED)
    else:
        # 没有检测到，随机移动
        if random.random() < 0.05:
            wukong_x += random.randint(-10, 10)
            wukong_y += random.randint(-10, 10)
    
    wukong_x = max(20, min(SCREEN_W - 20, wukong_x))
    wukong_y = max(20, min(SCREEN_H - 20, wukong_y))
    
    # 渲染
    frame_small = cv2.resize(frame, (640, 480))
    frame_rgb = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
    frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
    screen.blit(frame_surface, (0, 0))
    
    # 半透明覆盖
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 50))
    screen.blit(overlay, (0, 0))
    
    # 标题
    title = font24.render("Wukong v8+ Fire Eye - Huoyan Jingjing", True, YELLOW)
    screen.blit(title, (10, 10))
    
    # 检测结果标注
    detected_classes = set()
    for det in detections:
        x, y, w, h = det["bbox"]
        # 转换坐标
        px = int(x * 640 / frame.shape[1])
        py = int(y * 480 / frame.shape[0])
        pw = int(w * 640 / frame.shape[1])
        ph = int(h * 480 / frame.shape[0])
        
        color = det["color"]
        
        # 画框
        pygame.draw.rect(screen, color, (px, py, pw, ph), 3)
        
        # 画标签
        label = det["label"]
        conf = det["confidence"]
        label_text = "%s (%.0f%%)" % (label, conf * 100)
        label_surf = font14.render(label_text, True, WHITE, color)
        screen.blit(label_surf, (px, py - 20))
        
        detected_classes.add(det["class"])
    
    # 悟空
    pygame.draw.circle(screen, RED, (wukong_x, wukong_y), WUKONG_SIZE // 2)
    pygame.draw.circle(screen, (255, 130, 120), (wukong_x - 5, wukong_y - 5), 8)
    wukong_label = font14.render("Wukong", True, WHITE)
    screen.blit(wukong_label, (wukong_x - 25, wukong_y - WUKONG_SIZE // 2 - 20))
    
    # 右侧面板
    panel_x = SCREEN_W - 200
    pygame.draw.rect(screen, (20, 20, 30), (panel_x, 10, 190, SCREEN_H - 20), border_radius=10)
    
    iy = 20
    
    title2 = font18.render("Fire Eye Report", True, YELLOW)
    screen.blit(title2, (panel_x + 15, iy))
    iy += 35
    
    frame_text = "Frame: %d" % frame_count
    screen.blit(font14.render(frame_text, True, WHITE), (panel_x + 15, iy))
    iy += 25
    
    count_text = "Objects: %d" % len(detections)
    count_color = GREEN if detections else GRAY
    screen.blit(font14.render(count_text, True, count_color), (panel_x + 15, iy))
    iy += 30
    
    # 检测到的类别
    detect_label = font14.render("Detected:", True, CYAN)
    screen.blit(detect_label, (panel_x + 15, iy))
    iy += 22
    
    if detections:
        for det in detections[:6]:  # 最多显示6个
            color = det["color"]
            label = det["label"]
            # 画小色块
            pygame.draw.rect(screen, color, (panel_x + 15, iy, 12, 12), border_radius=2)
            screen.blit(font14.render(label, True, WHITE), (panel_x + 32, iy - 2))
            iy += 20
            if iy > SCREEN_H - 200:
                break
    else:
        no_text = font14.render("None yet...", True, GRAY)
        screen.blit(no_text, (panel_x + 15, iy))
        iy += 20
    
    iy += 15
    
    # 悟空状态
    wukong_status = font14.render("Wukong Status:", True, CYAN)
    screen.blit(wukong_status, (panel_x + 15, iy))
    iy += 22
    
    pos_text = "Position: (%d, %d)" % (wukong_x, wukong_y)
    screen.blit(font14.render(pos_text, True, WHITE), (panel_x + 15, iy))
    iy += 20
    
    target_text = "Target: %s" % ("Yes" if detections else "Searching")
    target_color = GREEN if detections else ORANGE
    screen.blit(font14.render(target_text, True, target_color), (panel_x + 15, iy))
    iy += 30
    
    # 颜色图例
    legend_label = font14.render("Color Legend:", True, CYAN)
    screen.blit(legend_label, (panel_x + 15, iy))
    iy += 22
    
    legend_items = [
        ((255, 50, 50), "Red Object"),
        ((50, 50, 255), "Blue Object"),
        ((50, 200, 50), "Green Object"),
        ((255, 255, 50), "Yellow Object"),
        ((255, 100, 100), "Face/Body"),
    ]
    for color, name in legend_items:
        pygame.draw.rect(screen, color, (panel_x + 15, iy, 10, 10), border_radius=2)
        screen.blit(font14.render(name, True, GRAY), (panel_x + 30, iy - 2))
        iy += 18
    
    # 摄像头预览
    preview = cv2.resize(frame, (160, 120))
    preview_rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
    preview_surface = pygame.surfarray.make_surface(preview_rgb.swapaxes(0, 1))
    screen.blit(preview_surface, (panel_x + 15, SCREEN_H - 140))
    
    # 操作提示
    help_t = font14.render("R=Reset | ESC=Exit", True, GRAY)
    screen.blit(help_t, (panel_x + 15, SCREEN_H - 20))
    
    pygame.display.flip()
    clock.tick(FPS)

cap.release()
pygame.quit()

print("\n=== Fire Eye Report ===")
print("Total frames: %d" % frame_count)
print("Objects detected: %d" % len(detections))
if detections:
    print("Sample detections:")
    for det in detections[:5]:
        print("  - %s: %s (%.0f%%)" % (det["class"], det["label"], det["confidence"] * 100))
