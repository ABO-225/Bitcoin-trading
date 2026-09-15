import unittest

import pandas as pd

from src.backtest import BacktestConfig, run_backtest
from src.strategy import StrategyConfig, add_indicators, generate_signals


def candles(closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=len(closes), freq="h", tz="UTC"),
        "open": closes, "high": closes, "low": closes, "close": closes, "volume": [1.0] * len(closes),
    })


class StrategyTests(unittest.TestCase):
    def test_indicator_input_is_not_mutated(self) -> None:
        raw = candles([100, 99, 98, 99, 101, 102])
        result = add_indicators(raw, StrategyConfig(fast_window=2, slow_window=3, trend_window=4, rsi_window=2))
        self.assertNotIn("ma_fast", raw.columns)
        self.assertIn("rsi", result.columns)

    def test_entry_signal_is_filled_on_following_open(self) -> None:
        raw = candles([100, 100, 99, 101, 103, 104])
        raw.loc[4, "open"] = 110  # The fill must use this next-bar price, not the prior close.
        strategy = StrategyConfig(fast_window=2, slow_window=3, trend_window=3, rsi_window=2, rsi_entry=0)
        signals = generate_signals(raw, strategy)
        result = run_backtest(raw, strategy, BacktestConfig(initial_cash=1_000, fee_rate=0))
        if (signals.signal == 1).any():
            first_signal = signals.index[signals.signal == 1][0]
            self.assertEqual(result.trades.iloc[0].timestamp, signals.iloc[first_signal + 1].timestamp)
            self.assertEqual(result.trades.iloc[0].price, raw.iloc[first_signal + 1].open)


if __name__ == "__main__":
    unittest.main()
