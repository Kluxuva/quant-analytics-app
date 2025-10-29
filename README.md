# Real-Time Quantitative Analytics Dashboard

A production-grade real-time analytics platform for pair trading strategies, featuring live data ingestion from Binance WebSocket, statistical analysis, and interactive visualization.

## 🚀 Features

### Core Functionality
- **Real-time Data Ingestion**: WebSocket connection to Binance Futures for live tick data
- **Multi-timeframe Resampling**: Automatic OHLCV conversion (1s, 1m, 5m)
- **Comprehensive Analytics**:
  - Hedge ratio computation (OLS, Huber, Theil-Sen regression)
  - Spread calculation and monitoring
  - Rolling z-score for mean reversion signals
  - Rolling correlation analysis
  - Augmented Dickey-Fuller (ADF) stationarity test
  - Liquidity metrics (volume analysis)
- **Alert System**: Custom alert creation with real-time monitoring
- **Interactive Dashboard**: Streamlit-based UI with Plotly charts
- **Data Export**: CSV/JSON export functionality

### Advanced Extensions
- Multiple regression methods for robust hedge estimation
- Liquidity filtering capabilities
- Alert history tracking
- Real-time price monitoring
- Modular architecture for easy extension

## 📋 Prerequisites

- Python 3.8 or higher
- Redis (optional - system falls back to in-memory if unavailable)
- Internet connection (for Binance WebSocket)

## 🛠️ Installation

### 1. Clone/Extract the Project
```bash
cd quant-analytics-app
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Optional: Install Redis (for better performance)
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# Windows
# Download from https://redis.io/download
```

## 🎯 Quick Start

### Single Command Launch
```bash
streamlit run app.py
```

The application will:
1. Initialize the SQLite database
2. Connect to Binance WebSocket
3. Start data ingestion and resampling
4. Launch the dashboard at `http://localhost:8501`

### Initial Setup (1-2 minutes)
- Wait for initial data accumulation
- Start with 1m timeframe for faster results
- Default symbols: BTCUSDT, ETHUSDT

## 📊 Usage Guide

### 1. Overview Tab
- View real-time prices for both symbols
- Candlestick charts with OHLCV data
- Volume analysis
- Data availability summary

### 2. Analytics Tab
- **Configure Parameters**:
  - Select symbol pair
  - Choose timeframe (1s/1m/5m)
  - Adjust rolling window size
  - Select regression method
- **Compute Analytics**: Click "Compute Analytics" button
- **View Results**:
  - Hedge ratio and R²
  - Spread and z-score charts
  - Rolling correlation
  - ADF stationarity test results

### 3. Alerts Tab
- **Create Alerts**: Define custom conditions (e.g., z-score > 2)
- **Monitor Active Alerts**: View and manage all alerts
- **Alert History**: Track triggered alerts

### 4. Data Export Tab
- Select symbol and timeframe
- Choose format (CSV/JSON)
- Download processed data
- View data availability

## 🏗️ Architecture

### System Design
```
┌─────────────────────────────────────────────────────────────┐
│                   FRONTEND (Streamlit)                       │
│  - Interactive Charts (Plotly)                               │
│  - Real-time Updates                                         │
│  - User Controls                                             │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│              BACKEND ORCHESTRATOR                            │
│  - Coordinates all services                                  │
│  - Manages data flow                                         │
└─────┬────────────────────┬────────────────────┬─────────────┘
      │                    │                    │
┌─────▼──────┐  ┌─────────▼────────┐  ┌────────▼──────────┐
│   WebSocket │  │  Data Resampler  │  │ Analytics Engine  │
│   Client    │  │  - Tick → OHLCV  │  │  - Statistics     │
│             │  │  - Multi-timeframe│  │  - Regression     │
└─────┬──────┘  └─────────┬─────────┘  │  - Tests          │
      │                    │             └────────┬───────────┘
      │                    │                      │
┌─────▼────────────────────▼──────────────────────▼───────────┐
│                    STORAGE LAYER                             │
│  - Redis: Real-time tick buffer (optional)                  │
│  - SQLite: Persistent OHLCV and analytics                   │
└──────────────────────────────────────────────────────────────┘
      ▲
      │
┌─────┴──────────┐
│ Binance WS API │
└────────────────┘
```

