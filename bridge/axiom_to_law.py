# -*- coding: utf-8 -*-
"""
wudao-core/bridge/axiom_to_law.py

道→通 翻译桥接代理。

实际实现位于：wukong/bridge/axiom_to_law.py
本文件通过 importlib 动态加载，绕过 wukong 非标准包结构问题。

两个 bridge 包同名共存：
  - wudao-core/bridge/  （道层·理论侧）
  - wukong/bridge/      （悟空层·执行侧）
"""

import os
import sys
import importlib.util

# 动态加载 wukong/bridge/axiom_to_law.py（用绝对路径，不依赖 wukong 包结构）
_BRIDGE_SRC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "wukong", "bridge", "axiom_to_law.py"
)

_spec = importlib.util.spec_from_file_location("wukong_bridge_axiom_to_law", _BRIDGE_SRC)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["wukong_bridge_axiom_to_law"] = _mod
_spec.loader.exec_module(_mod)

translate             = _mod.translate
translate_from_verifier = getattr(_mod, "translate_from_verifier", None)
_get_fusion_weights = _mod._get_fusion_weights
_modulate            = _mod._modulate
list_mappings        = getattr(_mod, "list_mappings", None)
AxiomOutput          = getattr(_mod, "AxiomOutput", None)

__all__ = [
    "translate",
    "translate_from_verifier",
    "_get_fusion_weights",
    "_modulate",
    "list_mappings",
    "AxiomOutput",
]
