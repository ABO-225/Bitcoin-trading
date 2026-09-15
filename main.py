"""Convenience entry point for the trading research toolkit."""

from __future__ import annotations

import argparse

from src.backtest import _main as backtest_main
from src.chart import _main as chart_main
from src.data import _main as download_main
from src.optimizer import _main as optimize_main


def main() -> None:
    parser = argparse.ArgumentParser(description="BTC/KRW research toolkit")
    parser.add_argument("command", choices=("download", "backtest", "optimize", "chart"))
    args, remainder = parser.parse_known_args()
    # Each subcommand owns its own documented options; preserve them verbatim.
    import sys
    sys.argv = [f"main.py {args.command}", *remainder]
    {"download": download_main, "backtest": backtest_main, "optimize": optimize_main, "chart": chart_main}[args.command]()


if __name__ == "__main__":
    main()
