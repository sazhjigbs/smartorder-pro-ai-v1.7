#!/usr/bin/env python3
"""
📊 SAFELOGIC SmartOrder PRO — Charts API
Real-time data endpoints for visualization
"""

from fastapi import APIRouter, Depends
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import random

from web.portal_v5_pro.auth_advanced import require_auth

router = APIRouter(prefix="/api/charts", tags=["charts"])

# Mock data storage (in production, use real database)
TRADE_HISTORY = []
PNL_HISTORY = []

def generate_mock_pnl_data(hours: int = 24) -> List[Dict]:
    """Generate mock P&L data for demonstration"""
    data = []
    start_time = datetime.now() - timedelta(hours=hours)
    base_pnl = 1000.0
    
    for i in range(hours * 6):  # Every 10 minutes
        timestamp = start_time + timedelta(minutes=i * 10)
        # Random walk
        change = random.uniform(-20, 30)
        base_pnl += change
        
        data.append({
            "timestamp": timestamp.isoformat(),
            "pnl": round(base_pnl, 2),
            "cumulative_pnl": round(base_pnl - 1000, 2)
        })
    
    return data

def generate_mock_trade_distribution() -> Dict:
    """Generate mock trade distribution data"""
    return {
        "win_trades": random.randint(40, 60),
        "loss_trades": random.randint(20, 40),
        "break_even": random.randint(5, 15)
    }

def generate_mock_performance_metrics() -> Dict:
    """Generate mock performance metrics"""
    return {
        "total_trades": random.randint(100, 200),
        "win_rate": round(random.uniform(55, 70), 2),
        "profit_factor": round(random.uniform(1.2, 2.5), 2),
        "sharpe_ratio": round(random.uniform(1.0, 3.0), 2),
        "max_drawdown": round(random.uniform(-15, -5), 2),
        "avg_win": round(random.uniform(50, 150), 2),
        "avg_loss": round(random.uniform(-80, -30), 2),
        "largest_win": round(random.uniform(300, 800), 2),
        "largest_loss": round(random.uniform(-400, -150), 2)
    }

def generate_mock_equity_curve(days: int = 30) -> List[Dict]:
    """Generate mock equity curve"""
    data = []
    start_time = datetime.now() - timedelta(days=days)
    equity = 10000.0
    
    for i in range(days):
        timestamp = start_time + timedelta(days=i)
        # Trend upward with volatility
        change = random.uniform(-200, 300)
        equity += change
        
        data.append({
            "date": timestamp.strftime("%Y-%m-%d"),
            "equity": round(equity, 2),
            "drawdown": round(min(0, equity - max([d["equity"] for d in data] + [10000])), 2)
        })
    
    return data

def generate_mock_hourly_performance() -> List[Dict]:
    """Generate performance by hour of day"""
    hours = []
    for hour in range(24):
        hours.append({
            "hour": f"{hour:02d}:00",
            "pnl": round(random.uniform(-50, 100), 2),
            "trades": random.randint(0, 15)
        })
    return hours

def generate_mock_asset_distribution() -> List[Dict]:
    """Generate portfolio distribution by asset"""
    assets = ["BTC", "ETH", "SOL", "BNB", "USDT"]
    total = 100
    distribution = []
    
    for asset in assets[:-1]:
        percentage = random.uniform(5, 30)
        total -= percentage
        distribution.append({
            "asset": asset,
            "percentage": round(percentage, 2),
            "value": round(random.uniform(1000, 5000), 2)
        })
    
    distribution.append({
        "asset": assets[-1],
        "percentage": round(total, 2),
        "value": round(random.uniform(1000, 5000), 2)
    })
    
    return distribution

@router.get("/pnl-realtime")
async def get_realtime_pnl(
    hours: int = 24,
    current_user: dict = Depends(require_auth)
):
    """
    Get real-time P&L data for charts
    Returns time series data for the last N hours
    """
    data = generate_mock_pnl_data(hours)
    
    return {
        "success": True,
        "data": data,
        "summary": {
            "total_pnl": round(data[-1]["cumulative_pnl"], 2) if data else 0,
            "change_24h": round(data[-1]["pnl"] - data[0]["pnl"], 2) if len(data) > 1 else 0,
            "last_update": datetime.now().isoformat()
        }
    }

