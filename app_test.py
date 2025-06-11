import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import random

# Page configuration
st.set_page_config(
    page_title="Stromness Museum Water Monitoring",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 0.5rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .live-temp {
        font-size: 3rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .last-update {
        font-size: 0.9rem;
        opacity: 0.8;
    }
    .status-good {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🌊 Stromness Museum Water Monitoring Buoy</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Real-time sea temperature monitoring from Stromness Harbor</p>', unsafe_allow_html=True)

# Demo mode warning
st.warning("⚠️ **DEMO MODE**: Running without Supabase connection. Using simulated data for testing.")

# Sidebar for controls
st.sidebar.header("📊 Data Controls")

# Time range selector
time_options = {
    "Last Hour": 1,
    "Last 6 Hours": 6, 
    "Last 24 Hours": 24,
    "Last 3 Days": 72,
    "Last Week": 168,
    "Last Month": 720
}

selected_range = st.sidebar.selectbox(
    "Select Time Range",
    options=list(time_options.keys()),
    index=2  # Default to Last 24 Hours
)

hours_back = time_options[selected_range]

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=True)

# Generate fake data for testing
@st.cache_data
def generate_fake_data(hours_back):
    # Generate timestamps
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours_back)
    
    # Create data points every 5 minutes
    timestamps = []
    current = start_time
    while current <= end_time:
        timestamps.append(current)
        current += timedelta(minutes=5)
    
    # Generate realistic temperature data (Scottish waters: 8-15°C)
    base_temp = 12.0
    temperatures = []
    for i, ts in enumerate(timestamps):
        # Add daily variation (warmer in afternoon)
        hour_effect = np.sin((ts.hour - 6) * np.pi / 12) * 1.5
        # Add some random noise
        noise = random.gauss(0, 0.3)
        # Add slow drift
        drift = np.sin(i * 0.01) * 0.5
        temp = base_temp + hour_effect + noise + drift
        temperatures.append(round(temp, 2))
    
    # Create DataFrame
    df = pd.DataFrame({
        'id': range(len(timestamps)),
        'timestamp': timestamps,
        'temperature': temperatures,
        'source': ['lora' if random.random() > 0.1 else 'manual' for _ in timestamps],
        'rssi': [random.randint(-80, -60) if random.random() > 0.1 else None for _ in timestamps],
        'location': ['Stromness Harbor'] * len(timestamps)
    })
    
    return df.sort_values('timestamp', ascending=False)

# Get fake latest reading
def get_fake_latest_reading():
    df = generate_fake_data(1)
    if not df.empty:
        return df.iloc[0].to_dict()
    return None

# Load data
df = generate_fake_data(hours_back)
latest_reading = get_fake_latest_reading()

# Main dashboard layout
col1, col2, col3 = st.columns([2, 1, 1])

# Live temperature display
with col1:
    if latest_reading:
        temp = latest_reading['temperature']
        timestamp = pd.to_datetime(latest_reading['timestamp'])
        source = latest_reading.get('source', 'unknown')
        rssi = latest_reading.get('rssi', 'N/A')
        
        # Calculate time since last reading
        time_diff = datetime.now() - timestamp.replace(tzinfo=None)
        
        if time_diff.total_seconds() < 300:  # Less than 5 minutes
            status_class = "status-good"
            status_text = "🟢 LIVE"
        elif time_diff.total_seconds() < 1800:  # Less than 30 minutes
            status_class = "status-warning" 
            status_text = "🟡 RECENT"
        else:
            status_class = "status-error"
            status_text = "🔴 OFFLINE"
        
        st.markdown(f"""
        <div class="metric-container">
            <div class="{status_class}">{status_text}</div>
            <div class="live-temp">{temp:.1f}°C</div>
            <div class="last-update">
                Last Updated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}<br>
                Source: {source.upper()} | Signal: {rssi} dBm
            </div>
        </div>
        """, unsafe_allow_html=True)

# Statistics
with col2:
    if not df.empty:
        st.metric(
            label="📊 Average Temperature",
            value=f"{df['temperature'].mean():.1f}°C",
            delta=f"{df['temperature'].std():.1f}°C std"
        )
        
        st.metric(
            label="🌡️ Temperature Range", 
            value=f"{df['temperature'].min():.1f}°C",
            delta=f"Max: {df['temperature'].max():.1f}°C"
        )

with col3:
    if not df.empty:
        st.metric(
            label="📈 Total Readings",
            value=len(df),
            delta=f"Over {selected_range.lower()}"
        )
        
        # Data source breakdown
        if 'source' in df.columns:
            lora_count = len(df[df['source'] == 'lora'])
            manual_count = len(df[df['source'] == 'manual'])
            st.metric(
                label="📡 LoRa Readings",
                value=lora_count,
                delta=f"Manual: {manual_count}"
            )

# Main chart
st.subheader(f"🌊 Temperature Trends - {selected_range}")

if not df.empty:
    # Create beautiful plotly chart
    fig = go.Figure()
    
    # Add temperature line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['temperature'],
        mode='lines+markers',
        name='Water Temperature',
        line=dict(color='#4fc3f7', width=3),
        marker=dict(size=6, color='#0277bd'),
        hovertemplate='<b>%{y:.1f}°C</b><br>%{x}<br><extra></extra>'
    ))
    
    # Styling
    fig.update_layout(
        title=dict(
            text="Sea Water Temperature Over Time",
            x=0.5,
            font=dict(size=20, color='#1f4e79')
        ),
        xaxis_title="Time",
        yaxis_title="Temperature (°C)",
        font=dict(size=12),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=500,
        xaxis=dict(
            gridcolor='rgba(128,128,128,0.2)',
            showgrid=True
        ),
        yaxis=dict(
            gridcolor='rgba(128,128,128,0.2)',
            showgrid=True
        ),
        hovermode='x unified'
    )
    
    # Add temperature zones
    fig.add_hline(y=15, line_dash="dash", line_color="blue", opacity=0.5, annotation_text="Cold")
    fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.5, annotation_text="Comfortable")
    fig.add_hline(y=25, line_dash="dash", line_color="red", opacity=0.5, annotation_text="Warm")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Additional charts in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Temperature Distribution")
        
        # Histogram
        fig_hist = px.histogram(
            df, 
            x='temperature',
            nbins=20,
            title="Temperature Frequency Distribution",
            color_discrete_sequence=['#4fc3f7']
        )
        fig_hist.update_layout(
            xaxis_title="Temperature (°C)",
            yaxis_title="Frequency",
            plot_bgcolor='rgba(0,0,0,0)',
            height=300
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        st.subheader("📈 Data Source Summary")
        
        if 'source' in df.columns:
            source_counts = df['source'].value_counts()
            
            fig_pie = px.pie(
                values=source_counts.values,
                names=source_counts.index,
                title="Readings by Source",
                color_discrete_sequence=['#4fc3f7', '#ffa726']
            )
            fig_pie.update_layout(height=300)
            st.plotly_chart(fig_pie, use_container_width=True)

# Data download section
st.subheader("💾 Download Historical Data")

download_col1, download_col2 = st.columns(2)

with download_col1:
    if not df.empty:
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📄 Download as CSV",
            data=csv_data,
            file_name=f"stromness_water_temp_DEMO_{selected_range.lower().replace(' ', '_')}.csv",
            mime="text/csv"
        )

with download_col2:
    if not df.empty:
        json_data = df.to_json(orient='records', date_format='iso')
        st.download_button(
            label="📋 Download as JSON", 
            data=json_data,
            file_name=f"stromness_water_temp_DEMO_{selected_range.lower().replace(' ', '_')}.json",
            mime="application/json"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🌊 <strong>Stromness Museum Water Monitoring System</strong> 🌊</p>
    <p>🚧 <strong>DEMO MODE</strong> - Using simulated data 🚧</p>
    <p><em>Built with ❤️ for marine research and education</em></p>
</div>
""", unsafe_allow_html=True)

# Status bar
with st.container():
    status_col1, status_col2, status_col3, status_col4 = st.columns(4)
    
    with status_col1:
        st.success("🟢 DEMO Mode")
    
    with status_col2:
        st.info(f"📊 {len(df)} fake readings")
    
    with status_col3:
        current_time = datetime.now().strftime("%H:%M:%S")
        st.info(f"🕐 {current_time}")
    
    with status_col4:
        st.warning("🔧 TEST DATA")

# Auto-refresh implementation
if auto_refresh:
    import time
    time.sleep(30)
    st.rerun()