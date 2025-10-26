# 🤖 SMART POSITION MANAGER - Gestion Intelligente des Positions

**Date :** 25 Octobre 2025  
**Objectif :** Détecter et gérer automatiquement toutes les positions ouvertes (Spot + Futures)

---

## 💡 CONCEPT PRINCIPAL

**Le bot devient un gestionnaire intelligent :**
- Détecte automatiquement toutes les positions ouvertes
- Analyse si elles sont profitables ou en perte
- Décide intelligemment : garder, vendre partiellement, ou fermer
- S'adapte au marché en temps réel
- Protège les gains et limite les pertes

---

## 🎯 MODULE 1 : AUTO POSITION DETECTOR

### Fonctionnalités

**1. Scan automatique au démarrage**
```python
def scan_all_positions():
    # Scan Spot
    spot_positions = get_spot_balances()
    
    # Scan Futures Long/Short
    futures_positions = get_futures_positions()
    
    # Combine et analyse
    all_positions = merge_positions(spot_positions, futures_positions)
    
    return all_positions
```

**2. Détection continue**
- Scan toutes les 10 secondes
- Détecte nouvelles positions (trades manuels)
- Met à jour état positions existantes
- Synchronise avec exchange

**3. Types positions détectées**

**SPOT :**
```python
Position Spot = {
    "symbol": "BTCUSDT",
    "quantity": 0.05,
    "avg_entry_price": 65000,
    "current_price": 67000,
    "pnl": +2000 USDT,
    "pnl_pct": +3.08%,
    "type": "SPOT"
}
```

**FUTURES LONG :**
```python
Position Long = {
    "symbol": "BTCUSDT",
    "side": "LONG",
    "quantity": 0.1,
    "leverage": 5x,
    "entry_price": 66000,
    "current_price": 67000,
    "pnl": +500 USDT,
    "pnl_pct": +1.52%,
    "liquidation_price": 52800,
    "margin_ratio": 85%,
    "type": "FUTURES"
}
```

**FUTURES SHORT :**
```python
Position Short = {
    "symbol": "ETHUSDT",
    "side": "SHORT",
    "quantity": 2.0,
    "leverage": 3x,
    "entry_price": 2500,
    "current_price": 2450,
    "pnl": +100 USDT,
    "pnl_pct": +2.00%,
    "liquidation_price": 3250,
    "margin_ratio": 92%,
    "type": "FUTURES"
}
```

---

## 🎯 MODULE 2 : INTELLIGENT DECISION ENGINE

### Analyse Position Spot

**Critères de décision :**

```python
def analyze_spot_position(position):
    # 1. Analyse PnL
    if pnl_pct > 10%:
        action = "SELL_PARTIAL (50%)"  # Sécurise profit
        reason = "Profit important atteint"
        
    elif pnl_pct > 5%:
        action = "HOLD + SET_ALERT"
        reason = "Bon profit, surveille"
        
    elif pnl_pct > 0%:
        action = "HOLD"
        reason = "Position profitable"
        
    elif pnl_pct > -3%:
        action = "HOLD + MONITOR"
        reason = "Petite perte acceptable"
        
    elif pnl_pct > -5%:
        action = "ALERT + PREPARE_EXIT"
        reason = "Perte significative"
        
    else:  # pnl_pct < -5%
        action = "SELL_NOW"
        reason = "Stop loss déclenché"
    
    # 2. Analyse tendance marché
    trend = detect_trend(position.symbol)
    
    if trend == "STRONG_UP" and position.pnl > 0:
        action = "HOLD"  # Laisse courir
        
    elif trend == "STRONG_DOWN" and position.pnl < 0:
        action = "SELL_NOW"  # Sort avant pire
        
    elif trend == "REVERSAL" and position.pnl > 2%:
        action = "SELL_PARTIAL"  # Sécurise
    
    # 3. Analyse technique
    rsi = get_rsi(position.symbol)
    
    if rsi > 80 and position.pnl > 3%:
        action = "SELL_PARTIAL (70%)"
        reason = "Suracheté + profit bon"
        
    elif rsi < 20 and position.pnl < 0:
        action = "HOLD"  # Attend rebond
        reason = "Survendu, possible rebond"
    
    # 4. Analyse volume
    volume_spike = detect_volume_spike()
    
    if volume_spike == "SELL_PRESSURE":
        action = "SELL_NOW"
        reason = "Pression vente forte"
    
    return {
        "action": action,
        "reason": reason,
        "confidence": calculate_confidence()
    }
```

