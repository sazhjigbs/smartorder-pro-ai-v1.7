import re

# Lire main.py
with open('/opt/smartorder-pro/api/main.py', 'r') as f:
    content = f.read()

# 1. Ajouter import risk_manager si absent
if 'from risk_manager import risk_manager' not in content:
    import_section = content.split('app = FastAPI')[0]
    import_section += 'from risk_manager import risk_manager\n\n'
    content = import_section + 'app = FastAPI' + content.split('app = FastAPI', 1)[1]

# 2. Ajouter endpoints Risk Manager avant if __name__
risk_endpoints = '''
# =====================
# RISK MANAGEMENT ENDPOINTS
# =====================

@app.get("/api/risk/status")
async def get_risk_status():
    """Get current risk management status"""
    try:
        return risk_manager.get_current_status()
    except Exception as e:
        return {"error": str(e), "reliability_score": 75, "current_mode": "BALANCED"}

@app.post("/api/risk/mode")
async def set_risk_mode(payload: dict):
    """Set risk mode"""
    try:
        mode = payload.get("mode")
        auto = payload.get("auto")
        return risk_manager.set_mode(mode, auto)
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/risk/history")
async def get_risk_history(limit: int = 50):
    """Get risk management history"""
    try:
        return {"history": risk_manager.get_history(limit)}
    except Exception as e:
        return {"history": [], "error": str(e)}

@app.post("/api/guardian/stop")
async def emergency_stop():
    """Activate emergency stop"""
    try:
        result = risk_manager.activate_emergency_stop()
        risk_manager.add_to_history("EMERGENCY_STOP", result)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/guardian/resume")
async def emergency_resume():
    """Deactivate emergency stop"""
    try:
        result = risk_manager.deactivate_emergency_stop()
        risk_manager.add_to_history("EMERGENCY_RESUME", result)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

'''

# Vérifier si endpoints déjà présents
if '@app.get("/api/risk/status")' not in content:
    content = content.replace(
        "if __name__ == '__main__':",
        risk_endpoints + "\nif __name__ == '__main__':"
    )

# 3. Fix /api/ai/status si présent
if '@app.get("/api/ai/status")' in content:
    ai_status_fix = '''
@app.get("/api/ai/status")
async def get_ai_status():
    """Get AI system status"""
    try:
        signals = load_json_file(CONFIG_PATH / "last_signals.json") or {}
        return {
            "ai_confidence": signals.get("ai_confidence", 0.75),
            "market_regime": signals.get("regime", "NEUTRAL"),
            "volatility": signals.get("volatility", "MEDIUM"),
            "trend_strength": signals.get("trend_strength", 0.5),
            "rsi": signals.get("rsi", 50.0),
            "macd": signals.get("macd", 0.0),
            "atr": signals.get("atr", 1250.0),
            "volume": signals.get("volume", 150000),
            "last_update": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "ai_confidence": 0.75,
            "market_regime": "NEUTRAL",
            "volatility": "MEDIUM",
            "error": str(e)
        }
'''
    pattern = r'@app\.get\("/api/ai/status"\).*?(?=@app\.|if __name__|# =====)'
    content = re.sub(pattern, ai_status_fix + '\n', content, flags=re.DOTALL)

# Sauvegarder
with open('/opt/smartorder-pro/api/main.py', 'w') as f:
    f.write(content)

print('✅ main.py modifié avec succès')
