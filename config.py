import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Database configuration
SQLITE_DB = str(DATA_DIR / "analytics.db")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Binance WebSocket configuration
BINANCE_WS_BASE = "wss://fstream.binance.com/ws"
DEFAULT_SYMBOLS = ["btcusdt", "ethusdt"]

# Resampling timeframes
TIMEFRAMES = ["1s", "1m", "5m"]

# Analytics configuration
DEFAULT_WINDOW_SIZE = 20
Z_SCORE_WINDOW = 20
CORRELATION_WINDOW = 50
ADF_SIGNIFICANCE = 0.05

# Alert configuration
ALERT_CHECK_INTERVAL = 1  # seconds

# Frontend configuration
STREAMLIT_PORT = 8501
UPDATE_INTERVAL = 500  # milliseconds
