"""Download and validate Upbit candle data without side effects on import."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
UPBIT_URL = "https://api.upbit.com/v1/candles/minutes/{unit}"


def fetch_candles(market: str = "KRW-BTC", unit: int = 60, count: int = 10_000, pause: float = 0.15) -> pd.DataFrame:
    """Fetch up to ``count`` candles, retrying transient HTTP failures."""
    if not 1 <= unit <= 240 or not 1 <= count:
        raise ValueError("unit must be 1..240 and count must be positive")
    session = requests.Session()
    rows: list[dict] = []
    cursor: str | None = None
    while len(rows) < count:
        params = {"market": market, "count": min(200, count - len(rows))}
        if cursor:
            params["to"] = cursor
        response = None
        for attempt in range(3):
            try:
                response = session.get(UPBIT_URL.format(unit=unit), params=params, timeout=15)
                response.raise_for_status()
                break
            except requests.RequestException:
                if attempt == 2:
                    raise
                time.sleep(2**attempt)
        batch = response.json() if response is not None else []
        if not batch:
            break
        rows.extend(batch)
        cursor = batch[-1]["candle_date_time_utc"]
        time.sleep(pause)
    data = pd.DataFrame(rows).rename(columns={
        "candle_date_time_utc": "timestamp", "opening_price": "open", "high_price": "high",
        "low_price": "low", "trade_price": "close", "candle_acc_trade_volume": "volume",
    })
    columns = ["timestamp", "open", "high", "low", "close", "volume"]
    if data.empty:
        return pd.DataFrame(columns=columns)
    data = data[columns].drop_duplicates("timestamp").sort_values("timestamp").tail(count).reset_index(drop=True)
    return data


def _main() -> None:
    parser = argparse.ArgumentParser(description="Download Upbit OHLCV candles.")
    parser.add_argument("--market", default="KRW-BTC")
    parser.add_argument("--unit", type=int, default=60)
    parser.add_argument("--count", type=int, default=10_000)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "btc_1h.csv")
    args = parser.parse_args()
    candles = fetch_candles(args.market, args.unit, args.count)
    if candles.empty:
        raise RuntimeError("Upbit returned no candle data")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    candles.to_csv(args.output, index=False)
    print(f"Saved {len(candles):,} candles to {args.output}")
    print(f"Range: {candles.timestamp.iloc[0]} to {candles.timestamp.iloc[-1]}")


if __name__ == "__main__":
    _main()
