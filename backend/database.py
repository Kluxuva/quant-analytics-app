from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import config

Base = declarative_base()

class TickData(Base):
    """Raw tick data from WebSocket"""
    __tablename__ = 'tick_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
    )

class ResampledData(Base):
    """Resampled OHLCV data"""
    __tablename__ = 'resampled_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    timeframe = Column(String, nullable=False)  # 1s, 1m, 5m
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    __table_args__ = (
        Index('idx_symbol_timeframe_timestamp', 'symbol', 'timeframe', 'timestamp'),
    )

class AnalyticsResult(Base):
    """Computed analytics results"""
    __tablename__ = 'analytics_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol_pair = Column(String, nullable=False, index=True)  # e.g., "btcusdt_ethusdt"
    timestamp = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String, nullable=False)
    
    # Statistics
    hedge_ratio = Column(Float)
    spread = Column(Float)
    z_score = Column(Float)
    correlation = Column(Float)
    adf_statistic = Column(Float)
    adf_pvalue = Column(Float)
    
    # Additional metrics
    spread_mean = Column(Float)
    spread_std = Column(Float)
    
    __table_args__ = (
        Index('idx_pair_timeframe_timestamp', 'symbol_pair', 'timeframe', 'timestamp'),
    )

# Database initialization
engine = create_engine(f'sqlite:///{config.SQLITE_DB}', echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(engine)
    print(f"Database initialized at {config.SQLITE_DB}")

def get_session():
    """Get a new database session"""
    return SessionLocal()
