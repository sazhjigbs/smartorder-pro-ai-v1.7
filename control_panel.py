"""
Trading Control Panel - Minimal stub
"""

class TradingControlPanel:
    """Minimal control panel for dashboard"""
    
    def __init__(self, engine, config):
        self.engine = engine
        self.config = config
        self.alert_system = None
    
    def get_status(self):
        """Return system status"""
        return {
            'engine_running': self.engine.is_running if self.engine else False,
            'connected': True,
            'mode': 'live',
            'uptime': '0h 0m'
        }
