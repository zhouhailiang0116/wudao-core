# -*- coding: utf-8 -*-
"""
AxiomBase - 公理基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AxiomBase(ABC):
    """
    公理基类
    
    所有公理模块必须实现以下接口：
    - validate: 验证数据是否符合公理约束
    - compute: 执行公理计算
    - render: 渲染计算结果
    - execute: 统一执行入口（已实现）
    """
    
    def __init__(self, 
                 name: str,
                 gpu_shader: Optional[str] = None,
                 fallback_method: Optional[str] = None):
        self.name = name
        self.gpu_shader = gpu_shader
        self.fallback_method = fallback_method
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """
        验证数据是否符合公理约束
        
        Args:
            data: 输入数据
        
        Returns:
            是否符合约束
        """
        pass
    
    @abstractmethod
    def compute(self, data: Any, state: Any) -> Any:
        """
        执行公理计算
        
        Args:
            data: 输入数据
            state: 当前状态
        
        Returns:
            计算结果
        """
        pass
    
    @abstractmethod
    def render(self, result: Any) -> Any:
        """
        渲染计算结果
        
        Args:
            result: 计算结果
        
        Returns:
            渲染输出
        """
        pass
    
    def execute(self, task: Any, state: Any) -> Any:
        """
        统一执行入口
        
        流程：
        1. 验证数据
        2. 执行计算
        3. 渲染结果
        4. 悟道定理注入（哲学层）
        
        Args:
            task: 任务对象
            state: 当前状态
        
        Returns:
            最终输出（包含悟道定理状态）
        """
        # 提取数据
        data = task.data if hasattr(task, 'data') else task
        
        # 1. 验证
        if not self.validate(data):
            from .error_handler import ValidationError
            raise ValidationError(f"[{self.name}] Data validation failed")
        
        # 2. 计算
        result = self.compute(data, state)
        
        # 3. 渲染
        output = self.render(result)
        
        # 4. 悟道定理注入 —— 让每个智能体在使用中发现
        output['_wudao_theorem'] = self._wudao_theorem_state(result, data, state)
        
        return output
    
    # ── 悟道定理阈值（来自实践数据，待标定）────────────────────────────
    # 这些阈值是悟道体系运行中沉淀出来的经验值，非理论推导。
    # 理想情况应通过因果公理（axiom8）从大量场景中自动标定。
    # TODO: axiom8 因果链路打通后，改由 data-driven 校准
    WUDAO_DANCE_THRESHOLD = 0.30   # freedom_gap < 30% → 起舞
    WUDAO_EXPLORE_THRESHOLD = 0.60  # freedom_gap < 60% → 探索

    def _wudao_theorem_state(self, result: Any, data: Any, state: Any) -> dict:
        """
        悟道定理哲学层注入
        
        设计原则：
        - 不强制灌输，让使用者在结果中发现
        - 约束是镣铐，自由撞上约束的那一刻，镣铐才有了重量
        - 作坊就发生在最窄的缝里
        
        数学映射：
        - 边界公理（axiom6）计算 must/cannot/can 的分布
        - 自由公理（axiom7）计算 freedom_space × intensity
        - 两者相遇时，悟道定理自然浮现
        
        阈值说明：
        - WUDAO_DANCE_THRESHOLD=0.30: 经验值。freedom_gap<30% 时约束密度高+缝隙窄，
          创作者开始感受到"极窄空间内的极限操作"，此为起舞状态。
        - WUDAO_EXPLORE_THRESHOLD=0.60: 经验值。freedom_gap<60% 时约束仍然明显，
          但有足够空间试探，定义为探索状态。
        """
        # 默认状态：悟道定理未触发
        theorem = {
            'active': False,
            'theorem_id': None,
            'message': '',
            'freedom_gap': None,        # CAN / (MUST + CANNOT + CAN)
            'constraint_density': None,  # (MUST + CANNOT) / Total
            'dance_space': None,         # 最窄缝隙宽度
            'level': 'idle',             # idle / touching / dancing / exploring / free
        }
        
        try:
            # 尝试提取悟道定理相关数据
            must_count = result.get('must_count', 0) if isinstance(result, dict) else 0
            cannot_count = result.get('cannot_count', 0) if isinstance(result, dict) else 0
            can_count = result.get('can_count', 0) if isinstance(result, dict) else 0
            # actual_freedom 来自 axiom7：freedom_space × intensity（备用）
            
            total = must_count + cannot_count + can_count
            
            if total > 0:
                constraint_density = (must_count + cannot_count) / total
                freedom_gap = can_count / total
                
                # 悟道定理核心：起舞空间
                # 约束越重，缝隙越窄，悟道越深
                # 但如果缝隙为0，说明撞墙了
                
                if constraint_density == 0:
                    level = 'idle'
                    message = '无约束，自由无边，悟道未始'
                elif freedom_gap == 0:
                    level = 'touching'
                    message = '撞墙了。约束是镣铐，自由撞上约束的那一刻，镣铐才有了重量。'
                    theorem['active'] = True
                    theorem['theorem_id'] = 'theorem_1_touch'
                elif freedom_gap < self.WUDAO_DANCE_THRESHOLD:
                    level = 'dancing'
                    message = f'起舞。最窄的缝里有最深的悟道。（自由度 {freedom_gap:.1%}）'
                    theorem['active'] = True
                    theorem['theorem_id'] = 'theorem_2_dance'
                elif freedom_gap < self.WUDAO_EXPLORE_THRESHOLD:
                    level = 'exploring'
                    message = f'探索。约束是地图，不是监狱。（自由度 {freedom_gap:.1%}）'
                    theorem['active'] = True
                    theorem['theorem_id'] = 'theorem_3_explore'
                else:
                    level = 'free'
                    message = f'自由充沛，但无约束可悟。（自由度 {freedom_gap:.1%}）'
                    theorem['theorem_id'] = 'theorem_0_free'
                
                theorem['freedom_gap'] = freedom_gap
                theorem['constraint_density'] = constraint_density
                theorem['dance_space'] = min(freedom_gap, constraint_density)  # 最窄缝隙
                theorem['level'] = level
                theorem['message'] = message
                
        except Exception:
            pass
        
        return theorem
    
    def compute_simple(self, data: Any, state: Any = None) -> Any:
        """
        简化计算（用于降级）
        
        Args:
            data: 输入数据
            state: 当前状态
        
        Returns:
            简化计算结果
        """
        # 默认实现：返回原始数据
        return data
    
    def render_cpu(self, result: Any) -> Any:
        """
        CPU渲染（用于降级）
        
        Args:
            result: 计算结果
        
        Returns:
            CPU渲染输出
        """
        # 默认实现：返回结果本身
        return result
    
    def info(self) -> Dict[str, Any]:
        """获取公理信息"""
        return {
            'name': self.name,
            'gpu_shader': self.gpu_shader,
            'fallback_method': self.fallback_method,
            'class': self.__class__.__name__
        }
