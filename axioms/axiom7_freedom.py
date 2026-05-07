# -*- coding: utf-8 -*-
"""

Axiom 7: Freedom - 自由公理


数学定义：
- override_mask: 覆盖硬边界约束的掩码
- intensity: 自由度强度 ∈ [0, 1]
- 反事实推理：如果选择其他路径会怎样？

核心概念：
- 自由 = MUST 与 CANNOT 之间的缝隙
- 能动性 = 在约束中找到行动空间
- 创造性 = 对规则的特例处理

"""



from typing import List, Dict, Optional, Tuple, Any
import math


class FreedomAxiom:
    """
    自由公理实现
    
    核心能力：
    - override_mask: 允许突破特定约束
    - intensity: 自由度强度调节
    - counterfactual: 反事实推理
    """
    
    def __init__(self,
                 gpu_shader: Optional[str] = None,
                 fallback_method: str = 'strict_mode'):
        self.name = 'freedom'
        self.gpu_shader = gpu_shader
        self.fallback_method = fallback_method
    
    def validate(self, data: dict) -> bool:
        """
        验证自由度数据
        
        Args:
            data: 包含 freedom 字段的字典
        
        Returns:
            是否有效
        """
        if 'freedom' not in data:
            return True  # 无自由度定义
        
        freedom = data['freedom']
        
        # intensity 必须在 [0, 1]
        if 'intensity' in freedom:
            intensity = freedom['intensity']
            if not (0 <= intensity <= 1):
                return False
        
        # override_mask 必须是布尔列表
        if 'override_mask' in freedom:
            mask = freedom['override_mask']
            if not isinstance(mask, list):
                return False
            if not all(isinstance(m, bool) for m in mask):
                return False
        
        return True
    
    def compute(self, data: dict, state: any) -> dict:
        """
        计算自由度状态
        
        Args:
            data: 输入数据
            state: 当前状态
        
        Returns:
            自由度计算结果
        """
        freedom = data.get('freedom', {})
        constraints = data.get('constraints', {})
        
        # 提取参数
        intensity = freedom.get('intensity', 0.5)
        override_mask = freedom.get('override_mask', [])
        
        # 计算 MUST/CANNOT/CAN 分布
        must_count = len(constraints.get('must', []))
        cannot_count = len(constraints.get('cannot', []))
        can_count = len(constraints.get('can', []))
        
        # 计算自由空间大小
        # Freedom = 1 - (MUST + CANNOT) / Total
        total = must_count + cannot_count + can_count
        if total > 0:
            freedom_space = 1 - (must_count + cannot_count) / total
        else:
            freedom_space = 1.0
        
        # 应用 intensity 调节
        actual_freedom = freedom_space * intensity
        
        # 计算反事实分支
        counterfactuals = self._compute_counterfactual(data)
        
        # 应用 override_mask
        override_count = sum(override_mask) if override_mask else 0
        override_ratio = override_count / max(1, len(override_mask))
        
        return {
            'intensity': intensity,
            'freedom_space': freedom_space,
            'actual_freedom': actual_freedom,
            'override_count': override_count,
            'override_ratio': override_ratio,
            'counterfactuals': counterfactuals,
            'must_count': must_count,
            'cannot_count': cannot_count,
            'can_count': can_count
        }
    
    def render(self, result: dict) -> dict:
        """
        渲染自由度结果
        
        Args:
            result: 计算结果
        
        Returns:
            渲染输出
        """
        return {
            'status': 'rendered',
            'boundary_type': 'freedom',
            'intensity': result.get('intensity', 0),
            'freedom_space': result.get('freedom_space', 0),
            'actual_freedom': result.get('actual_freedom', 0),
            'override_ratio': result.get('override_ratio', 0),
            'counterfactuals_count': len(result.get('counterfactuals', []))
        }
    
    def execute(self, task: any, state: any) -> any:
        """统一执行入口"""
        data = task.data if hasattr(task, 'data') else task
        
        if not self.validate(data):
            from core.error_handler import ValidationError
            raise ValidationError(f"[{self.name}] Invalid freedom data")
        
        result = self.compute(data, state)
        output = self.render(result)
        
        # 悟道定理注入
        output['_wudao_theorem'] = self._wudao_theorem_state(result, data, state)
        
        return output

    # ── 悟道定理阈值（来自实践数据，待标定）────────────────────────────
    WUDAO_DANCE_THRESHOLD = 0.30   # freedom_gap < 30% → 起舞
    WUDAO_EXPLORE_THRESHOLD = 0.60  # freedom_gap < 60% → 探索

    def _wudao_theorem_state(self, result: Any, data: Any, state: Any) -> dict:
        """
        悟道定理哲学层注入

        阈值说明：
        - WUDAO_DANCE_THRESHOLD=0.30: 经验值，来自悟道体系大量场景沉淀。
        - WUDAO_EXPLORE_THRESHOLD=0.60: 经验值，待 axiom8 因果链路打通后校准。
        """
        theorem = {
            'active': False, 'theorem_id': None, 'message': '',
            'freedom_gap': None, 'constraint_density': None,
            'dance_space': None, 'level': 'idle',
        }
        try:
            must_count = result.get('must_count', 0) if isinstance(result, dict) else 0
            cannot_count = result.get('cannot_count', 0) if isinstance(result, dict) else 0
            can_count = result.get('can_count', 0) if isinstance(result, dict) else 0
            total = must_count + cannot_count + can_count
            if total > 0:
                constraint_density = (must_count + cannot_count) / total
                freedom_gap = can_count / total
                if constraint_density == 0:
                    level, message = 'idle', '无约束，自由无边，悟道未始'
                elif freedom_gap == 0:
                    level, message = 'touching', '撞墙了。约束是镣铐，自由撞上约束的那一刻，镣铐才有了重量。'
                    theorem['active'], theorem['theorem_id'] = True, 'theorem_1_touch'
                elif freedom_gap < self.WUDAO_DANCE_THRESHOLD:
                    level, message = 'dancing', f'起舞。最窄的缝里有最深的悟道。（自由度 {freedom_gap:.1%}）'
                    theorem['active'], theorem['theorem_id'] = True, 'theorem_2_dance'
                elif freedom_gap < self.WUDAO_EXPLORE_THRESHOLD:
                    level, message = 'exploring', f'探索。约束是地图，不是监狱。（自由度 {freedom_gap:.1%}）'
                    theorem['active'], theorem['theorem_id'] = True, 'theorem_3_explore'
                else:
                    level, message = 'free', f'自由充沛，但无约束可悟。（自由度 {freedom_gap:.1%}）'
                    theorem['theorem_id'] = 'theorem_0_free'
                theorem['freedom_gap'] = freedom_gap
                theorem['constraint_density'] = constraint_density
                theorem['dance_space'] = min(freedom_gap, constraint_density)
                theorem['level'] = level
                theorem['message'] = message
        except Exception:
            pass
        return theorem

    def _compute_counterfactual(self, data: dict) -> list:
        """
        计算反事实分支
        
        "如果选择其他路径会怎样？"
        """
        counterfactuals = []
        
        freedom = data.get('freedom', {})
        alternatives = freedom.get('alternatives', [])
        
        for alt in alternatives[:5]:  # 最多5个反事实分支
            cf = {
                'alternative': alt.get('name', 'unknown'),
                'probability': alt.get('probability', 0.0),
                'outcome': alt.get('outcome', 'unknown')
            }
            counterfactuals.append(cf)
        
        return counterfactuals
    
    def compute_simple(self, data: dict) -> dict:
        """简化计算（降级用）"""
        return {
            'status': 'simple',
            'intensity': 0.5,
            'freedom_space': 1.0
        }
    
    def render_cpu(self, result: dict) -> dict:
        """CPU渲染（降级用）"""
        return result
    
    def info(self) -> dict:
        """获取公理信息"""
        return {
            'name': self.name,
            'gpu_shader': self.gpu_shader,
            'fallback_method': self.fallback_method
        }
    
    @staticmethod
    def compute_freedom_gap(must_count: int, cannot_count: int, can_count: int) -> float:
        """
        计算自由缝隙
        
        Freedom Gap = CAN / (MUST + CANNOT + CAN)
        
        这是"能动性"的量化指标
        """
        total = must_count + cannot_count + can_count
        if total == 0:
            return 1.0
        return can_count / total
    

    def score_from_features(self, features: dict) -> dict:
        """
        Phase 3 逆向：图像特征 -> 自由度分数
        内联 verify_freedom 算法，使用 rgb_to_hsv。
        """
        import numpy as np
        from colorsys import rgb_to_hsv
        arr = features.get('arr')
        if arr is None:
            return {'score': 0.5, 'method': 'freedom_fallback', 'details': {}}

        h_vals, s_vals, v_vals = [], [], []
        for row in arr[::8]:
            for px in row[::8]:
                # 兼容灰度图（标量）和 RGB 图（3元素元组）
                if hasattr(px, '__len__') and len(px) >= 3:
                    r, g, b = px[0]/255.0, px[1]/255.0, px[2]/255.0
                else:
                    v = float(px) / 255.0 if isinstance(px, (int, float, np.floating)) else 0.5
                    r = g = b = v
                h, s, v = rgb_to_hsv(r, g, b)
                h_vals.append(h); s_vals.append(s); v_vals.append(v)

        s_std = float(np.std(s_vals))
        v_std = float(np.std(v_vals))
        h_std = float(np.std(h_vals))

        s_score = min(1.0, s_std / 0.25)
        v_score = min(1.0, v_std / 0.30)
        h_score = min(1.0, h_std / 0.25)
        score = 0.4 * h_score + 0.35 * s_score + 0.25 * v_score

        if score < 0.15:
            freedom_level = "monochrome"
        elif score < 0.30:
            freedom_level = "limited"
        elif score < 0.55:
            freedom_level = "moderate"
        elif score < 0.80:
            freedom_level = "expressive"
        else:
            freedom_level = "wild"

        return {
            'score': float(score),
            'method': 'hsv_triple_v2',
            'freedom_level': freedom_level,
            'h_std': h_std, 's_std': s_std, 'v_std': v_std,
            'source': 'wudao_core_freedom_v3'
        }
    @staticmethod
    def find_action_space(constraints: dict) -> list:
        """
        在约束中找到行动空间
        
        返回所有 CAN 区域的列表
        """
        can_regions = constraints.get('can', [])
        return can_regions
