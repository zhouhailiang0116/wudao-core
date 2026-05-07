# -*- coding: utf-8 -*-
"""
core/indicators.py — 技术指标模块

数之法则·法二：指标计算

核心：
- 趋势指标
- 动量指标
- 波动指标
- 量能指标
"""

import pandas as pd
import numpy as np


class TechnicalIndicators:
    """技术指标计算"""

    @staticmethod
    def SMA(closes: list, period: int) -> list:
        """简单移动平均"""
        return pd.Series(closes).rolling(period).mean().tolist()

    @staticmethod
    def EMA(closes: list, period: int) -> list:
        """指数移动平均"""
        return pd.Series(closes).ewm(span=period).mean().tolist()

    @staticmethod
    def MACD(closes: list, fast: int = 12, slow: int = 26, signal: int = 9):
        """
        MACD指标
        
        返回：(dif, dea, macd柱)
        """
        ema_fast = pd.Series(closes).ewm(span=fast).mean()
        ema_slow = pd.Series(closes).ewm(span=slow).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal).mean()
        macd = (dif - dea) * 2
        return dif.tolist(), dea.tolist(), macd.tolist()

    @staticmethod
    def RSI(closes: list, period: int = 14) -> list:
        """相对强弱指标"""
        deltas = pd.Series(closes).diff()
        gain = deltas.where(deltas > 0, 0).rolling(period).mean()
        loss = (-deltas.where(deltas < 0, 0)).rolling(period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.tolist()

    @staticmethod
    def BOLL(closes: list, period: int = 20, std_dev: int = 2):
        """
        布林带
        
        返回：(upper, middle, lower)
        """
        middle = pd.Series(closes).rolling(period).mean()
        std = pd.Series(closes).rolling(period).std()
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        return upper.tolist(), middle.tolist(), lower.tolist()


class SignalGenerator:
    """信号生成器"""

    @staticmethod
    def golden_cross(mas: list, mas_fast: list) -> list:
        """
        金叉信号：短期均线从下穿上长期均线
        
        返回：1=金叉, -1=死叉, 0=无信号
        """
        signals = []
        for i in range(1, len(mas)):
            if mas_fast[i] > mas[i] and mas_fast[i-1] <= mas[i-1]:
                signals.append(1)  # 金叉
            elif mas_fast[i] < mas[i] and mas_fast[i-1] >= mas[i-1]:
                signals.append(-1)  # 死叉
            else:
                signals.append(0)
        return [0] + signals  # 第一个无信号

    @staticmethod
    def macd_cross(dif: list, dea: list) -> list:
        """
        MACD金叉死叉
        
        返回：1=金叉, -1=死叉, 0=无信号
        """
        signals = []
        for i in range(1, len(dif)):
            if dif[i] > dea[i] and dif[i-1] <= dea[i-1]:
                signals.append(1)
            elif dif[i] < dea[i] and dif[i-1] >= dea[i-1]:
                signals.append(-1)
            else:
                signals.append(0)
        return [0] + signals


# ==============================================
# 验证
# ==============================================
def verify_indicators():
    """验证指标计算"""
    import baostock as bs
    
    bs.login()
    rs = bs.query_history_k_data_plus(
        'sh.600519',
        'date,code,open,high,low,close,volume',
        '2026-01-01', '2026-04-04'
    )
    
    closes = []
    while rs.error_code == '0' and rs.next():
        closes.append(float(rs.get_row_data()[6]))
    
    bs.logout()
    
    print("=" * 50)
    print("技术指标验证")
    print("=" * 50)
    print(f"数据点数: {len(closes)}")
    
    # MA5, MA20
    ma5 = TechnicalIndicators.SMA(closes, 5)
    ma20 = TechnicalIndicators.SMA(closes, 20)
    print(f"MA5最后值: {ma5[-1]:.2f}")
    print(f"MA20最后值: {ma20[-1]:.2f}")
    
    # MACD
    dif, dea, macd = TechnicalIndicators.MACD(closes)
    print(f"DIF最后值: {dif[-1]:.4f}")
    print(f"DEA最后值: {dea[-1]:.4f}")
    print(f"MACD柱最后值: {macd[-1]:.4f}")
    
    # RSI
    rsi = TechnicalIndicators.RSI(closes, 14)
    print(f"RSI(14)最后值: {rsi[-1]:.2f}")
    
    # 信号
    signals = SignalGenerator.golden_cross(ma20, ma5)
    last_signal = signals[-1]
    print(f"\nMA金叉信号: {'买入' if last_signal == 1 else '卖出' if last_signal == -1 else '观望'}")


if __name__ == "__main__":
    verify_indicators()
