# -*- coding: utf-8 -*-
"""Signal Aggregator - Combine AI + Technical + Sentiment signals"""
import logging
from typing import Dict
from datetime import datetime

LOG = logging.getLogger(__name__)

class SignalAggregator:
    def __init__(self, weights: Dict = None):
        self.weights = weights or {'ai': 0.4, 'technical': 0.3, 'volume': 0.2, 'sentiment': 0.1}
        LOG.info(f"Signal Aggregator ready")
    
    def aggregate(self, signals: Dict) -> Dict:
        scores = {'long': 0, 'short': 0, 'neutral': 0}
        for source, signal in signals.items():
            if source not in self.weights:
                continue
            weight = self.weights[source]
            direction = signal.get('direction', 'neutral')
            confidence = signal.get('confidence', 0.5)
            scores[direction] += weight * confidence
        
        final_direction = max(scores, key=scores.get)
        return {
            'direction': final_direction if scores[final_direction] > 0.6 else 'neutral',
            'confidence': scores[final_direction],
            'scores': scores,
            'timestamp': datetime.now().isoformat()
        }
