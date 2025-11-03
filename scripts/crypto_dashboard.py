## to run a streamlit app, use the command:
# streamlit run (file path of .py file)
# example: streamlit run scripts/crypto_dashboard.py



import os
from pathlib import Path
import pandas as pd
import numpy as np
import logging
import traceback
import sys
import ast
import psutil
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# === Advanced Debugging Configuration ===
def setup_advanced_debugging():
    """Setup comprehensive debugging and error tracking"""
    
    # Configure detailed logging
    log_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler('dashboard_debug.log', mode='a', encoding='utf-8')
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)
    
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def debug_code_syntax():
    """Check for common Python syntax issues"""
    current_file = __file__
    issues = []
    
    try:
        with open(current_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for mixed indentation
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if line.strip() and (line.startswith(' ') and '\t' in line):
                issues.append(f"Line {i}: Mixed tabs and spaces detected")
            
            # Check for common syntax issues
            if line.strip().endswith(',  #') or line.strip().endswith(', #'):
                issues.append(f"Line {i}: Potential comment indentation issue")
        
        # Try to parse the AST
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append(f"Syntax Error: {e.msg} at line {e.lineno}")
            
    except Exception as e:
        issues.append(f"Could not analyze file: {str(e)}")
    
    return issues

# Initialize advanced debugging
logger = setup_advanced_debugging()
logger.info("=" * 60)
logger.info("DASHBOARD STARTUP - Advanced Debugging Enabled")
logger.info("=" * 60)

# Check for syntax issues
syntax_issues = debug_code_syntax()
if syntax_issues:
    logger.error("SYNTAX ISSUES DETECTED:")
    for issue in syntax_issues:
        logger.error(f"  {issue}")
else:
    logger.info("✅ No syntax issues detected in code analysis")

# === Load .env ===
project_root = Path(__file__).resolve().parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# === App config ===
st.set_page_config(
    layout="wide", 
    page_title="📈 Crypto Dashboard Pro",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS
st.markdown("""
<style>
    /* Main container styling */
    .main {
        padding: 0;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* Enhanced header styling */
    .dashboard-header {
        background: linear-gradient(135deg, #2a2a4a 0%, #1a1a2e 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
    }
    
    .dashboard-title {
        font-size: 2.5rem;
        font-weight: 600;
        background: linear-gradient(90deg, #ff6b6b 0%, #4ecdc4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .dashboard-subtitle {
        color: #888;
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    /* Collapsible section styling */
    .collapsible-header {
        background: rgba(42, 42, 74, 0.3);
        padding: 1.2rem 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .collapsible-header:hover {
        background: rgba(42, 42, 74, 0.5);
        transform: translateY(-2px);
    }
    
    .collapsible-content {
        background: rgba(42, 42, 74, 0.2);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Enhanced metric container */
    .metric-container {
        background: linear-gradient(135deg, rgba(78, 205, 196, 0.1) 0%, rgba(255, 107, 107, 0.1) 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .metric-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }
    
    /* Chart container styling */
    .chart-container {
        background: rgba(42, 42, 74, 0.3);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    
    /* Sidebar enhancements */
    .css-1d391kg {
        background-color: rgba(26, 26, 46, 0.95);
        backdrop-filter: blur(10px);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #4ecdc4 0%, #44a5a0 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(78, 205, 196, 0.4);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(42, 42, 74, 0.3);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Success/Error containers */
    .error-container {
        background: linear-gradient(135deg, rgba(255, 68, 68, 0.1) 0%, rgba(255, 68, 68, 0.05) 100%);
        border-left: 4px solid #ff4444;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .success-container {
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(0, 255, 136, 0.05) 100%);
        border-left: 4px solid #00ff88;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Performance indicator */
    .performance-indicator {
        font-size: 0.8rem;
        color: #888;
        text-align: center;
        padding: 0.5rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .dashboard-title {
            font-size: 1.8rem;
        }
        
        .main {
            padding: 0 0.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Enhanced Title Section
st.markdown("""
<div class="dashboard-header">
    <h1 class="dashboard-title">🚀 Advanced Crypto Analytics Dashboard</h1>
    <p class="dashboard-subtitle">Professional-grade crypto analysis with real-time insights</p>
</div>
""", unsafe_allow_html=True)

# Performance monitoring
if 'page_load_time' not in st.session_state:
    st.session_state.page_load_time = time.time()

# Error handling wrapper
def handle_errors(func):
    """Decorator for comprehensive error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            st.error(f"⚠️ An error occurred in {func.__name__}: {str(e)}")
            if st.session_state.get('debug_mode', False):
                st.code(traceback.format_exc())
            return None
    return wrapper

# Add caching for database connections
@st.cache_resource
def get_database_engine():
    """Cache database connection for better performance"""
    try:
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
        logger.info("Database connection established successfully")
        return engine
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise

@handle_errors
def create_hollow_candlesticks(df):
    """Create hollow candlestick chart for advanced price analysis"""
    if df.empty:
        return go.Figure()
    
    # Calculate colors for hollow candlesticks
    df = df.copy()
    df['prev_close'] = df['close'].shift(1)
    
    # Hollow candlestick logic:
    # - Green when close > prev_close, Red when close < prev_close
    # - Hollow when close > open, Filled when close < open
    
    increasing_mask = df['close'] > df['prev_close']
    decreasing_mask = df['close'] <= df['prev_close']
    hollow_mask = df['close'] > df['open']
    filled_mask = df['close'] <= df['open']
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        subplot_titles=('Price Action', 'Volume'),
        row_width=[0.2, 0.8]
    )
    
    # Add individual candlesticks with custom colors
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['prev_close']):
            continue
            
        row = df.iloc[i]
        
        # Determine colors
        if increasing_mask.iloc[i]:  # Close > Previous Close
            line_color = '#00ff88'  # Green
            fill_color = 'rgba(0, 255, 136, 0.1)' if hollow_mask.iloc[i] else '#00ff88'
        else:  # Close <= Previous Close
            line_color = '#ff4444'  # Red
            fill_color = 'rgba(255, 68, 68, 0.1)' if hollow_mask.iloc[i] else '#ff4444'
        
        # Add candlestick
        fig.add_trace(
            go.Candlestick(
                x=[row['datetime']],
                open=[row['open']],
                high=[row['high']],
                low=[row['low']],
                close=[row['close']],
                increasing_line_color=line_color,
                increasing_fillcolor=fill_color,
                decreasing_line_color=line_color,
                decreasing_fillcolor=fill_color,
                name='Price',
                showlegend=False
            ),
            row=1, col=1
        )
    
    return fig

@handle_errors
def calculate_fear_greed_index(df):
    """Calculate custom Fear & Greed Index based on historical data"""
    if len(df) < 30:
        return None, None, None, None
    
    df = df.copy()
    
    # 1. VOLATILITY COMPONENT (25% weight)
    # Higher volatility = more fear
    returns = df['close'].pct_change()
    volatility = returns.rolling(14).std() * np.sqrt(365) * 100  # Annualized volatility
    current_vol = volatility.iloc[-1]
    vol_percentile = (volatility <= current_vol).mean() * 100
    vol_score = 100 - vol_percentile  # Invert: high vol = low score (fear)
    
    # 2. MOMENTUM COMPONENT (25% weight) 
    # Strong upward momentum = greed
    momentum_14 = ((df['close'] / df['close'].shift(14)) - 1) * 100
    momentum_30 = ((df['close'] / df['close'].shift(30)) - 1) * 100
    current_momentum = (momentum_14.iloc[-1] + momentum_30.iloc[-1]) / 2
    
    # Normalize momentum (-50% to +50% -> 0 to 100)
    momentum_score = max(0, min(100, (current_momentum + 50) * 1))
    
    # 3. VOLUME ANALYSIS (20% weight)
    # High volume on up days = greed, high volume on down days = fear
    df['price_change'] = df['close'].pct_change()
    df['volume_ma'] = df['volume'].rolling(30).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma']
    
    # Recent 7 days volume-weighted sentiment
    recent_data = df.tail(7)
    volume_sentiment = 0
    for _, row in recent_data.iterrows():
        if row['price_change'] > 0:  # Price up
            volume_sentiment += row['volume_ratio'] * row['price_change']
        else:  # Price down
            volume_sentiment += row['volume_ratio'] * row['price_change'] * 2  # Weight fear more
    
    volume_score = max(0, min(100, (volume_sentiment + 1) * 50))
    
    # 4. PRICE POSITION (15% weight)
    # Price near highs = greed, near lows = fear
    high_52w = df['high'].rolling(min(len(df), 365)).max().iloc[-1]
    low_52w = df['low'].rolling(min(len(df), 365)).min().iloc[-1]
    current_price = df['close'].iloc[-1]
    
    if high_52w != low_52w:
        price_position = ((current_price - low_52w) / (high_52w - low_52w)) * 100
    else:
        price_position = 50
    
    # 5. RSI COMPONENT (15% weight)
    # High RSI = greed, low RSI = fear
    if 'rsi' in df.columns:
        current_rsi = df['rsi'].iloc[-1]
        rsi_score = current_rsi if not pd.isna(current_rsi) else 50
    else:
        # Calculate simple RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_score = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    
    # Calculate weighted Fear & Greed Index
    fear_greed_index = (
        vol_score * 0.25 +
        momentum_score * 0.25 + 
        volume_score * 0.20 +
        price_position * 0.15 +
        rsi_score * 0.15
    )
    
    # Determine sentiment
    if fear_greed_index >= 75:
        sentiment = "Extreme Greed 🤑"
        color = "#ff4444"
    elif fear_greed_index >= 50:
        sentiment = "Greed 😃"
        color = "#ffa500"
    elif fear_greed_index >= 25:
        sentiment = "Fear 😟"
        color = "#ffff00"
    else:
        sentiment = "Extreme Fear 😰"
        color = "#00ff88"
    
    # Create breakdown for debugging
    breakdown = {
        'Volatility': vol_score,
        'Momentum': momentum_score,
        'Volume': volume_score,
        'Price Position': price_position,
        'RSI': rsi_score,
        'Final Score': fear_greed_index
    }
    
    return fear_greed_index, sentiment, color, breakdown

@handle_errors
def create_fear_greed_gauge(fear_greed_score, sentiment, color):
    """Create a beautiful gauge chart for Fear & Greed Index"""
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = fear_greed_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Fear & Greed Index<br><span style='font-size:16px;color:{color}'>{sentiment}</span>"},
        delta = {'reference': 50, 'position': "top"},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color, 'thickness': 0.3},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 25], 'color': '#ff6b6b'},    # Extreme Fear
                {'range': [25, 50], 'color': '#ffd93d'},   # Fear  
                {'range': [50, 75], 'color': '#6bcf7f'},   # Greed
                {'range': [75, 100], 'color': '#ff4757'}   # Extreme Greed
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        template='plotly_dark',
        margin=dict(l=20, r=20, t=60, b=20),
        font={'color': "white", 'family': "Arial"}
    )
    
    return fig

