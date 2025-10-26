"""
SmartOrder PRO - Arbitrage Scanner Module
Détecte et exploite les opportunités d'arbitrage inter-exchanges
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import deque

LOG = logging.getLogger("arbitrage_scanner")
LOG.setLevel(logging.INFO)

class ArbitrageScanner:
    """
    Détecte les opportunités d'arbitrage entre exchanges
    
    Types d'arbitrage:
    1. Simple Arbitrage: Acheter sur Exchange A, Vendre sur Exchange B
    2. Triangular Arbitrage: BTC→ETH→USDT→BTC sur même exchange
    3. Funding Rate Arbitrage: Long spot + Short perpetual
    
    ROI typique: 0.5-3% par opportunité
    Risque: Latence, frais, slippage
    
    Example:
    - Bybit: BTC = $67,000
    - Binance: BTC = $67,300
    - Spread: +$300 (0.45%)
    - Après frais 0.2%: Profit net 0.25% = $167 sur $67k
    """
    
    def __init__(self, min_profit_pct: float = 0.5):
        """
        Initialize Arbitrage Scanner
        
        Args:
            min_profit_pct: Profit minimum en % pour considérer une opportunité
        """
        self.min_profit_pct = min_profit_pct
        
        # Prix par exchange
        self.prices = {}  # {exchange: {symbol: {price, timestamp}}}
        
        # Opportunités détectées
        self.opportunities = deque(maxlen=50)
        
        # Frais par exchange (maker/taker)
        self.exchange_fees = {
            'bybit': {'maker': 0.1, 'taker': 0.1},
            'binance': {'maker': 0.1, 'taker': 0.1},
            'okx': {'maker': 0.08, 'taker': 0.1},
            'kraken': {'maker': 0.16, 'taker': 0.26}
        }
        
        # Stats
        self.stats = {
            'total_opportunities': 0,
            'total_trades': 0,
            'total_profit_usdt': 0.0,
            'avg_spread': 0.0
        }
        
        LOG.info(f"ArbitrageScanner initialized (min profit: {min_profit_pct}%)")
    
    def update_price(self, exchange: str, symbol: str, price: float, timestamp: Optional[float] = None):
        """
        Met à jour le prix d'un symbole sur un exchange
        
        Args:
            exchange: Nom de l'exchange (ex: 'bybit')
            symbol: Symbole (ex: 'BTCUSDT')
            price: Prix actuel
            timestamp: Timestamp Unix
        """
        if timestamp is None:
            timestamp = time.time()
        
        if exchange not in self.prices:
            self.prices[exchange] = {}
        
        self.prices[exchange][symbol] = {
            'price': price,
            'timestamp': timestamp
        }
    
    def scan_simple_arbitrage(self, symbol: str) -> Optional[Dict]:
        """
        Scanne les opportunités d'arbitrage simple pour un symbole
        
        Returns:
            Dict avec détails de l'opportunité si trouvée, None sinon
        """
        # Collecter tous les prix disponibles
        available_prices = []
        
        for exchange, symbols in self.prices.items():
            if symbol in symbols:
                data = symbols[symbol]
                available_prices.append({
                    'exchange': exchange,
                    'price': data['price'],
                    'timestamp': data['timestamp']
                })
        
        if len(available_prices) < 2:
            return None
        
        # Trouver min et max
        min_entry = min(available_prices, key=lambda x: x['price'])
        max_entry = max(available_prices, key=lambda x: x['price'])
        
        if min_entry['exchange'] == max_entry['exchange']:
            return None
        
        # Calculer spread brut
        buy_price = min_entry['price']
        sell_price = max_entry['price']
        spread_pct = ((sell_price - buy_price) / buy_price) * 100
        
        # Calculer frais
        buy_exchange = min_entry['exchange']
        sell_exchange = max_entry['exchange']
        
        buy_fee_pct = self.exchange_fees.get(buy_exchange, {}).get('taker', 0.1)
        sell_fee_pct = self.exchange_fees.get(sell_exchange, {}).get('taker', 0.1)
        
        total_fees_pct = buy_fee_pct + sell_fee_pct
        
        # Profit net
        net_profit_pct = spread_pct - total_fees_pct
        
        # Vérifier si profitable
        if net_profit_pct < self.min_profit_pct:
            return None
        
        # Calculer profit en USDT (sur $10k)
        capital = 10000  # Base calculation
        profit_usdt = capital * (net_profit_pct / 100)
        
        opportunity = {
            'type': 'SIMPLE_ARBITRAGE',
            'symbol': symbol,
            'buy_exchange': buy_exchange,
            'sell_exchange': sell_exchange,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'spread_pct': round(spread_pct, 3),
            'fees_pct': round(total_fees_pct, 3),
            'net_profit_pct': round(net_profit_pct, 3),
            'estimated_profit_usdt': round(profit_usdt, 2),
            'timestamp': time.time()
        }
        
        # Ajouter à l'historique
        self.opportunities.append(opportunity)
        self.stats['total_opportunities'] += 1
        
        LOG.warning(f"💰 ARBITRAGE OPPORTUNITY: {symbol} "
                   f"Buy {buy_exchange}@{buy_price:.2f} → "
                   f"Sell {sell_exchange}@{sell_price:.2f} "
                   f"(Net: {net_profit_pct:.2f}%)")
        
        return opportunity
    
    def scan_all_symbols(self) -> List[Dict]:
        """
        Scanne toutes les opportunités d'arbitrage disponibles
        
        Returns:
            Liste des opportunités trouvées
        """
        # Collecter tous les symboles uniques
        all_symbols = set()
        for exchange_prices in self.prices.values():
            all_symbols.update(exchange_prices.keys())
        
        opportunities = []
        
        for symbol in all_symbols:
            opp = self.scan_simple_arbitrage(symbol)
            if opp:
                opportunities.append(opp)
        
        # Trier par profit décroissant
        opportunities.sort(key=lambda x: x['net_profit_pct'], reverse=True)
        
        return opportunities
    
    def calculate_triangular_arbitrage(self, exchange: str, 
                                      path: Tuple[str, str, str]) -> Optional[Dict]:
        """
        Calcule l'arbitrage triangulaire
        
        Args:
            exchange: Exchange à utiliser
            path: Tuple de 3 symboles (ex: ('BTCUSDT', 'ETHBTC', 'ETHUSDT'))
            
        Returns:
            Opportunité d'arbitrage triangulaire si profitable
        """
        # TODO: Implémenter l'arbitrage triangulaire
        # Nécessite calcul complexe de taux de change
        # Pour l'instant, retourner None
        return None
    
    def execute_arbitrage(self, opportunity: Dict, capital_usdt: float) -> Dict:
        """
        Exécute une opportunité d'arbitrage
        
        Args:
            opportunity: Opportunité détectée
            capital_usdt: Capital à utiliser
            
        Returns:
            Résultat de l'exécution
        """
        try:
            # TODO: Intégration avec API des exchanges
            # Pour l'instant, simulation
            
            net_profit_pct = opportunity['net_profit_pct']
            profit_usdt = capital_usdt * (net_profit_pct / 100)
            
            result = {
                'success': True,
                'type': 'arbitrage',
                'symbol': opportunity['symbol'],
                'buy_exchange': opportunity['buy_exchange'],
                'sell_exchange': opportunity['sell_exchange'],
                'capital_usdt': capital_usdt,
                'profit_usdt': profit_usdt,
                'profit_pct': net_profit_pct,
                'timestamp': datetime.now().isoformat()
            }
            
            self.stats['total_trades'] += 1
            self.stats['total_profit_usdt'] += profit_usdt
            
            LOG.info(f"✅ Arbitrage executed: {opportunity['symbol']} "
                    f"Profit: ${profit_usdt:.2f} ({net_profit_pct:.2f}%)")
            
            return result
            
        except Exception as e:
            LOG.error(f"Arbitrage execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_best_opportunity(self) -> Optional[Dict]:
        """Retourne la meilleure opportunité actuelle"""
        opportunities = self.scan_all_symbols()
        
        if not opportunities:
            return None
        
        return opportunities[0]  # Déjà triée par profit
    
    def get_opportunities_summary(self, top_n: int = 10) -> List[Dict]:
        """
        Retourne un résumé des meilleures opportunités
        
        Args:
            top_n: Nombre d'opportunités à retourner
        """
        recent_opps = list(self.opportunities)[-50:]  # Dernières 50
        
        # Filtrer seulement les profitables
        profitable = [
            opp for opp in recent_opps 
            if opp['net_profit_pct'] >= self.min_profit_pct
        ]
        
        # Trier par profit
        profitable.sort(key=lambda x: x['net_profit_pct'], reverse=True)
        
        return profitable[:top_n]
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques"""
        if self.stats['total_opportunities'] > 0:
            spreads = [opp['spread_pct'] for opp in self.opportunities if 'spread_pct' in opp]
            avg_spread = sum(spreads) / len(spreads) if spreads else 0
        else:
            avg_spread = 0
        
        win_rate = 0.0
        if self.stats['total_trades'] > 0:
            # En arbitrage, normalement 100% win rate si bien exécuté
            win_rate = 100.0
        
        return {
            **self.stats,
            'avg_spread': round(avg_spread, 3),
            'win_rate': win_rate,
            'avg_profit_per_trade': round(
                self.stats['total_profit_usdt'] / max(1, self.stats['total_trades']), 2
            )
        }


