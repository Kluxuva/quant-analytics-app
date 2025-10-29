import pandas as pd
from datetime import datetime, timedelta
import threading
import time
import logging
from typing import Dict, List

import config
from backend.database import get_session, TickData, ResampledData

logger = logging.getLogger(__name__)

class DataResampler:
    """Resamples tick data into OHLCV bars for different timeframes"""
    
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.running = False
        self.thread = None
        self.last_resample_time = {tf: datetime.now() for tf in config.TIMEFRAMES}
        
    def _get_tick_data(self, symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Fetch tick data from database for a time range"""
        session = get_session()
        try:
            ticks = session.query(TickData).filter(
                TickData.symbol == symbol,
                TickData.timestamp >= start_time,
                TickData.timestamp < end_time
            ).order_by(TickData.timestamp).all()
            
            if not ticks:
                return pd.DataFrame()
            
            data = [{
                'timestamp': tick.timestamp,
                'price': tick.price,
                'quantity': tick.quantity
            } for tick in ticks]
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        finally:
            session.close()
    
    def _resample_to_ohlcv(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """Resample tick data to OHLCV bars"""
        if df.empty:
            return pd.DataFrame()
        
        df = df.set_index('timestamp')
        
        # Resample based on timeframe
        ohlcv = df['price'].resample(timeframe).ohlc()
        volume = df['quantity'].resample(timeframe).sum()
        
        ohlcv['volume'] = volume
        ohlcv = ohlcv.dropna()
        
        return ohlcv.reset_index()
    
    def _save_resampled_data(self, symbol: str, timeframe: str, ohlcv_df: pd.DataFrame):
        """Save resampled OHLCV data to database"""
        if ohlcv_df.empty:
            return
        
        session = get_session()
        try:
            for _, row in ohlcv_df.iterrows():
                # Check if record already exists
                existing = session.query(ResampledData).filter(
                    ResampledData.symbol == symbol,
                    ResampledData.timeframe == timeframe,
                    ResampledData.timestamp == row['timestamp']
                ).first()
                
                if not existing:
                    record = ResampledData(
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=row['timestamp'],
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        volume=row['volume']
                    )
                    session.add(record)
            
            session.commit()
        except Exception as e:
            logger.error(f"Error saving resampled data: {e}")
            session.rollback()
        finally:
            session.close()
    
    def _resample_worker(self):
        """Background worker that resamples data periodically"""
        while self.running:
            try:
                now = datetime.now()
                
                for timeframe in config.TIMEFRAMES:
                    # Determine resample interval
                    if timeframe == "1s":
                        interval = timedelta(seconds=1)
                    elif timeframe == "1m":
                        interval = timedelta(minutes=1)
                    elif timeframe == "5m":
                        interval = timedelta(minutes=5)
                    else:
                        continue
                    
                    # Check if it's time to resample
                    if now - self.last_resample_time[timeframe] >= interval:
                        for symbol in self.symbols:
                            self._resample_symbol(symbol, timeframe, interval)
                        self.last_resample_time[timeframe] = now
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in resample worker: {e}")
                time.sleep(5)
    
    def _resample_symbol(self, symbol: str, timeframe: str, interval: timedelta):
        """Resample a single symbol for a specific timeframe"""
        try:
            end_time = datetime.now()
            start_time = end_time - interval * 2  # Get extra data for safety
            
            # Fetch tick data
            tick_df = self._get_tick_data(symbol, start_time, end_time)
            
            if tick_df.empty:
                return
            
            # Resample to OHLCV
            ohlcv_df = self._resample_to_ohlcv(tick_df, timeframe)
            
            # Save to database
            self._save_resampled_data(symbol, timeframe, ohlcv_df)
            
            logger.debug(f"Resampled {symbol} for {timeframe}: {len(ohlcv_df)} bars")
            
        except Exception as e:
            logger.error(f"Error resampling {symbol} for {timeframe}: {e}")
    
    def start(self):
        """Start the resampler background thread"""
        if self.running:
            logger.warning("Resampler already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._resample_worker, daemon=True)
        self.thread.start()
        logger.info("Data resampler started")
    
    def stop(self):
        """Stop the resampler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Data resampler stopped")
    
    def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """Get OHLCV data for a symbol and timeframe"""
        session = get_session()
        try:
            bars = session.query(ResampledData).filter(
                ResampledData.symbol == symbol,
                ResampledData.timeframe == timeframe
            ).order_by(ResampledData.timestamp.desc()).limit(limit).all()
            
            if not bars:
                return pd.DataFrame()
            
            data = [{
                'timestamp': bar.timestamp,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume
            } for bar in reversed(bars)]
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
            
        finally:
            session.close()
