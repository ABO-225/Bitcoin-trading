"""Walk-forward parameter selection for the strategy."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

try:
    from .backtest import DEFAULT_DATA, run_backtest
    from .strategy import StrategyConfig
except ImportError:
    from backtest import DEFAULT_DATA, run_backtest
    from strategy import StrategyConfig


def walk_forward(frame: pd.DataFrame, train_size: int = 3_000, test_size: int = 500, rsi_values: tuple[int, ...] = (40, 45, 50, 55, 60), trend_filter: bool = True) -> pd.DataFrame:
    """Select RSI on each training window and report unseen test performance."""
    if train_size < 2 or test_size < 2 or len(frame) < train_size + test_size:
        raise ValueError("Not enough rows for one train/test window")
    results: list[dict[str, float | int | str]] = []
    for number, start in enumerate(range(0, len(frame) - train_size - test_size + 1, test_size), start=1):
        train = frame.iloc[start : start + train_size]
        test_start = start + train_size
        # Include prior candles so test indicators have their real historical context.
        test_with_history = frame.iloc[max(0, test_start - 200) : test_start + test_size]
        selected_rsi, best_train_return = max(
            ((rsi, run_backtest(train, StrategyConfig(rsi_entry=rsi, use_trend_filter=trend_filter)).metrics["return_pct"]) for rsi in rsi_values),
            key=lambda item: item[1],
        )
        test_result = run_backtest(test_with_history, StrategyConfig(rsi_entry=selected_rsi, use_trend_filter=trend_filter))
        # Only report test-period return: equity at its first actual test candle vs final equity.
        curve = test_result.equity_curve.iloc[-test_size:]
        test_return = (curve.equity.iloc[-1] / curve.equity.iloc[0] - 1) * 100
        buy_hold = (curve.close.iloc[-1] / curve.close.iloc[0] - 1) * 100
        results.append({"round": number, "selected_rsi": selected_rsi, "train_return_pct": best_train_return,
                        "test_return_pct": test_return, "test_buy_hold_pct": buy_hold,
                        "test_max_drawdown_pct": curve.drawdown_pct.min()})
    return pd.DataFrame(results)


def _main() -> None:
    parser = argparse.ArgumentParser(description="Run walk-forward RSI selection.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--train-size", type=int, default=3_000)
    parser.add_argument("--test-size", type=int, default=500)
    parser.add_argument("--no-trend-filter", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    result = walk_forward(pd.read_csv(args.data), args.train_size, args.test_size, trend_filter=not args.no_trend_filter)
    print(result.to_string(index=False, float_format=lambda value: f"{value:.2f}"))
    print(f"\nAverage test return: {result.test_return_pct.mean():.2f}%")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(args.output, index=False)


if __name__ == "__main__":
    _main()
