# BTC/KRW Research Toolkit

Upbit BTC/KRW hourly candles for repeatable indicator research and long-only backtests. It is a research tool, not live-trading software or investment advice.

```powershell
.\venv\Scripts\python.exe main.py backtest --output-dir output
.\venv\Scripts\python.exe main.py optimize --output output\walk_forward.csv
.\venv\Scripts\python.exe main.py chart --output output\backtest_chart.png
.\venv\Scripts\python.exe main.py download --count 10000
```

The strategy creates a signal after a candle closes and executes it at the following candle's open. Fees are charged on both sides. `optimize` selects its RSI threshold only on the preceding training window and reports the later test window.
