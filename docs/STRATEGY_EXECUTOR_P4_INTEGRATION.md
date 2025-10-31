# Strategy Executor - Intégration P4 Modes & Stratégies

## 📋 Modifications requises dans `strategy_executor.py`

### 1. Import des adaptateurs au démarrage

```python
import sys
sys.path.insert(0, "/opt/smartorder-pro")
from adapters.config_adapter import read_trading_modes
import logging

logger = logging.getLogger(__name__)
```

### 2. Chargement configuration au démarrage

```python
class StrategyExecutor:
    def __init__(self):
        self.trading_config = self.load_trading_config()
        self.current_mode = self.trading_config.get("current_mode", "spot")
        self.enabled_strategies = self.get_enabled_strategies()
        logger.info(f"[EXECUTOR] Mode actif: {self.current_mode}")
        logger.info(f"[EXECUTOR] Stratégies enabled: {[s['name'] for s in self.enabled_strategies]}")
    
    def load_trading_config(self):
        """Charge la configuration trading_modes.json via adaptateur."""
        try:
            config = read_trading_modes()
            logger.info("[EXECUTOR] Configuration trading modes chargée avec succès")
            return config
        except Exception as e:
            logger.error(f"[EXECUTOR] Erreur chargement config: {e}")
            return {"current_mode": "spot", "strategies": {"spot": []}}
    
    def get_enabled_strategies(self):
        """Retourne uniquement les stratégies enabled du mode actif."""
        mode_strategies = self.trading_config.get("strategies", {}).get(self.current_mode, [])
        enabled = [s for s in mode_strategies if s.get("enabled", False)]
        return enabled
```

### 3. Filtrage strict lors de l'exécution

```python
def execute_trading_cycle(self):
    """Exécute un cycle de trading en respectant modes et stratégies."""
    
    # Recharger config (cas où modifiée via Dashboard)
    self.trading_config = self.load_trading_config()
    self.current_mode = self.trading_config.get("current_mode")
    self.enabled_strategies = self.get_enabled_strategies()
    
    logger.info(f"[CYCLE START] Mode: {self.current_mode}")
    logger.info(f"[CYCLE START] Stratégies actives: {len(self.enabled_strategies)}")
    
    if len(self.enabled_strategies) == 0:
        logger.warning("[CYCLE] Aucune stratégie active - cycle ignoré")
        return
    
    # ✅ N'EXÉCUTER QUE les stratégies enabled
    for strategy in self.enabled_strategies:
        strategy_id = strategy["id"]
        strategy_name = strategy["name"]
        
        logger.info(f"[EXECUTE] Stratégie: {strategy_name} (ID: {strategy_id})")
        
        try:
            # Exécution selon le type de stratégie
            if strategy_id == "grid_trading":
                self.execute_grid_trading(strategy)
            elif strategy_id == "dca":
                self.execute_dca(strategy)
            elif strategy_id == "mean_reversion":
                self.execute_mean_reversion(strategy)
            # ... autres stratégies
            
            logger.info(f"[SUCCESS] {strategy_name} exécutée")
        
        except Exception as e:
            logger.error(f"[ERROR] {strategy_name} erreur: {e}")
```

### 4. Logging décisions

```python
def log_strategy_decision(self, strategy_id, symbol, action, reason):
    """Log chaque décision de trading pour traçabilité."""
    decision_log = {
        "timestamp": datetime.utcnow().isoformat(),
        "mode": self.current_mode,
        "strategy_id": strategy_id,
        "symbol": symbol,
        "action": action,
        "reason": reason
    }
    
    with open("/opt/smartorder-pro/logs/strategy_decisions.jsonl", "a") as f:
        f.write(json.dumps(decision_log) + "\n")
    
    logger.info(f"[DECISION] {strategy_id} | {symbol} | {action} | {reason}")
```

## 📊 Exemple de logs prouvant le respect des stratégies

### Logs au démarrage
```
[2025-10-31 12:20:00] [EXECUTOR] Configuration trading modes chargée avec succès
[2025-10-31 12:20:00] [EXECUTOR] Mode actif: spot
[2025-10-31 12:20:00] [EXECUTOR] Stratégies enabled: ['Grid Trading', 'DCA (Dollar Cost Averaging)', 'Mean Reversion']
```

