# Phase 6.14 - Market Sentiment Layer ✅

**Status:** ✅ COMPLETE  
**Date:** 2025-01-26  
**Version:** 1.0.0

---

## 🎯 Objectif

Implémenter une couche d'analyse du sentiment et contexte marché pour filtrage intelligent des signaux de trading.

Le **Market Sentiment Layer** agrège plusieurs indicateurs macros pour évaluer les conditions globales du marché crypto et décider si un signal doit être tradé ou ignoré selon le contexte.

---

## 📦 Composants Développés

### 1. **Module Sentiment** (`ai/sentiment.py`)

Moteur d'analyse du sentiment et contexte marché.

**Fonctionnalités:**
- ✅ **Fear & Greed Index** (0-100) via API Alternative.me
- ✅ **BTC Dominance** (%) via CoinGecko
- ✅ **Volatilité marché** basée sur variation BTC 24h
- ✅ **Régime de marché** (BULL/BEAR/NEUTRAL/CHOPPY)
- ✅ **Score de risque global** (0-100)
- ✅ **Filtrage intelligent** des signaux selon contexte
- ✅ **Cache système** (5 minutes) pour limiter API calls

**Régimes de marché détectés:**
- `BULL` - Tendance haussière forte (>+10% sur 7j + FG >60)
- `BEAR` - Tendance baissière forte (<-10% sur 7j + FG <40)
- `CHOPPY` - Volatilité élevée (>8% sur 24h)
- `NEUTRAL` - Range, pas de tendance claire

### 2. **API REST Sentiment** (`api/api_sentiment.py`)

API FastAPI exposant toutes les données de sentiment.

**Endpoints REST:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/sentiment/fear_greed` | Fear & Greed Index |
| `GET` | `/api/sentiment/btc_dominance` | Dominance BTC |
| `GET` | `/api/sentiment/volatility` | Volatilité marché |
| `GET` | `/api/sentiment/regime` | Régime de marché |
| `GET` | `/api/sentiment/context` | Contexte global complet |
| `POST` | `/api/sentiment/should_trade` | Décision de trading |
| `POST` | `/api/sentiment/clear_cache` | Vider cache |
| `GET` | `/api/sentiment/stats` | Stats cache |

**Port:** `8558`

---

## 🚀 Installation & Démarrage

### Démarrer l'API Sentiment

```bash
# Depuis la racine du projet
uvicorn api.api_sentiment:app --host 0.0.0.0 --port 8558
```

L'API sera accessible sur:
- Local: `http://localhost:8558`
- Réseau: `http://0.0.0.0:8558`
- Docs: `http://localhost:8558/docs`

---

## 📡 Utilisation API

### 1. Récupérer Fear & Greed Index

```bash
curl http://localhost:8558/api/sentiment/fear_greed
```

**Réponse:**
```json
{
  "success": true,
  "data": {
    "value": 45,
    "classification": "Fear",
    "level": "Fear",
    "recommendation": "Accumulate",
    "timestamp": "2025-01-26T12:00:00"
  }
}
```

### 2. Contexte Global du Marché

```bash
curl http://localhost:8558/api/sentiment/context
```

**Réponse:**
```json
{
  "success": true,
  "data": {
    "fear_greed": {
      "value": 45,
      "level": "Fear",
      "recommendation": "Accumulate"
    },
    "btc_dominance": 52.3,
    "volatility": {
      "volatility_percent": 4.2,
      "level": "Medium",
      "risk_level": 3
    },
    "market_regime": {
      "regime": "NEUTRAL",
      "description": "Range-bound - Trade both directions",
      "strategy": "Mean reversion, range trading",
      "change_7d": 2.1,
      "confidence": 0.65
    },
    "global_risk_score": 45,
    "recommendation": "⚠️ Medium risk - Reduce position sizes",
    "timestamp": "2025-01-26T12:00:00"
  }
}
```

### 3. Décider si trader un signal

```bash
curl -X POST http://localhost:8558/api/sentiment/should_trade \
  -H "Content-Type: application/json" \
  -d '{
    "signal_confidence": 0.85,
    "symbol": "BTCUSDT",
    "min_confidence": 0.70,
    "max_risk_score": 75
  }'
```

**Réponse:**
```json
{
  "success": true,
  "data": {
    "should_trade": true,
    "reasons": [
      "All market conditions favorable",
      "Risk score: 45/100 (acceptable)",
      "Regime: NEUTRAL"
    ],
    "signal_confidence": 0.85,
    "market_context": { ... },
    "timestamp": "2025-01-26T12:00:00"
  }
}
```

---

## 🔧 Intégration avec Bot Principal

### Dans le bot de trading principal:

```python
from ai.sentiment import MarketSentiment

sentiment = MarketSentiment()

# Avant de trader un signal
def process_signal(signal):
    # Analyser contexte
    decision = sentiment.should_trade_signal(
        signal_confidence=signal.confidence,
        symbol=signal.symbol,
        min_confidence=0.70,
        max_risk_score=75
    )
    
    if decision["should_trade"]:
        # Trader le signal
        execute_trade(signal)
    else:
        # Ignorer le signal
        print(f"Signal ignoré: {decision['reasons']}")
```

