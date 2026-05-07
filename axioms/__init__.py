# -*- coding: utf-8 -*-
"""
Axioms - 公理模块包（wudao-core 道层）
========================================

当前状态（2026-04-09）：
  ✅ axiom1_growth     — 生长公理（内容节奏：慢起→爆发→收敛）
  ✅ axiom2_light      — 光照公理（光源位置/色温/强度/阴影）
  ✅ axiom3_color      — 色彩公理（配色方案：情绪→调色板）
  ✅ axiom4_layout     — 布局公理（PHI=1.618 / 三分焦点 / 视觉重心）
  ✅ axiom5_narrative  — 叙事公理（Hook→Body→CTA）
  ✅ axiom6_boundary   — 边界公理（MUST/CANNOT/CAN 三色约束）
  ✅ axiom7_freedom    — 自由公理（override_mask / intensity）
  ✅ axiom8_causal     — 因果公理（BFS因果链 / 置换检验）

  整体完成度：100% (8/8) ✅

关于 axiom1/3：
  wukong_constraints/axioms/axiomN_xxx.py 是"设计验证脚本"（裁判，事后PASS/FAIL），
  wudao-core 需要的是"AI 决策约束"（教练，事前算规则），两者语义不同。
  axiom1/3 应重新设计，不是从 wukong_constraints 升级。
"""

from .axiom_base import AxiomBase
from .axiom1_growth import GrowthAxiom
from .axiom2_light import LightAxiom
from .axiom3_color import ColorAxiom
from .axiom4_layout import LayoutAxiom
from .axiom5_narrative import NarrativeAxiom
from .axiom6_boundary import BoundaryAxiom
from .axiom7_freedom import FreedomAxiom
from .axiom8_causal import CausalAxiom

__all__ = [
    'AxiomBase',
    'GrowthAxiom',
    'LightAxiom',
    'ColorAxiom',
    'LayoutAxiom',
    'NarrativeAxiom',
    'BoundaryAxiom',
    'FreedomAxiom',
    'CausalAxiom',
]
