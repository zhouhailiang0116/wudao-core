# -*- coding: utf-8 -*-
"""

Axiom 2: Light - 光照公理


数学定义：
- 光照方向：direction = normalize(target - source)
- 衰减函数：attenuation(d) = 1 / (1 + k * d^2)
- 色温映射：temperature(K) → RGB（Tanner Helland 近似）
- 阴影长度：shadow_len = height / tan(angle)

核心概念：
- 光源位置与方向：决定高光和阴影方位
- 光照强度：控制明暗对比度（0~1）
- 色温：暖光(2700K) / 日光(5500K) / 冷光(7500K)
- 阴影：softness + direction + length
- 环境光：全局基础亮度，防死黑

"""



import sys as _sys
import os as _os
from pathlib import Path
from typing import Dict, Optional, Tuple
import math


class LightAxiom:
    """
    光照公理实现
    
    从场景描述（时间/天气/氛围）推算光源参数：
    - light_source: 光源位置 (x, y)
    - intensity:    光照强度 0~1
    - temperature:  色温（开尔文）
    - shadow:       阴影参数
    - ambient:      环境光
    """

    # ─── 色温预设（Tanner Helland RGB 近似）─────────────────────────
    COLOR_TEMPS = {
        "candle":    {"temp": 1800, "label": "烛光"},
        "warm":      {"temp": 2700, "label": "暖光（钨丝灯）"},
        "soft_warm": {"temp": 3500, "label": "柔暖（晨光）"},
        "neutral":   {"temp": 4500, "label": "中性白"},
        "daylight":  {"temp": 5500, "label": "日光（正午）"},
        "cloudy":    {"temp": 6500, "label": "阴天"},
        "cool":      {"temp": 7500, "label": "冷光（阴影）"},
        "overcast":  {"temp": 9000, "label": "阴天蓝"},
    }

    # ─── 天气到光照映射 ─────────────────────────────────────────────
    WEATHER_LIGHT = {
        "sunny":       {"intensity": 0.95, "ambient": 0.15, "shadow_soft": 0.2},
        "cloudy":      {"intensity": 0.65, "ambient": 0.35, "shadow_soft": 0.7},
        "overcast":    {"intensity": 0.45, "ambient": 0.45, "shadow_soft": 0.9},
        "rainy":       {"intensity": 0.35, "ambient": 0.40, "shadow_soft": 0.95},
        "snowy":       {"temp_override": 7000, "intensity": 0.80, "ambient": 0.50, "shadow_soft": 0.6},
        "foggy":       {"intensity": 0.50, "ambient": 0.50, "shadow_soft": 1.0},
        "golden_hour": {"intensity": 0.90, "ambient": 0.20, "shadow_soft": 0.3, "temp_override": 3200},
        "blue_hour":   {"intensity": 0.40, "ambient": 0.35, "shadow_soft": 0.5, "temp_override": 8500},
        "night":       {"intensity": 0.15, "ambient": 0.05, "shadow_soft": 0.8},
        "studio":      {"intensity": 0.85, "ambient": 0.25, "shadow_soft": 0.4},
    }

    # ─── 情绪到光照映射 ─────────────────────────────────────────────
    MOOD_LIGHT = {
        "warm":        {"temp_bias": -1500, "intensity_bias": 0.05},
        "cozy":        {"temp_bias": -2000, "intensity_bias": -0.15, "ambient_bias": 0.15},
        "dramatic":    {"intensity_bias": 0.10, "ambient_bias": -0.20, "shadow_soft_bias": -0.3},
        "fresh":       {"temp_bias": 500, "intensity_bias": 0.10, "ambient_bias": 0.10},
        "mysterious":  {"intensity_bias": -0.20, "ambient_bias": -0.15, "shadow_soft_bias": -0.2},
        "energetic":   {"intensity_bias": 0.15, "temp_bias": -500},
        "calm":        {"ambient_bias": 0.15, "shadow_soft_bias": 0.2},
        "professional":{"temp_bias": 200, "shadow_soft_bias": 0.1},
        "romantic":    {"temp_bias": -1800, "intensity_bias": -0.10, "ambient_bias": 0.10},
        "melancholic": {"temp_bias": 1000, "intensity_bias": -0.15, "ambient_bias": 0.05},
    }

    def __init__(self,
                 gpu_shader: Optional[str] = None,
                 fallback_method: str = 'auto'):
        self.name = 'light'
        self.gpu_shader = gpu_shader
        self.fallback_method = fallback_method

    # ════════════════════════════════════════════════════════════════
    #  接口实现
    # ════════════════════════════════════════════════════════════════

    def validate(self, data: dict) -> bool:
        """
        验证输入数据。
        
        最简约束：data 是 dict 即可。
        有 scene/canvas 时校验坐标范围。
        """
        if not isinstance(data, dict):
            return False

        # 如果提供了光源坐标，校验范围
        light = data.get("light_source", {})
        if isinstance(light, dict) and "x" in light and "y" in light:
            canvas = data.get("canvas", {"width": 800, "height": 600})
            if not (0 <= light["x"] <= canvas["width"] and 0 <= light["y"] <= canvas["height"]):
                return False

        return True

    def compute(self, data: dict, state: any) -> dict:
        """
        根据场景描述推算光照参数。
        
        输入字段（全部可选，有默认值）：
          scene:     dict  — {time, weather, location, ...}
          canvas:    dict  — {width, height}
          mood:      str   — 情绪关键词
          light_source: dict — {x, y} 手动指定光源位置（覆盖推算）
          target:    dict  — {x, y} 被照主体位置
        
        输出：
          light_source: {x, y}        — 光源位置
          target:       {x, y}        — 光照目标（主体中心）
          direction:    (dx, dy)      — 光照方向（归一化）
          intensity:    float          — 光照强度 0~1
          temperature:  int            — 色温（开尔文）
          rgb:          (r, g, b)      — 色温对应的 RGB
          ambient:      float          — 环境光强度 0~1
          shadow:       dict           — 阴影参数
        """
        canvas = data.get("canvas", {"width": 800, "height": 600})
        scene = data.get("scene", {})
        mood = data.get("mood", "")

        # ── 1. 推算光源位置 ─────────────────────────────────────
        light_pos = self._compute_light_position(scene, canvas, data)

        # ── 2. 推算光照方向 ─────────────────────────────────────
        target = data.get("target", {
            "x": canvas["width"] * 0.5,
            "y": canvas["height"] * 0.5,
        })
        direction = self._compute_direction(light_pos, target)

        # ── 3. 推算光照强度 ─────────────────────────────────────
        weather_cfg = self.WEATHER_LIGHT.get(scene.get("weather", "daylight"), {})
        intensity = self._clamp(weather_cfg.get("intensity", 0.75), 0, 1)

        # ── 4. 推算色温 ─────────────────────────────────────────
        base_temp = self._compute_temperature(scene)

        # ── 5. 环境光 ──────────────────────────────────────────
        ambient = self._clamp(weather_cfg.get("ambient", 0.20), 0, 1)

        # ── 6. 阴影参数 ────────────────────────────────────────
        shadow_soft = self._clamp(weather_cfg.get("shadow_soft", 0.5), 0, 1)

        # ── 7. 应用情绪偏移 ─────────────────────────────────────
        intensity, ambient, shadow_soft, base_temp = self._apply_mood(
            mood, intensity, ambient, shadow_soft, base_temp
        )

        # ── 8. 应用天气覆写 ─────────────────────────────────────
        base_temp = weather_cfg.get("temp_override", base_temp)

        # ── 9. 色温 → RGB ──────────────────────────────────────
        rgb = self._temperature_to_rgb(base_temp)

        return {
            "light_source": light_pos,
            "target": target,
            "direction": direction,
            "intensity": round(intensity, 3),
            "temperature": base_temp,
            "rgb": rgb,
            "ambient": round(ambient, 3),
            "shadow": {
                "softness": round(shadow_soft, 3),
                "direction_x": direction[0],
                "direction_y": direction[1],
                "length_factor": round(1.0 / max(0.1, intensity), 3),
            },
            "contrast": round(intensity - ambient, 3),
        }

    def render(self, result: dict) -> dict:
        """渲染输出：精简为 bridge 可用的格式。"""
        return {
            "status": "rendered",
            "boundary_type": "light",
            "light_source": result.get("light_source"),
            "target": result.get("target"),
            "direction": result.get("direction"),
            "intensity": result.get("intensity"),
            "temperature": result.get("temperature"),
            "rgb": result.get("rgb"),
            "ambient": result.get("ambient"),
            "shadow": result.get("shadow"),
            "contrast": result.get("contrast"),
            "valid": True,
        }

    def info(self) -> dict:
        return {
            "name": self.name,
            "gpu_shader": self.gpu_shader,
            "fallback_method": self.fallback_method,
        }

    # ════════════════════════════════════════════════════════════════
    #  内部计算
    # ════════════════════════════════════════════════════════════════

    def _compute_light_position(self, scene: dict, canvas: dict, data: dict) -> dict:
        """
        推算光源位置。
        
        规则：
          - 手动指定 → 直接用
          - 时间推算 → 基于太阳轨迹的简化模型
          - 默认 → 左上 45 度
        """
        # 手动指定优先
        manual = data.get("light_source")
        if isinstance(manual, dict) and "x" in manual and "y" in manual:
            return {"x": manual["x"], "y": manual["y"]}

        w = canvas["width"]
        h = canvas["height"]
        time_str = scene.get("time", "noon")
        location = scene.get("location", "outdoor")

        # 简化太阳轨迹模型
        # sunrise(6) → 东侧低 → noon(12) → 顶部 → sunset(18) → 西侧低
        hour = self._parse_time(time_str)

        if location == "outdoor":
            # 水平轨迹：6h=左, 12h=中, 18h=右
            t_norm = (hour - 6) / 12.0  # 0→1 over 6am-6pm
            t_norm = max(0, min(1, t_norm))

            x = w * 0.15 + w * 0.70 * t_norm  # 左15% → 右85%

            # 垂直轨迹：抛物线，正午最高
            y_peak = h * 0.05  # 最高点
            y_horizon = h * 0.85
            y = y_horizon - (y_horizon - y_peak) * math.sin(t_norm * math.pi)

            # 夜间 → 禁止（无直射光）
            if hour < 5.5 or hour > 18.5:
                return {"x": w * 0.5, "y": h * 0.02}

            return {"x": round(x, 1), "y": round(y, 1)}
        else:
            # 室内 → 固定光源位置（偏上方，模拟顶灯/窗户光）
            window_side = scene.get("window", "left")
            x = w * 0.15 if window_side == "left" else (w * 0.85 if window_side == "right" else w * 0.5)
            y = h * 0.15
            return {"x": round(x, 1), "y": round(y, 1)}

    def _compute_temperature(self, scene: dict) -> int:
        """
        从场景推算色温。
        
        规则：
          - 天气 → 基准色温
          - 时间微调（早晚暖，正午中性）
        """
        weather = scene.get("weather", "daylight")

        # 天气基准
        weather_temp_map = {
            "sunny": 5200, "cloudy": 6500, "overcast": 7000,
            "rainy": 7500, "snowy": 7000, "foggy": 8000,
            "golden_hour": 3200, "blue_hour": 8500,
            "night": 4000, "studio": 5500,
        }
        temp = weather_temp_map.get(weather, 5500)

        # 时间微调
        hour = self._parse_time(scene.get("time", "noon"))
        if 5 < hour < 9:
            temp -= 800   # 晨光偏暖
        elif 17 < hour < 20:
            temp -= 1200  # 晚霞偏暖
        elif 12 < hour < 14:
            temp += 200   # 正午偏中性

        return temp

    def _compute_direction(self, light: dict, target: dict) -> Tuple[float, float]:
        """计算光照方向（归一化向量：从光源指向目标）。"""
        dx = target["x"] - light["x"]
        dy = target["y"] - light["y"]
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 1e-6:
            return (0.0, 1.0)
        return (round(dx / dist, 4), round(dy / dist, 4))

    def _apply_mood(self, mood: str, intensity: float, ambient: float,
                    shadow_soft: float, temperature: int) -> Tuple[float, float, float, int]:
        """应用情绪偏移。"""
        if not mood:
            return intensity, ambient, shadow_soft, temperature

        mood = mood.lower()
        cfg = self.MOOD_LIGHT.get(mood, {})

        intensity = self._clamp(intensity + cfg.get("intensity_bias", 0), 0, 1)
        ambient = self._clamp(ambient + cfg.get("ambient_bias", 0), 0, 1)
        shadow_soft = self._clamp(shadow_soft + cfg.get("shadow_soft_bias", 0), 0, 1)
        temperature = max(1000, min(15000, temperature + cfg.get("temp_bias", 0)))

        return intensity, ambient, shadow_soft, temperature

    # ════════════════════════════════════════════════════════════════
    #  色温转换（Tanner Helland 近似算法）
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def _temperature_to_rgb(temp: int) -> Tuple[int, int, int]:
        """
        色温(K) → RGB。
        
        基于 Tanner Helland 的简化算法，范围 1000~40000K。
        """
        t = temp / 100.0

        # Red
        if t <= 66:
            r = 255
        else:
            r = 329.698727446 * ((t - 60) ** -0.1332047592)
            r = max(0, min(255, r))

        # Green
        if t <= 66:
            g = 99.4708025861 * math.log(t) - 161.1195681661
        else:
            g = 288.1221695283 * ((t - 60) ** -0.0755148492)
        g = max(0, min(255, g))

        # Blue
        if t >= 66:
            b = 255
        elif t <= 19:
            b = 0
        else:
            b = 138.5177312231 * math.log(t - 10) - 305.0447927307
            b = max(0, min(255, b))

        return (int(round(r)), int(round(g)), int(round(b)))

    # ════════════════════════════════════════════════════════════════
    #  工具函数
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def _clamp(value: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, value))

    @staticmethod
    def _parse_time(time_str: str) -> float:
        """
        解析时间字符串为小时数（24h）。
        
        支持: "7:30" / "07:30" / "7.5" / "morning" / "noon" / "afternoon" / "evening" / "night"
        """
        if not time_str:
            return 12.0

        # 关键词映射
        keyword_map = {
            "dawn": 5.5, "sunrise": 6.0, "early_morning": 7.0,
            "morning": 8.0, "late_morning": 10.0, "noon": 12.0,
            "afternoon": 14.0, "late_afternoon": 16.0,
            "golden_hour": 17.5, "sunset": 18.0, "evening": 19.0,
            "dusk": 20.0, "twilight": 21.0, "night": 22.0,
            "midnight": 0.0,
        }

        lower = time_str.lower().strip()
        if lower in keyword_map:
            return keyword_map[lower]

        # HH:MM 格式
        if ":" in time_str:
            try:
                parts = time_str.split(":")
                return int(parts[0]) + int(parts[1]) / 60.0
            except (ValueError, IndexError):
                pass

        # 纯数字
        try:
            val = float(time_str)
            if 0 <= val <= 24:
                return val
        except ValueError:
            pass

        return 12.0  # 默认正午

    def execute(self, task: any, state: any) -> any:
        """统一执行入口"""
        data = task.data if hasattr(task, 'data') else task
        if not self.validate(data):
            raise ValueError(f"[{self.name}] validate failed")
        result = self.compute(data, state)
        return self.render(result)

    def compute_simple(self, data: dict) -> dict:
        """简化计算（降级用）"""
        return {"status": "simple", "light": data.get("scene", {})}

    def score_from_features(self, features: dict) -> dict:
        """
        逆向：图像特征 → 光照分数（ quadrant 四大象限分析）
        
        调用 axiom_verifier.verify_light_style() ，
        使用九宫格象限分析光源位置，检测 rembrandt/butterfly/split/loop 四种光照风格。
        """
        arr = features.get('arr')
        if arr is None:
            return {'score': 0.5, 'method': 'light_fallback', 'details': {}}
        # Lazy import
        _path = str(Path(__file__).resolve().parent.parent.parent / "wukong" / "wukong_eye" / "core")
        if _path not in _sys.path:
            _sys.path.insert(0, _path)
        from axiom_verifier import verify_light_style
        
        result = verify_light_style(arr)
        return {
            'score': float(result.get('score', 0.5)),
            'method': 'verify_light_style',
            'lighting_style': result.get('lighting_style', 'unknown'),
            'quadrant_means': result.get('quadrant_means', []),
            'source': 'wudao_core_light_v2'
        }

    def render_cpu(self, result: dict) -> dict:
        """CPU 渲染（降级用）"""
        return result
