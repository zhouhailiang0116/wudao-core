# -*- coding: utf-8 -*-
"""
render_painter.py — 悟空层渲染器（完整学院派流程）
===================================================

重写版（2026-05-07）：照着 examples/egg.py 的完整学院派流程做。
包括：球面光影 + 地面投影 + 颗粒纹理 + 笔身后处理。

用法：
    python3 render_painter.py '{"form_rx":80,"form_ry":100,"light_dx":-0.5,...}'
    python3 render_painter.py --params /path/to/params.json --output /path/to/out.png
"""

import sys
import os
import json
import math
import argparse

# ─── 路径（必须先切目录，再 import）─────────────────────────────────
_WUKONG_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "wukong", "wukong_painter")
os.chdir(_WUKONG_PY)
sys.path.insert(0, _WUKONG_PY)

import numpy as np
from PIL import Image

from core.form import Egg, rotate_normal
from core.light import Light, FiveTones, Shadow
from core.texture import GrainTexture
from core.brush import BrushStyle
from utils.color import Color


def render(params: dict) -> "Image.Image":
    """
    完整学院派渲染流程，照着 examples/egg.py 写：
      1. 形体遮罩 + 法向量
      2. 旋转法向量
      3. 光照计算（Lambert + 五调子）
      4. 颗粒纹理
      5. 地面投影
      6. 笔触后处理
    """
    # ── 参数解析 ────────────────────────────────────────────────
    size       = tuple(params.get("size", [512, 512]))
    form_rx    = params.get("form_rx", 60)
    form_ry    = params.get("form_ry", 80)
    angle_deg  = params.get("angle_deg", 30)           # 新增：旋转角
    light_dx   = params.get("light_dx", -0.5)
    light_dy   = params.get("light_dy", -0.7)
    light_dz   = params.get("light_dz", 0.5)
    base_color = tuple(params.get("base_color", [255, 220, 180]))
    bg_color   = tuple(params.get("bg_color",   [40, 44, 52]))
    shadow_col = tuple(params.get("shadow_color", [20, 15, 10]))
    grain_intensity = params.get("grain_intensity", 0.10)
    brush_style     = params.get("brush_style", "academic")

    # ── 1. 初始化画布 ──────────────────────────────────────────
    img = Image.new('RGB', size, bg_color)
    pixels = np.zeros((size[1], size[0], 3), dtype=np.float32)

    # ── 2. 形体 ────────────────────────────────────────────────
    cx, cy = size[0] // 2, size[1] // 2 - 10
    egg = Egg(cx, cy, form_rx, form_ry)

    # ── 3. 坐标网格（相对坐标）─────────────────────────────────
    h, w = size[1], size[0]
    y_idx, x_idx = np.mgrid[:h, :w]
    x_rel = (x_idx - cx).astype(np.float32)
    y_rel = (y_idx - cy).astype(np.float32)

    # ── 4. 形体遮罩 ────────────────────────────────────────────
    mask = egg.get_mask(x_rel, y_rel)

    # ── 5. 法向量 + 旋转 ───────────────────────────────────────
    nx, ny, nz = egg.get_normal(x_rel, y_rel)
    nx_r, ny_r = rotate_normal(nx, ny, angle_deg)

    # ── 6. 光照 ────────────────────────────────────────────────
    light = Light(dx=light_dx, dy=light_dy, dz=light_dz)
    diffuse = light.get_diffuse(nx_r, ny_r, nz)

    # ── 7. 五调子亮度 ──────────────────────────────────────────
    brightness = FiveTones.get_brightness(diffuse)

    # ── 8. 颗粒纹理 ────────────────────────────────────────────
    texture = GrainTexture(intensity=grain_intensity)
    r_ch, g_ch, b_ch = texture.apply(
        base_color=base_color,
        brightness=brightness,
        diffuse=diffuse,
        mask=mask.astype(np.float32)
    )

    # ── 9. 合成到像素 ──────────────────────────────────────────
    pixels[:, :, 0] = np.clip(r_ch, 0, 255)
    pixels[:, :, 1] = np.clip(g_ch, 0, 255)
    pixels[:, :, 2] = np.clip(b_ch, 0, 255)

    # ── 10. 地面投影（独立叠加，不是光影的一部分）──────────────
    shadow_mask = Shadow.cast_shadow(
        size, cx, cy, form_rx, form_ry,
        offset_x=15, offset_y=0.87, blur_sigma=7
    )
    shadow_r, shadow_g, shadow_b = shadow_col
    for c_idx, shadow_val in enumerate([shadow_r, shadow_g, shadow_b]):
        pixels[:, :, c_idx] = (
            pixels[:, :, c_idx] * (1 - shadow_mask * 0.6)
            + shadow_val * shadow_mask
        )

    # ── 11. 转 PIL ─────────────────────────────────────────────
    img = Image.fromarray(pixels.astype(np.uint8)).convert('RGB')

    # ── 12. 学院派笔触后处理 ───────────────────────────────────
    processor = BrushStyle.academic()
    img = processor.process(img)

    return img


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="悟空层 painter 渲染器（完整学院派）")
    parser.add_argument("params", nargs="?", help="JSON 参数字符串或 @filepath")
    parser.add_argument("--params", dest="params_file", help="JSON 文件路径")
    parser.add_argument("--output", "-o", dest="output", default=None, help="输出图像路径")
    args = parser.parse_args()

    # 读取参数
    if args.params_file:
        with open(args.params_file, "r", encoding="utf-8") as f:
            params = json.load(f)
    elif args.params:
        p = args.params.strip()
        if p.startswith("@"):
            with open(p[1:], "r", encoding="utf-8") as f:
                params = json.load(f)
        else:
            params = json.loads(p)
    else:
        print("Error: 需要提供参数（JSON 字符串或 --params 文件）")
        sys.exit(1)

    output_path = args.output or params.get("output")

    img = render(params)

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        img.save(output_path)
        print(f"OK: {output_path}")
    else:
        img.save(sys.stdout.buffer, format="PNG")
