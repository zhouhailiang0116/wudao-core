# -*- coding: utf-8 -*-
"""
AgentCore - 七公理统一核心

职责：
- 注册公理模块
- 中央状态管理
- 统一调度执行
- 错误处理fallback
"""

from .agent_core import AgentCore
from .state_manager import StateManager
from .memory_system import MemorySystem
from .error_handler import ErrorHandler
from .axiom_loader import AxiomLoader

__all__ = [
    'AgentCore',
    'StateManager', 
    'MemorySystem',
    'ErrorHandler',
    'AxiomLoader'
]

__version__ = '1.0.0'
