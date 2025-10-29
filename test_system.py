#!/usr/bin/env python3
"""
Test Script for Quant Analytics Application

Verifies that all components are working correctly.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import config
        from backend.database import init_db, get_session
        from backend.websocket_client import BinanceWebSocketClient
        from backend.resampler import DataResampler
        from backend.analytics import AnalyticsEngine
        from backend.alerts import Alert, AlertManager
        from backend.orchestrator import BackendOrchestrator
        print("  ✅ All imports successful")
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False

def test_database():
    """Test database initialization"""
    print("\n🧪 Testing database...")
    
    try:
        from backend.database import init_db, get_session, TickData
        
        # Initialize
        init_db()
        print("  ✅ Database initialized")
        
        # Test session
        session = get_session()
        session.close()
        print("  ✅ Database session created")
        
        return True
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        return False

def test_websocket_client():
    """Test WebSocket client initialization"""
    print("\n🧪 Testing WebSocket client...")
    
    try:
        from backend.websocket_client import BinanceWebSocketClient
        
        client = BinanceWebSocketClient(['btcusdt'])
        print("  ✅ WebSocket client created")
        
        # Don't actually start it in test
        print("  ✅ WebSocket client ready")
        
        return True
    except Exception as e:
        print(f"  ❌ WebSocket client test failed: {e}")
        return False

def test_resampler():
    """Test data resampler"""
    print("\n🧪 Testing data resampler...")
    
    try:
        from backend.resampler import DataResampler
        
        resampler = DataResampler(['btcusdt'])
        print("  ✅ Resampler created")
        
        return True
    except Exception as e:
        print(f"  ❌ Resampler test failed: {e}")
        return False

def test_analytics():
    """Test analytics engine"""
    print("\n🧪 Testing analytics engine...")
    
    try:
        from backend.analytics import AnalyticsEngine
        import pandas as pd
        import numpy as np
        
        engine = AnalyticsEngine()
        print("  ✅ Analytics engine created")
        
        # Test basic stats
        df = pd.DataFrame({
            'close': np.random.randn(100) * 100 + 50000,
            'volume': np.random.randn(100) * 1000 + 5000
        })
        
        stats = engine.compute_basic_stats(df)
        assert 'mean' in stats
        print("  ✅ Basic stats computation works")
        
        # Test z-score
        series = pd.Series(np.random.randn(100))
        z_score = engine.compute_z_score(series, window=20)
        print("  ✅ Z-score computation works")
        
        return True
    except Exception as e:
        print(f"  ❌ Analytics test failed: {e}")
        return False

def test_alert_manager():
    """Test alert manager"""
    print("\n🧪 Testing alert manager...")
    
    try:
        from backend.alerts import Alert, AlertManager
        
        manager = AlertManager()
        print("  ✅ Alert manager created")
        
        # Create test alert
        alert = Alert(
            name="Test Alert",
            condition="greater",
            metric="z_score",
            threshold=2.0,
            symbol_pair="btcusdt_ethusdt"
        )
        manager.add_alert(alert)
        print("  ✅ Alert created and added")
        
        # Test alert check
        analytics_data = {
            'btcusdt_ethusdt': {
                'z_score': 2.5
            }
        }
        triggered = manager.check_alerts(analytics_data)
        assert len(triggered) > 0
        print("  ✅ Alert checking works")
        
        return True
    except Exception as e:
        print(f"  ❌ Alert manager test failed: {e}")
        return False

def test_orchestrator():
    """Test backend orchestrator"""
    print("\n🧪 Testing orchestrator...")
    
    try:
        from backend.orchestrator import BackendOrchestrator
        
        # Just test initialization, don't start services
        orchestrator = BackendOrchestrator(['btcusdt', 'ethusdt'])
        print("  ✅ Orchestrator created")
        
        return True
    except Exception as e:
        print(f"  ❌ Orchestrator test failed: {e}")
        return False

def test_config():
    """Test configuration"""
    print("\n🧪 Testing configuration...")
    
    try:
        import config
        
        assert hasattr(config, 'DEFAULT_SYMBOLS')
        assert hasattr(config, 'TIMEFRAMES')
        assert hasattr(config, 'SQLITE_DB')
        print("  ✅ Configuration loaded")
        
        return True
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("  Running Component Tests")
    print("="*60 + "\n")
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Database", test_database),
        ("WebSocket Client", test_websocket_client),
        ("Data Resampler", test_resampler),
        ("Analytics Engine", test_analytics),
        ("Alert Manager", test_alert_manager),
        ("Orchestrator", test_orchestrator),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ Unexpected error in {name}: {e}")
            results.append((name, False))
    
    print("\n" + "="*60)
    print("  Test Summary")
    print("="*60 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\n  Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 All tests passed! System is ready.")
        return True
    else:
        print("\n  ⚠️  Some tests failed. Please check the errors above.")
        return False

def main():
    """Main entry point"""
    success = run_all_tests()
    
    if success:
        print("\n" + "="*60)
        print("  Ready to start the application!")
        print("  Run: python start.py")
        print("  Or:  streamlit run app.py")
        print("="*60 + "\n")
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("  Please fix the errors and try again")
        print("="*60 + "\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