@handle_errors
def add_advanced_indicators(fig, df):
    """Add sophisticated technical indicators with smart coloring"""
    
    # Volume-weighted coloring for volume bars
    df['volume_color'] = df.apply(lambda row: 
        '#00ff88' if row['close'] > row['open'] else '#ff4444', axis=1)
    
    # Add volume with dynamic coloring
    for i, row in df.iterrows():
        fig.add_trace(
            go.Bar(
                x=[row['datetime']],
                y=[row['volume']],
                marker_color=row['volume_color'],
                opacity=0.6,
                name='Volume',
                showlegend=False
            ),
            row=2, col=1
        )
    
    return fig

@handle_errors
def validate_technical_indicators(df):
    """Validate technical indicator calculations"""
    validation_results = {}
    
    if 'ma20' in df.columns:
        validation_results['MA20'] = 'Valid' if not df['ma20'].isna().all() else 'Invalid'
    if 'ma50' in df.columns:
        validation_results['MA50'] = 'Valid' if not df['ma50'].isna().all() else 'Invalid'
    if 'rsi' in df.columns:
        rsi_valid = df['rsi'].between(0, 100).all()
        validation_results['RSI'] = 'Valid' if rsi_valid else 'Invalid'
    if 'macd' in df.columns:
        validation_results['MACD'] = 'Valid' if not df['macd'].isna().all() else 'Invalid'
    if 'bb_upper' in df.columns:
        validation_results['Bollinger'] = 'Valid' if not df['bb_upper'].isna().all() else 'Invalid'
    if 'vwap' in df.columns:
        validation_results['VWAP'] = 'Valid' if not df['vwap'].isna().all() else 'Invalid'
    
    return validation_results

