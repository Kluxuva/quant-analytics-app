# System Architecture Diagram

## High-Level Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                        USER INTERFACE                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Streamlit Web Application                     │ │
│  │                                                            │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │ │
│  │  │ Overview │ │Analytics │ │  Alerts  │ │  Export  │    │ │
│  │  │   Tab    │ │   Tab    │ │   Tab    │ │   Tab    │    │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │ │
│  │                                                            │ │
│  │  Features:                                                 │ │
│  │  - Real-time price charts (Candlestick)                   │ │
│  │  - Volume analysis                                         │ │
│  │  - Spread & Z-score visualization                         │ │
│  │  - Correlation heatmaps                                    │ │
│  │  - Interactive controls                                    │ │
│  │  - Alert configuration UI                                  │ │
│  │  - Data export buttons                                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              │ HTTP/API Calls                    │
│                              ▼                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                     BACKEND ORCHESTRATOR                         │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │               orchestrator.py                              │ │
│  │                                                            │ │
│  │  Responsibilities:                                          │ │
│  │  - Coordinate all backend services                         │ │
│  │  - Manage service lifecycle                                │ │
│  │  - Provide unified API to frontend                         │ │
│  │  - Handle graceful shutdown                                │ │
│  │  - Data flow coordination                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│              ┌───────────────┼───────────────┐                  │
│              │               │               │                  │
│              ▼               ▼               ▼                  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   WebSocket  │    │     Data     │    │  Analytics   │
│    Client    │    │  Resampler   │    │    Engine    │
│              │    │              │    │              │
│ websocket_   │    │ resampler.py │    │ analytics.py │
│ client.py    │    │              │    │              │
│              │    │              │    │              │
│ - Connect to │    │ - Convert    │    │ - Hedge      │
│   Binance WS │    │   tick →     │    │   ratio      │
│ - Buffer     │    │   OHLCV      │    │ - Spread     │
│   ticks      │    │ - Multi-     │    │ - Z-score    │
│ - Store in   │    │   timeframe  │    │ - Correlation│
│   Redis      │    │   (1s/1m/5m) │    │ - ADF test   │
│ - Persist    │    │ - Background │    │ - Liquidity  │
│   to DB      │    │   worker     │    │   metrics    │
│              │    │              │    │              │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                       STORAGE LAYER                              │
│                                                                  │
│  ┌────────────────────┐              ┌────────────────────┐    │
│  │   Redis (Cache)    │              │  SQLite Database   │    │
│  │                    │              │                    │    │
│  │  - Tick buffer     │              │  Tables:           │    │
│  │  - Last 1000 ticks │              │  - tick_data       │    │
│  │  - Real-time       │              │  - resampled_data  │    │
│  │    access          │              │  - analytics_      │    │
│  │  - Optional        │              │    results         │    │
│  │    (falls back to  │              │                    │    │
│  │    in-memory)      │              │  Features:         │    │
│  │                    │              │  - Indexed queries │    │
│  │                    │              │  - ACID            │    │
│  │                    │              │  - Persistent      │    │
│  └────────────────────┘              │  - Lightweight     │    │
│                                       └────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
                           ▲
                           │
                           │ WebSocket Stream
                           │
┌──────────────────────────────────────────────────────────────────┐
│                   EXTERNAL DATA SOURCE                           │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │           Binance Futures WebSocket API                    │ │
│  │                                                            │ │
│  │  wss://fstream.binance.com/ws/{symbol}@trade              │ │
│  │                                                            │ │
│  │  Provides:                                                 │ │
│  │  - Real-time tick data                                     │ │
│  │  - Symbol, Price, Quantity, Timestamp                      │ │
│  │  - High frequency updates                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## Component Interaction Flow

### 1. Data Ingestion Flow
```
Binance WS → WebSocket Client → Redis Buffer → SQLite (tick_data)
                    │
                    └─→ In-Memory Buffer (fallback)
```

### 2. Data Processing Flow
```
SQLite (tick_data) → Resampler → OHLCV Bars → SQLite (resampled_data)
                                      │
                                      └─→ Multiple Timeframes (1s, 1m, 5m)
```

### 3. Analytics Flow
```
SQLite (resampled_data) → Analytics Engine → Computations → SQLite (analytics_results)
                               │                                    │
                               │                                    ▼
                               └─────────────────────────→ Alert Manager
                                                                    │
                                                                    ▼
                                                           Trigger Alerts
```

### 4. Visualization Flow
```
Frontend Request → Orchestrator → Database Query → Data Processing → Plotly Charts
                                       │
                                       └─→ Real-time Updates (via polling)
```