---

### Analyse Position Futures Long

**Critères spécifiques Long :**

```python
def analyze_long_position(position):
    # 1. Protection liquidation
    distance_liquidation = (position.current_price - position.liquidation_price) / position.liquidation_price * 100
    
    if distance_liquidation < 5%:
        action = "CLOSE_NOW"
        reason = "⚠️ DANGER liquidation proche"
        priority = "CRITICAL"
        
    elif distance_liquidation < 10%:
        action = "REDUCE_SIZE (50%)"
        reason = "Liquidation trop proche"
        priority = "HIGH"
    
    # 2. Analyse PnL
    if position.pnl_pct > 10%:
        action = "CLOSE_PARTIAL (50%) + TRAILING_SL"
        reason = "Gros profit, sécurise + laisse courir"
        
    elif position.pnl_pct > 5%:
        action = "MOVE_SL_TO_BREAKEVEN"
        reason = "Profit OK, protège capital"
        
    elif position.pnl_pct < -3%:
        action = "MONITOR_CLOSE"
        reason = "Perte, surveille de près"
        
    elif position.pnl_pct < -5%:
        action = "CLOSE_NOW"
        reason = "Stop loss atteint"
    
    # 3. Analyse tendance
    trend = detect_trend(position.symbol)
    
    if trend == "REVERSAL_DOWN":
        if position.pnl > 0:
            action = "CLOSE_50%"
            reason = "Retournement, sécurise profit"
        else:
            action = "CLOSE_100%"
            reason = "Retournement + perte = exit"
    
    # 4. Funding rate (Perpetual)
    funding = get_funding_rate(position.symbol)
    
    if funding > 0.05%:  # Funding très élevé
        action = "CONSIDER_CLOSE"
        reason = "Funding rate trop cher pour long"
    
    # 5. Support/Resistance
    support = find_nearest_support(position.symbol)
    current_price = position.current_price
    
    if current_price < support and position.pnl < 0:
        action = "CLOSE_NOW"
        reason = "Cassure support + perte"
    
    return {
        "action": action,
        "reason": reason,
        "priority": priority
    }
```

---

### Analyse Position Futures Short

**Critères spécifiques Short :**

```python
def analyze_short_position(position):
    # 1. Protection liquidation
    distance_liquidation = (position.liquidation_price - position.current_price) / position.liquidation_price * 100
    
    if distance_liquidation < 5%:
        action = "CLOSE_NOW"
        reason = "⚠️ DANGER liquidation proche"
        priority = "CRITICAL"
    
    # 2. Analyse PnL
    if position.pnl_pct > 10%:
        action = "CLOSE_PARTIAL (50%) + TRAILING_SL"
        reason = "Gros profit short, sécurise"
        
    elif position.pnl_pct > 5%:
        action = "MOVE_SL_TO_BREAKEVEN"
        reason = "Bon profit, protège"
    
    # 3. Analyse tendance
    trend = detect_trend(position.symbol)
    
    if trend == "REVERSAL_UP":
        if position.pnl > 0:
            action = "CLOSE_75%"  # Plus agressif sur short
            reason = "Retournement haussier, exit short"
        else:
            action = "CLOSE_100%"
            reason = "Retournement + perte short = danger"
    
    # 4. Analyse momentum
    momentum = get_momentum(position.symbol)
    
    if momentum == "STRONG_BULLISH":
        action = "CLOSE_NOW"
        reason = "Momentum contre short = exit"
    
    # 5. Resistance
    resistance = find_nearest_resistance(position.symbol)
    current_price = position.current_price
    
    if current_price > resistance and position.pnl < 0:
        action = "CLOSE_NOW"
        reason = "Cassure résistance + perte short"
    
    # 6. Funding rate
    funding = get_funding_rate(position.symbol)
    
    if funding < -0.05%:  # Funding négatif élevé
        action = "CONSIDER_CLOSE"
        reason = "Funding rate trop cher pour short"
    
    return {
        "action": action,
        "reason": reason,
        "priority": priority
    }
```