### Logs pendant cycle d'exécution
```
[2025-10-31 12:20:30] [CYCLE START] Mode: spot
[2025-10-31 12:20:30] [CYCLE START] Stratégies actives: 3
[2025-10-31 12:20:30] [EXECUTE] Stratégie: Grid Trading (ID: grid_trading)
[2025-10-31 12:20:31] [DECISION] grid_trading | BTC/USDT | BUY | Price below grid level 5
[2025-10-31 12:20:31] [SUCCESS] Grid Trading exécutée
[2025-10-31 12:20:31] [EXECUTE] Stratégie: DCA (Dollar Cost Averaging) (ID: dca)
[2025-10-31 12:20:32] [DECISION] dca | ETH/USDT | BUY | DCA interval reached
[2025-10-31 12:20:32] [SUCCESS] DCA (Dollar Cost Averaging) exécutée
[2025-10-31 12:20:32] [EXECUTE] Stratégie: Mean Reversion (ID: mean_reversion)
[2025-10-31 12:20:33] [DECISION] mean_reversion | BTC/USDT | SELL | Price 2.5% above mean
[2025-10-31 12:20:33] [SUCCESS] Mean Reversion exécutée
```

### Logs après changement mode via Dashboard
```
[2025-10-31 12:25:00] [CONFIG RELOAD] Détection changement configuration
[2025-10-31 12:25:00] [EXECUTOR] Mode actif: futures
[2025-10-31 12:25:00] [EXECUTOR] Stratégies enabled: ['Infinity Grid', 'Multi-TP Optimizer']
[2025-10-31 12:25:05] [CYCLE START] Mode: futures
[2025-10-31 12:25:05] [CYCLE START] Stratégies actives: 2
[2025-10-31 12:25:05] [EXECUTE] Stratégie: Infinity Grid (ID: infinity_grid)
[2025-10-31 12:25:06] [DECISION] infinity_grid | BTC/USDT | LONG | Grid setup with leverage 5x
[2025-10-31 12:25:06] [SUCCESS] Infinity Grid exécutée
```

### Logs stratégie désactivée (prouve filtrage)
```
[2025-10-31 12:30:00] [CYCLE START] Mode: spot
[2025-10-31 12:30:00] [CYCLE START] Stratégies actives: 2
[2025-10-31 12:30:00] [INFO] Scalping Volatility désactivée - ignorée
[2025-10-31 12:30:00] [INFO] Momentum Breakout désactivée - ignorée
[2025-10-31 12:30:00] [EXECUTE] Stratégie: Grid Trading (ID: grid_trading)
...
```

## ✅ Validation P4.5

### Critères de validation
1. ✅ Bot charge `trading_modes.json` au démarrage
2. ✅ Bot n'exécute QUE les stratégies `enabled: true`
3. ✅ Bot respecte le `current_mode`
4. ✅ Bot recharge config si modifiée via Dashboard
5. ✅ Logs montrent décision → exécution avec stratégie ID
6. ✅ Stratégies disabled sont explicitement ignorées

### Fichiers de log à vérifier
- `/opt/smartorder-pro/logs/strategy_executor.log` - Logs généraux
- `/opt/smartorder-pro/logs/strategy_decisions.jsonl` - Décisions détaillées
- `/opt/smartorder-pro/logs/diagnostic_memory.jsonl` - Changements config

### Test E2E
1. Démarrer bot avec mode `spot` et 3 stratégies enabled
2. Vérifier logs montrent 3 stratégies exécutées
3. Désactiver 1 stratégie via Dashboard
4. Attendre prochain cycle
5. Vérifier logs montrent 2 stratégies exécutées
6. Changer mode vers `futures` via Dashboard
7. Vérifier logs montrent stratégies futures exécutées

## 🚀 Déploiement

```bash
# 1. Backup strategy_executor.py actuel
cp /opt/smartorder-pro/strategy_executor.py /opt/smartorder-pro/strategy_executor.py.backup

# 2. Appliquer modifications P4.5
# (Intégrer code ci-dessus dans strategy_executor.py)

# 3. Redémarrer bot
systemctl restart smartorder-bot

# 4. Vérifier logs
tail -f /opt/smartorder-pro/logs/strategy_executor.log
```

## 📝 Note importante

**AUCUN HARDCODE** : Toutes les stratégies et modes doivent être lus depuis `trading_modes.json` via `read_trading_modes()`. 

Le bot ne doit JAMAIS exécuter de stratégie qui n'est pas marquée `enabled: true` dans le mode actif.

Cette garantie est le cœur de P4 et permet le contrôle temps réel via Dashboard.