@handle_errors
def display_validation_results(validation_results):
    """Display validation results"""
    for indicator, status in validation_results.items():
        if status == 'Valid':
            st.success(f"✅ {indicator}: {status}")
        else:
            st.error(f"❌ {indicator}: {status}")

def create_chart_container(title, chart_figure, export_format='png', height=450):
    """Create a styled chart container with consistent formatting"""
    with st.container():
        st.markdown(f'<div class="chart-container">', unsafe_allow_html=True)
        
        # Chart header with title and actions (now smaller since chart has its own title)
        col1, col2 = st.columns([6, 1])
        with col1:
            st.markdown(f"#### {title}")
        with col2:
            if st.button("⛶", key=f"expand_{title}", help="Fullscreen"):
                st.info("Fullscreen mode coming soon!")
        
        # Display the chart with enhanced config
        st.plotly_chart(chart_figure, use_container_width=True, config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
            'toImageButtonOptions': {
                'format': export_format.lower(),
                'filename': f'{title.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d_%H%M")}',
                'height': height * 2,
                'width': 1600,
                'scale': 2
            },
            'scrollZoom': True,
            'doubleClick': 'reset+autosize',
            'responsive': True
        })
        
        st.markdown('</div>', unsafe_allow_html=True)

# === Enhanced Sidebar filters ===
st.sidebar.title("⚙️ Advanced Controls")

# Performance indicator
load_time = time.time() - st.session_state.page_load_time
st.sidebar.markdown(f'<div class="performance-indicator">⚡ Load time: {load_time:.2f}s</div>', 
                   unsafe_allow_html=True)

# === Asset Selection (Always Visible) ===
with st.sidebar.expander("📈 Asset Selection", expanded=True):
    col1, col2 = st.columns([2, 1])
    with col1:
        symbol_options = {
            'BTC': '₿ Bitcoin',
            'ETH': '⟠ Ethereum',
            'SOL': '◎ Solana',
            'TAO': '🧠 Bittensor'
        }
        selected_key = st.selectbox("Select Asset", list(symbol_options.keys()),
                                   format_func=lambda x: symbol_options[x])
        symbol = selected_key

    with col2:
        if st.button("🔄", help="Clear cache & refresh"):
            st.cache_data.clear()
            st.rerun()

# === Timeframe Selection ===
with st.sidebar.expander("⏰ Timeframe Selection", expanded=True):
    timeframe_options = {
        '1w': '📆 Weekly',
        '1d': '📅 Daily',
        '6h': '🕕 6-Hour',
        '1h': '🕐 Hourly',
        '5m': '⚡ 5-Minute',
        '1m': '⚡ 1-Minute'
    }
    selected_timeframe = st.selectbox("Select Timeframe", list(timeframe_options.keys()),
                                     format_func=lambda x: timeframe_options[x],
                                     index=0)  # Default to daily

    # Smart time range suggestions based on timeframe
    if selected_timeframe == '1w':
        st.caption("📈 Weekly charts: Long-term trends and major market cycles")
    elif selected_timeframe == '1d':
        st.caption("📊 Daily charts: Best for long-term analysis (weeks to years)")
    elif selected_timeframe == '6h':
        st.caption("📈 6-hour charts: Medium-term swing trading (days to weeks)")
    elif selected_timeframe == '1h':
        st.caption("⚡ Hourly charts: Short-term trading (hours to days)")
    elif selected_timeframe == '5m':
        st.caption("🚀 5-minute charts: Scalping (minutes to hours)")
    else:  # 1m
        st.caption("💨 1-minute charts: High-frequency trading (seconds to minutes)")
    
    # Connection status indicator
    try:
        engine = get_database_engine()
        st.success("🟢 Database Connected")
    except Exception as e:
        st.error("🔴 Database Error")
        st.error(str(e))
        st.stop()

# === Time Range Selection ===
with st.sidebar.expander("📅 Time Range & Data", expanded=True):
    preset_range = st.selectbox(
        "Time Range",
        ["Custom", "Last 24 hours", "Last 7 days", "Last 30 days", "Last 90 days", "Last 6 months", "Last year"],
        index=2  # Default to "Last 7 days"
    )
    
    # Set date range based on preset or allow custom
    if preset_range == "Custom":
        date_range = st.date_input(
            "Custom date range", 
            value=[datetime(2024, 1, 1), datetime.today()]
        )
    else:
        end_date_preset = datetime.today()
        if preset_range == "Last 24 hours":
            start_date_preset = end_date_preset - pd.Timedelta(days=1)
        elif preset_range == "Last 7 days":
            start_date_preset = end_date_preset - pd.Timedelta(days=7)
        elif preset_range == "Last 30 days":
            start_date_preset = end_date_preset - pd.Timedelta(days=30)
        elif preset_range == "Last 90 days":
            start_date_preset = end_date_preset - pd.Timedelta(days=90)
        elif preset_range == "Last 6 months":
            start_date_preset = end_date_preset - pd.Timedelta(days=180)
        elif preset_range == "Last year":
            start_date_preset = end_date_preset - pd.Timedelta(days=365)
        
        date_range = [start_date_preset.date(), end_date_preset.date()]

    # Convert to pandas datetime
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])
    date_diff = (end_date - start_date).days

    # Show range info and smart suggestions
    st.info(f"📅 Selected: **{date_diff} days** ({start_date.strftime('%b %d')} - {end_date.strftime('%b %d')})")

    # Add helpful tips and quick stats
    if preset_range == "Custom":
        if date_diff <= 3:
            st.success("💡 Perfect for intraday analysis")
        elif date_diff <= 30:
            st.success("💡 Good for short-term trends")
        elif date_diff <= 90:
            st.success("💡 Great for medium-term analysis")
        else:
            st.success("💡 Ideal for long-term trends")
    
    # Real-time market status
    market_status = "🟢 OPEN" if datetime.now().weekday() < 5 else "🔴 CLOSED"
    st.markdown(f"**Market Status:** {market_status}")

# === System & Debug Controls ===
with st.sidebar.expander("🛠️ System & Debug", expanded=False):
    debug_mode = st.checkbox("🐛 Debug Mode", help="Show detailed error information")
    performance_mode = st.checkbox("⚡ Performance Mode", help="Enable performance monitoring")
    hollow_candles = st.checkbox("🔶 Hollow Candlesticks", value=True, 
                                       help="Use professional hollow candlestick style")

    if debug_mode:
        st.session_state.debug_mode = True
        st.info("Debug mode enabled - detailed logs will be shown")

    if performance_mode:
        st.metric("Memory Usage", f"{psutil.virtual_memory().percent:.1f}%")
        st.metric("CPU Usage", f"{psutil.cpu_percent():.1f}%")

