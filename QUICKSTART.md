# Quick Setup Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Optional - Start Redis (for better performance)
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS  
brew install redis
brew services start redis

# Windows
# Download from https://redis.io/download

# Skip this if you don't have Redis - app will work without it
```

### Step 3: Run the Application
```bash
# Option 1: Quick start script (recommended)
python start.py

# Option 2: Direct Streamlit
streamlit run app.py
```

That's it! The dashboard will open at http://localhost:8501

## ⏱️ First Time Usage

1. **Wait 1-2 minutes** for initial data collection
2. Start with **1m timeframe** for faster results
3. Click **"Compute Analytics"** in the Analytics tab
4. Explore the features!

## 🎯 Key Features

- **Overview Tab**: Real-time prices and charts
- **Analytics Tab**: Hedge ratio, spread, z-score, correlation, ADF test
- **Alerts Tab**: Create custom alerts for trading signals
- **Data Export Tab**: Download data as CSV or JSON

## 🧪 Test the System

Before running, verify everything works:
```bash
python test_system.py
```

## 📖 Documentation

- **README.md**: Complete documentation
- **ARCHITECTURE.md**: System design details
- **CHATGPT_USAGE.md**: AI usage transparency
- **DELIVERABLES.md**: Assignment checklist

## 🐛 Troubleshooting

### No data appearing?
- Wait 2-3 minutes for data accumulation
- Check internet connection
- Verify Binance API is accessible

### Redis connection error?
- App will automatically fall back to in-memory buffer
- No action needed unless you want Redis performance

### Database error?
- Delete `data/analytics.db` and restart

## 🎓 For Evaluators

This project demonstrates:
- Real-time data ingestion and processing
- Statistical analytics for pair trading
- Interactive visualization with Streamlit
- Modular, extensible architecture
- Production-ready code patterns
- Comprehensive documentation

**Time to first results**: ~2 minutes
**Recommended starting timeframe**: 1m

Enjoy exploring the application! 🎉