---

## 🎯 MODULE 3 : AUTO ACTIONS EXECUTOR

### Actions Automatiques

**1. HOLD (Garder)**
```python
def action_hold(position):
    # Continue surveillance
    log(f"Position {position.symbol} maintenue")
    
    # Met à jour trailing stop si existe
    if position.has_trailing_stop:
        update_trailing_stop(position)
    
    # Vérifie alertes
    check_price_alerts(position)
```

**2. SELL_PARTIAL (Vente partielle Spot)**
```python
def action_sell_partial_spot(position, percentage):
    # Calcule quantité à vendre
    sell_qty = position.quantity * (percentage / 100)
    
    # Exécute ordre
    order = place_market_sell(
        symbol=position.symbol,
        quantity=sell_qty
    )
    
    # Log
    log(f"Vendu {percentage}% de {position.symbol}")
    
    # Notif Telegram
    notify_telegram(f"✅ Profit partiel: Vendu {percentage}% {position.symbol} @ {order.price}")
    
    # Met à jour position
    position.quantity -= sell_qty
```

**3. CLOSE_PARTIAL (Fermeture partielle Futures)**
```python
def action_close_partial_futures(position, percentage):
    # Calcule quantité à fermer
    close_qty = position.quantity * (percentage / 100)
    
    # Exécute ordre opposé
    if position.side == "LONG":
        order = place_market_sell(
            symbol=position.symbol,
            quantity=close_qty,
            reduce_only=True
        )
    else:  # SHORT
        order = place_market_buy(
            symbol=position.symbol,
            quantity=close_qty,
            reduce_only=True
        )
    
    # Log
    log(f"Fermé {percentage}% position {position.side} {position.symbol}")
    
    # Notif
    notify_telegram(f"✅ Profit sécurisé: Fermé {percentage}% {position.side} {position.symbol}")
    
    # Calcul profit
    profit = calculate_partial_profit(position, close_qty)
    
    # Met à jour
    position.quantity -= close_qty
```

**4. CLOSE_NOW (Fermeture totale)**
```python
def action_close_now(position):
    if position.type == "SPOT":
        # Vend tout le spot
        order = place_market_sell(
            symbol=position.symbol,
            quantity=position.quantity
        )
        action_type = "Vente"
        
    elif position.type == "FUTURES":
        # Ferme position futures
        if position.side == "LONG":
            order = place_market_sell(
                symbol=position.symbol,
                quantity=position.quantity,
                reduce_only=True
            )
        else:  # SHORT
            order = place_market_buy(
                symbol=position.symbol,
                quantity=position.quantity,
                reduce_only=True
            )
        action_type = "Fermeture"
    
    # Calcul PnL final
    final_pnl = calculate_final_pnl(position, order.price)
    
    # Notif
    emoji = "🟢" if final_pnl > 0 else "🔴"
    notify_telegram(f"{emoji} {action_type} complète {position.symbol}: PnL = {final_pnl:.2f} USDT ({position.pnl_pct:.2f}%)")
    
    # Remove position
    remove_position(position.id)
```

