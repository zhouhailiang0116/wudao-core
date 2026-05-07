# -*- coding: utf-8 -*-
"""
ErrorHandler - 统一错误处理
"""

from typing import Any, Dict, Optional
import traceback


class ValidationError(Exception):
    """数据不符合公理约束"""
    pass


class ComputeError(Exception):
    """计算过程出错"""
    pass


class RenderError(Exception):
    """渲染过程出错"""
    pass


class ErrorHandler:
    """
    统一错误处理
    
    策略：
    - ValidationError: 返回默认值
    - ComputeError: 降级计算
    - RenderError: CPU fallback
    - 其他异常: 记录日志，返回None
    """
    
    def __init__(self):
        self.error_log = []
        self.max_log_size = 100
    
    def fallback(self, error: Exception, task: Any, axioms: Dict[str, Any]) -> Optional[Any]:
        """
        错误降级处理
        
        Args:
            error: 捕获的异常
            task: 任务对象
            axioms: 公理注册表
        
        Returns:
            降级后的结果，或None
        """
        # 记录错误
        self._log_error(error, task)
        
        # 根据异常类型处理
        if isinstance(error, ValidationError):
            return self._default_value(task)
        
        elif isinstance(error, ComputeError):
            return self._degraded_compute(task, axioms)
        
        elif isinstance(error, RenderError):
            return self._cpu_fallback(task, axioms)
        
        else:
            # 未知异常
            print(f"[ErrorHandler] Unknown error: {type(error).__name__}: {error}")
            return self._default_value(task)
    
    def _log_error(self, error: Exception, task: Any) -> None:
        """记录错误日志"""
        from datetime import datetime
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'task': str(task)[:200] if task else None,
            'traceback': traceback.format_exc()
        }
        
        if len(self.error_log) >= self.max_log_size:
            self.error_log.pop(0)
        
        self.error_log.append(entry)
        
        # 打印简短信息
        print(f"[ErrorHandler] {entry['error_type']}: {entry['error_message'][:100]}")
    
    def _default_value(self, task: Any) -> Dict[str, Any]:
        """返回安全默认值"""
        return {
            'status': 'fallback',
            'reason': 'validation_failed',
            'task': str(task)[:100] if task else None
        }
    
    def _degraded_compute(self, task: Any, axioms: Dict[str, Any]) -> Optional[Any]:
        """降级计算（简化算法）"""
        print(f"[ErrorHandler] Attempting degraded compute...")
        
        # task 可能是 dict 或对象，统一用 .get() 兼容两种情况
        axiom_name = (
            task.get('axiom') if isinstance(task, dict)
            else getattr(task, 'axiom', None)
        )
        task_data = (
            task.get('data', task) if isinstance(task, dict)
            else getattr(task, 'data', task)
        )

        if axiom_name and axiom_name in axioms:
            axiom = axioms[axiom_name]
            if hasattr(axiom, 'compute_simple'):
                try:
                    return axiom.compute_simple(task_data)
                except Exception as e:
                    print(f"[ErrorHandler] Degraded compute also failed: {e}")
        
        return self._default_value(task)
    
    def _cpu_fallback(self, task: Any, axioms: Dict[str, Any]) -> Optional[Any]:
        """CPU降级渲染"""
        print(f"[ErrorHandler] Attempting CPU fallback...")
        
        # task 可能是 dict 或对象，统一用 .get() 兼容两种情况
        axiom_name = (
            task.get('axiom') if isinstance(task, dict)
            else getattr(task, 'axiom', None)
        )
        task_result = (
            task.get('result') if isinstance(task, dict)
            else getattr(task, 'result', None)
        )

        if axiom_name and axiom_name in axioms:
            axiom = axioms[axiom_name]
            if hasattr(axiom, 'render_cpu'):
                try:
                    return axiom.render_cpu(task_result)
                except Exception as e:
                    print(f"[ErrorHandler] CPU fallback also failed: {e}")
        
        return self._default_value(task)
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """获取最近的错误"""
        return self.error_log[-limit:]
    
    def clear_log(self) -> None:
        """清空错误日志"""
        self.error_log = []
        print("[ErrorHandler] Log cleared")