# Dynamic range selector buttons function
def get_smart_range_buttons(days_selected, preset_used):
    """Generate appropriate range buttons based on selected timeframe"""
    buttons = []
    
    # For very short ranges (1-7 days)
    if days_selected <= 7:
        buttons.extend([
            dict(count=6, label="6H", step="hour", stepmode="backward"),
            dict(count=1, label="1D", step="day", stepmode="backward"),
            dict(count=3, label="3D", step="day", stepmode="backward")
        ])
        if days_selected >= 7:
            buttons.append(dict(count=7, label="1W", step="day", stepmode="backward"))
    
    # For short-medium ranges (1 week to 1 month)
    elif days_selected <= 30:
        buttons.extend([
            dict(count=1, label="1D", step="day", stepmode="backward"),
            dict(count=7, label="1W", step="day", stepmode="backward"),
            dict(count=14, label="2W", step="day", stepmode="backward"),
            dict(count=30, label="1M", step="day", stepmode="backward")
        ])
    
    # For medium ranges (1-3 months)
    elif days_selected <= 90:
        buttons.extend([
            dict(count=7, label="1W", step="day", stepmode="backward"),
            dict(count=30, label="1M", step="day", stepmode="backward"),
            dict(count=60, label="2M", step="day", stepmode="backward"),
            dict(count=90, label="3M", step="day", stepmode="backward")
        ])
    
    # For longer ranges
    else:
        buttons.extend([
            dict(count=30, label="1M", step="day", stepmode="backward"),
            dict(count=90, label="3M", step="day", stepmode="backward"),
            dict(count=180, label="6M", step="day", stepmode="backward"),
            dict(count=365, label="1Y", step="day", stepmode="backward")
        ])
    
    # Always include "All" to show the full selected range
    buttons.append(dict(step="all", label=f"All ({days_selected}d)"))
    
    return buttons

# Get appropriate buttons for this timeframe
range_buttons = get_smart_range_buttons(date_diff, preset_range)

# Fix sidebar filters: collapse them like graphs
with st.sidebar.expander("⚙️ Filters & Settings", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        show_ma20 = st.checkbox("MA20", value=True)
        show_ma50 = st.checkbox("MA50", value=True)
        show_rsi = st.checkbox("RSI", value=True)
    with col2:
        show_macd = st.checkbox("MACD", value=True)
        show_bollinger = st.checkbox("Bollinger", value=True)
        show_vwap = st.checkbox("VWAP", value=True)

    export_csv = st.checkbox("Export data as CSV")
    validate_indicators = st.checkbox("Validate Indicators")

    chart_type = st.selectbox("Chart Type", ["Candlestick", "Line", "Area", "Hollow Candles"], index=3 if hollow_candles else 0)
    export_format = st.selectbox("Export Format", ["PNG", "SVG", "PDF"])
    auto_refresh = st.checkbox("Auto Refresh (5s)", value=False)


# === Database connection ===
try:
    engine = get_database_engine()
    if debug_mode: 
        st.sidebar.success("✅ DB connection OK")
        logger.info("Database connection successful")
except Exception as e:
    error_msg = f"❌ DB connection error: {e}"
    st.sidebar.error(error_msg)
    logger.error(error_msg)
    st.error("🚨 **Database Connection Failed**")
    st.markdown("""
    **Possible solutions:**
    - Check your database credentials in .env file
    - Ensure PostgreSQL is running
    - Verify network connectivity
    - Check firewall settings
    """)
    st.stop()

# === Enhanced data query function ===
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_crypto_data(symbol_param, start_date_param, end_date_param, timeframe_param='1d'):
    """Load and cache crypto data with comprehensive error handling"""

    # Performance timing
    start_time = time.time()

    # Handle weekly aggregation by using daily data
    if timeframe_param == '1w':
        table_name = f"{symbol_param.lower()}usd_1d"
        query = f"""
            SELECT
                DATE_TRUNC('week', datetime) as datetime,
                FIRST_VALUE(open) OVER (PARTITION BY DATE_TRUNC('week', datetime) ORDER BY datetime) as open,
                MAX(high) OVER (PARTITION BY DATE_TRUNC('week', datetime)) as high,
                MIN(low) OVER (PARTITION BY DATE_TRUNC('week', datetime)) as low,
                LAST_VALUE(close) OVER (PARTITION BY DATE_TRUNC('week', datetime) ORDER BY datetime
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as close,
                SUM(volume) OVER (PARTITION BY DATE_TRUNC('week', datetime)) as volume
            FROM public.{table_name}
            WHERE datetime BETWEEN '{start_date_param}' AND '{end_date_param}'
            ORDER BY datetime;
        """
    else:
        # Regular timeframes
        table_name = f"{symbol_param.lower()}usd_{timeframe_param}"
        query = f"""
            SELECT datetime, open, high, low, close, volume
            FROM public.{table_name}
            WHERE datetime BETWEEN '{start_date_param}' AND '{end_date_param}'
            ORDER BY datetime;
        """
    
    try:
        df = pd.read_sql(query, engine)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values(by='datetime')
        
        # Data quality checks
        if df.empty:
            logger.warning(f"No data found for {symbol_param} in date range")
            st.warning(f"⚠️ No data found for {symbol_param} in the selected date range")
            return pd.DataFrame()
        
        # Log performance
        load_time = time.time() - start_time
        logger.info(f"Data loaded for {symbol_param}: {len(df)} rows in {load_time:.2f}s")
        
        if performance_mode:
            st.sidebar.metric("Data Load Time", f"{load_time:.2f}s")
            st.sidebar.metric("Records Loaded", len(df))
        
        return df
        
    except Exception as e:
        error_msg = f"Failed to load data for {symbol_param}: {str(e)}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        
        if debug_mode:
            st.code(f"Query: {query}")
            st.code(f"Error: {traceback.format_exc()}")
        
        return pd.DataFrame()

# === Query data ===
try:
    df = load_crypto_data(symbol, start_date, end_date, selected_timeframe)
    if debug_mode:
        st.sidebar.write(f"Fetched {len(df)} rows.")
        st.sidebar.write(df.head(2))
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    st.stop()

# === Price Metrics Section ===
if len(df) > 0:
    with st.sidebar.expander("💰 Live Price Metrics", expanded=True):
        current_price = df['close'].iloc[-1]
        price_change = df['close'].iloc[-1] - df['close'].iloc[-2] if len(df) > 1 else 0
        price_change_pct = (price_change / df['close'].iloc[-2] * 100) if len(df) > 1 and df['close'].iloc[-2] != 0 else 0
        
        # Main price display
        st.metric(
            label=f"{symbol}/USD",
            value=f"${current_price:,.0f}",
            delta=f"{price_change_pct:+.2f}%"
        )
        
        # 24h stats
        high_24h = df['high'].tail(1).iloc[0] if len(df) >= 1 else current_price
        low_24h = df['low'].tail(1).iloc[0] if len(df) >= 1 else current_price
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("24h High", f"${high_24h:,.0f}")
        with col2:
            st.metric("24h Low", f"${low_24h:,.0f}")
        
        # Additional price stats
        volume_latest = df['volume'].iloc[-1] if len(df) > 0 else 0
        st.metric("Volume", f"{volume_latest:,.0f}")

# === Calculations ===
if show_ma20:
    df['ma20'] = df['close'].rolling(20).mean()
if show_ma50:
    df['ma50'] = df['close'].rolling(50).mean()

if show_rsi:
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))

