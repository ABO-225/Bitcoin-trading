# BTC/KRW Research Toolkit

Upbit BTC/KRW hourly candles for repeatable indicator research and long-only backtests. 
I am keep working on it.

```powershell
.\venv\Scripts\python.exe main.py backtest --output-dir output
.\venv\Scripts\python.exe main.py optimize --output output\walk_forward.csv
.\venv\Scripts\python.exe main.py chart --output output\backtest_chart.png
.\venv\Scripts\python.exe main.py download --count 10000
```

Creates a signal after a candle closes and executes it at the following candle. 
Fees are charged. 
`optimize` selects its RSI threshold only on the preceding training window and reports the later test window.

LETS EARN MONEY GOOOOO
