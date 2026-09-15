"""Create a portable price/equity chart from a backtest."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

try:
    from .backtest import DEFAULT_DATA, run_backtest
except ImportError:
    from backtest import DEFAULT_DATA, run_backtest


def save_chart(frame: pd.DataFrame, output: Path) -> None:
    result = run_backtest(frame)
    curve = result.equity_curve
    fig, (price_ax, equity_ax) = plt.subplots(2, 1, figsize=(13, 8), sharex=True, layout="constrained")
    price_ax.plot(curve.timestamp, curve.close, label="BTC/KRW close", color="#2563eb", linewidth=1)
    buys, sells = curve[curve.signal == 1], curve[curve.signal == -1]
    price_ax.scatter(buys.timestamp, buys.close, marker="^", color="#16a34a", label="Buy signal")
    price_ax.scatter(sells.timestamp, sells.close, marker="v", color="#dc2626", label="Sell signal")
    price_ax.set_ylabel("KRW"); price_ax.legend(); price_ax.grid(alpha=.2)
    equity_ax.plot(curve.timestamp, curve.equity, label="Strategy equity", color="#7c3aed")
    equity_ax.set_ylabel("KRW"); equity_ax.set_xlabel("Time (UTC)"); equity_ax.legend(); equity_ax.grid(alpha=.2)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150); plt.close(fig)


def _main() -> None:
    parser = argparse.ArgumentParser(description="Save a BTC/KRW strategy chart.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=Path("output") / "backtest_chart.png")
    args = parser.parse_args()
    save_chart(pd.read_csv(args.data), args.output)
    print(f"Saved chart to {args.output}")


if __name__ == "__main__":
    _main()