### Component Design

#### 1. Data Ingestion (`backend/websocket_client.py`)
- Connects to Binance WebSocket streams
- Buffers tick data in Redis/memory
- Persists to SQLite database
- Thread-safe implementation

#### 2. Data Resampler (`backend/resampler.py`)
- Converts tick data to OHLCV bars
- Supports multiple timeframes
- Background worker for continuous resampling
- Efficient database operations

#### 3. Analytics Engine (`backend/analytics.py`)
- Statistical computations
- Multiple regression algorithms
- Time-series analysis (ADF test)
- Modular analytics functions

#### 4. Alert System (`backend/alerts.py`)
- Custom alert definitions
- Real-time condition monitoring
- Alert history tracking
- Callback support

#### 5. Orchestrator (`backend/orchestrator.py`)
- Coordinates all backend services
- Provides unified API
- Manages lifecycle
- Handles graceful shutdown

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Symbols to track
DEFAULT_SYMBOLS = ["btcusdt", "ethusdt"]

# Timeframes
TIMEFRAMES = ["1s", "1m", "5m"]

# Analytics parameters
DEFAULT_WINDOW_SIZE = 20
Z_SCORE_WINDOW = 20
CORRELATION_WINDOW = 50
ADF_SIGNIFICANCE = 0.05