**5. MOVE_SL_TO_BREAKEVEN (Stop Loss à breakeven)**
```python
def action_move_sl_breakeven(position):
    # Calcule prix breakeven (entry + fees)
    breakeven_price = position.entry_price * 1.001  # +0.1% pour fees
    
    # Place/update stop loss
    if position.type == "FUTURES":
        if position.side == "LONG":
            sl_order = place_stop_loss_sell(
                symbol=position.symbol,
                quantity=position.quantity,
                stop_price=breakeven_price
            )
        else:  # SHORT
            sl_order = place_stop_loss_buy(
                symbol=position.symbol,
                quantity=position.quantity,
                stop_price=breakeven_price
            )
    
    # Log
    log(f"Stop loss moved to breakeven @ {breakeven_price}")
    
    # Notif
    notify_telegram(f"🛡️ Protection activée: SL à breakeven sur {position.symbol}")
```

**6. TRAILING_STOP (Stop suiveur)**
```python
def action_set_trailing_stop(position, distance_pct):
    # Active trailing stop
    position.trailing_stop = True
    position.trailing_distance = distance_pct
    
    # Calcule prix initial trailing
    if position.side == "LONG" or position.type == "SPOT":
        trailing_price = position.current_price * (1 - distance_pct/100)
    else:  # SHORT
        trailing_price = position.current_price * (1 + distance_pct/100)
    
    position.trailing_stop_price = trailing_price
    
    # Log
    log(f"Trailing stop activé @ {distance_pct}% sur {position.symbol}")
    
    # Notif
    notify_telegram(f"🎯 Trailing stop activé: {distance_pct}% sur {position.symbol}")
```

---

## 🎯 MODULE 4 : RISK PROTECTION SYSTEM

### Protections Automatiques

**1. Liquidation Guard (Futures)**
```python
def liquidation_guard():
    for position in get_futures_positions():
        distance = calculate_liquidation_distance(position)
        
        if distance < 5%:
            # URGENCE - Ferme immédiatement
            action_close_now(position)
            notify_telegram(f"🚨 URGENCE: Position {position.symbol} fermée - liquidation imminente")
            
        elif distance < 10%:
            # WARNING - Réduit taille
            action_close_partial_futures(position, 50)
            notify_telegram(f"⚠️ WARNING: Position {position.symbol} réduite - liquidation proche")
            
        elif distance < 15%:
            # ALERT - Surveille
            notify_telegram(f"⚠️ ALERT: {position.symbol} - Distance liquidation {distance:.1f}%")
```

**2. Drawdown Protection**
```python
def drawdown_protection():
    total_pnl = calculate_total_pnl()
    daily_pnl_pct = total_pnl / initial_capital * 100
    
    if daily_pnl_pct < -5%:  # -5% perte journalière
        # STOP TRADING
        close_all_losing_positions()
        set_mode("SAFE_MODE")
        notify_telegram("🛑 SAFE MODE: Drawdown -5% atteint - Toutes positions perdantes fermées")
        
    elif daily_pnl_pct < -3%:
        # REDUCE RISK
        reduce_all_leverage(50%)
        notify_telegram("⚠️ Réduction risque: Drawdown -3% - Leverage réduit 50%")
```

**3. Correlation Protection**
```python
def correlation_protection():
    positions = get_all_positions()
    
    # Détecte surexposition
    btc_exposure = sum(p.value for p in positions if "BTC" in p.symbol)
    total_exposure = sum(p.value for p in positions)
    
    if btc_exposure / total_exposure > 0.7:  # >70% sur BTC
        notify_telegram("⚠️ Surexposition BTC: 70%+ du capital")
        # Suggère diversification
```

