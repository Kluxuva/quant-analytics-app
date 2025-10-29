import threading
import time
import logging
from datetime import datetime
from typing import List, Dict, Callable
import json

logger = logging.getLogger(__name__)

class Alert:
    """Alert configuration"""
    
    def __init__(self, 
                 name: str,
                 condition: str,
                 metric: str,
                 threshold: float,
                 symbol_pair: str,
                 enabled: bool = True):
        self.name = name
        self.condition = condition  # 'greater', 'less', 'equal'
        self.metric = metric  # 'z_score', 'spread', 'correlation', etc.
        self.threshold = threshold
        self.symbol_pair = symbol_pair
        self.enabled = enabled
        self.triggered_count = 0
        self.last_triggered = None
    
    def check(self, value: float) -> bool:
        """Check if alert condition is met"""
        if not self.enabled:
            return False
        
        if self.condition == 'greater':
            return value > self.threshold
        elif self.condition == 'less':
            return value < self.threshold
        elif self.condition == 'equal':
            return abs(value - self.threshold) < 0.001
        elif self.condition == 'greater_equal':
            return value >= self.threshold
        elif self.condition == 'less_equal':
            return value <= self.threshold
        
        return False
    
    def trigger(self):
        """Mark alert as triggered"""
        self.triggered_count += 1
        self.last_triggered = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert alert to dictionary"""
        return {
            'name': self.name,
            'condition': self.condition,
            'metric': self.metric,
            'threshold': self.threshold,
            'symbol_pair': self.symbol_pair,
            'enabled': self.enabled,
            'triggered_count': self.triggered_count,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None
        }

class AlertManager:
    """Manages and monitors alerts"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_history: List[Dict] = []
        self.running = False
        self.thread = None
        self.callbacks: List[Callable] = []
        self.max_history = 100
    
    def add_alert(self, alert: Alert):
        """Add a new alert"""
        self.alerts.append(alert)
        logger.info(f"Added alert: {alert.name}")
    
    def remove_alert(self, alert_name: str):
        """Remove an alert by name"""
        self.alerts = [a for a in self.alerts if a.name != alert_name]
        logger.info(f"Removed alert: {alert_name}")
    
    def get_alert(self, alert_name: str) -> Alert:
        """Get alert by name"""
        for alert in self.alerts:
            if alert.name == alert_name:
                return alert
        return None
    
    def update_alert(self, alert_name: str, **kwargs):
        """Update alert properties"""
        alert = self.get_alert(alert_name)
        if alert:
            for key, value in kwargs.items():
                if hasattr(alert, key):
                    setattr(alert, key, value)
            logger.info(f"Updated alert: {alert_name}")
    
    def check_alerts(self, analytics_data: Dict):
        """Check all alerts against current analytics data"""
        triggered = []
        
        for alert in self.alerts:
            if not alert.enabled:
                continue
            
            # Get the metric value from analytics data
            symbol_pair = alert.symbol_pair
            if symbol_pair not in analytics_data:
                continue
            
            pair_data = analytics_data[symbol_pair]
            metric_value = pair_data.get(alert.metric)
            
            if metric_value is None:
                continue
            
            # Check condition
            if alert.check(metric_value):
                alert.trigger()
                triggered.append(alert)
                
                # Record in history
                event = {
                    'timestamp': datetime.now().isoformat(),
                    'alert_name': alert.name,
                    'metric': alert.metric,
                    'value': metric_value,
                    'threshold': alert.threshold,
                    'condition': alert.condition,
                    'symbol_pair': symbol_pair
                }
                self.alert_history.append(event)
                
                # Trim history
                if len(self.alert_history) > self.max_history:
                    self.alert_history = self.alert_history[-self.max_history:]
                
                # Trigger callbacks
                for callback in self.callbacks:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.error(f"Error in alert callback: {e}")
        
        return triggered
    
    def add_callback(self, callback: Callable):
        """Add callback function to be called when alert triggers"""
        self.callbacks.append(callback)
    
    def get_all_alerts(self) -> List[Dict]:
        """Get all alerts as dictionaries"""
        return [alert.to_dict() for alert in self.alerts]
    
    def get_alert_history(self, limit: int = 50) -> List[Dict]:
        """Get recent alert history"""
        return self.alert_history[-limit:]
    
    def clear_history(self):
        """Clear alert history"""
        self.alert_history = []
        logger.info("Cleared alert history")
    
    def create_preset_alerts(self, symbol1: str, symbol2: str):
        """Create common preset alerts for a symbol pair"""
        pair = f"{symbol1}_{symbol2}"
        
        presets = [
            Alert(f"High Z-Score ({pair})", "greater", "current_z_score", 2.0, pair),
            Alert(f"Low Z-Score ({pair})", "less", "current_z_score", -2.0, pair),
            Alert(f"Extreme High Z-Score ({pair})", "greater", "current_z_score", 3.0, pair),
            Alert(f"Extreme Low Z-Score ({pair})", "less", "current_z_score", -3.0, pair),
            Alert(f"Low Correlation ({pair})", "less", "current_correlation", 0.5, pair),
        ]
        
        for alert in presets:
            self.add_alert(alert)
        
        logger.info(f"Created {len(presets)} preset alerts for {pair}")

# Global alert manager instance
alert_manager = AlertManager()
