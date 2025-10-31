"""
Emotion AI Detector - Version RÉELLE
Analyse sentiment Twitter/Reddit avec APIs officielles + NLP
"""
import time
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("emotion_ai_real")


@dataclass
class SocialPost:
    source: str  # twitter, reddit
    text: str
    author: str
    timestamp: float
    score: int = 0  # likes/upvotes
    sentiment_score: float = 0.0  # -1 à +1


class SentimentScore:
    EXTREMELY_BULLISH = 2
    BULLISH = 1
    NEUTRAL = 0
    BEARISH = -1
    EXTREMELY_BEARISH = -2


class EmotionDetectorReal:
    """Détecteur d'émotions avec APIs Twitter/Reddit réelles"""
    
    def __init__(
        self,
        twitter_bearer_token: Optional[str] = None,
        reddit_client_id: Optional[str] = None,
        reddit_client_secret: Optional[str] = None,
        use_transformers: bool = True
    ):
        self.twitter_bearer = twitter_bearer_token
        self.reddit_id = reddit_client_id
        self.reddit_secret = reddit_client_secret
        self.use_transformers = use_transformers
        
        # Initialise clients
        self.twitter_client = None
        self.reddit_client = None
        
        if twitter_bearer_token:
            self._init_twitter()
        
        if reddit_client_id and reddit_client_secret:
            self._init_reddit()
        
        # Initialise NLP model
        self.sentiment_model = None
        if use_transformers:
            self._init_nlp_model()
        
        # Mots-clés pour sentiment basique (fallback)
        self.bullish_keywords = [
            'moon', 'bullish', 'pump', 'buy', 'long', 'hodl', 'rally',
            'breakout', 'profits', 'gains', 'lambo', 'ATH', 'all time high'
        ]
        
        self.bearish_keywords = [
            'crash', 'dump', 'sell', 'short', 'bearish', 'scam', 'FUD',
            'panic', 'loss', 'drop', 'plunge', 'bubble', 'correction'
        ]
        
        LOG.info(f"✅ Emotion AI Detector REAL initialisé")
        LOG.info(f"   Twitter API: {'✅' if self.twitter_client else '❌'}")
        LOG.info(f"   Reddit API: {'✅' if self.reddit_client else '❌'}")
        LOG.info(f"   NLP Model: {'✅' if self.sentiment_model else '❌'}")
    
    def _init_twitter(self):
        """Initialise Twitter API v2"""
        try:
            import tweepy
            self.twitter_client = tweepy.Client(
                bearer_token=self.twitter_bearer,
                wait_on_rate_limit=True
            )
            LOG.info("✅ Twitter API connecté")
        except Exception as e:
            LOG.error(f"❌ Twitter API erreur: {e}")
            self.twitter_client = None
    
    def _init_reddit(self):
        """Initialise Reddit API"""
        try:
            import praw
            self.reddit_client = praw.Reddit(
                client_id=self.reddit_id,
                client_secret=self.reddit_secret,
                user_agent="SmartOrderBot/1.0"
            )
            LOG.info("✅ Reddit API connecté")
        except Exception as e:
            LOG.error(f"❌ Reddit API erreur: {e}")
            self.reddit_client = None
    
    def _init_nlp_model(self):
        """Initialise modèle NLP pour sentiment"""
        try:
            from transformers import pipeline
            self.sentiment_model = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment",
                max_length=512,
                truncation=True
            )
            LOG.info("✅ NLP Model chargé")
        except Exception as e:
            LOG.warning(f"⚠️ NLP Model non disponible: {e}")
            self.sentiment_model = None
    
    def scrape_twitter(self, symbol: str = "BTC", limit: int = 100) -> List[SocialPost]:
        """Récupère tweets réels"""
        if not self.twitter_client:
            LOG.warning("⚠️ Twitter API non configuré")
            return []
        
        LOG.info(f"📥 Scraping Twitter pour ${symbol}")
        
        try:
            # Query Twitter
            query = f"${symbol} OR #{symbol} lang:en -is:retweet"
            
            tweets = self.twitter_client.search_recent_tweets(
                query=query,
                max_results=min(limit, 100),  # Max 100 par requête
                tweet_fields=['created_at', 'public_metrics']
            )
            
            posts = []
            
            if tweets.data:
                for tweet in tweets.data:
                    posts.append(SocialPost(
                        source='twitter',
                        text=tweet.text,
                        author=f"user_{tweet.id[:8]}",
                        timestamp=tweet.created_at.timestamp(),
                        score=tweet.public_metrics.get('like_count', 0)
                    ))
            
            LOG.info(f"✅ {len(posts)} tweets récupérés")
            return posts
        
        except Exception as e:
            LOG.error(f"❌ Erreur Twitter scraping: {e}")
            return []
    
    def scrape_reddit(self, symbol: str = "BTC", limit: int = 50) -> List[SocialPost]:
        """Récupère posts Reddit réels"""
        if not self.reddit_client:
            LOG.warning("⚠️ Reddit API non configuré")
            return []
        
        LOG.info(f"📥 Scraping Reddit pour {symbol}")
        
        try:
            subreddits = ['CryptoCurrency', 'Bitcoin', 'CryptoMarkets', 'BitcoinMarkets']
            posts = []
            
            for sub_name in subreddits:
                try:
                    subreddit = self.reddit_client.subreddit(sub_name)
                    
                    # Hot posts
                    for post in subreddit.hot(limit=limit // len(subreddits)):
                        # Check si symbol mentionné
                        text = post.title + " " + post.selftext
                        if symbol.lower() in text.lower():
                            posts.append(SocialPost(
                                source='reddit',
                                text=text[:500],  # Limite taille
                                author=post.author.name if post.author else "deleted",
                                timestamp=post.created_utc,
                                score=post.score
                            ))
                
                except Exception as e:
                    LOG.warning(f"⚠️ Erreur subreddit {sub_name}: {e}")
                    continue
            
            LOG.info(f"✅ {len(posts)} posts Reddit récupérés")
            return posts
        
        except Exception as e:
            LOG.error(f"❌ Erreur Reddit scraping: {e}")
            return []
    
    def analyze_sentiment_nlp(self, text: str) -> float:
        """Analyse sentiment avec NLP (transformers)"""
        if not self.sentiment_model:
            return self._analyze_sentiment_keywords(text)
        
        try:
            result = self.sentiment_model(text[:512])[0]
            
            # Convertit label en score -1 à +1
            label = result['label'].lower()
            confidence = result['score']
            
            if 'positive' in label:
                return confidence
            elif 'negative' in label:
                return -confidence
            else:
                return 0
        
        except Exception as e:
            LOG.warning(f"⚠️ NLP erreur: {e}, fallback keywords")
            return self._analyze_sentiment_keywords(text)
    
    def _analyze_sentiment_keywords(self, text: str) -> float:
        """Analyse sentiment basique par mots-clés (fallback)"""
        text_lower = text.lower()
        
        bullish_count = sum(1 for word in self.bullish_keywords if word in text_lower)
        bearish_count = sum(1 for word in self.bearish_keywords if word in text_lower)
        
        total = bullish_count + bearish_count
        if total == 0:
            return 0
        
        # Score normalisé -1 à +1
        score = (bullish_count - bearish_count) / total
        return score
    
    def analyze_posts(self, posts: List[SocialPost]) -> Dict:
        """Analyse batch de posts"""
        if not posts:
            return {
                'overall_sentiment': 'neutral',
                'sentiment_score': 0,
                'bullish_count': 0,
                'bearish_count': 0,
                'neutral_count': 0,
                'total_posts': 0
            }
        
        LOG.info(f"🔍 Analyse de {len(posts)} posts...")
        
        bullish = 0
        bearish = 0
        neutral = 0
        total_score = 0
        
        for post in posts:
            # Analyse sentiment
            sentiment_score = self.analyze_sentiment_nlp(post.text)
            post.sentiment_score = sentiment_score
            
            # Pondère par popularité (likes/score)
            weighted_score = sentiment_score * (1 + post.score / 100)
            total_score += weighted_score
            
            # Catégorise
            if sentiment_score > 0.3:
                bullish += 1
            elif sentiment_score < -0.3:
                bearish += 1
            else:
                neutral += 1
        
        # Score global
        avg_score = total_score / len(posts)
        
        # Détermine sentiment
        if avg_score > 0.3:
            overall = 'bullish'
        elif avg_score < -0.3:
            overall = 'bearish'
        else:
            overall = 'neutral'
        
        LOG.info(f"✅ Sentiment: {overall} ({avg_score:.2f})")
        
        return {
            'overall_sentiment': overall,
            'sentiment_score': avg_score,
            'bullish_count': bullish,
            'bearish_count': bearish,
            'neutral_count': neutral,
            'total_posts': len(posts),
            'bullish_pct': (bullish / len(posts)) * 100,
            'bearish_pct': (bearish / len(posts)) * 100,
            'posts': posts
        }
    
    def detect_fomo_panic(self, posts: List[SocialPost]) -> Dict:
        """Détecte FOMO (fear of missing out) et Panic"""
        fomo_keywords = ['fomo', 'moon', 'lambo', 'all in', 'yolo']
        panic_keywords = ['panic', 'crash', 'dump', 'sell everything', 'rugpull']
        
        fomo_count = 0
        panic_count = 0
        
        for post in posts:
            text_lower = post.text.lower()
            
            if any(kw in text_lower for kw in fomo_keywords):
                fomo_count += 1
            
            if any(kw in text_lower for kw in panic_keywords):
                panic_count += 1
        
        total = len(posts)
        
        fomo_level = (fomo_count / total) * 100 if total > 0 else 0
        panic_level = (panic_count / total) * 100 if total > 0 else 0
        
        # Alerte si FOMO/Panic > 20%
        alert = None
        if fomo_level > 20:
            alert = 'FOMO_HIGH'
        elif panic_level > 20:
            alert = 'PANIC_HIGH'
        
        return {
            'fomo_level': fomo_level,
            'panic_level': panic_level,
            'fomo_count': fomo_count,
            'panic_count': panic_count,
            'alert': alert
        }
    
    def get_market_emotion(self, symbol: str = "BTC") -> Dict:
        """
        Analyse complète du sentiment de marché
        Scrape Twitter + Reddit et analyse
        """
        LOG.info(f"🧠 Analyse émotion marché pour {symbol}")
        
        # 1. Scrape sources
        twitter_posts = self.scrape_twitter(symbol, limit=100)
        reddit_posts = self.scrape_reddit(symbol, limit=50)
        
        all_posts = twitter_posts + reddit_posts
        
        if not all_posts:
            LOG.warning("⚠️ Aucun post récupéré")
            return {
                'error': 'No data available',
                'overall_sentiment': 'neutral',
                'sentiment_score': 0
            }
        
        # 2. Analyse sentiment
        sentiment_result = self.analyze_posts(all_posts)
        
        # 3. Détecte FOMO/Panic
        fomo_panic = self.detect_fomo_panic(all_posts)
        
        # 4. Génère recommandation
        recommendation = self._get_recommendation(
            sentiment_result['overall_sentiment'],
            fomo_panic.get('alert')
        )
        
        return {
            **sentiment_result,
            'fomo_panic': fomo_panic,
            'recommendation': recommendation,
            'sources': {
                'twitter': len(twitter_posts),
                'reddit': len(reddit_posts)
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_recommendation(self, sentiment: str, alert: Optional[str]) -> str:
        """Génère recommandation trading"""
        if alert == 'FOMO_HIGH':
            return 'CAUTION - FOMO élevé, possibilité de top'
        elif alert == 'PANIC_HIGH':
            return 'OPPORTUNITY - Panic élevé, possibilité de bottom'
        elif sentiment == 'bullish':
            return 'POSITIVE - Sentiment bullish, peut entrer en position'
        elif sentiment == 'bearish':
            return 'NEGATIVE - Sentiment bearish, éviter longs'
        else:
            return 'NEUTRAL - Attendre signal plus clair'


# Mode DEMO pour tests sans APIs
class EmotionDetectorDemo(EmotionDetectorReal):
    """Version demo avec données simulées"""
    
    def __init__(self):
        super().__init__(use_transformers=False)
        LOG.info("⚠️ Mode DEMO activé (données simulées)")
    
    def scrape_twitter(self, symbol: str = "BTC", limit: int = 100) -> List[SocialPost]:
        """Génère tweets simulés"""
        import random
        
        demo_tweets = [
            f"${symbol} to the moon! 🚀",
            f"#{symbol} bullish breakout incoming",
            f"Just bought more {symbol}, HODL strong",
            f"{symbol} looking bearish, might dump",
            f"Selling my {symbol}, too risky",
            f"{symbol} sideways, waiting for signal"
        ]
        
        posts = []
        for i in range(min(limit, 20)):
            posts.append(SocialPost(
                source='twitter',
                text=random.choice(demo_tweets),
                author=f"user_{i}",
                timestamp=time.time(),
                score=random.randint(10, 200)
            ))
        
        return posts
    
    def scrape_reddit(self, symbol: str = "BTC", limit: int = 50) -> List[SocialPost]:
        """Génère posts Reddit simulés"""
        import random
        
        demo_posts = [
            f"{symbol} analysis - bullish pattern forming",
            f"Why {symbol} will reach new ATH",
            f"{symbol} bearish divergence spotted",
            f"Time to sell {symbol}?",
            f"{symbol} consolidation phase"
        ]
        
        posts = []
        for i in range(min(limit, 10)):
            posts.append(SocialPost(
                source='reddit',
                text=random.choice(demo_posts),
                author=f"redditor_{i}",
                timestamp=time.time(),
                score=random.randint(5, 100)
            ))
        
        return posts


if __name__ == "__main__":
    # Test en mode DEMO
    LOG.info("\n" + "=" * 50)
    LOG.info("TEST: Emotion AI Detector (MODE DEMO)")
    LOG.info("=" * 50)
    
    detector = EmotionDetectorDemo()
    
    result = detector.get_market_emotion("BTC")
    
    print(f"\n🧠 Résultats Analyse Émotion:")
    print(f"   Sentiment: {result['overall_sentiment']}")
    print(f"   Score: {result['sentiment_score']:.2f}")
    print(f"   Bullish: {result['bullish_pct']:.1f}%")
    print(f"   Bearish: {result['bearish_pct']:.1f}%")
    print(f"   Posts analysés: {result['total_posts']}")
    
    print(f"\n⚠️  FOMO/Panic:")
    fomo = result['fomo_panic']
    print(f"   FOMO: {fomo['fomo_level']:.1f}%")
    print(f"   Panic: {fomo['panic_level']:.1f}%")
    print(f"   Alert: {fomo.get('alert', 'None')}")
    
    print(f"\n💡 Recommandation:")
    print(f"   {result['recommendation']}")
    
    print(f"\n📊 Sources:")
    print(f"   Twitter: {result['sources']['twitter']}")
    print(f"   Reddit: {result['sources']['reddit']}")