**4. Time-Based Exit**
```python
def time_based_exit():
    for position in get_all_positions():
        holding_time = now() - position.open_time
        
        # Position spot > 30 jours en perte
        if position.type == "SPOT" and holding_time > 30 * 24 * 3600 and position.pnl < 0:
            action_sell_partial_spot(position, 50)
            log(f"Position {position.symbol} trop longue en perte - Sortie partielle")
        
        # Position futures > 7 jours
        if position.type == "FUTURES" and holding_time > 7 * 24 * 3600:
            if position.pnl > 0:
                action_close_partial_futures(position, 50)
            else:
                action_close_now(position)
            log(f"Position futures {position.symbol} trop longue - Exit")
```

---

## 🎯 MODULE 5 : SMART PROFIT TAKING

### Stratégies de Sortie Intelligente

**1. Pyramidal Exit (Sortie progressive)**
```python
def pyramidal_exit(position):
    if position.pnl_pct > 3%:
        action_close_partial(position, 25)  # Première sortie
        
    if position.pnl_pct > 5%:
        action_close_partial(position, 25)  # Deuxième sortie
        
    if position.pnl_pct > 8%:
        action_close_partial(position, 25)  # Troisième sortie
        
    # 25% restant avec trailing stop
    if position.pnl_pct > 10%:
        action_set_trailing_stop(position, 2)  # Trailing 2%
```

**2. Fibonacci Exit**
```python
def fibonacci_exit(position):
    entry = position.entry_price
    current = position.current_price
    
    # Calcule niveaux Fibo
    fib_levels = calculate_fibonacci(entry, current)
    
    if current >= fib_levels['0.382']:
        action_close_partial(position, 25)
        
    if current >= fib_levels['0.618']:
        action_close_partial(position, 50)  # 50% des restants
        
    if current >= fib_levels['1.000']:
        action_close_partial(position, 75)  # Exit quasi total
```

**3. Volatility-Based Exit**
```python
def volatility_exit(position):
    atr = get_atr(position.symbol)
    entry = position.entry_price
    
    # TP selon ATR
    tp_distance = atr * 2
    tp_price = entry + tp_distance if position.side == "LONG" else entry - tp_distance
    
    if position.current_price >= tp_price:
        action_close_partial(position, 50)
        # Continue avec trailing
        action_set_trailing_stop(position, atr / position.current_price * 100)
```

---

## 🎯 MODULE 6 : NOTIFICATION SYSTEM

### Alertes Intelligentes

```python
def notify_position_status(position, decision):
    # Format message
    emoji = "🟢" if position.pnl > 0 else "🔴"
    
    message = f"""
{emoji} **Position {position.symbol}**

**Type:** {position.type} {position.side if position.type == "FUTURES" else ""}
**Entry:** ${position.entry_price:,.2f}
**Current:** ${position.current_price:,.2f}
**PnL:** ${position.pnl:,.2f} ({position.pnl_pct:+.2f}%)

**Décision IA:** {decision.action}
**Raison:** {decision.reason}
**Confiance:** {decision.confidence}%

{get_market_context(position.symbol)}
    """
    
    # Envoie Telegram
    send_telegram(message)
    
    # Log dashboard
    log_dashboard(position, decision)
```

---

## 📊 EXEMPLE SCÉNARIOS COMPLETS

### Scénario 1 : Position Spot BTC profitable

**État détecté :**
```
Symbol: BTCUSDT
Type: SPOT
Quantity: 0.05 BTC
Entry: $65,000
Current: $70,000
PnL: +$250 (+7.69%)
Trend: STRONG_UP
RSI: 72
```

**Décision IA :**
```
Action: SELL_PARTIAL (30%) + SET_TRAILING_STOP (2%)
Reason: Profit bon + RSI élevé → sécurise partiel + laisse courir
Confidence: 85%
```

**Exécution :**
1. Vend 0.015 BTC @ $70,000 = +$75 sécurisé
2. Garde 0.035 BTC avec trailing stop 2%
3. Si prix monte à $72,000 → trailing à $70,560
4. Si retrace → vend à $70,560 → profit total sécurisé

---

### Scénario 2 : Position Futures Long en danger