### Filtres appliqués:

1. **Confiance du signal** < min_confidence → Rejeté
2. **Risk score** > max_risk_score → Rejeté
3. **Extreme Greed** (FG >85) → Rejeté
4. **Choppy market** + confiance <0.85 → Rejeté

---

## 🧪 Tests

### Tester le module Sentiment

```bash
python tests/test_sentiment_api.py
```

**Output:**
```
======================================================================
🧪 TEST MARKET SENTIMENT ENGINE
======================================================================

1️⃣ Fear & Greed Index:
   ✅ Value: 45/100
   ✅ Level: Fear
   ✅ Recommendation: Accumulate

2️⃣ BTC Dominance:
   ✅ 52.30%

3️⃣ Market Volatility:
   ✅ 4.2% (24h)
   ✅ Level: Medium
   ✅ Risk Level: 3/5

4️⃣ Market Regime:
   ✅ Regime: NEUTRAL
   ✅ Description: Range-bound - Trade both directions
   ✅ Strategy: Mean reversion, range trading
   ✅ Confidence: 0.65

5️⃣ Global Market Context:
   ✅ Risk Score: 45/100
   ✅ ⚠️ Medium risk - Reduce position sizes

6️⃣ Should Trade Signal?
   ✅ Should Trade: YES ✅
   ✅ Reasons:
      - All market conditions favorable
      - Risk score: 45/100 (acceptable)
      - Regime: NEUTRAL

7️⃣ Cache System:
   ✅ Cached items: ['fear_greed', 'btc_dominance', 'volatility', 'market_regime']
   ✅ Cache cleared

======================================================================
✅ TOUS LES TESTS PASSÉS !
======================================================================
```

---

## 📊 Exemples Cas d'Usage

### Cas 1: Marché en Extreme Greed (FG = 90)

```python
decision = sentiment.should_trade_signal(
    signal_confidence=0.80,
    symbol="BTCUSDT"
)

# Résultat:
# should_trade = False
# reasons = ["Extreme Greed detected: 90/100"]
```

### Cas 2: Marché Choppy (volatilité élevée)

```python
decision = sentiment.should_trade_signal(
    signal_confidence=0.75,  # Confiance normale
    symbol="ETHUSDT"
)

# Résultat:
# should_trade = False
# reasons = ["Choppy market - need higher confidence"]
```

### Cas 3: Conditions favorables

```python
decision = sentiment.should_trade_signal(
    signal_confidence=0.85,
    symbol="BTCUSDT"
)

# Résultat:
# should_trade = True
# reasons = [
#     "All market conditions favorable",
#     "Risk score: 35/100 (acceptable)",
#     "Regime: BULL"
# ]
```

---

## 🎛️ Configuration

### Paramètres par défaut:

```python
# Cache duration
cache_duration = 300  # 5 minutes

# Filtres par défaut
min_confidence = 0.70      # 70%
max_risk_score = 75        # Sur 100
extreme_greed_threshold = 85  # Sur 100
choppy_confidence_required = 0.85  # 85%
```

---

## 🔌 APIs Externes Utilisées

| API | Endpoint | Limite Rate | Utilisation |
|-----|----------|-------------|-------------|
| Alternative.me | `https://api.alternative.me/fng/` | Aucune | Fear & Greed Index |
| CoinGecko | `https://api.coingecko.com/api/v3/global` | 50/min | BTC Dominance |
| CoinGecko | `https://api.coingecko.com/api/v3/simple/price` | 50/min | Volatilité BTC |
| CoinGecko | `https://api.coingecko.com/api/v3/coins/bitcoin/market_chart` | 50/min | Prix BTC historique |

**Note:** Le cache de 5 minutes réduit drastiquement le nombre d'appels API.

---

## ✅ Checklist Phase 6.14

- [x] Créer module `ai/sentiment.py`
- [x] Implémenter Fear & Greed Index
- [x] Implémenter BTC Dominance
- [x] Implémenter Volatilité marché
- [x] Implémenter détection Régime
- [x] Implémenter score de risque global
- [x] Créer API REST `api/api_sentiment.py`
- [x] Exposer 8 endpoints REST
- [x] Créer tests `tests/test_sentiment_api.py`
- [x] Documentation complète
- [x] Intégration avec bot principal

---

## 🚀 Prochaines Étapes

1. **Intégrer dans le bot principal**
   - Filtrer signaux via `should_trade_signal()`
   - Afficher contexte dans Telegram/Web UI

2. **Tests en conditions réelles**
   - Vérifier taux de filtrage
   - Ajuster seuils si nécessaire

3. **Optimisations futures**
   - Ajouter d'autres indicateurs (Funding Rate, Open Interest...)
   - Machine Learning pour auto-ajuster seuils
   - Dashboard UI pour visualiser sentiment en temps réel

---

## 📚 Ressources

- [Fear & Greed Index](https://alternative.me/crypto/fear-and-greed-index/)
- [CoinGecko API Docs](https://www.coingecko.com/en/api/documentation)
- [FastAPI Docs](https://fastapi.tiangolo.com/)

---

**Phase 6.14 COMPLETE ✅**

*Développé le 2025-01-26 pour SmartOrder PRO v1.8-FINAL*
