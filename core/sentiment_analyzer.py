"""
SmartOrder PRO - Sentiment Analyzer Module
Analyse le sentiment du marché via news, social, fear/greed index
"""

import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque
import re

LOG = logging.getLogger("sentiment_analyzer")
LOG.setLevel(logging.INFO)

class SentimentAnalyzer:
    """
    Analyse le sentiment du marché pour optimiser les décisions
    
    Sources de sentiment:
    1. Fear & Greed Index (0-100)
    2. News Headlines (positif/négatif/neutre)
    3. Social Media (Twitter, Reddit mentions)
    4. Funding Rates (optimisme des traders)
    5. Open Interest (engagement du marché)
    
    Sentiment Score: 0-100
    - 0-20: Extreme Fear (opportunité d'achat)
    - 20-40: Fear
    - 40-60: Neutral
    - 60-80: Greed
    - 80-100: Extreme Greed (prudence, possible top)
    
    Stratégie contrarian: "Be greedy when others are fearful"
    """
    
    def __init__(self):
        """Initialize Sentiment Analyzer"""
        self.sentiment_history = {}  # {symbol: deque([sentiment_data])}
        
        # Keywords pour analyse de texte
        self.positive_keywords = [
            'bull', 'bullish', 'moon', 'pump', 'rocket', 'up', 'rally',
            'breakout', 'surge', 'gain', 'profit', 'win', 'positive',
            'buy', 'long', 'accumulate', 'hodl', 'strong', 'good'
        ]
        
        self.negative_keywords = [
            'bear', 'bearish', 'dump', 'crash', 'down', 'fall', 'drop',
            'breakdown', 'loss', 'negative', 'sell', 'short', 'panic',
            'fear', 'bad', 'weak', 'scam', 'rug', 'dead'
        ]
        
        # Market-wide sentiment
        self.market_sentiment = {
            'fear_greed_index': 50,  # 0-100
            'trending_sentiment': 'NEUTRAL',
            'social_volume': 'NORMAL'
        }
        
        # Stats
        self.stats = {
            'total_analyses': 0,
            'extreme_fear_count': 0,
            'extreme_greed_count': 0
        }
        
        LOG.info("SentimentAnalyzer initialized")
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyse le sentiment d'un texte (news, tweet, etc.)
        
        Args:
            text: Texte à analyser
            
        Returns:
            {
                'sentiment': 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL',
                'score': -100 to +100,
                'keywords_found': [str]
            }
        """
        text_lower = text.lower()
        
        # Compter keywords positifs et négatifs
        positive_count = sum(
            1 for keyword in self.positive_keywords 
            if re.search(r'\b' + keyword + r'\b', text_lower)
        )
        
        negative_count = sum(
            1 for keyword in self.negative_keywords 
            if re.search(r'\b' + keyword + r'\b', text_lower)
        )
        
        # Calculer score
        total_keywords = positive_count + negative_count
        
        if total_keywords == 0:
            sentiment = 'NEUTRAL'
            score = 0
        else:
            score = ((positive_count - negative_count) / total_keywords) * 100
            
            if score > 30:
                sentiment = 'POSITIVE'
            elif score < -30:
                sentiment = 'NEGATIVE'
            else:
                sentiment = 'NEUTRAL'
        
        return {
            'sentiment': sentiment,
            'score': round(score, 1),
            'positive_count': positive_count,
            'negative_count': negative_count
        }
    
    def update_fear_greed_index(self, index_value: int):
        """
        Met à jour le Fear & Greed Index
        
        Args:
            index_value: 0-100 (0=extreme fear, 100=extreme greed)
        """
        self.market_sentiment['fear_greed_index'] = max(0, min(100, index_value))
        
        if index_value < 20:
            level = 'EXTREME_FEAR'
            self.stats['extreme_fear_count'] += 1
        elif index_value < 40:
            level = 'FEAR'
        elif index_value < 60:
            level = 'NEUTRAL'
        elif index_value < 80:
            level = 'GREED'
        else:
            level = 'EXTREME_GREED'
            self.stats['extreme_greed_count'] += 1
        
        self.market_sentiment['trending_sentiment'] = level
        
        LOG.info(f"Fear & Greed Index updated: {index_value} ({level})")
    
    def add_social_mention(self, symbol: str, mention: Dict):
        """
        Ajoute une mention social media
        
        Args:
            mention: {
                'text': str,
                'source': 'twitter' | 'reddit' | 'news',
                'timestamp': float,
                'engagement': int (likes, upvotes, etc.)
            }
        """
        if symbol not in self.sentiment_history:
            self.sentiment_history[symbol] = deque(maxlen=100)
        
        # Analyser le texte
        text_sentiment = self.analyze_text(mention['text'])
        
        # Ajouter à l'historique
        self.sentiment_history[symbol].append({
            'timestamp': mention.get('timestamp', time.time()),
            'source': mention.get('source', 'unknown'),
            'sentiment': text_sentiment['sentiment'],
            'score': text_sentiment['score'],
            'engagement': mention.get('engagement', 0),
            'text': mention['text'][:100]  # Garder les 100 premiers caractères
        })
    
    def calculate_sentiment_score(self, symbol: str, periods: int = 20) -> Dict:
        """
        Calcule le sentiment score global pour un symbole
        
        Args:
            symbol: Symbole (ex: 'BTCUSDT')
            periods: Nombre de mentions récentes à considérer
            
        Returns:
            {
                'sentiment_score': 0-100,
                'sentiment_level': str,
                'positive_ratio': 0-100,
                'social_volume': int,
                'trending': bool
            }
        """
        if symbol not in self.sentiment_history:
            return self._neutral_sentiment(symbol)
        
        mentions = list(self.sentiment_history[symbol])[-periods:]
        
        if len(mentions) < 3:
            return self._neutral_sentiment(symbol)
        
        # Calculer ratios
        positive_count = sum(1 for m in mentions if m['sentiment'] == 'POSITIVE')
        negative_count = sum(1 for m in mentions if m['sentiment'] == 'NEGATIVE')
        neutral_count = len(mentions) - positive_count - negative_count
        
        total = len(mentions)
        positive_ratio = (positive_count / total) * 100
        negative_ratio = (negative_count / total) * 100
        
        # Score pondéré par engagement
        total_engagement = sum(m['engagement'] for m in mentions)
        
        if total_engagement > 0:
            weighted_score = sum(
                m['score'] * (m['engagement'] / total_engagement)
                for m in mentions
            )
        else:
            # Score simple
            weighted_score = sum(m['score'] for m in mentions) / len(mentions)
        
        # Convertir en 0-100
        sentiment_score = ((weighted_score + 100) / 2)  # -100..100 → 0..100
        
        # Niveau
        if sentiment_score < 30:
            level = 'VERY_NEGATIVE'
        elif sentiment_score < 45:
            level = 'NEGATIVE'
        elif sentiment_score < 55:
            level = 'NEUTRAL'
        elif sentiment_score < 70:
            level = 'POSITIVE'
        else:
            level = 'VERY_POSITIVE'
        
        # Trending = volume social > moyenne
        is_trending = len(mentions) > 10  # Seuil simple
        
        result = {
            'symbol': symbol,
            'sentiment_score': round(sentiment_score, 1),
            'sentiment_level': level,
            'positive_ratio': round(positive_ratio, 1),
            'negative_ratio': round(negative_ratio, 1),
            'neutral_ratio': round((neutral_count / total) * 100, 1),
            'social_volume': len(mentions),
            'total_engagement': total_engagement,
            'trending': is_trending,
            'timestamp': time.time()
        }
        
        self.stats['total_analyses'] += 1
        
        LOG.info(f"Sentiment for {symbol}: {sentiment_score:.0f} ({level})")
        
        return result
    
    def _neutral_sentiment(self, symbol: str) -> Dict:
        """Sentiment neutre par défaut"""
        return {
            'symbol': symbol,
            'sentiment_score': 50.0,
            'sentiment_level': 'NEUTRAL',
            'positive_ratio': 33.3,
            'negative_ratio': 33.3,
            'neutral_ratio': 33.3,
            'social_volume': 0,
            'total_engagement': 0,
            'trending': False,
            'timestamp': time.time()
        }
    
    def get_trading_signal(self, symbol: str) -> Dict:
        """
        Génère un signal de trading basé sur le sentiment
        
        Stratégie contrarian:
        - Extreme Fear → BUY (opportunité)
        - Extreme Greed → SELL (risque de correction)
        
        Returns:
            {
                'signal': 'BUY' | 'SELL' | 'HOLD',
                'confidence': 0-100,
                'reasoning': str,
                'strategy': 'CONTRARIAN' | 'MOMENTUM'
            }
        """
        sentiment_data = self.calculate_sentiment_score(symbol)
        sentiment_score = sentiment_data['sentiment_score']
        fear_greed = self.market_sentiment['fear_greed_index']
        
        # Stratégie contrarian (par défaut)
        if sentiment_score < 30 and fear_greed < 40:
            signal = 'BUY'
            confidence = (40 - sentiment_score) * 2  # Plus bas = plus confiant
            reasoning = f"Extreme fear detected (sentiment: {sentiment_score:.0f}, F&G: {fear_greed})"
            strategy = 'CONTRARIAN'
        
        elif sentiment_score > 70 and fear_greed > 60:
            signal = 'SELL'
            confidence = (sentiment_score - 60) * 2
            reasoning = f"Extreme greed detected (sentiment: {sentiment_score:.0f}, F&G: {fear_greed})"
            strategy = 'CONTRARIAN'
        
        # Stratégie momentum (si trending fort)
        elif sentiment_data['trending'] and sentiment_score > 60:
            signal = 'BUY'
            confidence = min(70, sentiment_data['social_volume'] * 2)
            reasoning = f"Strong positive momentum (trending, sentiment: {sentiment_score:.0f})"
            strategy = 'MOMENTUM'
        
        elif sentiment_data['trending'] and sentiment_score < 40:
            signal = 'SELL'
            confidence = min(70, sentiment_data['social_volume'] * 2)
            reasoning = f"Strong negative momentum (trending, sentiment: {sentiment_score:.0f})"
            strategy = 'MOMENTUM'
        
        else:
            signal = 'HOLD'
            confidence = 0
            reasoning = "Neutral sentiment, no strong signal"
            strategy = 'NEUTRAL'
        
        return {
            'symbol': symbol,
            'signal': signal,
            'confidence': round(min(100, confidence), 1),
            'reasoning': reasoning,
            'strategy': strategy,
            'sentiment_score': sentiment_score,
            'fear_greed_index': fear_greed,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_market_sentiment(self) -> Dict:
        """Retourne le sentiment global du marché"""
        fear_greed = self.market_sentiment['fear_greed_index']
        
        # Interprétation
        if fear_greed < 25:
            interpretation = "Extreme Fear - Great buying opportunity"
            action = 'ACCUMULATE'
        elif fear_greed < 45:
            interpretation = "Fear - Good time to buy"
            action = 'BUY'
        elif fear_greed < 55:
            interpretation = "Neutral - No strong signal"
            action = 'HOLD'
        elif fear_greed < 75:
            interpretation = "Greed - Consider taking profits"
            action = 'TAKE_PROFIT'
        else:
            interpretation = "Extreme Greed - High risk, reduce exposure"
            action = 'REDUCE'
        
        return {
            'fear_greed_index': fear_greed,
            'level': self.market_sentiment['trending_sentiment'],
            'interpretation': interpretation,
            'recommended_action': action,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques"""
        return {
            **self.stats,
            'symbols_tracked': len(self.sentiment_history),
            'market_fear_greed': self.market_sentiment['fear_greed_index']
        }


