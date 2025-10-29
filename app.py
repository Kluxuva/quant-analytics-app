import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from backend.orchestrator import get_backend, start_backend
from backend.alerts import Alert, alert_manager

# Page configuration
st.set_page_config(
    page_title="Quant Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize backend
@st.cache_resource
def initialize_backend():
    """Initialize and start backend services"""
    backend = start_backend()
    time.sleep(3)  # Wait for initial data
    return backend

# Utility functions
def create_price_chart(df1, df2, symbol1, symbol2):
    """Create dual-axis price chart"""
    if df1.empty or df2.empty:
        return None
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(x=df1['timestamp'], y=df1['close'], 
                   name=symbol1.upper(), line=dict(color='blue')),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(x=df2['timestamp'], y=df2['close'], 
                   name=symbol2.upper(), line=dict(color='red')),
        secondary_y=True
    )
    
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text=f"{symbol1.upper()} Price", secondary_y=False)
    fig.update_yaxes(title_text=f"{symbol2.upper()} Price", secondary_y=True)
    fig.update_layout(height=400, hovermode='x unified')
    
    return fig

def create_spread_chart(spread_dict, z_score_dict):
    """Create spread and z-score chart"""
    if not spread_dict or not z_score_dict:
        return None
    
    timestamps = list(spread_dict.keys())
    spread_values = list(spread_dict.values())
    z_score_values = list(z_score_dict.values())
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Spread", "Z-Score"),
        vertical_spacing=0.1
    )
    
    fig.add_trace(
        go.Scatter(x=timestamps, y=spread_values, name="Spread", 
                   line=dict(color='green')),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=timestamps, y=z_score_values, name="Z-Score",
                   line=dict(color='purple')),
        row=2, col=1
    )
    
    # Add horizontal lines for z-score thresholds
    fig.add_hline(y=2, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=-2, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=1)
    
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Spread", row=1, col=1)
    fig.update_yaxes(title_text="Z-Score", row=2, col=1)
    fig.update_layout(height=600, showlegend=True)
    
    return fig

def create_correlation_chart(corr_dict):
    """Create correlation chart"""
    if not corr_dict:
        return None
    
    timestamps = list(corr_dict.keys())
    corr_values = list(corr_dict.values())
    
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=timestamps, y=corr_values, name="Correlation",
                   line=dict(color='orange'), fill='tozeroy')
    )
    
    fig.add_hline(y=0.7, line_dash="dash", line_color="green", 
                  annotation_text="Strong Correlation")
    fig.add_hline(y=0.3, line_dash="dash", line_color="yellow",
                  annotation_text="Weak Correlation")
    
    fig.update_layout(
        title="Rolling Correlation",
        xaxis_title="Time",
        yaxis_title="Correlation",
        height=400,
        hovermode='x'
    )
    
    return fig

def create_volume_chart(df, symbol):
    """Create volume chart"""
    if df.empty or 'volume' not in df.columns:
        return None
    
    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=df['timestamp'], y=df['volume'], name="Volume",
               marker_color='lightblue')
    )
    
    fig.update_layout(
        title=f"{symbol.upper()} Volume",
        xaxis_title="Time",
        yaxis_title="Volume",
        height=300
    )
    
    return fig