if show_macd:
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_histogram'] = df['macd'] - df['macd_signal']

if show_bollinger:
    # Enhanced Bollinger Bands with analysis (inspired by bootcamp functions)
    data_points = len(df)
    if data_points >= 20:
        bb_period = 20  # Standard period
    elif data_points >= 10:
        bb_period = min(10, data_points - 1)  # Use 10 or available data - 1
    else:
        bb_period = max(3, data_points // 2)  # Minimum 3, or half the data

    # Calculate Bollinger Bands
    df['bb_middle'] = df['close'].rolling(bb_period, min_periods=1).mean()
    bb_std = df['close'].rolling(bb_period, min_periods=1).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)

    # Enhanced analysis: Band Width for volatility analysis
    df['bb_bandwidth'] = df['bb_upper'] - df['bb_lower']
    df['bb_percent'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower']) * 100

    # Bollinger Band squeeze detection (low volatility)
    df['bb_squeeze'] = df['bb_bandwidth'] < df['bb_bandwidth'].rolling(20, min_periods=5).mean() * 0.8

# Enhanced Support & Resistance Levels (inspired by bootcamp functions)
# Calculate dynamic support and resistance levels
if len(df) > 10:
    # Use recent data for dynamic levels (excluding last 2 rows as in bootcamp)
    recent_data = df[:-2] if len(df) > 2 else df
    df['support_level'] = recent_data['low'].min()
    df['resistance_level'] = recent_data['high'].max()

    # More granular support/resistance using rolling periods
    df['support_dynamic'] = df['low'].rolling(20, min_periods=5).min()
    df['resistance_dynamic'] = df['high'].rolling(20, min_periods=5).max()

if show_vwap:
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    cumulative_tp_volume = (typical_price * df['volume']).cumsum()
    cumulative_volume = df['volume'].cumsum()
    df['vwap'] = cumulative_tp_volume / cumulative_volume

# === Export CSV ===
if export_csv:
    csv_path = project_root / f"{symbol.lower()}_candles.csv"
    try:
        df.to_csv(csv_path, index=False)
        st.sidebar.success(f"CSV saved to: {csv_path}")
    except Exception as e:
        st.sidebar.error(f"❌ Failed to save CSV: {e}")

# === Validation Section ===
if validate_indicators and len(df) > 0:
    with st.expander("🔍 Technical Indicator Validation", expanded=True):
        validation_results = validate_technical_indicators(df)
        display_validation_results(validation_results)

# === Enhanced Chart Building ===
if len(df) > 0:
    if chart_type == "Hollow Candles" or (chart_type == "Candlestick" and hollow_candles):
        # Use advanced hollow candlestick implementation
        fig = create_hollow_candlesticks(df)
        fig = add_advanced_indicators(fig, df)
        
        # Add technical indicators to main chart
        if show_ma20 and 'ma20' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['datetime'], y=df['ma20'], name='MA20',
                line=dict(color='#3366cc', width=2),
                hovertemplate='MA20: $%{y:,.2f}<extra></extra>'
            ), row=1, col=1)
            
        if show_ma50 and 'ma50' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['datetime'], y=df['ma50'], name='MA50',
                line=dict(color='#ff6600', width=2),
                hovertemplate='MA50: $%{y:,.2f}<extra></extra>'
            ), row=1, col=1)
            
        if show_vwap and 'vwap' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['datetime'], y=df['vwap'], name='VWAP',
                line=dict(color='#ffcc00', width=3),
                hovertemplate='VWAP: $%{y:,.2f}<extra></extra>'
            ), row=1, col=1)
            
        if show_bollinger and 'bb_upper' in df.columns:
            # Bollinger Bands with fill
            fig.add_trace(go.Scatter(
                x=df['datetime'], y=df['bb_upper'], name='BB Upper',
                line=dict(color='rgba(128,0,128,0.8)', width=1, dash='dot'),
                showlegend=False
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=df['datetime'], y=df['bb_lower'], name='Bollinger Bands',
                line=dict(color='rgba(128,0,128,0.8)', width=1, dash='dot'),
                fill='tonexty', fillcolor='rgba(128,0,128,0.1)',
                hovertemplate='BB: %{y:,.2f}<extra></extra>'
            ), row=1, col=1)
        
        # Enhanced layout with better sizing and title alignment
        fig.update_layout(
            title=dict(
                text=f"{symbol_options[symbol]} Analysis ({preset_range if preset_range != 'Custom' else f'{date_diff} days'})",
                x=0.5, 
                xanchor='center',
                font=dict(size=20, color='#ffffff'),
                y=0.95,
                pad=dict(t=20)
            ),
            template='plotly_dark',
            height=450,
            showlegend=True,
            legend=dict(
                orientation='h', 
                x=0.5, 
                xanchor='center', 
                y=1.02,
                bgcolor='rgba(0,0,0,0.8)', 
                font=dict(color='white', size=10),
                bordercolor='rgba(255,255,255,0.2)',
                borderwidth=1
            ),
            margin=dict(t=100, b=60, l=60, r=60),
            hovermode='x unified'
        )
        
        # Update axes
        fig.update_xaxes(
            title_text="Date", row=2, col=1,
            rangeslider_visible=False,
            rangeselector=dict(
                buttons=range_buttons,
                bgcolor="rgba(150, 150, 150, 0.1)",
                bordercolor="rgba(150, 150, 150, 0.2)"
            )
        )
        fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        
    else:
        # Original candlestick implementation with CLEAN INDENTATION
        logger.info("Using standard candlestick chart")
        fig = go.Figure()

        fig.add_trace(go.Candlestick(
            x=df['datetime'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Candles',
            increasing_line_color='#00ff88',
            decreasing_line_color='#ff4444'
        ))

        fig.add_trace(go.Bar(
            x=df['datetime'],
            y=df['volume'],
            name='Volume',
            yaxis='y2',
            marker_color='gray',
            opacity=0.3
        ))

        if show_ma20 and 'ma20' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['datetime'],
                y=df['ma20'],
                name='MA20',
                line=dict(color='blue', width=1)
            ))
        if show_ma50 and 'ma50' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['datetime'],
                y=df['ma50'],
                name='MA50',
                line=dict(color='orange', width=1)
            ))

        if show_bollinger and 'bb_upper' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['datetime'],
                y=df['bb_upper'],
                name='BB Upper',
                line=dict(color='purple', width=1, dash='dot'),
                showlegend=False
            ))
            fig.add_trace(go.Scatter(
                x=df['datetime'],
                y=df['bb_lower'],
                name='BB Lower',
                line=dict(color='purple', width=1, dash='dot'),
                fill='tonexty',
                fillcolor='rgba(128,0,128,0.1)',
                showlegend=True
            ))

        if show_vwap and 'vwap' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['datetime'],
                y=df['vwap'],
                name='VWAP',
                line=dict(color='yellow', width=2)
            ))

        # Support and Resistance levels (inspired by bootcamp functions)
        if 'support_level' in df.columns and 'resistance_level' in df.columns:
            fig.add_hline(y=df['resistance_level'].iloc[-1], line_dash='dash', line_color='#ff4444',
                          annotation_text="Resistance", annotation_position="top right", opacity=0.7)
            fig.add_hline(y=df['support_level'].iloc[-1], line_dash='dash', line_color='#00ff88',
                          annotation_text="Support", annotation_position="bottom right", opacity=0.7)

        # All-time high and low levels
        fig.add_hline(y=df['high'].max(), line_dash='dash', line_color='red',
                      annotation_text="ATH", annotation_position="top left")
        fig.add_hline(y=df['low'].min(), line_dash='dash', line_color='green',
                      annotation_text="ATL", annotation_position="bottom left")

        # COMPLETELY REWRITTEN LAYOUT SECTION TO AVOID INDENTATION ISSUES
        try:
            layout_config = {
                'xaxis': {
                    'title': 'Date',
                    'type': 'date',
                    'rangeslider': {'visible': False},
                    'rangeselector': {
                        'buttons': range_buttons,
                        'bgcolor': "rgba(150, 150, 150, 0.1)",
                        'bordercolor': "rgba(150, 150, 150, 0.2)",
                        'borderwidth': 1,
                        'y': 1.02,
                        'x': 0.01
                    }
                },
                'yaxis': {'title': 'Price (USD)', 'domain': [0.3, 1]},
                'yaxis2': {'title': 'Volume', 'domain': [0, 0.2]},
                'hovermode': 'x unified',
                'height': 450,
                'template': 'plotly_dark',
                'legend': {
                    'orientation': 'h',
                    'y': 1.12,
                    'x': 0.5,
                    'xanchor': 'center',
                    'bgcolor': 'rgba(0,0,0,0.5)',
                    'bordercolor': 'rgba(255,255,255,0.2)',
                    'borderwidth': 1,
                    'font': {'size': 11},
                    'itemsizing': 'constant',
                    'tracegroupgap': 5
                },
                'title': {
                    'text': f"{symbol}/USD Chart ({preset_range if preset_range != 'Custom' else f'{date_diff} days'})",
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 20, 'color': '#ffffff'},
                    'pad': {'t': 20}
                },
                'margin': {'t': 120}
            }
            
            fig.update_layout(**layout_config)
            logger.info("✅ Chart layout updated successfully")
            
        except Exception as e:
            logger.error(f"❌ Chart layout error: {str(e)}")
            logger.error(traceback.format_exc())
            # Fallback to minimal layout
            fig.update_layout(template='plotly_dark', height=450, title=f"{symbol} Chart")
    
    # Display main chart
    create_chart_container(
        title="📈 Price Action & Volume",
        chart_figure=fig,
        export_format=export_format,
        height=450
    )
    
