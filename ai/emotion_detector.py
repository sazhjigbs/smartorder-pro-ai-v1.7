"""
Emotion AI Detector
Analyse le sentiment du marché via Twitter/Reddit/News
"""
import time
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from collections import Counter


class SentimentScore(Enum):
    EXTREMELY_BEARISH = -2
    BEARISH = -1
    NEUTRAL = 0
    BULLISH = 1
    EXTREMELY_BULLISH = 2


@dataclass
class SocialPost:
    """Post social media"""
    source: str  # twitter, reddit, news
    text: str
    author: str
    timestamp: float
    likes: int = 0
    retweets: int = 0
    comments: int = 0


class EmotionDetector:
    """Détecteur d'émotions et sentiment du marché"""
    
    def __init__(self):
        self.sentiment_history: List[Dict] = []
        
        # Mots-clés pour analyse de sentiment
        self.bullish_keywords = [
            'moon', 'bullish', 'buy', 'pump', 'rocket', 'green', 'profit',
            'gain', 'up', 'high', 'breakout', 'rally', 'surge', 'soar',
            'ath', 'all time high', 'momentum', 'accumulate', 'hold', 'hodl'
        ]
        
        self.bearish_keywords = [
            'dump', 'bearish', 'sell', 'crash', 'red', 'loss', 'down',
            'low', 'breakdown', 'decline', 'fall', 'drop', 'collapse',
            'bear', 'correction', 'resistance', 'fear', 'panic'
        ]
        
        self.extreme_bullish = ['to the moon', 'all in', 'life savings', 'lamborghini', 'wen lambo']
        self.extreme_bearish = ['scam', 'rug pull', 'ponzi', 'worthless', 'dead']
    
    def analyze_post(self, post: SocialPost) -> Dict:
        """Analyse le sentiment d'un post"""
        text_lower = post.text.lower()
        
        # Compter mots-clés
        bullish_count = sum(1 for keyword in self.bullish_keywords if keyword in text_lower)
        bearish_count = sum(1 for keyword in self.bearish_keywords if keyword in text_lower)
        
        # Vérifier extrêmes
        is_extreme_bullish = any(keyword in text_lower for keyword in self.extreme_bullish)
        is_extreme_bearish = any(keyword in text_lower for keyword in self.extreme_bearish)
        
        # Calculer score
        if is_extreme_bullish:
            sentiment = SentimentScore.EXTREMELY_BULLISH
            score = 2.0
        elif is_extreme_bearish:
            sentiment = SentimentScore.EXTREMELY_BEARISH
            score = -2.0
        elif bullish_count > bearish_count * 2:
            sentiment = SentimentScore.BULLISH
            score = 1.0
        elif bearish_count > bullish_count * 2:
            sentiment = SentimentScore.BEARISH
            score = -1.0
        else:
            sentiment = SentimentScore.NEUTRAL
            score = 0.0
        
        # Poids selon engagement
        weight = 1.0 + (post.likes / 100) + (post.retweets / 50)
        weighted_score = score * min(weight, 3.0)  # Max 3x weight
        
        return {
            "sentiment": sentiment,
            "score": score,
            "weighted_score": weighted_score,
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "engagement": post.likes + post.retweets + post.comments
        }
    
    def analyze_batch(self, posts: List[SocialPost]) -> Dict:
        """Analyse un batch de posts"""
        if not posts:
            return {
                "overall_sentiment": SentimentScore.NEUTRAL.value,
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "total_posts": 0
            }
        
        analyses = [self.analyze_post(post) for post in posts]
        
        # Score moyen pondéré
        total_weight = sum(a["weighted_score"] for a in analyses)
        avg_weighted_score = total_weight / len(analyses)
        
        # Déterminer sentiment global
        if avg_weighted_score >= 1.5:
            overall = SentimentScore.EXTREMELY_BULLISH
        elif avg_weighted_score >= 0.5:
            overall = SentimentScore.BULLISH
        elif avg_weighted_score <= -1.5:
            overall = SentimentScore.EXTREMELY_BEARISH
        elif avg_weighted_score <= -0.5:
            overall = SentimentScore.BEARISH
        else:
            overall = SentimentScore.NEUTRAL
        
        # Confiance basée sur nombre de posts et cohérence
        scores = [a["score"] for a in analyses]
        score_variance = sum((s - avg_weighted_score)**2 for s in scores) / len(scores)
        confidence = min(len(posts) / 100, 1.0) * (1 - min(score_variance, 1.0))
        
        # Distribution des sentiments
        sentiment_counts = Counter(a["sentiment"].value for a in analyses)
        
        result = {
            "overall_sentiment": overall.value,
            "sentiment_score": avg_weighted_score,
            "confidence": confidence,
            "total_posts": len(posts),
            "sentiment_distribution": dict(sentiment_counts),
            "avg_engagement": sum(a["engagement"] for a in analyses) / len(analyses),
            "timestamp": time.time()
        }
        
        self.sentiment_history.append(result)
        
        return result
    
    def get_market_emotion(self, symbol: str, posts: List[SocialPost]) -> Dict:
        """
        Analyse l'émotion du marché pour un symbol
        Retourne un signal actionnable
        """
        # Filtrer posts pertinents au symbol
        symbol_posts = [
            post for post in posts
            if symbol.lower() in post.text.lower() or
               symbol.replace('USDT', '').lower() in post.text.lower()
        ]
        
        if not symbol_posts:
            return {
                "symbol": symbol,
                "signal": "NEUTRAL",
                "strength": 0,
                "reason": "No relevant posts found"
            }
        
        analysis = self.analyze_batch(symbol_posts)
        
        # Générer signal
        score = analysis["sentiment_score"]
        confidence = analysis["confidence"]
        
        if score >= 1.0 and confidence > 0.6:
            signal = "STRONG_BUY"
            strength = min(score * confidence, 10.0)
        elif score >= 0.5 and confidence > 0.5:
            signal = "BUY"
            strength = score * confidence * 5
        elif score <= -1.0 and confidence > 0.6:
            signal = "STRONG_SELL"
            strength = abs(score) * confidence * 10
        elif score <= -0.5 and confidence > 0.5:
            signal = "SELL"
            strength = abs(score) * confidence * 5
        else:
            signal = "NEUTRAL"
            strength = 0
        
        return {
            "symbol": symbol,
            "signal": signal,
            "strength": strength,
            "sentiment_score": score,
            "confidence": confidence,
            "total_posts": len(symbol_posts),
            "overall_sentiment": analysis["overall_sentiment"],
            "timestamp": time.time()
        }
    
    def detect_fomo_panic(self, posts: List[SocialPost]) -> Dict:
        """Détecte FOMO (Fear Of Missing Out) ou panique"""
        text_combined = " ".join(post.text.lower() for post in posts)
        
        # Indicateurs FOMO
        fomo_indicators = ['fomo', 'all in', 'yolo', 'life savings', 'sell house', 'moon']
        fomo_score = sum(text_combined.count(indicator) for indicator in fomo_indicators)
        
        # Indicateurs panique
        panic_indicators = ['panic', 'sell everything', 'crash', 'dump', 'exit', 'scam']
        panic_score = sum(text_combined.count(indicator) for indicator in panic_indicators)
        
        # Normaliser
        total_posts = len(posts) if posts else 1
        fomo_level = min(fomo_score / total_posts * 10, 10.0)
        panic_level = min(panic_score / total_posts * 10, 10.0)
        
        if fomo_level > 7.0:
            emotion = "EXTREME_FOMO"
            action = "CONTRARIAN_SELL"  # Vendre quand FOMO extrême
        elif panic_level > 7.0:
            emotion = "EXTREME_PANIC"
            action = "CONTRARIAN_BUY"  # Acheter quand panique extrême
        elif fomo_level > 4.0:
            emotion = "FOMO"
            action = "CAUTION"
        elif panic_level > 4.0:
            emotion = "PANIC"
            action = "OPPORTUNITY"
        else:
            emotion = "NORMAL"
            action = "NEUTRAL"
        
        return {
            "emotion": emotion,
            "action": action,
            "fomo_level": fomo_level,
            "panic_level": panic_level,
            "recommendation": self._get_recommendation(emotion)
        }
    
    def _get_recommendation(self, emotion: str) -> str:
        """Recommandation basée sur l'émotion"""
        recommendations = {
            "EXTREME_FOMO": "Marché surchauffé - Envisager de prendre des profits",
            "EXTREME_PANIC": "Opportunité d'achat - Le marché est survendu",
            "FOMO": "Prudence - Ne pas céder à la pression d'achat",
            "PANIC": "Rester calme - Peut être une opportunité",
            "NORMAL": "Conditions de marché normales"
        }
        return recommendations.get(emotion, "Aucune recommandation")
    
    def get_sentiment_trend(self, hours: int = 24) -> Dict:
        """Analyse la tendance du sentiment sur X heures"""
        cutoff_time = time.time() - (hours * 3600)
        recent = [h for h in self.sentiment_history if h["timestamp"] > cutoff_time]
        
        if len(recent) < 2:
            return {"trend": "INSUFFICIENT_DATA"}
        
        # Comparer début vs fin
        first_half = recent[:len(recent)//2]
        second_half = recent[len(recent)//2:]
        
        avg_first = sum(h["sentiment_score"] for h in first_half) / len(first_half)
        avg_second = sum(h["sentiment_score"] for h in second_half) / len(second_half)
        
        change = avg_second - avg_first
        
        if change > 0.5:
            trend = "IMPROVING"
        elif change < -0.5:
            trend = "DETERIORATING"
        else:
            trend = "STABLE"
        
        return {
            "trend": trend,
            "change": change,
            "current_sentiment": avg_second,
            "previous_sentiment": avg_first,
            "num_datapoints": len(recent)
        }


# Exemple d'utilisation
if __name__ == "__main__":
    detector = EmotionDetector()
    
    # Posts simulés
    posts = [
        SocialPost("twitter", "BTC to the moon! 🚀 All in!", "user1", time.time(), likes=150, retweets=50),
        SocialPost("reddit", "Bitcoin is crashing, time to sell", "user2", time.time(), likes=20),
        SocialPost("twitter", "HODL strong, bullish af", "user3", time.time(), likes=200, retweets=80),
        SocialPost("reddit", "Bearish pattern forming", "user4", time.time(), likes=30),
    ]
    
    # Analyse
    result = detector.analyze_batch(posts)
    print(f"✅ Sentiment: {result['overall_sentiment']}")
    print(f"📊 Score: {result['sentiment_score']:.2f}")
    print(f"🎯 Confidence: {result['confidence']:.2%}")
    
    # Signal trading
    signal = detector.get_market_emotion("BTCUSDT", posts)
    print(f"\n📈 Signal: {signal['signal']}")
    print(f"💪 Strength: {signal['strength']:.1f}/10")
    
    # FOMO/Panic
    emotion = detector.detect_fomo_panic(posts)
    print(f"\n😱 Emotion: {emotion['emotion']}")
    print(f"💡 Recommendation: {emotion['recommendation']}")