# Main app
def main():
    st.title("📊 Real-Time Quantitative Analytics Dashboard")
    st.markdown("---")
    
    # Initialize backend
    try:
        backend = initialize_backend()
    except Exception as e:
        st.error(f"Failed to initialize backend: {e}")
        return
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Symbol selection
    available_symbols = backend.symbols
    if len(available_symbols) >= 2:
        symbol1 = st.sidebar.selectbox(
            "Symbol 1",
            available_symbols,
            index=0,
            key="symbol1"
        )
        symbol2 = st.sidebar.selectbox(
            "Symbol 2",
            available_symbols,
            index=1,
            key="symbol2"
        )
    else:
        st.error("Need at least 2 symbols configured")
        return
    
    # Timeframe selection
    timeframe = st.sidebar.selectbox(
        "Timeframe",
        config.TIMEFRAMES,
        index=1,  # Default to 1m
        key="timeframe"
    )
    
    # Analytics parameters
    st.sidebar.subheader("Analytics Parameters")
    window_size = st.sidebar.slider(
        "Rolling Window Size",
        min_value=10,
        max_value=100,
        value=config.DEFAULT_WINDOW_SIZE,
        step=5
    )
    
    regression_method = st.sidebar.selectbox(
        "Regression Method",
        ["ols", "huber", "theil_sen"],
        index=0
    )
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
    if auto_refresh:
        refresh_interval = st.sidebar.slider(
            "Refresh Interval (seconds)",
            min_value=1,
            max_value=30,
            value=5
        )
    
    # Main content
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview", 
        "📊 Analytics", 
        "🔔 Alerts", 
        "💾 Data Export",
        "ℹ️ Info"
    ])
    
    # Tab 1: Overview
    with tab1:
        st.header("Market Overview")
        
        # Latest prices
        col1, col2, col3 = st.columns(3)
        latest_prices = backend.get_latest_prices()
        
        with col1:
            st.metric(
                f"{symbol1.upper()} Price",
                f"${latest_prices.get(symbol1, 0):.2f}"
            )
        
        with col2:
            st.metric(
                f"{symbol2.upper()} Price",
                f"${latest_prices.get(symbol2, 0):.2f}"
            )
        
        with col3:
            data_summary = backend.get_data_summary()
            total_bars = sum(data_summary.get(symbol1, {}).values())
            st.metric("Data Points", total_bars)
        
        st.markdown("---")
        
        # Price charts
        col1, col2 = st.columns(2)
        
        with col1:
            df1 = backend.get_ohlcv_data(symbol1, timeframe)
            if not df1.empty:
                fig = go.Figure(data=[
                    go.Candlestick(
                        x=df1['timestamp'],
                        open=df1['open'],
                        high=df1['high'],
                        low=df1['low'],
                        close=df1['close']
                    )
                ])
                fig.update_layout(
                    title=f"{symbol1.upper()} - {timeframe}",
                    height=400,
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"Waiting for {symbol1.upper()} data...")
        
        with col2:
            df2 = backend.get_ohlcv_data(symbol2, timeframe)
            if not df2.empty:
                fig = go.Figure(data=[
                    go.Candlestick(
                        x=df2['timestamp'],
                        open=df2['open'],
                        high=df2['high'],
                        low=df2['low'],
                        close=df2['close']
                    )
                ])
                fig.update_layout(
                    title=f"{symbol2.upper()} - {timeframe}",
                    height=400,
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"Waiting for {symbol2.upper()} data...")
        
        # Volume charts
        col1, col2 = st.columns(2)
        with col1:
            if not df1.empty:
                vol_fig = create_volume_chart(df1, symbol1)
                if vol_fig:
                    st.plotly_chart(vol_fig, use_container_width=True)
        
        with col2:
            if not df2.empty:
                vol_fig = create_volume_chart(df2, symbol2)
                if vol_fig:
                    st.plotly_chart(vol_fig, use_container_width=True)
    
    # Tab 2: Analytics
    with tab2:
        st.header("Pair Trading Analytics")
        
        if st.button("🔄 Compute Analytics"):
            with st.spinner("Computing analytics..."):
                analytics = backend.compute_analytics(
                    symbol1, symbol2, timeframe,
                    window_size=window_size,
                    regression_method=regression_method
                )
                
                if analytics:
                    st.session_state['analytics'] = analytics
                    st.success("Analytics computed successfully!")
                else:
                    st.warning("Insufficient data for analytics. Please wait for more data to accumulate.")
        
        # Display analytics if available
        if 'analytics' in st.session_state:
            analytics = st.session_state['analytics']
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Hedge Ratio", f"{analytics.get('hedge_ratio', 0):.4f}")
            
            with col2:
                st.metric("R²", f"{analytics.get('r_squared', 0):.4f}")
            
            with col3:
                st.metric("Current Z-Score", 
                         f"{analytics.get('current_z_score', 0):.2f}")
            
            with col4:
                st.metric("Correlation", 
                         f"{analytics.get('current_correlation', 0):.4f}")
            
            st.markdown("---")
            
            # Spread and Z-Score charts
            spread_fig = create_spread_chart(
                analytics.get('spread', {}),
                analytics.get('z_score', {})
            )
            if spread_fig:
                st.plotly_chart(spread_fig, use_container_width=True)
            
            # Correlation chart
            corr_fig = create_correlation_chart(analytics.get('correlation', {}))
            if corr_fig:
                st.plotly_chart(corr_fig, use_container_width=True)
            
            # ADF Test Results
            st.subheader("Stationarity Test (ADF)")
            adf_result = analytics.get('adf_test', {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ADF Statistic", f"{adf_result.get('statistic', 0):.4f}")
            with col2:
                st.metric("P-Value", f"{adf_result.get('pvalue', 0):.4f}")
            with col3:
                is_stationary = adf_result.get('is_stationary', False)
                st.metric("Stationary", "✅ Yes" if is_stationary else "❌ No")
            
            # Critical values
            crit_vals = adf_result.get('critical_values', {})
            if crit_vals:
                st.write("Critical Values:")
                crit_df = pd.DataFrame([crit_vals])
                st.dataframe(crit_df, use_container_width=True)
            
            # Spread statistics
            st.subheader("Spread Statistics")
            spread_stats = analytics.get('spread_stats', {})
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Mean", f"{spread_stats.get('mean', 0):.4f}")
            with col2:
                st.metric("Std Dev", f"{spread_stats.get('std', 0):.4f}")
            with col3:
                st.metric("Current", f"{spread_stats.get('current', 0):.4f}")
    
    # Tab 3: Alerts
    with tab3:
        st.header("Alert Management")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Create New Alert")
            
            alert_name = st.text_input("Alert Name")
            
            col_a, col_b = st.columns(2)
            with col_a:
                metric = st.selectbox(
                    "Metric",
                    ["current_z_score", "current_correlation", "hedge_ratio", "spread"]
                )
            
            with col_b:
                condition = st.selectbox(
                    "Condition",
                    ["greater", "less", "greater_equal", "less_equal"]
                )
            
            threshold = st.number_input("Threshold", value=2.0, step=0.1)
            
            if st.button("➕ Add Alert"):
                if alert_name:
                    alert = Alert(
                        name=alert_name,
                        condition=condition,
                        metric=metric,
                        threshold=threshold,
                        symbol_pair=f"{symbol1}_{symbol2}"
                    )
                    alert_manager.add_alert(alert)
                    st.success(f"Alert '{alert_name}' created!")
                else:
                    st.error("Please provide an alert name")
        
        with col2:
            st.subheader("Quick Actions")
            if st.button("🗑️ Clear History"):
                alert_manager.clear_history()
                st.success("Alert history cleared!")
        
        st.markdown("---")
        
        # Active alerts
        st.subheader("Active Alerts")
        alerts = alert_manager.get_all_alerts()
        
        if alerts:
            alert_df = pd.DataFrame(alerts)
            st.dataframe(alert_df, use_container_width=True)
            
            # Remove alert
            alert_to_remove = st.selectbox(
                "Select alert to remove",
                [a['name'] for a in alerts]
            )
            if st.button("Remove Selected Alert"):
                alert_manager.remove_alert(alert_to_remove)
                st.success(f"Removed alert: {alert_to_remove}")
                st.rerun()
        else:
            st.info("No active alerts. Create one above!")
        
        st.markdown("---")
        
        # Alert history
        st.subheader("Alert History")
        history = alert_manager.get_alert_history(20)
        
        if history:
            history_df = pd.DataFrame(history)
            st.dataframe(history_df, use_container_width=True)
        else:
            st.info("No alerts triggered yet")
    
    # Tab 4: Data Export
    with tab4:
        st.header("Data Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_symbol = st.selectbox(
                "Select Symbol",
                backend.symbols,
                key="export_symbol"
            )
        
        with col2:
            export_timeframe = st.selectbox(
                "Select Timeframe",
                config.TIMEFRAMES,
                key="export_timeframe"
            )
        
        export_format = st.radio(
            "Export Format",
            ["csv", "json"],
            horizontal=True
        )
        
        if st.button("📥 Export Data"):
            with st.spinner("Exporting..."):
                filepath = backend.export_data(
                    export_symbol,
                    export_timeframe,
                    export_format
                )
                
                if filepath:
                    st.success(f"Data exported to: {filepath}")
                    
                    # Provide download link
                    df = backend.get_ohlcv_data(export_symbol, export_timeframe, 10000)
                    if not df.empty:
                        if export_format == "csv":
                            csv = df.to_csv(index=False)
                            st.download_button(
                                "⬇️ Download CSV",
                                csv,
                                f"{export_symbol}_{export_timeframe}.csv",
                                "text/csv"
                            )
                        else:
                            json_str = df.to_json(orient='records', date_format='iso')
                            st.download_button(
                                "⬇️ Download JSON",
                                json_str,
                                f"{export_symbol}_{export_timeframe}.json",
                                "application/json"
                            )
                else:
                    st.error("No data available for export")
        
        st.markdown("---")
        
        # Data summary
        st.subheader("Available Data Summary")
        summary = backend.get_data_summary()
        summary_df = pd.DataFrame(summary).T
        st.dataframe(summary_df, use_container_width=True)
    
    # Tab 5: Info
    with tab5:
        st.header("System Information")
        
        st.markdown("""
        ### Features
        - **Real-time Data Ingestion**: Live tick data from Binance WebSocket
        - **Multi-timeframe Resampling**: 1s, 1m, 5m OHLCV bars
        - **Pair Trading Analytics**:
          - Hedge ratio via OLS/Huber/Theil-Sen regression
          - Spread calculation and z-score monitoring
          - Rolling correlation analysis
          - ADF stationarity test
        - **Alert System**: Custom alerts with real-time monitoring
        - **Data Export**: CSV and JSON export options
        
        ### Architecture
        - **Backend**: Python with SQLite + Redis
        - **Frontend**: Streamlit with Plotly charts
        - **Real-time Updates**: WebSocket streaming
        - **Modular Design**: Loosely coupled components
        
        ### Usage Tips
        1. Wait 1-2 minutes for initial data accumulation
        2. Start with 1m timeframe for faster results
        3. Adjust window size based on timeframe (higher for longer timeframes)
        4. Monitor z-score for mean reversion opportunities
        5. Use alerts to catch trading signals automatically
        
        ### Current Configuration
        """)
        
        config_data = {
            "Symbols": ", ".join(backend.symbols),
            "Timeframes": ", ".join(config.TIMEFRAMES),
            "Database": config.SQLITE_DB,
            "Default Window": config.DEFAULT_WINDOW_SIZE,
            "Z-Score Window": config.Z_SCORE_WINDOW,
            "Correlation Window": config.CORRELATION_WINDOW
        }
        
        for key, value in config_data.items():
            st.text(f"{key}: {value}")
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()
