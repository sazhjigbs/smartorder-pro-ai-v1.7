"""
Alert System - Minimal stub
"""

class AlertSystem:
    """Minimal alert system"""
    
    def __init__(self, config):
        self.config = config
        self.alerts = []
    
    def get_alerts(self):
        """Return recent alerts"""
        return self.alerts
