# -*- coding: utf-8 -*-
"""
core/risk.py — 风险管理模块

数之法则·法三：风控体系

核心：
- 仓位管理
- 止损计算
- 盈亏比
"""

class RiskManager:
    """风险管理器"""

    def __init__(self, total_capital: float, max_position: float = 0.2):
        """
        参数：
        - total_capital: 总资金
        - max_position: 单只股票最大仓位（默认20%）
        """
        self.capital = total_capital
        self.max_position = max_position

    def position_size(self, price: float, stop_loss_pct: float = 0.05) -> dict:
        """
        计算仓位
        
        参数：
        - price: 买入价格
        - stop_loss_pct: 止损比例
        
        返回：{'shares': 股数, 'cost': 成本, 'stop_loss': 止损价}
        """
        max_shares_value = self.capital * self.max_position
        shares = int(max_shares_value / price / 100) * 100  # 取整百股
        cost = shares * price
        stop_loss = price * (1 - stop_loss_pct)
        
        return {
            'shares': shares,
            'cost': cost,
            'stop_loss': stop_loss,
            'risk_per_trade': cost * stop_loss_pct,
        }

    def risk_reward_ratio(self, entry: float, target: float, stop: float) -> float:
        """
        计算盈亏比
        
        参数：
        - entry: 入场价
        - target: 目标价
        - stop: 止损价
        """
        risk = abs(entry - stop)
        reward = abs(target - entry)
        return reward / risk if risk > 0 else 0

    def position_adjust(self, current_price: float, entry: float, 
                       stop_loss_pct: float, trail_pct: float = 0.02) -> dict:
        """
        动态调整止损（追踪止损）
        
        参数：
        - current_price: 当前价格
        - entry: 入场价
        - stop_loss_pct: 初始止损比例
        - trail_pct: 追踪止损比例
        """
        profit_pct = (current_price - entry) / entry
        
        if profit_pct < 0:
            # 亏损期，使用固定止损
            stop = entry * (1 - stop_loss_pct)
        else:
            # 盈利期，追踪止损
            highest_since_entry = entry * (1 + trail_pct * 2)  # 简化
            stop = current_price * (1 - trail_pct)
        
        return {
            'stop_loss': stop,
            'profit_pct': profit_pct * 100,
            'action': '止损' if current_price < stop else '持有'
        }


class Backtester:
    """回测引擎"""

    def __init__(self, initial_capital: float = 100000):
        self.capital = initial_capital
        self.initial = initial_capital
        self.trades = []
        self.equity_curve = [initial_capital]

    def add_trade(self, entry_price: float, exit_price: float, 
                  shares: int, direction: str = 'long'):
        """
        添加一笔交易记录
        
        参数：
        - entry_price: 入场价
        - exit_price: 出场价
        - shares: 股数
        - direction: 方向（long=做多, short=做空）
        """
        if direction == 'long':
            pnl = (exit_price - entry_price) * shares
        else:
            pnl = (entry_price - exit_price) * shares
        
        self.capital += pnl
        self.trades.append({
            'entry': entry_price,
            'exit': exit_price,
            'shares': shares,
            'pnl': pnl,
            'direction': direction,
        })
        self.equity_curve.append(self.capital)

    def summary(self) -> dict:
        """回测统计"""
        if not self.trades:
            return {}
        
        pnls = [t['pnl'] for t in self.trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        total_return = (self.capital - self.initial) / self.initial * 100
        max_drawdown = min(
            (self.initial - min(eq)) / self.initial * 100
            for eq in self.equity_curve
        )
        
        return {
            'total_return': f"{total_return:.2f}%",
            'total_trades': len(self.trades),
            'win_rate': f"{len(wins)/len(pnls)*100:.1f}%",
            'avg_win': f"{sum(wins)/len(wins):.2f}" if wins else 0,
            'avg_loss': f"{sum(losses)/len(losses):.2f}" if losses else 0,
            'max_drawdown': f"{max_drawdown:.2f}%",
            'final_capital': f"{self.capital:.2f}",
        }


# ==============================================
# 验证
# ==============================================
def verify_risk():
    """验证风险管理"""
    rm = RiskManager(total_capital=100000, max_position=0.2)
    
    print("=" * 50)
    print("风险管理验证")
    print("=" * 50)
    
    pos = rm.position_size(price=100, stop_loss_pct=0.05)
    print(f"买入价: 100")
    print(f"股数: {pos['shares']}")
    print(f"成本: {pos['cost']:.2f}")
    print(f"止损价: {pos['stop_loss']:.2f}")
    print(f"单笔风险: {pos['risk_per_trade']:.2f}")
    
    rr = rm.risk_reward_ratio(entry=100, target=110, stop=95)
    print(f"\n盈亏比(目标110,止损95): {rr:.2f}")
    
    # 回测
    bt = Backtester(initial_capital=100000)
    bt.add_trade(100, 105, 200)  # 赚
    bt.add_trade(105, 102, 200)  # 亏
    bt.add_trade(102, 112, 200)   # 赚
    
    summary = bt.summary()
    print("\n" + "=" * 50)
    print("回测统计")
    print("=" * 50)
    for k, v in summary.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    verify_risk()
