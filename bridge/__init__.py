# -*- coding: utf-8 -*-
"""
bridge

道层 → 悟空层 翻译桥接
公理结论 → 法则参数
"""

from .axiom_to_law import translate, _get_fusion_weights, _modulate, list_mappings

__all__ = ['translate', '_get_fusion_weights', '_modulate', 'list_mappings']
