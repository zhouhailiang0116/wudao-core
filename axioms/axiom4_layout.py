# -*- coding: utf-8 -*-
"""

Axiom 4: Layout - 布局公理


数学定义：
- 黄金分割：φ = (1 + √5) / 2 ≈ 1.618
- 三分法则：1/3 线交叉点为焦点
- 视觉重心：weighted_centroid = Σ(pos_i × weight_i) / Σ(weight_i)
- 负空间比：negative_space = 1 - (foreground_area / total_area)

核心概念：
- 黄金分割：最和谐的视觉比例
- 三分法则：快速构图指南
- 视觉重心：注意力焦点定位
- 负空间：呼吸感与层次

"""



from typing import List, Dict, Optional, Tuple
import math
from pathlib import Path
import sys as _sys


class LayoutAxiom:
    """
    布局公理实现
    
    四大布局法则：
    - 黄金分割（φ = 1.618）
    - 三分法则（1/3 线焦点）
    - 视觉重心（加权质心）
    - 负空间比（呼吸感）
    """
    
    # 黄金比例常数
    PHI = (1 + math.sqrt(5)) / 2  # ≈ 1.618
    
    def __init__(self,
                 gpu_shader: Optional[str] = None,
                 fallback_method: str = 'grid_layout'):
        self.name = 'layout'
        self.gpu_shader = gpu_shader
        self.fallback_method = fallback_method
    
    def validate(self, data: dict) -> bool:
        """
        验证数据是否符合布局约束
        
        Args:
            data: 包含 elements 列表的字典
        
        Returns:
            是否符合约束
        """
        if 'elements' not in data:
            return True  # 无元素约束
        
        elements = data['elements']
        
        # 检查元素是否在画布范围内
        canvas = data.get('canvas', {'width': 800, 'height': 600})
        
        for elem in elements:
            if 'position' not in elem:
                continue
            
            pos = elem['position']
            size = elem.get('size', {'width': 100, 'height': 100})
            
            # 边界检查
            if pos['x'] < 0 or pos['y'] < 0:
                return False
            if pos['x'] + size['width'] > canvas['width']:
                return False
            if pos['y'] + size['height'] > canvas['height']:
                return False
        
        return True
    
    def compute(self, data: dict, state: any) -> dict:
        """
        计算布局状态
        
        Args:
            data: 输入数据
            state: 当前状态
        
        Returns:
            布局计算结果
        """
        elements = data.get('elements', [])
        canvas = data.get('canvas', {'width': 800, 'height': 600})
        
        # 计算三分法则焦点
        third_points = self._compute_third_points(canvas)
        
        # 计算视觉重心
        visual_center = self._compute_visual_center(elements)
        
        # 计算负空间比
        negative_space = self._compute_negative_space(elements, canvas)
        
        # 计算黄金矩形
        golden_rect = self._compute_golden_rectangle(canvas)
        
        # 找到最近焦点
        nearest_focus = self._find_nearest_focus(visual_center, third_points)
        
        # 计算谱分析（布局-谱分析桥接）
        spectral_analysis = self._compute_spectral_analysis(elements, canvas)
        
        return {
            'third_points': third_points,
            'visual_center': visual_center,
            'negative_space_ratio': negative_space,
            'golden_rectangle': golden_rect,
            'nearest_focus': nearest_focus,
            'phi': self.PHI,
            'element_count': len(elements),
            # 谱分析结果（新增）
            'spectral_stability': spectral_analysis.get('stability_score', 0.5),
            'spectral_connectivity': spectral_analysis.get('algebraic_connectivity', 0),
            'spectral_clusters': spectral_analysis.get('estimated_clusters', 1),
            'spectral_interpretation': spectral_analysis.get('interpretation', ''),
        }
    
    def render(self, result: dict) -> dict:
        """
        渲染布局结果
        
        Args:
            result: 计算结果
        
        Returns:
            渲染输出
        """
        return {
            'status': 'rendered',
            'boundary_type': 'layout',
            'visual_center': result.get('visual_center'),
            'negative_space': result.get('negative_space_ratio'),
            'nearest_focus': result.get('nearest_focus'),
            'phi': result.get('phi'),
            'valid': True
        }
    
    def execute(self, task: any, state: any) -> any:
        """统一执行入口"""
        data = task.data if hasattr(task, 'data') else task
        
        if not self.validate(data):
            from core.error_handler import ValidationError
            raise ValidationError(f"[{self.name}] Layout constraint violated")
        
        result = self.compute(data, state)
        return self.render(result)
    
    def _compute_third_points(self, canvas: dict) -> list:
        """
        计算三分法则焦点
        
        焦点位于 1/3 和 2/3 线的交叉点
        """
        w = canvas.get('width', 800)
        h = canvas.get('height', 600)
        
        return [
            {'x': w / 3, 'y': h / 3},
            {'x': 2 * w / 3, 'y': h / 3},
            {'x': w / 3, 'y': 2 * h / 3},
            {'x': 2 * w / 3, 'y': 2 * h / 3}
        ]
    
    def _compute_visual_center(self, elements: list) -> dict:
        """
        计算视觉重心（加权质心）
        
        weighted_centroid = Σ(pos_i × weight_i) / Σ(weight_i)
        """
        if not elements:
            return {'x': 0.5, 'y': 0.5}  # 默认中心
        
        total_weight = 0
        weighted_x = 0
        weighted_y = 0
        
        for elem in elements:
            pos = elem.get('position', {'x': 0, 'y': 0})
            weight = elem.get('visual_weight', 1.0)
            
            weighted_x += pos['x'] * weight
            weighted_y += pos['y'] * weight
            total_weight += weight
        
        if total_weight == 0:
            return {'x': 0.5, 'y': 0.5}
        
        return {
            'x': weighted_x / total_weight,
            'y': weighted_y / total_weight
        }
    
    def _compute_negative_space(self, elements: list, canvas: dict) -> float:
        """
        计算负空间比
        
        negative_space = 1 - (foreground_area / total_area)
        """
        total_area = canvas.get('width', 800) * canvas.get('height', 600)
        
        foreground_area = 0
        for elem in elements:
            size = elem.get('size', {'width': 100, 'height': 100})
            foreground_area += size['width'] * size['height']
        
        if total_area == 0:
            return 1.0
        
        return max(0, 1 - foreground_area / total_area)
    
    def _compute_golden_rectangle(self, canvas: dict) -> dict:
        """
        计算黄金矩形
        
        宽度:高度 = φ:1 或 1:φ
        """
        w = canvas.get('width', 800)
        h = canvas.get('height', 600)
        
        # 根据画布比例选择方向
        if w > h:
            # 横向黄金矩形
            rect_width = h * self.PHI
            rect_height = h
        else:
            # 纵向黄金矩形
            rect_width = w
            rect_height = w * self.PHI
        
        return {
            'width': rect_width,
            'height': rect_height,
            'phi': self.PHI
        }
    
    def _find_nearest_focus(self, visual_center: dict, third_points: list) -> dict:
        """
        找到最近的焦点
        """
        min_dist = float('inf')
        nearest = third_points[0] if third_points else {'x': 0, 'y': 0}
        
        for point in third_points:
            dist = math.sqrt(
                (visual_center['x'] - point['x']) ** 2 +
                (visual_center['y'] - point['y']) ** 2
            )
            if dist < min_dist:
                min_dist = dist
                nearest = point
        
        return {
            'point': nearest,
            'distance': min_dist
        }
    
    def _compute_spectral_analysis(self, elements: list, canvas: dict) -> dict:
        """
        谱图理论分析构图稳定性
        
        使用 layout_spectral_bridge 连接谱分析与布局公理
        
        返回:
            dict: {
                'stability_score': float,      # 构图稳定性 0-1
                'algebraic_connectivity': float,  # 代数连通性
                'estimated_clusters': int,      # 估计的视觉聚类数
                'interpretation': str          # 数学解读
            }
        """
        try:
            from layout_spectral_bridge import LayoutSpectralBridge
            
            # 转换元素格式
            layout_elements = []
            canvas_w = canvas.get('width', 800)
            canvas_h = canvas.get('height', 600)
            
            for i, elem in enumerate(elements):
                # 获取位置
                pos = elem.get('position', {'x': 0, 'y': 0})
                x = pos.get('x', 0)
                y = pos.get('y', 0)
                
                # 获取大小
                size = elem.get('size', {'width': 100, 'height': 100})
                if isinstance(size, dict):
                    width = size.get('width', 100)
                    height = size.get('height', 100)
                    area = width * height
                else:
                    area = float(size)
                
                # 获取权重
                weight = elem.get('visual_weight', 1.0)
                
                # 获取重要性
                importance = elem.get('importance', i + 1)
                
                layout_elements.append({
                    'id': elem.get('id', f'elem_{i}'),
                    'position': {'x': x, 'y': y},
                    'size': area,
                    'visual_weight': weight,
                    'importance': importance
                })
            
            # 如果元素太少，直接返回默认值
            if len(layout_elements) < 2:
                return {
                    'stability_score': 0.5,
                    'algebraic_connectivity': 0,
                    'estimated_clusters': len(layout_elements) or 1,
                    'interpretation': '元素不足，无法进行谱分析'
                }
            
            # 构建布局图并分析
            bridge = LayoutSpectralBridge(
                distance_threshold=min(canvas_w, canvas_h) / 2
            )
            layout_data = {
                'elements': layout_elements,
                'canvas': canvas
            }
            
            result = bridge.analyze_layout(layout_data)
            return result.to_dict()
            
        except Exception as e:
            # 谱分析失败时返回默认值
            return {
                'stability_score': 0.5,
                'algebraic_connectivity': 0,
                'estimated_clusters': len(elements) or 1,
                'interpretation': f'谱分析不可用: {str(e)[:50]}'
            }
    
    def compute_simple(self, data: dict) -> dict:
        """简化计算（降级用）"""
        return {
            'status': 'simple',
            'elements': data.get('elements', [])
        }
    
    def render_cpu(self, result: dict) -> dict:
        """CPU渲染（降级用）"""
        return result
    



    def score_from_features(self, features: dict) -> dict:
        arr = features.get('arr')
        if arr is None:
            return {'score': 0.5, 'method': 'fallback', 'details': {}}
        _path = str(Path(__file__).resolve().parent.parent.parent / "wukong" / "wukong_eye" / "core")
        if _path not in _sys.path:
            _sys.path.insert(0, _path)
        from axiom_verifier import verify_layout as _vf
        result = _vf(arr)
        return {'score': float(result.get('score', 0.5)), 'method': 'verify_layout', 'source': 'wudao_core_phase2'}
    def info(self) -> dict:
        """获取公理信息"""
        return {
            'name': self.name,
            'gpu_shader': self.gpu_shader,
            'fallback_method': self.fallback_method,
            'phi': self.PHI
        }