@router.get("/trade-distribution")
async def get_trade_distribution(current_user: dict = Depends(require_auth)):
    """
    Get trade win/loss distribution
    For pie/donut charts
    """
    data = generate_mock_trade_distribution()
    
    return {
        "success": True,
        "data": data,
        "total_trades": sum(data.values())
    }

@router.get("/performance-metrics")
async def get_performance_metrics(current_user: dict = Depends(require_auth)):
    """
    Get comprehensive performance metrics
    """
    metrics = generate_mock_performance_metrics()
    
    return {
        "success": True,
        "metrics": metrics
    }

@router.get("/equity-curve")
async def get_equity_curve(
    days: int = 30,
    current_user: dict = Depends(require_auth)
):
    """
    Get equity curve over time
    """
    data = generate_mock_equity_curve(days)
    
    return {
        "success": True,
        "data": data,
        "summary": {
            "starting_equity": data[0]["equity"] if data else 0,
            "current_equity": data[-1]["equity"] if data else 0,
            "total_return": round(((data[-1]["equity"] / data[0]["equity"] - 1) * 100), 2) if data else 0,
            "max_drawdown": min([d["drawdown"] for d in data]) if data else 0
        }
    }

@router.get("/hourly-performance")
async def get_hourly_performance(current_user: dict = Depends(require_auth)):
    """
    Get performance breakdown by hour of day
    """
    data = generate_mock_hourly_performance()
    
    return {
        "success": True,
        "data": data,
        "best_hour": max(data, key=lambda x: x["pnl"]),
        "worst_hour": min(data, key=lambda x: x["pnl"])
    }

@router.get("/asset-distribution")
async def get_asset_distribution(current_user: dict = Depends(require_auth)):
    """
    Get portfolio distribution by asset
    """
    data = generate_mock_asset_distribution()
    
    return {
        "success": True,
        "data": data,
        "total_value": sum([d["value"] for d in data])
    }

@router.get("/recent-trades")
async def get_recent_trades(
    limit: int = 50,
    current_user: dict = Depends(require_auth)
):
    """
    Get recent trade history
    """
    trades = []
    
    for i in range(limit):
        timestamp = datetime.now() - timedelta(minutes=i * 15)
        side = random.choice(["BUY", "SELL"])
        pnl = random.uniform(-100, 200)
        
        trades.append({
            "id": f"trade_{i}",
            "timestamp": timestamp.isoformat(),
            "symbol": random.choice(["BTCUSDT", "ETHUSDT", "SOLUSDT"]),
            "side": side,
            "quantity": round(random.uniform(0.001, 1.0), 4),
            "price": round(random.uniform(20000, 50000), 2),
            "pnl": round(pnl, 2),
            "status": "CLOSED"
        })
    
    return {
        "success": True,
        "trades": trades,
        "summary": {
            "total_pnl": sum([t["pnl"] for t in trades]),
            "winning_trades": len([t for t in trades if t["pnl"] > 0]),
            "losing_trades": len([t for t in trades if t["pnl"] < 0])
        }
    }

@router.get("/monthly-summary")
async def get_monthly_summary(
    months: int = 12,
    current_user: dict = Depends(require_auth)
):
    """
    Get monthly P&L summary
    """
    data = []
    start_date = datetime.now() - timedelta(days=months * 30)
    
    for i in range(months):
        month_date = start_date + timedelta(days=i * 30)
        pnl = random.uniform(-1000, 3000)
        
        data.append({
            "month": month_date.strftime("%b %Y"),
            "pnl": round(pnl, 2),
            "trades": random.randint(50, 200),
            "win_rate": round(random.uniform(50, 70), 2)
        })
    
    return {
        "success": True,
        "data": data,
        "summary": {
            "total_pnl": sum([d["pnl"] for d in data]),
            "best_month": max(data, key=lambda x: x["pnl"]),
            "worst_month": min(data, key=lambda x: x["pnl"])
        }
    }
