"""
Backend package for real-time quantitative analytics.

This package provides:
- Real-time data ingestion from Binance WebSocket
- Multi-timeframe data resampling (tick to OHLCV)
- Statistical analytics (hedge ratio, spread, z-score, correlation, ADF)
- Alert management system
- Database persistence layer
"""

from backend.orchestrator import get_backend, start_backend
from backend.alerts import alert_manager

__all__ = ['get_backend', 'start_backend', 'alert_manager']

__version__ = '1.0.0'
