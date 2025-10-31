import json

# Watchlist
watchlist = {"pairs": ["BTC/USDT", "ETH/USDT"], "updated_at": "2025-10-31T10:48:00Z"}
with open("/opt/smartorder-pro/config/watchlist.json", "w") as f:
    json.dump(watchlist, f, indent=2)

# Risk config
risk = {"max_position_size_usdt": 1000, "stop_loss_pct": 2.0, "take_profit_pct": 3.0, "max_open_trades": 5, "max_daily_loss_usdt": 100}
with open("/opt/smartorder-pro/config/risk_config.json", "w") as f:
    json.dump(risk, f, indent=2)

# Paper wallet
wallet = {"balance_usdt": 10000.0, "equity_usdt": 10000.0, "unrealized_pnl_usdt": 0.0, "realized_pnl_usdt": 0.0, "updated_at": "2025-10-31T10:48:00Z"}
with open("/opt/smartorder-pro/config/paper_wallet.json", "w") as f:
    json.dump(wallet, f, indent=2)

print("✅ Configs JSON créés")