## Alert System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Alert Manager                          │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │              Alert Definitions                    │ │
│  │                                                   │ │
│  │  Alert {                                          │ │
│  │    name: string                                   │ │
│  │    condition: greater/less/equal                  │ │
│  │    metric: z_score/correlation/etc.               │ │
│  │    threshold: float                               │ │
│  │    symbol_pair: string                            │ │
│  │    enabled: boolean                               │ │
│  │  }                                                │ │
│  └───────────────────────────────────────────────────┘ │
│                         │                               │
│                         ▼                               │
│  ┌───────────────────────────────────────────────────┐ │
│  │            Condition Checking                     │ │
│  │                                                   │ │
│  │  - Receives analytics data                        │ │
│  │  - Evaluates each alert condition                 │ │
│  │  - Tracks trigger history                         │ │
│  └───────────────────────────────────────────────────┘ │
│                         │                               │
│                         ▼                               │
│  ┌───────────────────────────────────────────────────┐ │
│  │            Callback Execution                     │ │
│  │                                                   │ │
│  │  - Trigger registered callbacks                   │ │
│  │  - Log to alert history                           │ │
│  │  - Update trigger count                           │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Threading Model

```
Main Thread
    │
    ├─→ Streamlit UI Thread (Frontend)
    │
    └─→ Backend Orchestrator
            │
            ├─→ WebSocket Client Thread
            │       └─→ Continuous connection to Binance
            │
            └─→ Data Resampler Thread
                    └─→ Periodic OHLCV generation
```

## Database Schema

### tick_data Table
```sql
CREATE TABLE tick_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR NOT NULL,
    timestamp DATETIME NOT NULL,
    price FLOAT NOT NULL,
    quantity FLOAT NOT NULL,
    INDEX idx_symbol_timestamp (symbol, timestamp)
);
```

### resampled_data Table
```sql
CREATE TABLE resampled_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR NOT NULL,
    timeframe VARCHAR NOT NULL,
    timestamp DATETIME NOT NULL,
    open FLOAT NOT NULL,
    high FLOAT NOT NULL,
    low FLOAT NOT NULL,
    close FLOAT NOT NULL,
    volume FLOAT NOT NULL,
    INDEX idx_symbol_timeframe_timestamp (symbol, timeframe, timestamp)
);
```

### analytics_results Table
```sql
CREATE TABLE analytics_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_pair VARCHAR NOT NULL,
    timestamp DATETIME NOT NULL,
    timeframe VARCHAR NOT NULL,
    hedge_ratio FLOAT,
    spread FLOAT,
    z_score FLOAT,
    correlation FLOAT,
    adf_statistic FLOAT,
    adf_pvalue FLOAT,
    spread_mean FLOAT,
    spread_std FLOAT,
    INDEX idx_pair_timeframe_timestamp (symbol_pair, timeframe, timestamp)
);
```

## Design Principles

### 1. Loose Coupling
- Components communicate through well-defined interfaces
- Easy to swap implementations (e.g., PostgreSQL instead of SQLite)
- Minimal dependencies between modules

### 2. Separation of Concerns
- Data ingestion (WebSocket Client)
- Data processing (Resampler)
- Analytics computation (Analytics Engine)
- Visualization (Frontend)
- Each has single responsibility

### 3. Scalability Considerations
- **Current**: Single machine, SQLite, optional Redis
- **Future**: 
  - Replace SQLite with PostgreSQL/TimescaleDB
  - Add message queue (Kafka/RabbitMQ)
  - Horizontal scaling of analytics workers
  - Load balancer for frontend
  - Distributed Redis cluster

### 4. Extensibility
- New data sources: Implement client interface
- New analytics: Add methods to analytics engine
- New timeframes: Update configuration
- New visualizations: Add to frontend

### 5. Fault Tolerance
- WebSocket reconnection logic
- Database transaction handling
- Graceful degradation (Redis optional)
- Error logging throughout

## Technology Choices Rationale

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Frontend | Streamlit | Rapid development, built-in reactivity |
| Visualization | Plotly | Interactive, professional charts |
| Database | SQLite | Zero-config, sufficient for prototype |
| Cache | Redis | Fast, optional (graceful fallback) |
| WebSocket | websocket-client | Reliable, well-maintained |
| Analytics | pandas/numpy/scipy | Industry standard for quant |
| Threading | Python threading | Simple, adequate for I/O-bound |

## Performance Characteristics

### Latency
- **WebSocket to DB**: < 100ms
- **Tick to OHLCV**: 1s - 5m (based on timeframe)
- **Analytics computation**: < 500ms (for typical window)
- **UI update**: Configurable (1-30 seconds)

### Throughput
- **Tick ingestion**: ~10-100 ticks/second
- **OHLCV generation**: Real-time based on timeframe
- **Analytics**: Computed on demand
- **Database**: Limited by SQLite (~50k writes/sec)

### Storage
- **Tick data**: ~1KB per tick
- **OHLCV data**: ~100 bytes per bar
- **Analytics**: ~200 bytes per result
- **Growth**: ~1GB per week (2 symbols, full tick data)

## Monitoring & Observability

### Logging
- Component-level logging
- Configurable log levels
- Separate log files per component

### Metrics (Future)
- Tick ingestion rate
- Analytics computation time
- Alert trigger frequency
- Database query performance

### Health Checks (Future)
- WebSocket connection status
- Database connectivity
- Redis availability
- Data freshness