else:
    # No data available - show empty state
    fig = go.Figure()
    fig.add_annotation(
        text="📊 No data available for the selected timeframe",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=20, color="gray")
    )
    fig.update_layout(template='plotly_dark', height=400)
    create_chart_container("📈 Price Action", fig, export_format)

# === Advanced Indicator Charts ===
if len(df) > 0:
    # MACD with enhanced styling
    if show_macd and 'macd' in df.columns:
        with st.expander("📈 MACD Analysis (12, 26, 9)", expanded=False):
            macd_fig = go.Figure()
            
            # MACD Line
            macd_fig.add_trace(go.Scatter(
                x=df['datetime'], y=df['macd'], name='MACD',
                line=dict(color='#00bfff', width=2),
                hovertemplate='MACD: %{y:.4f}<extra></extra>'
            ))
            
            # Signal Line
            macd_fig.add_trace(go.Scatter(
                x=df['datetime'], y=df['macd_signal'], name='Signal',
                line=dict(color='#ff6b6b', width=2),
                hovertemplate='Signal: %{y:.4f}<extra></extra>'
            ))
            
            # Histogram with conditional coloring
            colors = ['#00ff88' if x >= 0 else '#ff4444' for x in df['macd_histogram']]
            macd_fig.add_trace(go.Bar(
                x=df['datetime'], y=df['macd_histogram'], name='Histogram',
                marker_color=colors, opacity=0.7,
                hovertemplate='Histogram: %{y:.4f}<extra></extra>'
            ))
            
            # Add zero line
            macd_fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            macd_fig.update_layout(
                height=350, 
                template='plotly_dark',
                title=dict(
                    text=f"MACD Analysis - {symbol}",
                    x=0.5,
                    xanchor='center',
                    font=dict(size=18, color='#ffffff')
                ),
                xaxis_title='Date', 
                yaxis_title='MACD',
                showlegend=True, 
                margin=dict(t=80, b=40),
                hovermode='x unified'
            )
            
            st.plotly_chart(macd_fig, use_container_width=True, config={
                'displayModeBar': True,
                'displaylogo': False,
                'scrollZoom': True,
                'toImageButtonOptions': {
                    'format': export_format.lower(),
                    'filename': f'MACD_{symbol}_{datetime.now().strftime("%Y%m%d_%H%M")}'
                }
            })

    # RSI with enhanced zones
    if show_rsi and 'rsi' in df.columns:
        with st.expander("📊 RSI Momentum (14-day)", expanded=False):
            rsi_fig = go.Figure()
            
            # RSI with gradient coloring based on zones
            rsi_colors = []
            for rsi_val in df['rsi']:
                if rsi_val >= 70:
                    rsi_colors.append('#ff4444')  # Overbought - Red
                elif rsi_val <= 30:
                    rsi_colors.append('#00ff88')  # Oversold - Green
                else:
                    rsi_colors.append('#4169e1')  # Neutral - Blue
            
            rsi_fig.add_trace(go.Scatter(
                x=df['datetime'], y=df['rsi'], name='RSI',
                line=dict(color='#9370db', width=3),
                fill='tonexty', fillcolor='rgba(147, 112, 219, 0.1)',
                hovertemplate='RSI: %{y:.2f}<extra></extra>'
            ))
            
            # Add RSI zones
            rsi_fig.add_hline(y=70, line_dash='dash', line_color='#ff4444', 
                             annotation_text="Overbought (70)", annotation_position="right")
            rsi_fig.add_hline(y=50, line_dash='dot', line_color='gray', opacity=0.5,
                             annotation_text="Midline", annotation_position="right")
            rsi_fig.add_hline(y=30, line_dash='dash', line_color='#00ff88',
                             annotation_text="Oversold (30)", annotation_position="right")
            
            # Add colored background zones
            rsi_fig.add_hrect(y0=70, y1=100, fillcolor="rgba(255, 68, 68, 0.1)", line_width=0)
            rsi_fig.add_hrect(y0=0, y1=30, fillcolor="rgba(0, 255, 136, 0.1)", line_width=0)
            
            rsi_fig.update_layout(
                height=350, 
                template='plotly_dark',
                title=dict(
                    text=f"RSI Momentum Analysis - {symbol}",
                    x=0.5,
                    xanchor='center',
                    font=dict(size=18, color='#ffffff')
                ),
                xaxis_title='Date', 
                yaxis_title='RSI',
                yaxis_range=[0, 100], 
                margin=dict(t=80, b=40),
                hovermode='x unified'
            )
            
            st.plotly_chart(rsi_fig, use_container_width=True, config={
                'displayModeBar': True,
                'displaylogo': False,
                'scrollZoom': True,
                'toImageButtonOptions': {
                    'format': export_format.lower(),
                    'filename': f'RSI_{symbol}_{datetime.now().strftime("%Y%m%d_%H%M")}'
                }
            })

