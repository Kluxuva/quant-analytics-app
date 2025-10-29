import logging
import time
import signal
import sys
from typing import List
import pandas as pd

import config
from backend.database import init_db, get_session, ResampledData
from backend.websocket_client import BinanceWebSocketClient
from backend.resampler import DataResampler
from backend.analytics import AnalyticsEngine
from backend.alerts import alert_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BackendOrchestrator:
    """Main orchestrator for backend services"""
    
    def __init__(self, symbols: List[str] = None):
        if symbols is None:
            symbols = config.DEFAULT_SYMBOLS
        
        self.symbols = [s.lower() for s in symbols]
        
        # Initialize components
        self.ws_client = BinanceWebSocketClient(self.symbols)
        self.resampler = DataResampler(self.symbols)
        self.analytics_engine = AnalyticsEngine()
        self.alert_manager = alert_manager
        
        # Create preset alerts
        if len(self.symbols) >= 2:
            self.alert_manager.create_preset_alerts(
                self.symbols[0], self.symbols[1]
            )
        
        # State
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        #signal.signal(signal.SIGINT, self._signal_handler)
        #signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Shutdown signal received")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """Start all backend services"""
        logger.info("Starting backend services...")
        
        # Initialize database
        init_db()
        
        # Start WebSocket client
        self.ws_client.start()
        time.sleep(2)  # Wait for initial connection
        
        # Start resampler
        self.resampler.start()
        
        # Process historical data if needed
        logger.info("Checking for historical data to process...")
        self._process_historical_data()
        
        self.running = True
        logger.info("Backend services started successfully")
    
    def _process_historical_data(self):
        """Process any unprocessed historical tick data into OHLCV bars"""
        try:
            from backend.database import get_session, TickData, ResampledData
            
            session = get_session()
            
            for symbol in self.symbols:
                for timeframe in config.TIMEFRAMES:
                    # Check if we have bars for this timeframe
                    bar_count = session.query(ResampledData).filter(
                        ResampledData.symbol == symbol,
                        ResampledData.timeframe == timeframe
                    ).count()
                    
                    # Skip if already have enough data
                    if bar_count >= 100:
                        logger.info(f"Skipping {symbol} - {timeframe} (already has {bar_count} bars)")
                        continue
                    
                    # ONLY process 1s timeframe from historical data
                    # 1m and 5m will accumulate naturally as live data comes in
                    if timeframe != '1s':
                        logger.info(f"Skipping {symbol} - {timeframe} (will accumulate from live data)")
                        continue
                    
                    logger.info(f"Processing historical data for {symbol} - {timeframe}")
                    
                    # Get last 100K ticks for 1s bars (gives ~1600 bars)
                    tick_limit = 100000
                    
                    ticks = session.query(TickData).filter(
                        TickData.symbol == symbol
                    ).order_by(TickData.timestamp.desc()).limit(tick_limit).all()
                    
                    if not ticks:
                        logger.info(f"No ticks found for {symbol}")
                        continue
                    
                    # Reverse to chronological order
                    ticks = list(reversed(ticks))
                    
                    logger.info(f"Processing {len(ticks)} recent ticks for {symbol} - {timeframe}")
                    
                    # Quick DataFrame conversion
                    df = pd.DataFrame([
                        {
                            'timestamp': pd.to_datetime(t.timestamp),
                            'price': float(t.price),
                            'quantity': float(t.quantity)
                        } for t in ticks
                    ])
                    
                    if df.empty:
                        continue
                    
                    df = df.set_index('timestamp')
                    
                    # Resample to 1s
                    ohlcv = df['price'].resample(timeframe).ohlc()
                    volume = df['quantity'].resample(timeframe).sum()
                    ohlcv['volume'] = volume
                    ohlcv = ohlcv.dropna().reset_index()
                    
                    if not ohlcv.empty:
                        # Save
                        self.resampler._save_resampled_data(symbol, timeframe, ohlcv)
                        logger.info(f"✓ Processed {len(ohlcv)} {timeframe} bars for {symbol}")
                    else:
                        logger.warning(f"No OHLCV data created for {symbol} - {timeframe}")
            
            session.close()
            logger.info("Historical data processing complete")
            
        except Exception as e:
            logger.error(f"Error processing historical data: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def stop(self):
        """Stop all backend services"""
        logger.info("Stopping backend services...")
        
        self.running = False
        self.ws_client.stop()
        self.resampler.stop()
        
        logger.info("Backend services stopped")
    
    def get_latest_prices(self) -> dict:
        """Get latest prices for all symbols"""
        return {
            symbol: self.ws_client.get_latest_price(symbol)
            for symbol in self.symbols
        }
    
    def get_ohlcv_data(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """Get OHLCV data for a symbol"""
        return self.resampler.get_ohlcv(symbol, timeframe, limit)
    
    def compute_analytics(self, 
                         symbol1: str, 
                         symbol2: str, 
                         timeframe: str,
                         window_size: int = None,
                         regression_method: str = 'ols') -> dict:
        """Compute pair analytics"""
        df1 = self.get_ohlcv_data(symbol1, timeframe)
        df2 = self.get_ohlcv_data(symbol2, timeframe)
        
        if df1.empty or df2.empty:
            return {}
        
        analytics = self.analytics_engine.compute_pair_analytics(
            df1, df2, symbol1, symbol2, timeframe,
            window_size=window_size,
            regression_method=regression_method
        )
        
        # Check alerts
        if analytics:
            self.alert_manager.check_alerts({
                f"{symbol1}_{symbol2}": analytics
            })
        
        return analytics
    
    def get_basic_stats(self, symbol: str, timeframe: str) -> dict:
        """Get basic statistics for a symbol"""
        df = self.get_ohlcv_data(symbol, timeframe)
        if df.empty:
            return {}
        return self.analytics_engine.compute_basic_stats(df)
    
    def get_liquidity_metrics(self, symbol: str, timeframe: str) -> dict:
        """Get liquidity metrics for a symbol"""
        df = self.get_ohlcv_data(symbol, timeframe)
        if df.empty:
            return {}
        return self.analytics_engine.compute_liquidity_metrics(df)
    
    def export_data(self, symbol: str, timeframe: str, format: str = 'csv') -> str:
        """Export data to file"""
        df = self.get_ohlcv_data(symbol, timeframe, limit=10000)
        
        if df.empty:
            return None
        
        filename = f"{config.DATA_DIR}/{symbol}_{timeframe}_{int(time.time())}.{format}"
        
        if format == 'csv':
            df.to_csv(filename, index=False)
        elif format == 'json':
            df.to_json(filename, orient='records', date_format='iso')
        
        logger.info(f"Exported data to {filename}")
        return filename
    
    def get_data_summary(self) -> dict:
        """Get summary of available data"""
        session = get_session()
        try:
            summary = {}
            for symbol in self.symbols:
                summary[symbol] = {}
                for timeframe in config.TIMEFRAMES:
                    count = session.query(ResampledData).filter(
                        ResampledData.symbol == symbol,
                        ResampledData.timeframe == timeframe
                    ).count()
                    summary[symbol][timeframe] = count
            return summary
        finally:
            session.close()

# Global backend instance
backend = None

def get_backend() -> BackendOrchestrator:
    """Get or create global backend instance"""
    global backend
    if backend is None:
        backend = BackendOrchestrator()
    return backend

def start_backend(symbols: List[str] = None):
    """Start the backend services"""
    global backend
    backend = BackendOrchestrator(symbols)
    backend.start()
    return backend