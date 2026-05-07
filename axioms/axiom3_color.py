# -*- coding: utf-8 -*-
"""

Axiom 3: Color - 色彩和谐公理


数学定义：
- 色相和谐：H_i ∈ HarmonySet(H_primary, type)
- 比例约束：ratio_primary ∈ [0.40, 0.75], ratio_secondary ∈ [0.20, 0.35]
- 对比度：contrast(primary, bg) >= 3.0

核心概念：
- 情绪→色相映射（passion→红/橙，calm→绿/蓝...）
- 配色方案类型（互补/三色/分裂互补/类似）
- 颜色角色分配（primary/secondary/accent/background/text）

"""



from typing import Dict, List, Optional, Tuple
import math
import colorsys
import sys as _sys
from pathlib import Path

# wukong_eye/core 动态路径
_WK = Path(__file__).resolve().parent.parent.parent / "wukong"
_WK_EYE = str(_WK / "wukong_eye" / "core")
if _WK_EYE not in _sys.path:
    _sys.path.insert(0, _WK_EYE)
try:
    from axiom_verifier import verify_color as _verify_color_fn
    _HAS_VERIFY_COLOR = True
except ImportError:
    _HAS_VERIFY_COLOR = False


class ColorAxiom:
    """
    色彩和谐公理实现
    
    从情绪/风格推算配色方案：
    - palette: 调色板（主色/辅色/强调色/背景/文字）
    - harmony_type: 配色类型
    - ratios: 颜色比例
    """

    # ════════════════════════════════════════════════════════════════
    #  情绪→色相映射（复用 lesson4_color_mood.py）
    # ════════════════════════════════════════════════════════════════

    MOOD_HUE_RANGES = {
        'passion':      [(0, 30), (330, 360)],      # 红/橙
        'warm_energy':  [(30, 90)],                 # 橙/黄
        'calm':         [(90, 180)],                # 绿/青
        'cool':         [(180, 270)],               # 蓝/紫
        'neutral':      [(0, 360)],                 # 全色相
        'dramatic':     [(0, 30), (330, 360)],      # 强红（高饱和）
        'peaceful':     [(90, 150)],                # 柔和绿
        'mysterious':   [(240, 300)],               # 深紫/蓝
        'energetic':    [(0, 60)],                  # 暖色
        'melancholic':  [(200, 260)],               # 蓝紫
    }

    # 情绪→配色类型默认值
    MOOD_HARMONY_DEFAULTS = {
        'passion':      'complementary',
        'warm_energy':  'split_complementary',
        'calm':         'analogous',
        'cool':         'analogous',
        'dramatic':     'complementary',
        'peaceful':     'analogous',
        'mysterious':   'split_complementary',
        'energetic':    'triadic',
        'melancholic':  'analogous',
        'neutral':      'triadic',
    }

    # 情绪→饱和度/明度调整
    MOOD_SATURATION = {
        'passion':      (0.75, 0.85),   # (sat_mult, val_mult)
        'warm_energy':  (0.80, 0.90),
        'calm':         (0.50, 0.70),
        'cool':         (0.55, 0.75),
        'dramatic':     (0.90, 0.70),   # 高饱和，低明度
        'peaceful':     (0.40, 0.80),   # 低饱和
        'mysterious':   (0.60, 0.50),   # 低明度
        'energetic':    (0.85, 0.90),
        'melancholic':  (0.45, 0.60),
        'neutral':      (0.50, 0.75),
    }

    # ════════════════════════════════════════════════════════════════
    #  配色方案类型
    # ════════════════════════════════════════════════════════════════

    HARMONY_TYPES = {
        'complementary': {
            'desc': '互补色（强对比）',
            'offsets': [0, 180],  # 主色 ± 180°
        },
        'triadic': {
            'desc': '三色（平衡）',
            'offsets': [0, 120, 240],  # 主色 ± 120°
        },
        'split_complementary': {
            'desc': '分裂互补（张力+和谐）',
            'offsets': [0, 150, 210],  # 主色 + 互补两侧
        },
        'analogous': {
            'desc': '类似色（统一）',
            'offsets': [0, 30, 330],  # 主色 ± 30°
        },
        'tetradic': {
            'desc': '四色（复杂）',
            'offsets': [0, 90, 180, 270],  # 主色 ± 90°
        },
    }

    # ════════════════════════════════════════════════════════════════
    #  颜色角色与比例
    # ════════════════════════════════════════════════════════════════

    COLOR_ROLES = ['primary', 'secondary', 'accent', 'background', 'text']

    # 默认比例（primary 50%, secondary 30%, accent 10%）
    DEFAULT_RATIOS = {
        'primary':   0.50,
        'secondary': 0.30,
        'accent':    0.10,
        'background': 1.00,  # 背景覆盖全画布
        'text':      1.00,   # 文字独立
    }

    def __init__(self,
                 gpu_shader: Optional[str] = None,
                 fallback_method: str = 'auto'):
        self.name = 'color'
        self.gpu_shader = gpu_shader
        self.fallback_method = fallback_method

    # ════════════════════════════════════════════════════════════════
    #  接口实现
    # ════════════════════════════════════════════════════════════════

    def validate(self, data: dict) -> bool:
        """
        验证输入数据。
        
        最简约束：data 是 dict。
        """
        if not isinstance(data, dict):
            return False
        return True

    def compute(self, data: dict, state: any) -> dict:
        """
        推算配色方案。
        
        输入字段（全部可选）：
          mood:          str   — 情绪关键词（passion/calm/dramatic...）
          style:         str   — 风格（realistic/stylized/dramatic）
          base_color:    tuple — 主体基色 RGB（可选，覆盖自动推断）
          harmony_type:  str   — 配色类型（可选，覆盖 mood 默认）
          palette_size:  int   — 调色板大小（默认 5）
        
        输出：
          palette:       list[dict] — 调色板
          harmony_type:  str        — 配色类型
          mood:          str        — 情绪
          primary_hue:   float      — 主色相（0-360）
          contrast:      float      — 主色vs背景对比度
        """
        # ── 1. 确定情绪 ─────────────────────────────────────
        mood = data.get('mood', 'neutral')
        style = data.get('style', 'realistic')

        # ── 2. 确定主色相 ───────────────────────────────────
        base_color = data.get('base_color')
        if base_color:
            # 用户提供基色 → 提取色相
            primary_hue = self._rgb_to_hue(*base_color)
        else:
            # 从情绪推断
            primary_hue = self._mood_to_hue(mood)

        # ── 3. 确定配色类型 ─────────────────────────────────
        harmony_type = data.get('harmony_type')
        if not harmony_type:
            harmony_type = self.MOOD_HARMONY_DEFAULTS.get(mood, 'triadic')

        # ── 4. 生成配色方案 ─────────────────────────────────
        palette = self._generate_palette(
            primary_hue, harmony_type, mood, style
        )

        # ── 5. 计算对比度 ───────────────────────────────────
        primary_rgb = palette[0]['rgb']
        bg_rgb = palette[3]['rgb']
        contrast = self._contrast_ratio(primary_rgb, bg_rgb)

        # ── 6. 验证比例约束 ─────────────────────────────────
        ratios_valid = self._validate_ratios(palette)

        return {
            'palette': palette,
            'harmony_type': harmony_type,
            'harmony_desc': self.HARMONY_TYPES.get(harmony_type, {}).get('desc', ''),
            'mood': mood,
            'style': style,
            'primary_hue': round(primary_hue, 1),
            'contrast': round(contrast, 2),
            'ratios_valid': ratios_valid,
            'palette_size': len(palette),
        }

    def render(self, result: dict) -> dict:
        """渲染输出：精简格式。"""
        return {
            'status': 'rendered',
            'boundary_type': 'color',
            'palette': result.get('palette'),
            'harmony_type': result.get('harmony_type'),
            'mood': result.get('mood'),
            'primary_hue': result.get('primary_hue'),
            'contrast': result.get('contrast'),
            'valid': result.get('ratios_valid', True),
        }

    def info(self) -> dict:
        return {
            'name': self.name,
            'gpu_shader': self.gpu_shader,
            'fallback_method': self.fallback_method,
        }

    # ════════════════════════════════════════════════════════════════
    #  内部计算
    # ════════════════════════════════════════════════════════════════

    def _mood_to_hue(self, mood: str) -> float:
        """从情绪推断主色相。"""
        ranges = self.MOOD_HUE_RANGES.get(mood.lower(), [(0, 360)])
        # 取第一个范围的中间值
        lo, hi = ranges[0]
        return (lo + hi) / 2

    def _generate_palette(self, primary_hue: float, harmony_type: str,
                          mood: str, style: str) -> List[dict]:
        """
        生成配色方案。
        
        返回：[
          {role: 'primary', rgb: (r,g,b), ratio: 0.50},
          {role: 'secondary', rgb: (r,g,b), ratio: 0.30},
          {role: 'accent', rgb: (r,g,b), ratio: 0.10},
          {role: 'background', rgb: (r,g,b), ratio: 1.00},
          {role: 'text', rgb: (r,g,b), ratio: 1.00},
        ]
        """
        # 配色偏移
        harmony_cfg = self.HARMONY_TYPES.get(harmony_type, self.HARMONY_TYPES['triadic'])
        offsets = harmony_cfg['offsets']

        # 情绪→饱和度/明度调整
        sat_mult, val_mult = self.MOOD_SATURATION.get(mood, (0.60, 0.75))

        # 生成颜色
        colors = []
        for i, offset in enumerate(offsets[:3]):  # 最多 3 色
            hue = (primary_hue + offset) % 360
            sat = 0.70 * sat_mult
            val = 0.80 * val_mult

            # 风格调整
            if style == 'dramatic':
                sat = min(1.0, sat * 1.2)
                val = val * 0.85
            elif style == 'stylized':
                sat = min(1.0, sat * 1.1)

            rgb = self._hsv_to_rgb(hue, sat, val)
            colors.append(rgb)

        # 补充背景色和文字色
        # 背景：低饱和、低明度
        bg_hue = (primary_hue + 180) % 360  # 互补色方向
        bg_rgb = self._hsv_to_rgb(bg_hue, 0.08, 0.12)

        # 文字：与背景对比
        text_rgb = (240, 235, 230) if self._luminance(bg_rgb) < 0.5 else (30, 30, 30)

        # 组装调色板
        roles = ['primary', 'secondary', 'accent', 'background', 'text']
        ratios = [0.50, 0.30, 0.10, 1.00, 1.00]

        palette = []
        for i, role in enumerate(roles):
            if i < 3:
                rgb = colors[i] if i < len(colors) else colors[0]
                ratio = ratios[i]
            elif role == 'background':
                rgb = bg_rgb
                ratio = 1.00
            else:  # text
                rgb = text_rgb
                ratio = 1.00

            palette.append({
                'role': role,
                'rgb': rgb,
                'ratio': ratio,
            })

        return palette

    def _validate_ratios(self, palette: List[dict]) -> bool:
        """验证颜色比例约束。"""
        primary_ratio = None
        secondary_ratio = None

        for item in palette:
            if item['role'] == 'primary':
                primary_ratio = item['ratio']
            elif item['role'] == 'secondary':
                secondary_ratio = item['ratio']

        if primary_ratio is None:
            return False

        # 主色应在 40-75%
        if not (0.40 <= primary_ratio <= 0.75):
            return False

        return True

    # ════════════════════════════════════════════════════════════════
    #  色彩工具函数
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def _rgb_to_hue(r: int, g: int, b: int) -> float:
        """RGB 转色相（0-360）。"""
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        return h * 360

    @staticmethod
    def _hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
        """HSV 转 RGB。"""
        r, g, b = colorsys.hsv_to_rgb(h / 360, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))

    @staticmethod
    def _luminance(rgb: Tuple[int, int, int]) -> float:
        """计算相对亮度。"""
        r, g, b = [x / 255.0 for x in rgb]
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def _contrast_ratio(self, rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
        """计算对比度。"""
        l1, l2 = self._luminance(rgb1), self._luminance(rgb2)
        return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

    def execute(self, task: any, state: any) -> any:
        """统一执行入口"""
        data = task.data if hasattr(task, 'data') else task
        if not self.validate(data):
            raise ValueError(f"[{self.name}] validate failed")
        result = self.compute(data, state)
        return self.render(result)

    def compute_simple(self, data: dict) -> dict:
        """简化计算（降级用）"""
        return {"status": "simple", "mood": data.get("mood", "neutral")}




    def score_from_features(self, features: dict) -> dict:
        arr = features.get('arr')
        if arr is None:
            return {'score': 0.5, 'method': 'fallback', 'details': {}}
        if not _HAS_VERIFY_COLOR:
            return {'score': 0.5, 'method': 'fallback', 'details': {'reason': 'axiom_verifier not available'}}
        result = _verify_color_fn(arr)
        return {'score': float(result.get('score', 0.5)), 'method': 'verify_color', 'source': 'wudao_core_phase2'}
    def render_cpu(self, result: dict) -> dict:
        """CPU 渲染（降级用）"""
        return result
