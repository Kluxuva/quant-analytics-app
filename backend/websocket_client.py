import json
import websocket
import threading
import time
from datetime import datetime
from collections import deque
import redis
import logging
from typing import List, Dict, Any

import config
from backend.database import get_session, TickData

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BinanceWebSocketClient:
    """WebSocket client for Binance futures tick data"""
    
    def __init__(self, symbols: List[str]):
        self.symbols = [s.lower() for s in symbols]
        self.ws = None
        self.running = False
        self.thread = None
        
        # Redis for real-time buffer
        try:
            self.redis_client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Redis not available: {e}. Using in-memory buffer.")
            self.redis_client = None
        
        # In-memory buffer for recent ticks
        self.tick_buffer = {symbol: deque(maxlen=1000) for symbol in self.symbols}
        
    def _build_ws_url(self) -> str:
        """Build WebSocket URL for multiple symbols"""
        streams = [f"{symbol}@trade" for symbol in self.symbols]
        stream_str = "/".join(streams)
        return f"{config.BINANCE_WS_BASE}/{stream_str}"
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            
            # Parse trade data
            symbol = data.get('s', '').lower()
            price = float(data.get('p', 0))
            quantity = float(data.get('q', 0))
            timestamp = datetime.fromtimestamp(data.get('T', 0) / 1000)
            
            tick = {
                'symbol': symbol,
                'timestamp': timestamp.isoformat(),
                'price': price,
                'quantity': quantity
            }
            
            # Store in buffer
            if symbol in self.tick_buffer:
                self.tick_buffer[symbol].append(tick)
            
            # Store in Redis
            if self.redis_client:
                key = f"tick:{symbol}"
                self.redis_client.lpush(key, json.dumps(tick))
                self.redis_client.ltrim(key, 0, 999)  # Keep last 1000 ticks
            
            # Periodically save to database (every 10th tick to reduce I/O)
            if len(self.tick_buffer[symbol]) % 10 == 0:
                self._save_to_db(symbol, tick)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _save_to_db(self, symbol: str, tick: Dict[str, Any]):
        """Save tick data to SQLite database"""
        try:
            session = get_session()
            tick_record = TickData(
                symbol=symbol,
                timestamp=datetime.fromisoformat(tick['timestamp']),
                price=tick['price'],
                quantity=tick['quantity']
            )
            session.add(tick_record)
            session.commit()
            session.close()
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.info(f"WebSocket closed: {close_status_code} - {close_msg}")
        if self.running:
            logger.info("Attempting to reconnect...")
            time.sleep(5)
            self._start_ws()
    
    def _on_open(self, ws):
        """Handle WebSocket open"""
        logger.info(f"WebSocket connected for symbols: {', '.join(self.symbols)}")
    
    def _start_ws(self):
        """Start WebSocket connection"""
        url = self._build_ws_url()
        self.ws = websocket.WebSocketApp(
            url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        self.ws.run_forever()
    
    def start(self):
        """Start WebSocket client in background thread"""
        if self.running:
            logger.warning("WebSocket client already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._start_ws, daemon=True)
        self.thread.start()
        logger.info("WebSocket client started")
    
    def stop(self):
        """Stop WebSocket client"""
        self.running = False
        if self.ws:
            self.ws.close()
        logger.info("WebSocket client stopped")
    
    def get_recent_ticks(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent ticks from buffer"""
        symbol = symbol.lower()
        if symbol not in self.tick_buffer:
            return []
        return list(self.tick_buffer[symbol])[-limit:]
    
    def get_latest_price(self, symbol: str) -> float:
        """Get latest price for a symbol"""
        symbol = symbol.lower()
        if symbol in self.tick_buffer and len(self.tick_buffer[symbol]) > 0:
            return self.tick_buffer[symbol][-1]['price']
        return 0.0
