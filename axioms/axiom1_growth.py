# -*- coding: utf-8 -*-
"""

Axiom 1: Growth - 生长公理（内容节奏约束）


数学定义：
- 能量曲线：E(t) = f(t; phase, peak_time, intensity)
- 相位约束：phase_i ⊂ timeline, phase_i ∩ phase_j = ∅ (i≠j)
- 峰值定位：t_peak = argmax(E(t))
- 收敛速率：decay_rate = -dE/dt | t > t_peak

核心概念：
- 慢起(attention)：低能量开场，建立认知
- 爆发(climax)：能量峰值，核心信息
- 收敛(settle)：能量回落，总结/CTA
- 节奏模板：预设的能量曲线形态

"""



from typing import Dict, List, Optional, Tuple
import math


class GrowthAxiom:
    """
    生长公理实现
    
    从内容/目标推算节奏曲线：
    - timeline: 时间轴分段
    - energy_curve: 能量分布
    - peak_position: 峰值位置
    - pattern: 节奏模式
    """

    # ─── 节奏模板（归一化能量曲线）──────────────────────────────
    PATTERNS = {
        "rise-fall": {
            "desc": "慢起→爆发→收敛（经典叙事）",
            "phases": ["attention", "climax", "settle"],
            "peak_ratio": 0.6,      # 峰值在 60% 位置
            "rise_slope": 0.8,      # 上升斜率
            "decay_rate": 1.2,      # 衰减速率
        },
        "build-peak": {
            "desc": "持续构建→单峰→快速收尾",
            "phases": ["build", "peak", "release"],
            "peak_ratio": 0.75,
            "rise_slope": 0.6,
            "decay_rate": 2.0,      # 快速收尾
        },
        "steady": {
            "desc": "平稳输出（教学/说明）",
            "phases": ["intro", "content", "summary"],
            "peak_ratio": 0.5,
            "rise_slope": 0.3,      # 平缓
            "decay_rate": 0.5,      # 缓慢收敛
        },
        "hook-cta": {
            "desc": "强开场→主体→强CTA（营销）",
            "phases": ["hook", "body", "cta"],
            "peak_ratio": 0.9,      # CTA 位置为次峰值
            "rise_slope": 1.0,
            "decay_rate": 0.8,
            "has_initial_hook": True,
        },
        "wave": {
            "desc": "波浪式（长内容）",
            "phases": ["rise1", "peak1", "valley", "peak2", "settle"],
            "peak_ratio": 0.4,      # 第一峰
            "rise_slope": 0.7,
            "decay_rate": 0.6,
            "second_peak_ratio": 0.8,
        },
    }

    # ─── 内容类型→节奏映射 ─────────────────────────────────────
    CONTENT_RHYTHM = {
        "story": "rise-fall",
        "narrative": "rise-fall",
        "tutorial": "steady",
        "howto": "steady",
        "marketing": "hook-cta",
        "sales": "hook-cta",
        "drama": "build-peak",
        "presentation": "build-peak",
        "longform": "wave",
        "documentary": "wave",
    }

    # ─── 情绪→节奏偏移 ─────────────────────────────────────────
    MOOD_RHYTHM = {
        "dramatic": {"peak_bias": -0.1, "intensity_mult": 1.3},
        "calm": {"peak_bias": 0.0, "intensity_mult": 0.7},
        "energetic": {"peak_bias": 0.05, "intensity_mult": 1.2},
        "mysterious": {"peak_bias": 0.1, "intensity_mult": 0.8},
        "urgent": {"peak_bias": -0.2, "intensity_mult": 1.5},
        "peaceful": {"peak_bias": 0.1, "intensity_mult": 0.6},
    }

    def __init__(self,
                 gpu_shader: Optional[str] = None,
                 fallback_method: str = 'auto'):
        self.name = 'growth'
        self.gpu_shader = gpu_shader
        self.fallback_method = fallback_method

    # ════════════════════════════════════════════════════════════════
    #  接口实现
    # ════════════════════════════════════════════════════════════════

    def validate(self, data: dict) -> bool:
        """
        验证输入数据。
        
        最简约束：data 是 dict。
        有 duration 时校验 > 0。
        """
        if not isinstance(data, dict):
            return False

        duration = data.get("duration")
        if duration is not None and duration <= 0:
            return False

        return True

    def compute(self, data: dict, state: any) -> dict:
        """
        推算内容节奏参数。
        
        输入字段（全部可选）：
          content_type:  str   — 内容类型（story/tutorial/marketing...）
          duration:      float — 总时长（秒/帧数）
          segments:      int   — 分段数（默认 10）
          mood:          str   — 情绪关键词
          pattern:       str   — 指定节奏模式（覆盖自动推断）
          custom_phases: list  — 自定义阶段划分
        
        输出：
          pattern:       str           — 节奏模式名称
          phases:        list[dict]    — 阶段划分
          energy_curve:  list[float]   — 能量曲线（归一化 0~1）
          peak_position: float         — 峰值位置（0~1）
          peak_index:    int           — 峰值索引
          timing:        dict          — 时间节点
        """
        # ── 1. 推断节奏模式 ─────────────────────────────────────
        pattern_name = data.get("pattern")
        if not pattern_name:
            content_type = data.get("content_type", "story")
            pattern_name = self.CONTENT_RHYTHM.get(content_type, "rise-fall")
        
        pattern_cfg = self.PATTERNS.get(pattern_name, self.PATTERNS["rise-fall"])

        # ── 2. 计算分段 ─────────────────────────────────────────
        duration = data.get("duration", 1.0)
        segments = data.get("segments", 10)
        segments = max(3, min(100, segments))

        # ── 3. 生成能量曲线 ─────────────────────────────────────
        energy_curve = self._generate_energy_curve(
            pattern_cfg, segments, data.get("mood")
        )

        # ── 4. 定位峰值 ─────────────────────────────────────────
        peak_idx = energy_curve.index(max(energy_curve))
        peak_position = peak_idx / max(1, segments - 1)

        # ── 5. 划分阶段 ─────────────────────────────────────────
        phases = self._compute_phases(
            pattern_cfg, segments, duration, energy_curve
        )

        # ── 6. 时间节点 ─────────────────────────────────────────
        timing = {
            "duration": duration,
            "segment_duration": duration / segments,
            "peak_time": peak_position * duration,
            "phases": {p["name"]: p["time_range"] for p in phases},
        }

        return {
            "pattern": pattern_name,
            "pattern_desc": pattern_cfg["desc"],
            "phases": phases,
            "energy_curve": energy_curve,
            "peak_position": round(peak_position, 3),
            "peak_index": peak_idx,
            "timing": timing,
            "segments": segments,
            "intensity": round(max(energy_curve), 3),
            # 动力学分析（Growth-Dynamics Bridge）
            **self._compute_dynamics_analysis(energy_curve, pattern_name),
        }

    def render(self, result: dict) -> dict:
        """渲染输出：精简格式。"""
        return {
            "status": "rendered",
            "boundary_type": "growth",
            "pattern": result.get("pattern"),
            "phases": result.get("phases"),
            "energy_curve": result.get("energy_curve"),
            "peak_position": result.get("peak_position"),
            "peak_index": result.get("peak_index"),
            "timing": result.get("timing"),
            "intensity": result.get("intensity"),
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

    def _generate_energy_curve(self, pattern: dict, segments: int, 
                                mood: Optional[str]) -> List[float]:
        """
        生成能量曲线。
        
        核心算法：分段高斯 + 指数衰减
        """
        peak_ratio = pattern["peak_ratio"]
        rise_slope = pattern["rise_slope"]
        decay_rate = pattern["decay_rate"]

        # 应用情绪偏移
        if mood:
            mood_cfg = self.MOOD_RHYTHM.get(mood.lower(), {})
            peak_ratio = self._clamp(peak_ratio + mood_cfg.get("peak_bias", 0), 0.2, 0.9)
            intensity_mult = mood_cfg.get("intensity_mult", 1.0)
        else:
            intensity_mult = 1.0

        peak_idx = int(peak_ratio * (segments - 1))

        curve = []
        for i in range(segments):
            t = i / max(1, segments - 1)  # 归一化位置 0~1

            if i <= peak_idx:
                # 上升段：sigmoid-like
                t_norm = t / max(0.01, peak_ratio)
                energy = self._sigmoid(t_norm * rise_slope * 4 - 2)
            else:
                # 衰减段：指数衰减
                t_decay = (t - peak_ratio) / max(0.01, 1 - peak_ratio)
                energy = math.exp(-decay_rate * t_decay)

            # 波浪模式：添加第二峰
            if pattern.get("second_peak_ratio"):
                t2 = pattern["second_peak_ratio"]
                if abs(t - t2) < 0.15:
                    energy = max(energy, 0.7 * math.exp(-((t - t2) / 0.1) ** 2))

            # Hook 模式：开场强峰
            if pattern.get("has_initial_hook") and t < 0.15:
                energy = max(energy, 0.6 + 0.4 * math.exp(-((t - 0.05) / 0.05) ** 2))

            energy = self._clamp(energy * intensity_mult, 0, 1)
            curve.append(round(energy, 3))

        return curve

    def _compute_phases(self, pattern: dict, segments: int, 
                        duration: float, curve: List[float]) -> List[dict]:
        """划分阶段。"""
        phase_names = pattern["phases"]
        num_phases = len(phase_names)

        # 简单均分（可扩展为能量阈值划分）
        phase_len = segments // num_phases

        phases = []
        total_time = 0.0
        for i, name in enumerate(phase_names):
            start_idx = i * phase_len
            end_idx = (i + 1) * phase_len if i < num_phases - 1 else segments

            phase_duration = (end_idx - start_idx) / segments * duration
            avg_energy = sum(curve[start_idx:end_idx]) / max(1, end_idx - start_idx)

            phases.append({
                "name": name,
                "index": i,
                "segment_range": [start_idx, end_idx],
                "time_range": [round(total_time, 2), round(total_time + phase_duration, 2)],
                "duration": round(phase_duration, 2),
                "avg_energy": round(avg_energy, 3),
            })
            total_time += phase_duration

        return phases
    
    def _compute_dynamics_analysis(self, energy_curve: List[float], pattern_name: str) -> dict:
        """
        动力系统分析节奏曲线的稳定性
        
        使用 Lyapunov 指数衡量节奏的"有趣程度"
        """
        try:
            from axiom_math_bridges import GrowthDynamicsBridge
            
            bridge = GrowthDynamicsBridge()
            result = bridge.analyze_rhythm(energy_curve, pattern_name)
            
            return {
                'lyapunov_exponent': result.lyapunov_exponent,
                'chaos_level': result.chaos_level,
                'dynamics_stability': result.dynamics_stability,
                'dynamics_interpretation': result.interpretation,
            }
        except Exception as e:
            import logging as _log
            _log.warning(f"[axiom1_growth] GrowthDynamicsBridge 不可用，动力学分析退化为默认值: {e}")
            return {
                'lyapunov_exponent': 0.0,
                'chaos_level': 'unknown',
                'dynamics_stability': 0.5,
                'dynamics_interpretation': f'动力学分析不可用: {str(e)[:50]}',
            }

    # ════════════════════════════════════════════════════════════════
    #  工具函数
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def _sigmoid(x: float) -> float:
        """Sigmoid 函数。"""
        return 1 / (1 + math.exp(-x))

    @staticmethod
    def _clamp(value: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, value))

    def execute(self, task: any, state: any) -> any:
        """统一执行入口"""
        data = task.data if hasattr(task, 'data') else task
        if not self.validate(data):
            raise ValueError(f"[{self.name}] validate failed")
        result = self.compute(data, state)
        return self.render(result)

    def compute_simple(self, data: dict) -> dict:
        """简化计算（降级用）"""
        return {"status": "simple", "pattern": data.get("pattern", "rise-fall")}

    def score_from_features(self, features: dict) -> dict:
        """
        Phase 3 逆向：图像特征 -> 生成分数

        Sobel 边缘密度（纹理丰富度代理）+ Game of Life 涌现度。
        评分逻辑直接内联，不再调用 verify_growth（打破循环依赖）。
        """
        arr = features.get('arr')
        if arr is None:
            return {'score': 0.5, 'method': 'growth_fallback', 'details': {}}

        # Sobel 边缘密度
        import numpy as np
        gray = arr.mean(axis=2).astype(float)
        gx, gy = np.gradient(gray)
        sobel = np.sqrt(gx**2 + gy**2)
        threshold = float(np.percentile(sobel.flatten(), 70))
        edge_density = float(np.sum(sobel > threshold) / sobel.size)
        edge_strength = float(sobel[sobel > threshold].mean() / 255.0) if np.any(sobel > threshold) else 0.0
        sobel_score = min(1.0, max(0.0, edge_strength / 0.15))

        # Game of Life 涌现度（lazy import cellular 模块）
        import sys as _sys
        _MK = str(Path(__file__).resolve().parent.parent.parent / "wukong" / "wukong_math" / "core")
        if _MK not in _sys.path:
            _sys.path.insert(0, _MK)
        try:
            import cellular as _cel_mod
            # Binary: Game of Life 需要 0/1 状态
            gray_01 = gray / 255.0 if gray.max() > 1.0 else gray
            binary = (gray_01 > 0.5).astype(np.uint8)
            # 运行 5 步 Game of Life
            cell_counts = []
            state = binary
            for _ in range(5):
                state = _cel_mod.next_generation(state)
                cell_counts.append(int(state.sum()))
            if not cell_counts:
                emergence_ratio, gol_entropy, cell_final = 1.0, 0.0, 0
            else:
                initial = max(1, cell_counts[0])
                emergence_ratio = cell_counts[-1] / initial
                cell_final = cell_counts[-1]
                feat = _cel_mod.growth_features(state)
                gol_entropy = float(feat.get('entropy', 0.0))
        except Exception as e:
            import logging as _log
            _log.warning(f"[axiom1_growth] cellular 模块不可用，Game of Life 涌现度退化为默认值: {e}")
            emergence_ratio, gol_entropy, cell_final = 0.5, 0.0, gray.size // 2

        # Gol 评分
        if emergence_ratio < 0.3:
            gol_score = 0.1
        elif emergence_ratio > 3.0:
            gol_score = 0.3
        else:
            gol_score = min(1.0, emergence_ratio / 2.5)

        # 综合：边缘 0.6 + 涌现 0.4
        score = 0.6 * sobel_score + 0.4 * gol_score

        return {
            'score': float(score),
            'method': 'sobel_gol_v1',
            'edge_density': float(edge_density),
            'sobel_score': float(sobel_score),
            'gol_score': float(gol_score),
            'emergence_ratio': float(emergence_ratio),
            'source': 'wudao_core_growth_v3'
        }
    def render_cpu(self, result: dict) -> dict:
        """CPU 渲染（降级用）"""
        return result