# Database paths
SQLITE_DB = str(DATA_DIR / "analytics.db")
```

## 📈 Analytics Methodology

### Hedge Ratio Estimation
**Purpose**: Determine the optimal ratio for pair trading

**Methods**:
1. **OLS (Ordinary Least Squares)**: Fast, standard regression
2. **Huber Regression**: Robust to outliers
3. **Theil-Sen Regression**: Highly robust, slower

**Formula**: `Y = β * X + α`
- β = hedge ratio
- Used to construct market-neutral spread

### Spread Construction
**Formula**: `Spread = Price_Y - (HedgeRatio * Price_X)`

**Purpose**: Create stationary series for mean reversion

### Z-Score Calculation
**Formula**: `Z = (Spread - μ) / σ`
- μ = rolling mean of spread
- σ = rolling standard deviation

**Trading Signal Interpretation**:
- Z > 2: Spread overextended (potential short)
- Z < -2: Spread overextended (potential long)
- Z → 0: Mean reversion opportunity

### Augmented Dickey-Fuller Test
**Purpose**: Test spread stationarity

**Interpretation**:
- p-value < 0.05: Spread is stationary (good for mean reversion)
- p-value ≥ 0.05: Spread is non-stationary (poor for mean reversion)

### Rolling Correlation
**Purpose**: Monitor relationship strength

**Interpretation**:
- Correlation > 0.7: Strong positive relationship
- Correlation < 0.3: Weak relationship (risky for pair trading)

## 🎨 Extensibility

### Adding New Data Sources
1. Implement new client in `backend/` following `websocket_client.py` pattern
2. Update `orchestrator.py` to include new source
3. Minimal changes required due to loose coupling

### Adding New Analytics
1. Add method to `analytics.py`
2. Call from `orchestrator.py`
3. Update frontend to display results

### Adding New Timeframes
1. Add to `config.TIMEFRAMES`
2. Resampler automatically handles new timeframes

### Scaling Considerations
**Current Design Supports**:
- Multiple data sources via adapter pattern
- Horizontal scaling of analytics (separate processes)
- Database can be swapped (PostgreSQL/TimescaleDB for production)
- Redis cluster for distributed caching

**Future Enhancements**:
- Message queue (RabbitMQ/Kafka) for event-driven architecture
- Microservices deployment
- Time-series database (InfluxDB/TimescaleDB)
- Kubernetes orchestration

## 🤖 LLM Usage Transparency

### ChatGPT/Claude Usage
This project was developed with significant assistance from AI language models:

**Areas of AI Assistance**:
1. **Architecture Design**: Initial system design and component structure
2. **Code Implementation**: Complete implementation of all modules
3. **Documentation**: README, docstrings, and comments
4. **Best Practices**: Threading, error handling, database design
5. **Statistical Methods**: Implementation of regression and tests

**Prompts Used** (examples):
- "Design a modular architecture for real-time pair trading analytics"
- "Implement WebSocket client for Binance with tick data buffering"
- "Create Streamlit dashboard with real-time updates and Plotly charts"
- "Implement OLS, Huber, and Theil-Sen regression for hedge ratio"
- "Design alert system with callback support"

**Human Contributions**:
- Requirements analysis
- Architecture decisions
- Testing and validation
- Configuration and deployment

## 📝 Project Structure

```
quant-analytics-app/
├── app.py                      # Streamlit frontend application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── backend/
│   ├── database.py            # SQLAlchemy models and DB setup
│   ├── websocket_client.py    # Binance WebSocket client
│   ├── resampler.py           # Tick to OHLCV conversion
│   ├── analytics.py           # Statistical computations
│   ├── alerts.py              # Alert system
│   └── orchestrator.py        # Backend coordinator
├── data/                       # SQLite database (auto-created)
├── logs/                       # Application logs (auto-created)
└── docs/                       # Additional documentation
```

## 🔍 Data Flow

1. **Ingestion**: Binance WebSocket → `websocket_client.py` → Redis/Memory buffer
2. **Persistence**: Buffer → SQLite `tick_data` table (periodic)
3. **Resampling**: SQLite ticks → `resampler.py` → SQLite `resampled_data` table
4. **Analytics**: OHLCV data → `analytics.py` → SQLite `analytics_results` table
5. **Visualization**: SQLite → `orchestrator.py` → Streamlit frontend
6. **Alerts**: Analytics → `alerts.py` → Callback execution

## 🚨 Known Limitations

1. **Initial Data Delay**: Requires 1-2 minutes for sufficient data
2. **Single Machine**: Current implementation not distributed
3. **Limited History**: SQLite suitable for development, not large-scale production
4. **Network Dependency**: Requires stable internet connection
5. **Redis Optional**: Falls back to in-memory (limited capacity)

## 🔐 Security Notes

- No authentication required (local deployment)
- Database stored locally
- No sensitive data handling
- For production: Add authentication, encryption, and access controls

## 🐛 Troubleshooting

### WebSocket Connection Issues
```bash
# Check internet connection
# Verify Binance API is accessible
curl https://fstream.binance.com/fapi/v1/ping
```

### Redis Connection Issues
```bash
# Check Redis status
redis-cli ping
# Should return "PONG"

# If unavailable, app will use in-memory buffer
```

### Database Issues
```bash
# Reset database
rm data/analytics.db
# Restart application
```

### Insufficient Data
- Wait 2-3 minutes for data accumulation
- Start with 1m timeframe (faster accumulation)
- Check WebSocket connection in logs

## 📚 Dependencies

Core libraries and their purposes:
- `streamlit`: Interactive web dashboard
- `plotly`: Interactive charts
- `pandas`: Data manipulation
- `numpy`: Numerical computations
- `scipy/statsmodels`: Statistical tests
- `scikit-learn`: Regression algorithms
- `websocket-client`: WebSocket connection
- `sqlalchemy`: Database ORM
- `redis`: Optional caching layer

## 🎓 Educational Value

This project demonstrates:
- Real-time data pipeline design
- Statistical pair trading concepts
- WebSocket integration
- Database design and ORM usage
- Multi-threading and async patterns
- Interactive data visualization
- Modular software architecture
- Production-ready code practices

## 📄 License

This project is for educational and evaluation purposes.

## 👤 Author

Pranav - Quant Developer Assignment for Gemscap Global Analyst Pvt. Ltd.

## 🙏 Acknowledgments

- Binance for WebSocket API
- Streamlit for the framework
- Plotly for visualization
- Claude/ChatGPT for development assistance
