import json
import random
import os

def compute_ai_scores(symbol):
    """Simule un score AI basé sur RSI/MACD/BB"""
    score = random.randint(50, 90)
    file_path = "/opt/smartorder-pro/config/ai_scores.json"
    try:
        scores = {}
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                scores = json.load(f)
        scores[symbol] = score
        with open(file_path, "w") as f:
            json.dump(scores, f, indent=4)
        print(f"[ai_scoring] {symbol}: {score}")
    except Exception as e:
        print(f"[ai_scoring ERROR] {e}")
    return score
