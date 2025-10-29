#!/usr/bin/env python3
"""
Quick Start Script for Quant Analytics Application

This script initializes and starts the entire application.
"""

import sys
import os
import subprocess
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """Check if required packages are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'streamlit',
        'pandas',
        'numpy',
        'plotly',
        'websocket',
        'sqlalchemy',
        'scipy',
        'statsmodels',
        'sklearn'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("\nInstall them with:")
        print("  pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies installed")
    return True

def check_redis():
    """Check if Redis is available"""
    print("\n🔍 Checking Redis...")
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, db=0)
        client.ping()
        print("✅ Redis is available")
        return True
    except Exception as e:
        print("⚠️  Redis not available (will use in-memory buffer)")
        print(f"   Error: {e}")
        return False

def initialize_database():
    """Initialize the database"""
    print("\n🗄️  Initializing database...")
    try:
        from backend.database import init_db
        init_db()
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def start_application():
    """Start the Streamlit application"""
    print("\n🚀 Starting application...")
    print("\n" + "="*60)
    print("  Quant Analytics Dashboard")
    print("="*60)
    print("\nThe application will start in a few seconds...")
    print("\n📊 Dashboard will open at: http://localhost:8501")
    print("\n⏱️  Please wait 1-2 minutes for initial data collection")
    print("\nPress Ctrl+C to stop the application\n")
    print("="*60 + "\n")
    
    time.sleep(2)
    
    # Start Streamlit
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 'app.py',
            '--server.headless', 'true',
            '--browser.gatherUsageStats', 'false'
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")

def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("  Quant Analytics Application - Quick Start")
    print("="*60 + "\n")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check Redis (optional)
    check_redis()
    
    # Initialize database
    if not initialize_database():
        sys.exit(1)
    
    # Start application
    start_application()

if __name__ == "__main__":
    main()
