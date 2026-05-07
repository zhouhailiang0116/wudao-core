# wukong-quant — 数之法则（量化）

> 数字是宇宙的语言。

---

## 定位

金融量化分析：股票数据、风险评估、指标计算。

---

## 核心模块

| 模块 | 文件 | 内容 |
|------|------|------|
| indicators | indicators.py | 均线/布林带/RSI/MACD |
| risk | risk.py | 风险管理/仓位计算 |

---

## 调用方式

```python
import sys
sys.path.insert(0, r'C:\Users\周海亮\.qclaw\workspace\wukong\wukong-quant')

from core.indicators import sma, ema, bollinger_bands
from core.risk import calculate_position_size

# 均线
ma5 = sma(prices, window=5)
ma20 = sma(prices, window=20)

# 布林带
bb = bollinger_bands(prices, window=20, num_std=2)
```

---

## 与其他法则联动

| 法则 | 联动方式 |
|------|---------|
| wukong-math | probability（蒙特卡洛风险模拟） |
| wukong-video | 量化数据可视化图表 |


---

## 数学依赖

本模块依赖 `wukong-math` 的以下能力：

- probability (蒙特卡洛风险)
- probability (moving_average均线)

```python
import sys
sys.path.insert(0, r'C:\Users\周海亮\.qclaw\workspace\wukong\wukong-math')
from core import Vec2, lerp, perlin_noise_1d  # 按需导入
```