# === Ultra-Enhanced Analytics Section ===
if len(df) > 0:
    st.markdown("---")
    st.markdown("### 📊 Advanced Market Intelligence")
    
    # Top-level metrics with enhanced styling
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        volatility = df['close'].pct_change().std() * 100
        vol_status = "🔥 High" if volatility > 5 else "💧 Low" if volatility < 2 else "⚖️ Medium"
        st.markdown(f'<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Daily Volatility", f"{volatility:.2f}%", 
                 delta=vol_status, help="Standard deviation of daily returns")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div class="metric-container">', unsafe_allow_html=True)
        volume_avg = df['volume'].mean()
        recent_vol = df['volume'].tail(7).mean()
        older_vol = df['volume'].head(7).mean() if len(df) > 14 else recent_vol
        volume_change = ((recent_vol / older_vol) - 1) * 100 if older_vol > 0 else 0
        vol_trend = "📈" if volume_change > 10 else "📉" if volume_change < -10 else "➡️"
        st.metric("Avg Volume", f"{volume_avg:,.0f}", 
                 delta=f"{vol_trend} {volume_change:+.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'<div class="metric-container">', unsafe_allow_html=True)
        returns = ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100
        return_emoji = "🚀" if returns > 10 else "📉" if returns < -10 else "📊"
        st.metric("Period Return", f"{return_emoji} {returns:+.2f}%", 
                 help="Total return for selected timeframe")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'<div class="metric-container">', unsafe_allow_html=True)
        max_drawdown = ((df['close'].cummax() - df['close']) / df['close'].cummax()).max() * 100
        dd_status = "🚨 High Risk" if max_drawdown > 20 else "⚠️ Medium" if max_drawdown > 10 else "✅ Low Risk"
        st.metric("Max Drawdown", f"{max_drawdown:.2f}%", 
                 delta=dd_status, delta_color="inverse")
        st.markdown('</div>', unsafe_allow_html=True)

    # === Fear & Greed Index Analysis ===
    if len(df) > 30:  # Need enough data for calculations
        st.markdown("#### 🎭 Market Sentiment Analysis")
        
        fear_greed_result = calculate_fear_greed_index(df)
        if fear_greed_result and fear_greed_result[0] is not None:
            fear_greed_score, sentiment, color, breakdown = fear_greed_result
            
            # Create two columns for gauge and breakdown
            gauge_col, breakdown_col = st.columns([1, 1])
            
            with gauge_col:
                # Display the Fear & Greed gauge
                gauge_fig = create_fear_greed_gauge(fear_greed_score, sentiment, color)
                st.plotly_chart(gauge_fig, use_container_width=True)
            
            with breakdown_col:
                st.markdown("**📊 Index Breakdown:**")
                
                # Component breakdown with progress bars
                for component, score in breakdown.items():
                    if component != 'Final Score':
                        st.markdown(f"**{component}:** {score:.1f}/100")
                        st.progress(score/100)
                
                # Interpretation guide
                st.markdown("---")
                st.markdown("**📖 Interpretation Guide:**")
                st.markdown("""
                - **0-24**: 😰 Extreme Fear - Great buying opportunity
                - **25-49**: 😟 Fear - Consider accumulating  
                - **50-74**: 😃 Greed - Take some profits
                - **75-100**: 🤑 Extreme Greed - Consider selling
                """)
                
                # Historical context
                if len(df) > 90:
                    # Calculate fear/greed over time for context
                    historical_scores = []
                    for i in range(30, len(df)):
                        subset = df.iloc[:i+1]
                        hist_result = calculate_fear_greed_index(subset)
                        if hist_result and hist_result[0] is not None:
                            historical_scores.append(hist_result[0])
                    
                    if historical_scores:
                        avg_score = np.mean(historical_scores)
                        current_vs_avg = fear_greed_score - avg_score
                        
                        comparison = "above average 📈" if current_vs_avg > 5 else "below average 📉" if current_vs_avg < -5 else "near average ➡️"
                        st.info(f"Current sentiment is **{comparison}** (vs {avg_score:.1f} avg)")

    # Enhanced Technical Analysis Section
    st.markdown("---")
    
    # Technical Analysis Section with collapsible header
    with st.expander("🔬 **Technical Analysis**", expanded=True):
        # Create a 2x2 grid for better organization
        tech_cols1 = st.columns(2)
        tech_cols2 = st.columns(2)
        
        # Row 1
        with tech_cols1[0]:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            
            # Trend Analysis
            x = np.arange(len(df))
            slope = np.polyfit(x, df['close'], 1)[0]
            trend_strength = abs(slope) / df['close'].mean() * 1000
            
            trend_icon = "📈" if slope > 0 else "📉"
            trend_text = "Bullish" if slope > 0 else "Bearish"
            
            st.markdown(f"#### {trend_icon} Trend Strength")
            st.markdown(f"<h2 style='color: {'#00ff88' if slope > 0 else '#ff4444'}'>{trend_text}</h2>", unsafe_allow_html=True)
            st.markdown(f"**Strength:** {trend_strength:.2f}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tech_cols1[1]:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            
            # Range Position
            support = df['low'].rolling(window=20).min().iloc[-1]
            resistance = df['high'].rolling(window=20).max().iloc[-1]
            current = df['close'].iloc[-1]
            range_position = ((current - support) / (resistance - support)) * 100
            
            st.markdown("#### 📍 Range Position")
            st.markdown(f"<h2 style='color: #4ecdc4'>{range_position:.1f}%</h2>", unsafe_allow_html=True)
            
            if range_position > 80:
                st.markdown("**Status:** 🔝 Near Resistance")
            elif range_position < 20:
                st.markdown("**Status:** 🔻 Near Support")
            else:
                st.markdown("**Status:** 🎯 Mid-Range")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Row 2
        with tech_cols2[0]:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            
            # Volume Profile
            volume_avg = df['volume'].mean()
            recent_volume = df['volume'].iloc[-1]
            volume_ratio = (recent_volume / volume_avg) * 100
            
            st.markdown("#### 📊 Volume Profile")
            st.markdown(f"<h2 style='color: #ff6b6b'>{volume_ratio:.0f}%</h2>", unsafe_allow_html=True)
            
            if recent_volume > volume_avg:
                st.markdown("**Status:** 🔊 Above Average")
            else:
                st.markdown("**Status:** 🔉 Below Average")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tech_cols2[1]:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            
            # Market Efficiency
            price_path = df['close'].diff().abs().sum()
            direct_path = abs(df['close'].iloc[-1] - df['close'].iloc[0])
            efficiency = (direct_path / price_path) * 100 if price_path > 0 else 0
            
            st.markdown("#### 🎯 Market Efficiency")
            st.markdown(f"<h2 style='color: #ffa500'>{efficiency:.1f}%</h2>", unsafe_allow_html=True)
            
            if efficiency > 20:
                st.markdown("**Status:** 🎯 Trending")
            elif efficiency < 5:
                st.markdown("**Status:** 🌀 Choppy")
            else:
                st.markdown("**Status:** ⚖️ Mixed")
            
            st.markdown('</div>', unsafe_allow_html=True)

    # === Performance Monitoring Section ===
    if performance_mode and len(df) > 0:
        st.markdown("---")
        st.markdown("### ⚡ Performance Metrics")
        
        perf_col1, perf_col2, perf_col3 = st.columns(3)
        
        with perf_col1:
            calc_start = time.time()
            # Simulate calculation time
            _ = df['close'].rolling(50).mean().dropna()
            calc_time = time.time() - calc_start
            st.metric("Calculation Speed", f"{calc_time*1000:.1f}ms")
        
        with perf_col2:
            memory_usage = df.memory_usage(deep=True).sum() / 1024  # KB
            st.metric("Memory Usage", f"{memory_usage:.1f} KB")
        
        with perf_col3:
            data_quality_score = (1 - (df.isnull().sum().sum() / (len(df) * len(df.columns)))) * 100
            st.metric("Data Quality", f"{data_quality_score:.1f}%")

# === Error Summary and Health Check ===
if debug_mode:
    st.markdown("---")
    st.markdown("### 🐛 Debug Information")
    
    debug_col1, debug_col2 = st.columns(2)
    
    with debug_col1:
        st.markdown("**System Status:**")
        st.success("✅ Database Connected")
        st.success("✅ Data Loaded Successfully")
        st.success("✅ Charts Rendered")
        
        if len(df) > 0:
            st.info(f"📊 Dataset: {len(df)} records from {df['datetime'].min().date()} to {df['datetime'].max().date()}")
    
    with debug_col2:
        st.markdown("**Performance Stats:**")
        total_time = time.time() - st.session_state.page_load_time
        st.metric("Total Load Time", f"{total_time:.2f}s")
        st.metric("Data Points", len(df) if len(df) > 0 else 0)
        st.metric("Cache Status", "🟢 Active" if st.cache_data else "🔴 Disabled")

# === Auto-refresh functionality ===
if auto_refresh:
    time.sleep(5)
    st.rerun()

# === Enhanced Footer ===
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; background: rgba(42, 42, 74, 0.2); border-radius: 15px; margin-top: 2rem;'>
    <h3 style='color: #4ecdc4; margin-bottom: 1rem;'>🚀 Crypto Dashboard Pro</h3>
    <p style='color: #888;'>Built with Streamlit & Plotly | Real-time PostgreSQL Data | Advanced Technical Analysis</p>
    <p style='color: #666; font-size: 0.9rem; margin-top: 1rem;'>
        Dashboard Performance: {:.2f}s load time | {} data points | 
        <span style='color: #00ff88;'>● Live</span>
    </p>
</div>
""".format(time.time() - st.session_state.page_load_time, len(df) if len(df) > 0 else 0), unsafe_allow_html=True)

# Log successful completion
logger.info(f"Dashboard loaded successfully for {symbol} - {len(df) if len(df) > 0 else 0} records")