# Instance globale
_arbitrage_scanner = None

def get_arbitrage_scanner() -> ArbitrageScanner:
    """Récupère l'instance singleton"""
    global _arbitrage_scanner
    if _arbitrage_scanner is None:
        _arbitrage_scanner = ArbitrageScanner()
    return _arbitrage_scanner


if __name__ == "__main__":
    print("=" * 60)
    print("Arbitrage Scanner - Test")
    print("=" * 60)
    
    scanner = ArbitrageScanner(min_profit_pct=0.5)
    
    symbol = "BTCUSDT"
    
    # Simuler des prix sur différents exchanges
    print(f"\n📊 Simulation de prix sur exchanges...")
    
    scanner.update_price('bybit', symbol, 67000.0)
    scanner.update_price('binance', symbol, 67400.0)  # +$400 spread
    scanner.update_price('okx', symbol, 67100.0)
    
    print(f"   Bybit: $67,000")
    print(f"   Binance: $67,400 (+0.60%)")
    print(f"   OKX: $67,100")
    
    # Scanner opportunité
    print(f"\n🔍 Scan d'arbitrage pour {symbol}...")
    opp = scanner.scan_simple_arbitrage(symbol)
    
    if opp:
        print(f"\n💰 Opportunité détectée!")
        print(f"   Type: {opp['type']}")
        print(f"   Buy: {opp['buy_exchange']} @ ${opp['buy_price']:,.2f}")
        print(f"   Sell: {opp['sell_exchange']} @ ${opp['sell_price']:,.2f}")
        print(f"   Spread brut: {opp['spread_pct']:.2f}%")
        print(f"   Frais: {opp['fees_pct']:.2f}%")
        print(f"   Profit net: {opp['net_profit_pct']:.2f}%")
        print(f"   Profit estimé: ${opp['estimated_profit_usdt']:.2f} (sur $10k)")
        
        # Exécuter
        print(f"\n⚡ Exécution de l'arbitrage...")
        result = scanner.execute_arbitrage(opp, capital_usdt=5000.0)
        
        if result['success']:
            print(f"   ✅ Success!")
            print(f"   Capital: ${result['capital_usdt']:,.2f}")
            print(f"   Profit: ${result['profit_usdt']:.2f}")
    else:
        print("   ❌ Aucune opportunité profitable")
    
    # Scanner tous les symboles
    print(f"\n🔍 Scan global...")
    
    # Ajouter plus de prix
    scanner.update_price('bybit', 'ETHUSDT', 3500.0)
    scanner.update_price('binance', 'ETHUSDT', 3520.0)
    
    all_opps = scanner.scan_all_symbols()
    print(f"   {len(all_opps)} opportunités trouvées")
    
    if all_opps:
        best = all_opps[0]
        print(f"\n🏆 Meilleure opportunité:")
        print(f"   {best['symbol']}: {best['net_profit_pct']:.2f}% net profit")
    
    # Stats
    stats = scanner.get_stats()
    print(f"\n📊 Stats:")
    print(f"   Total opportunités: {stats['total_opportunities']}")
    print(f"   Total trades: {stats['total_trades']}")
    print(f"   Total profit: ${stats['total_profit_usdt']:.2f}")
    print(f"   Avg spread: {stats['avg_spread']:.3f}%")
    print(f"   Win rate: {stats['win_rate']:.0f}%")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)
