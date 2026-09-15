"""Long-only, all-in backtester with realistic next-open fills."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

try:
    from .strategy import StrategyConfig, generate_signals
except ImportError:  # Supports `python src/backtest.py`.
    from strategy import StrategyConfig, generate_signals

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "btc_1h.csv"


@dataclass(frozen=True)
class BacktestConfig:
    initial_cash: float = 10_000_000
    fee_rate: float = 0.0005


@dataclass
class BacktestResult:
    metrics: dict[str, float | int]
    equity_curve: pd.DataFrame
    trades: pd.DataFrame


def run_backtest(frame: pd.DataFrame, strategy: StrategyConfig = StrategyConfig(), config: BacktestConfig = BacktestConfig()) -> BacktestResult:
    if config.initial_cash <= 0 or not 0 <= config.fee_rate < 1:
        raise ValueError("initial_cash must be positive and fee_rate must be in [0, 1)")
    data = generate_signals(frame, strategy)
    if len(data) < 2:
        raise ValueError("At least two candles are required")
    cash, units, entry_cost, pending_signal = config.initial_cash, 0.0, None, 0
    trades: list[dict[str, object]] = []
    equity, positions = [], []
    for i, row in data.iterrows():
        if i and pending_signal == 1 and cash > 0:
            units = cash * (1 - config.fee_rate) / row["open"]
            entry_cost, cash = cash, 0.0
            trades.append({"timestamp": row["timestamp"], "side": "BUY", "price": row["open"], "units": units, "net_return_pct": None})
        elif i and pending_signal == -1 and units > 0:
            proceeds = units * row["open"] * (1 - config.fee_rate)
            net_return = ((proceeds / entry_cost) - 1) * 100 if entry_cost else None
            trades.append({"timestamp": row["timestamp"], "side": "SELL", "price": row["open"], "units": units, "net_return_pct": net_return})
            cash, units, entry_cost = proceeds, 0.0, None
        pending_signal = int(row["signal"])
        equity.append(cash + units * row["close"])
        positions.append(units)
    curve = data[["timestamp", "close", "signal"]].copy()
    curve["equity"], curve["position_units"] = equity, positions
    curve["drawdown_pct"] = (curve["equity"] / curve["equity"].cummax() - 1) * 100
    trades_df = pd.DataFrame(trades, columns=["timestamp", "side", "price", "units", "net_return_pct"])
    closed = trades_df.loc[trades_df["side"] == "SELL", "net_return_pct"].dropna()
    metrics: dict[str, float | int] = {
        "initial_cash": config.initial_cash, "final_equity": float(curve["equity"].iloc[-1]),
        "return_pct": float((curve["equity"].iloc[-1] / config.initial_cash - 1) * 100),
        "buy_hold_return_pct": float((data["close"].iloc[-1] / data["close"].iloc[0] - 1) * 100),
        "max_drawdown_pct": float(curve["drawdown_pct"].min()), "orders": len(trades_df),
        "closed_trades": len(closed), "win_rate_pct": float((closed > 0).mean() * 100) if len(closed) else 0.0,
    }
    return BacktestResult(metrics, curve, trades_df)


def _main() -> None:
    parser = argparse.ArgumentParser(description="Run a BTC/KRW moving-average backtest.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--rsi-entry", type=float, default=50)
    parser.add_argument("--trend-filter", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    result = run_backtest(pd.read_csv(args.data), StrategyConfig(rsi_entry=args.rsi_entry, use_trend_filter=args.trend_filter))
    print(pd.Series(result.metrics).to_string())
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        result.equity_curve.to_csv(args.output_dir / "equity_curve.csv", index=False)
        result.trades.to_csv(args.output_dir / "trades.csv", index=False)


if __name__ == "__main__":
    _main()