**État détecté :**
```
Symbol: ETHUSDT
Type: FUTURES LONG
Leverage: 5x
Entry: $2,500
Current: $2,420
PnL: -$40 (-3.2%)
Liquidation: $2,000
Distance: 17.4%
Trend: WEAK_DOWN
```

**Décision IA :**
```
Action: CLOSE_NOW
Reason: Perte + tendance faible + liquidation < 20%
Priority: HIGH
Confidence: 92%
```

**Exécution :**
1. Ferme position immédiatement
2. Perte -$40 limitée
3. Évite perte plus importante
4. Capital préservé pour meilleure opportunité

---

### Scénario 3 : Position Short profitable

**État détecté :**
```
Symbol: SOLUSDT
Type: FUTURES SHORT
Leverage: 3x
Entry: $180
Current: $165
PnL: +$45 (+8.33%)
Trend: STRONG_DOWN
Support: $160
```

**Décision IA :**
```
Action: CLOSE_PARTIAL (50%) + TRAILING_STOP (1.5%)
Reason: Gros profit + trend continue + proche support
Confidence: 88%
```

**Exécution :**
1. Ferme 50% position → +$22.5 sécurisé
2. Garde 50% avec trailing 1.5%
3. Si continue down → profit continue
4. Si rebond → exit auto avec profit

---

## ⚙️ CONFIGURATION

### .env Settings

```bash
# Smart Position Manager
SMART_POSITION_MANAGER=true
AUTO_DETECT_POSITIONS=true
SCAN_INTERVAL=10  # Scan toutes les 10s

# Risk Thresholds
LIQUIDATION_ALERT=15%      # Alerte si < 15% liquidation
LIQUIDATION_REDUCE=10%     # Réduit si < 10%
LIQUIDATION_CLOSE=5%       # Ferme si < 5%
MAX_DRAWDOWN_DAILY=5%      # Stop si -5% jour

# Profit Taking
AUTO_PROFIT_TAKING=true
PARTIAL_PROFIT_1=3%        # 25% @ +3%
PARTIAL_PROFIT_2=5%        # 25% @ +5%
PARTIAL_PROFIT_3=8%        # 25% @ +8%
TRAILING_ACTIVATION=5%     # Trailing si > +5%

# Stop Loss
AUTO_STOP_LOSS=true
SPOT_SL_PCT=5%            # SL spot à -5%
FUTURES_SL_PCT=3%         # SL futures à -3%
AUTO_BREAKEVEN=true       # Move SL breakeven @ +2%

# Time-Based
MAX_SPOT_HOLD_DAYS=30     # Max 30 jours spot en perte
MAX_FUTURES_HOLD_DAYS=7   # Max 7 jours futures
```

---

## 📈 PERFORMANCE ATTENDUE

| Métrique | Target |
|----------|--------|
| **Positions sauvées** | 80%+ détectées |
| **Pertes évitées** | -50% drawdown |
| **Profits sécurisés** | +30% gains locked |
| **Liquidations évitées** | 100% |
| **Response time** | <5 secondes |

---

## 🎯 ROADMAP

### Phase 1 (Semaine 1)
- [ ] Auto Position Detector
- [ ] Decision Engine Spot
- [ ] Decision Engine Futures
- [ ] Basic Actions Executor

### Phase 2 (Semaine 2)
- [ ] Risk Protection System
- [ ] Liquidation Guard
- [ ] Drawdown Protection
- [ ] Notification System

### Phase 3 (Semaine 3)
- [ ] Smart Profit Taking
- [ ] Trailing Stop Advanced
- [ ] Time-Based Exit
- [ ] Tests & Backtests

**Temps total : 3 semaines (~120h)**

---

**Document créé le :** 25 Octobre 2025, 23:35 UTC  
**Module :** Smart Position Manager  
**Objectif :** Gérer intelligemment TOUTES les positions existantes 🤖
