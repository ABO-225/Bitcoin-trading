"""Indicators and signals for the moving-average crossover strategy."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class StrategyConfig:
    fast_window: int = 20
    slow_window: int = 50
    trend_window: int = 200
    rsi_window: int = 14
    rsi_entry: float = 50.0
    use_trend_filter: bool = False


def add_indicators(frame: pd.DataFrame, config: StrategyConfig) -> pd.DataFrame:
    """Return a validated copy with MA and Wilder RSI columns."""
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    if min(config.fast_window, config.slow_window, config.trend_window, config.rsi_window) < 1:
        raise ValueError("Indicator windows must be positive")

    data = frame.copy().sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="raise")
    for column in ("open", "high", "low", "close", "volume"):
        data[column] = pd.to_numeric(data[column], errors="raise")
    if (data[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("OHLC prices must be positive")

    data["ma_fast"] = data["close"].rolling(config.fast_window, min_periods=config.fast_window).mean()
    data["ma_slow"] = data["close"].rolling(config.slow_window, min_periods=config.slow_window).mean()
    data["ma_trend"] = data["close"].rolling(config.trend_window, min_periods=config.trend_window).mean()
    delta = data["close"].diff()
    gains, losses = delta.clip(lower=0), -delta.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / config.rsi_window, min_periods=config.rsi_window, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / config.rsi_window, min_periods=config.rsi_window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    data["rsi"] = (100 - 100 / (1 + rs)).where(avg_loss != 0, 100.0)
    return data


def generate_signals(frame: pd.DataFrame, config: StrategyConfig) -> pd.DataFrame:
    """Add signal: 1 entry, -1 exit, 0 otherwise; execute at next candle open."""
    data = add_indicators(frame, config)
    crossed_up = (data["ma_fast"].shift(1) <= data["ma_slow"].shift(1)) & (data["ma_fast"] > data["ma_slow"])
    crossed_down = (data["ma_fast"].shift(1) >= data["ma_slow"].shift(1)) & (data["ma_fast"] < data["ma_slow"])
    buy = crossed_up & (data["rsi"] >= config.rsi_entry)
    if config.use_trend_filter:
        buy &= data["ma_slow"] > data["ma_trend"]
    data["signal"] = 0
    data.loc[buy, "signal"] = 1
    data.loc[crossed_down, "signal"] = -1
    return data
