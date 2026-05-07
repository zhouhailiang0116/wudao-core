# -*- coding: utf-8 -*-
"""

Axiom 6: Boundary - 边界公理


数学定义：
- IoU(A, B) = |A ∩ B| / |A ∪ B| = 0  (互斥边界)
- 嵌套约束：inner ⊂ outer
- 动态边界：boundary(t) = f(I(t), t)

核心概念：
- MUST: 硬边界，绝对不可违反
- CANNOT: 否定边界，排除区域
- CAN: 软边界，可协商空间

"""



from typing import List, Tuple, Optional, Any
import math
import sys as _sys
from pathlib import Path

# wukong_eye/core 动态路径
_WK = Path(__file__).resolve().parent.parent.parent / "wukong"
_WK_EYE = str(_WK / "wukong_eye" / "core")
if _WK_EYE not in _sys.path:
    _sys.path.insert(0, _WK_EYE)
try:
    from axiom_verifier import verify_boundary as _verify_boundary_fn
    _HAS_VERIFY_BOUNDARY = True
except ImportError:
    _HAS_VERIFY_BOUNDARY = False


class BoundaryAxiom:
    """
    边界公理实现
    
    三类边界：
    - MUST: 必须包含（核心区域）
    - CANNOT: 不能包含（禁区）
    - CAN: 可选包含（协商区域）
    """
    
    def __init__(self, 
                 gpu_shader: Optional[str] = None,
                 fallback_method: str = 'no_overlap'):
        self.name = 'boundary'
        self.gpu_shader = gpu_shader
        self.fallback_method = fallback_method
    
    def validate(self, data: dict) -> bool:
        """
        验证数据是否符合边界约束
        
        Args:
            data: 包含 boundaries 列表的字典
        
        Returns:
            是否符合约束
        """
        if 'boundaries' not in data:
            return True  # 无边界约束
        
        boundaries = data['boundaries']
        
        # 检查 MUST 边界
        must_regions = [b for b in boundaries if b.get('type') == 'MUST']
        cannot_regions = [b for b in boundaries if b.get('type') == 'CANNOT']
        
        # MUST 区域不能与 CANNOT 区域重叠
        for must in must_regions:
            for cannot in cannot_regions:
                if self._check_overlap(must, cannot):
                    return False
        
        return True
    
    def compute(self, data: dict, state: any) -> dict:
        """
        计算边界状态
        
        Args:
            data: 输入数据
            state: 当前状态
        
        Returns:
            边界计算结果
        """
        boundaries = data.get('boundaries', [])
        time_t = state.get('t', 0) if state else 0
        
        # 分类边界
        must_regions = []
        cannot_regions = []
        can_regions = []
        
        for b in boundaries:
            b_type = b.get('type', 'CAN')
            if b_type == 'MUST':
                must_regions.append(b)
            elif b_type == 'CANNOT':
                cannot_regions.append(b)
            else:
                can_regions.append(b)
        
        # 计算动态边界
        dynamic_boundaries = self._compute_dynamic(boundaries, time_t)
        
        # 计算 IoU 矩阵
        iou_matrix = self._compute_iou_matrix(boundaries)
        
        # 计算拓扑分析（Boundary-Topology Bridge）
        topology_analysis = self._compute_topology_analysis(boundaries, data.get('canvas', {'width': 800, 'height': 600}))
        
        return {
            'must_count': len(must_regions),
            'cannot_count': len(cannot_regions),
            'can_count': len(can_regions),
            'dynamic_boundaries': dynamic_boundaries,
            'iou_matrix': iou_matrix,
            'violations': self._find_violations(iou_matrix),
            # 拓扑分析结果
            'topology_stability': topology_analysis.get('stability', 0.5),
            'betti_numbers': topology_analysis.get('betti', [0, 0, 0]),
            'topology_interpretation': topology_analysis.get('interpretation', ''),
        }
    
    def render(self, result: dict) -> dict:
        """
        渲染边界结果
        
        Args:
            result: 计算结果
        
        Returns:
            渲染输出
        """
        return {
            'status': 'rendered',
            'boundary_type': 'boundary',
            'must_count': result.get('must_count', 0),
            'cannot_count': result.get('cannot_count', 0),
            'can_count': result.get('can_count', 0),
            'violations': result.get('violations', []),
            'valid': len(result.get('violations', [])) == 0
        }
    
    def execute(self, task: any, state: any) -> any:
        """统一执行入口"""
        data = task.data if hasattr(task, 'data') else task
        
        if not self.validate(data):
            from core.error_handler import ValidationError
            raise ValidationError(f"[{self.name}] Boundary constraint violated")
        
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

    def _check_overlap(self, region1: dict, region2: dict) -> bool:
        """
        检查两个区域是否重叠
        
        简化实现：矩形区域
        """
        if 'rect' not in region1 or 'rect' not in region2:
            return False
        
        r1 = region1['rect']  # (x1, y1, x2, y2)
        r2 = region2['rect']
        
        # 检查矩形重叠
        return not (r1[2] < r2[0] or r1[0] > r2[2] or 
                    r1[3] < r2[1] or r1[1] > r2[3])
    
    def _compute_iou(self, region1: dict, region2: dict) -> float:
        """
        计算两个区域的 IoU
        """
        if 'rect' not in region1 or 'rect' not in region2:
            return 0.0
        
        r1 = region1['rect']
        r2 = region2['rect']
        
        # 计算交集
        inter_x1 = max(r1[0], r2[0])
        inter_y1 = max(r1[1], r2[1])
        inter_x2 = min(r1[2], r2[2])
        inter_y2 = min(r1[3], r2[3])
        
        if inter_x2 < inter_x1 or inter_y2 < inter_y1:
            inter_area = 0
        else:
            inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        
        # 计算并集
        area1 = (r1[2] - r1[0]) * (r1[3] - r1[1])
        area2 = (r2[2] - r2[0]) * (r2[3] - r2[1])
        union_area = area1 + area2 - inter_area
        
        if union_area == 0:
            return 0.0
        
        return inter_area / union_area
    
    def _compute_iou_matrix(self, boundaries: list) -> list:
        """
        计算边界 IoU 矩阵
        """
        n = len(boundaries)
        matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(i+1, n):
                iou = self._compute_iou(boundaries[i], boundaries[j])
                matrix[i][j] = iou
                matrix[j][i] = iou
        
        return matrix
    
    def _compute_dynamic(self, boundaries: list, time_t: float) -> list:
        """
        计算动态边界
        
        boundary(t) = base + amplitude * sin(ω * t)
        """
        dynamic = []
        
        for b in boundaries:
            if 'dynamic' in b:
                dyn = b['dynamic']
                base = b.get('rect', (0, 0, 100, 100))
                amp = dyn.get('amplitude', 10)
                freq = dyn.get('frequency', 1.0)
                
                # 简化：只移动 y 坐标
                offset = amp * math.sin(2 * math.pi * freq * time_t)
                
                dynamic_rect = (
                    base[0],
                    base[1] + offset,
                    base[2],
                    base[3] + offset
                )
                
                dynamic.append({
                    'type': b.get('type'),
                    'rect': dynamic_rect,
                    'time': time_t
                })
        
        return dynamic
    
    def _find_violations(self, iou_matrix: list) -> list:
        """
        找出违反约束的区域对
        """
        violations = []
        n = len(iou_matrix)
        
        for i in range(n):
            for j in range(i+1, n):
                if iou_matrix[i][j] > 0.1:  # IoU 阈值
                    violations.append({
                        'regions': (i, j),
                        'iou': iou_matrix[i][j]
                    })
        
        return violations
    
    def _compute_topology_analysis(self, boundaries: list, canvas: dict) -> dict:
        """
        拓扑学分析边界系统的稳定性
        
        使用 Betti 数衡量边界的拓扑特征
        """
        try:
            from axiom_math_bridges import BoundaryTopologyBridge
            
            # 转换边界格式
            regions = []
            for b in boundaries:
                if 'rect' in b:
                    x0, y0, x1, y1 = b['rect']
                    regions.append({
                        'type': b.get('type', 'CAN'),
                        'bbox': (int(x0), int(y0), int(x1), int(y1))
                    })
            
            if len(regions) < 1:
                return {
                    'stability': 0.5,
                    'betti': [0, 0, 0],
                    'interpretation': '边界不足，无法进行拓扑分析'
                }
            
            # 分析
            bridge = BoundaryTopologyBridge()
            canvas_size = (canvas.get('width', 800), canvas.get('height', 600))
            result = bridge.analyze_boundary_system(regions, canvas_size)
            
            return {
                'stability': result.topology_stability,
                'betti': [result.betti_0, result.betti_1, result.betti_2],
                'interpretation': result.interpretation
            }
        except Exception as e:
            return {
                'stability': 0.5,
                'betti': [0, 0, 0],
                'interpretation': f'拓扑分析不可用: {str(e)[:50]}'
            }
    
    def compute_simple(self, data: dict) -> dict:
        """简化计算（降级用）"""
        return {'status': 'simple', 'boundaries': data.get('boundaries', [])}
    
    def render_cpu(self, result: dict) -> dict:
        """CPU渲染（降级用）"""
        return result
    



    def score_from_features(self, features: dict) -> dict:
        arr = features.get('arr')
        if arr is None:
            return {'score': 0.5, 'method': 'fallback', 'details': {}}
        if not _HAS_VERIFY_BOUNDARY:
            return {'score': 0.5, 'method': 'fallback', 'details': {'reason': 'axiom_verifier not available'}}
        result = _verify_boundary_fn(arr)
        return {'score': float(result.get('score', 0.5)), 'method': 'verify_boundary', 'source': 'wudao_core_phase2'}
    def info(self) -> dict:
        """获取公理信息"""
        return {
            'name': self.name,
            'gpu_shader': self.gpu_shader,
            'fallback_method': self.fallback_method
        }
