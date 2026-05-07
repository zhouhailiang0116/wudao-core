# -*- coding: utf-8 -*-
"""
StateManager - 中央状态管理
"""

from typing import Dict, Any, Optional
from datetime import datetime
import copy


class StateManager:
    """
    中央状态管理
    
    管理维度：
    - 位置（空间）
    - 时间（叙事）
    - 数据（量化）
    - 约束（边界）
    """
    
    def __init__(self):
        # 空间状态
        self.space = {
            'x': 0,
            'y': 0,
            'z': 0,
            'depth': 0,
            'width': 800,
            'height': 600
        }
        
        # 时间状态
        self.time = {
            't': 0,
            'I_t': 0,  # 信息密度
            'R_t': 0,  # 节奏谱
            'fps': 60,
            'frame': 0
        }
        
        # 数据状态
        self.data = {
            'price': 0,
            'volume': 0,
            'ma5': 0,
            'ma20': 0,
            'macd': 0
        }
        
        # 约束状态
        self.constraints = {
            'must': [],
            'cannot': [],
            'can': []
        }
        
        # 自由状态
        self.free = {}
        
        # 历史记录
        self.history: list = []
        self.max_history = 100
    
    def update(self, key: str, value: Any, namespace: str = None) -> None:
        """
        更新状态
        
        Args:
            key: 状态键
            value: 状态值
            namespace: 命名空间（space/time/data/constraints/free）
        """
        if namespace == 'space':
            if key in self.space:
                self.space[key] = value
            else:
                self.free[key] = value
        elif namespace == 'time':
            if key in self.time:
                self.time[key] = value
            else:
                self.free[key] = value
        elif namespace == 'data':
            if key in self.data:
                self.data[key] = value
            else:
                self.free[key] = value
        elif namespace == 'constraints':
            if key in self.constraints:
                self.constraints[key] = value
            else:
                self.free[key] = value
        else:
            # 自动判断
            if key in self.space:
                self.space[key] = value
            elif key in self.time:
                self.time[key] = value
            elif key in self.data:
                self.data[key] = value
            elif key in self.constraints:
                self.constraints[key] = value
            else:
                self.free[key] = value
        
        # 记录历史
        self._add_history()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取状态"""
        if key in self.space:
            return self.space[key]
        elif key in self.time:
            return self.time[key]
        elif key in self.data:
            return self.data[key]
        elif key in self.constraints:
            return self.constraints[key]
        else:
            return self.free.get(key, default)
    
    def snapshot(self) -> Dict[str, Any]:
        """生成状态快照（用于记忆同步）"""
        return {
            'space': copy.deepcopy(self.space),
            'time': copy.deepcopy(self.time),
            'data': copy.deepcopy(self.data),
            'constraints': copy.deepcopy(self.constraints),
            'free': copy.deepcopy(self.free),
            'timestamp': datetime.now().isoformat()
        }
    
    def restore(self, snapshot: Dict[str, Any]) -> None:
        """从快照恢复状态"""
        self.space = copy.deepcopy(snapshot.get('space', self.space))
        self.time = copy.deepcopy(snapshot.get('time', self.time))
        self.data = copy.deepcopy(snapshot.get('data', self.data))
        self.constraints = copy.deepcopy(snapshot.get('constraints', self.constraints))
        self.free = copy.deepcopy(snapshot.get('free', self.free))
    
    def _add_history(self) -> None:
        """添加历史记录"""
        if len(self.history) >= self.max_history:
            self.history.pop(0)
        self.history.append(self.snapshot())
    
    def undo(self, steps: int = 1) -> bool:
        """撤销状态"""
        if len(self.history) >= steps:
            snapshot = self.history[-steps]
            self.restore(snapshot)
            return True
        return False
    
    def reset(self) -> None:
        """重置状态"""
        self.space = {
            'x': 0, 'y': 0, 'z': 0, 'depth': 0,
            'width': 800, 'height': 600
        }
        self.time = {
            't': 0, 'I_t': 0, 'R_t': 0,
            'fps': 60, 'frame': 0
        }
        self.data = {
            'price': 0, 'volume': 0,
            'ma5': 0, 'ma20': 0, 'macd': 0
        }
        self.constraints = {
            'must': [], 'cannot': [], 'can': []
        }
        self.free = {}
        self.history = []
