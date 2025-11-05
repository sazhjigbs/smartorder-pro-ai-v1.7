#!/usr/bin/env python3
"""
Script pour ajouter les endpoints manquants à l'API
Sans modifier la structure existante
"""

import sys

# Code des endpoints à ajouter
NEW_ENDPOINTS = '''
# ============================================================================
# ENDPOINTS ADDITIONNELS v2.4 - Ajoutés le 2025-11-04
# ============================================================================

@app.get("/api/ai/status")
async def get_ai_status():
    """Get AI system status and scores"""
    try:
        # Load market regime data
        regime_data = load_json_file(CONFIG_DIR / "last_signals.json")
        
        if regime_data:
            return {
                "ai_confidence": regime_data.get("ai_confidence", 0.75),
                "market_regime": regime_data.get("regime", "NEUTRAL"),
                "volatility": regime_data.get("volatility", "MEDIUM"),
                "trend_strength": regime_data.get("trend_strength", 0.5),
                "rsi": regime_data.get("rsi", 50.0),
                "macd": regime_data.get("macd", 0.0),
                "atr": regime_data.get("atr", 1250.0),
                "volume": regime_data.get("volume", 150000),
                "last_update": regime_data.get("updated_at", datetime.now().isoformat())
            }
        else:
            return {
                "ai_confidence": 0.75,
                "market_regime": "NEUTRAL",
                "volatility": "MEDIUM",
                "trend_strength": 0.5,
                "rsi": 50.0,
                "macd": 0.0,
                "atr": 1250.0,
                "volume": 150000,
                "last_update": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting AI status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pnl")
async def get_pnl(range: str = "today"):
    """Get PnL data for specified range"""
    try:
        pnl_data = load_json_file(CONFIG_DIR / "pnl_tracker.json")
        
        if not pnl_data:
            return {
                "total": 0.0,
                "today": 0.0,
                "week": 0.0,
                "month": 0.0,
                "range": range
            }
        
        # Return data based on range
        if range == "today":
            return {
                "total": pnl_data.get("total_pnl", 0.0),
                "today": pnl_data.get("daily_pnl", 0.0),
                "range": "today"
            }
        elif range == "week":
            return {
                "total": pnl_data.get("total_pnl", 0.0),
                "week": pnl_data.get("weekly_pnl", 0.0),
                "range": "week"
            }
        elif range == "month":
            return {
                "total": pnl_data.get("total_pnl", 0.0),
                "month": pnl_data.get("monthly_pnl", 0.0),
                "range": "month"
            }
        else:
            return {
                "total": pnl_data.get("total_pnl", 0.0),
                "today": pnl_data.get("daily_pnl", 0.0),
                "week": pnl_data.get("weekly_pnl", 0.0),
                "month": pnl_data.get("monthly_pnl", 0.0),
                "range": "all"
            }
    except Exception as e:
        logger.error(f"Error getting PnL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs/tail")
async def get_logs(lines: int = 200):
    """Get last N lines of logs"""
    try:
        logs_dir = Path("/opt/smartorder-pro/logs")
        log_file = logs_dir / "bot.log"
        
        if not log_file.exists():
            return {"logs": [], "count": 0}
        
        # Read last N lines
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "logs": [line.strip() for line in last_lines],
            "count": len(last_lines),
            "total": len(all_lines)
        }
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        # Return empty logs instead of error
        return {"logs": [], "count": 0, "error": str(e)}

# ============================================================================
# FIN DES ENDPOINTS ADDITIONNELS
# ============================================================================
'''

def add_endpoints_to_api(api_file_path):
    """Add new endpoints to API file"""
    print(f"Reading {api_file_path}...")
    
    with open(api_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if endpoints already exist
    if "/api/ai/status" in content:
        print("⚠️  Endpoints already exist, skipping...")
        return False
    
    # Find the position to insert (before if __name__)
    split_marker = "if __name__ == '__main__':"
    if split_marker not in content:
        print("❌ Could not find insertion point")
        return False
    
    parts = content.split(split_marker)
    
    # Insert new endpoints
    new_content = parts[0] + NEW_ENDPOINTS + "\n" + split_marker + parts[1]
    
    # Write back
    print(f"Writing updated content to {api_file_path}...")
    with open(api_file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Endpoints added successfully!")
    return True

if __name__ == "__main__":
    api_file = "/opt/smartorder-pro/api/main.py"
    
    if len(sys.argv) > 1:
        api_file = sys.argv[1]
    
    success = add_endpoints_to_api(api_file)
    sys.exit(0 if success else 1)