# Instance globale
_sentiment_analyzer = None

def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Récupère l'instance singleton"""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer


if __name__ == "__main__":
    print("=" * 60)
    print("Sentiment Analyzer - Test")
    print("=" * 60)
    
    analyzer = SentimentAnalyzer()
    
    symbol = "BTCUSDT"
    
    # Test analyse de texte
    print("\n📝 Test d'analyse de texte...")
    
    texts = [
        "Bitcoin is going to the moon! 🚀 Bullish rally incoming!",
        "Massive dump incoming, bearish breakdown, sell now!",
        "Bitcoin price remains stable at $67k"
    ]
    
    for text in texts:
        result = analyzer.analyze_text(text)
        print(f"   '{text[:50]}...'")
        print(f"   → {result['sentiment']} (score: {result['score']:.0f})")
    
    # Mettre à jour Fear & Greed
    print("\n😱 Test Fear & Greed Index...")
    analyzer.update_fear_greed_index(25)  # Extreme Fear
    
    market = analyzer.get_market_sentiment()
    print(f"   Index: {market['fear_greed_index']}")
    print(f"   Level: {market['level']}")
    print(f"   Interpretation: {market['interpretation']}")
    print(f"   Action: {market['recommended_action']}")
    
    # Simuler mentions sociales
    print(f"\n📱 Simulation de mentions sociales...")
    
    # Mentions positives (sentiment positif)
    for i in range(15):
        analyzer.add_social_mention(symbol, {
            'text': "Bitcoin looking bullish! Great buying opportunity 🚀",
            'source': 'twitter',
            'engagement': 100 + i * 10
        })
    
    # Quelques mentions négatives
    for i in range(5):
        analyzer.add_social_mention(symbol, {
            'text': "Bitcoin crash incoming, sell everything!",
            'source': 'reddit',
            'engagement': 50
        })
    
    print(f"   {len(analyzer.sentiment_history[symbol])} mentions ajoutées")
    
    # Calculer sentiment
    print(f"\n💭 Calcul du sentiment pour {symbol}...")
    sentiment = analyzer.calculate_sentiment_score(symbol)
    
    print(f"   Score: {sentiment['sentiment_score']:.1f}/100")
    print(f"   Level: {sentiment['sentiment_level']}")
    print(f"   Positive: {sentiment['positive_ratio']:.0f}%")
    print(f"   Negative: {sentiment['negative_ratio']:.0f}%")
    print(f"   Social volume: {sentiment['social_volume']}")
    print(f"   Trending: {sentiment['trending']}")
    
    # Signal de trading
    print(f"\n💡 Génération du signal...")
    signal = analyzer.get_trading_signal(symbol)
    
    print(f"   Signal: {signal['signal']}")
    print(f"   Confidence: {signal['confidence']:.1f}%")
    print(f"   Strategy: {signal['strategy']}")
    print(f"   Reasoning: {signal['reasoning']}")
    
    # Stats
    stats = analyzer.get_stats()
    print(f"\n📊 Stats:")
    print(f"   Total analyses: {stats['total_analyses']}")
    print(f"   Symbols tracked: {stats['symbols_tracked']}")
    print(f"   Extreme fear events: {stats['extreme_fear_count']}")
    print(f"   Extreme greed events: {stats['extreme_greed_count']}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)
