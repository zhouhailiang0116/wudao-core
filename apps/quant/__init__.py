# -*- coding: utf-8 -*-
"""
wudao-core/apps/quant/
=======================
【迁移来源】wukong/wukong_quant/
【迁移日期】2026-04-08
【迁移原因】量化是业务层应用，非视觉法则核心，移入 wudao-core/apps/

内容：
- core/indicators.py   — 技术指标（MACD/RSI/KDJ/布林带）
- core/risk.py         — 风控模块（仓位/止损/回撤）
- teaching.md          — 量化学法
"""

from .core.indicators import *
from .core.risk import *
