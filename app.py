import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from supabase import Client
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    .project-info {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    # Try to get from Streamlit secrets first (for cloud deployment)
    try:
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]
    except:
        # Fallback to environment variables (for local development)
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("❌ Supabase credentials not found! Please check your secrets configuration.")
        st.info("For local development: Check your .env file")
        st.info("For Streamlit Cloud: Check your app secrets")
        st.stop()
    
    # Use older client initialization to avoid proxy error
    from supabase import Client
    return Client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_supabase()

# Header
st.markdown('<h1 class="main-header">🌊 Stromness Museum Water Monitoring Buoy</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Real-time sea temperature monitoring from Stromness Harbor</p>', unsafe_allow_html=True)

# Project opener
st.markdown("""
<div style="background: #f8f9fa; padding: 1.5rem; border-radius: 10px; margin: 2rem 0; border-left: 4px solid #667eea;">
<p style="margin: 0; font-size: 1.1rem; line-height: 1.6; color: #333;">
This sea temperature monitoring buoy was designed by <strong>Tern 360</strong> in partnership with the <strong>West Mainland Youth Achievement group</strong>. It was part of an Oceans/Wellbeing/Arts and Youth project coordinated by <strong>Stromness Museum</strong> in 2025. It was funded by the <strong>Orkney Youth Local Action Group (YLAG)</strong>.
</p>
</div>
""", unsafe_allow_html=True)

# Deployment date - from environment variable or default
deployment_date_str = os.getenv("DEPLOYMENT_DATE", "2024-11-01")
try:
    DEPLOYMENT_DATE = datetime.strptime(deployment_date_str, "%Y-%m-%d")
except ValueError:
    DEPLOYMENT_DATE = datetime(2024, 11, 1)  # Fallback default
    
deployment_days = (datetime.now() - DEPLOYMENT_DATE).days
st.markdown(f'<p style="text-align: center; color: #666; margin-bottom: 2rem;">📅 This project started on {DEPLOYMENT_DATE.strftime("%B %d, %Y")} • {deployment_days} days of monitoring</p>', unsafe_allow_html=True)

# Sidebar for controls
st.sidebar.header("📊 Dashboard Controls")
st.sidebar.markdown("*Controls statistics and additional charts below*")

# Time range selector - Extended options
time_options = {
    "Last Hour": 1,
    "Last 6 Hours": 6, 
    "Last 24 Hours": 24,
    "Last 3 Days": 72,
    "Last Week": 168,
    "Last Month": 720,
    "Last 3 Months": 2160,
    "Last Year": 8760,
    "All Data": None  # None means no time limit
}

selected_range = st.sidebar.selectbox(
    "Select Time Range",
    options=list(time_options.keys()),
    index=2  # Default to Last 24 Hours
)

hours_back = time_options[selected_range]

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=True)

# Add refresh interval for auto-refresh
if auto_refresh:
    st.sidebar.info("🔄 Page will refresh automatically every 30 seconds")
    
    # Initialize session state for timing
    if 'last_run' not in st.session_state:
        st.session_state.last_run = time.time()
    
    # Check if it's time to refresh
    elapsed = time.time() - st.session_state.last_run
    
    if elapsed >= 30:
        st.session_state.last_run = time.time()
        st.cache_data.clear()
        st.rerun()
    else:
        # Show countdown
        remaining = int(30 - elapsed)
        st.sidebar.markdown(f"⏱️ Next refresh: {remaining}s")
        
        # Use a small sleep and rerun to update countdown
        time.sleep(1)
        st.rerun()

@st.cache_data(ttl=60)  # Cache for 1 minute
def load_temperature_data(hours_back):
    try:
        # Query Supabase
        if hours_back is None:  # All data
            response = supabase.table('water_temperature').select("*").order('timestamp', desc=True).execute()
        else:
            # Calculate start time
            start_time = datetime.now() - timedelta(hours=hours_back)
            start_time_str = start_time.isoformat()
            response = supabase.table('water_temperature').select("*").gte('timestamp', start_time_str).order('timestamp', desc=True).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=30)  # Cache for 30 seconds for live data
def get_latest_reading():
    try:
        response = supabase.table('water_temperature').select("*").order('timestamp', desc=True).limit(1).execute()
        
        if response.data:
            return response.data[0]
        else:
            return None
    except Exception as e:
        st.error(f"Error getting latest reading: {str(e)}")
        return None

# Load data
df = load_temperature_data(hours_back)
latest_reading = get_latest_reading()

# Main dashboard layout
col1, col2, col3 = st.columns([2, 1, 1])

# Live temperature display
with col1:
    if latest_reading:
        temp = latest_reading['temperature']
        timestamp = pd.to_datetime(latest_reading['timestamp'])
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
                Signal Strength: {rssi} dBm
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-container">
            <div class="status-error">🔴 NO DATA</div>
            <div class="live-temp">--°C</div>
            <div class="last-update">No readings available</div>
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
        
        # Maximum temperature
        max_temp = df['temperature'].max()
        max_date = df.loc[df['temperature'].idxmax(), 'timestamp']
        st.metric(
            label="🌡️ Maximum",
            value=f"{max_temp:.1f}°C",
            delta=f"on {max_date.strftime('%b %d')}"
        )
    else:
        st.metric("📊 Average Temperature", "--°C")
        st.metric("🌡️ Maximum", "--°C")

with col3:
    if not df.empty:
        # Minimum temperature
        min_temp = df['temperature'].min()
        min_date = df.loc[df['temperature'].idxmin(), 'timestamp']
        st.metric(
            label="❄️ Minimum",
            value=f"{min_temp:.1f}°C",
            delta=f"on {min_date.strftime('%b %d')}"
        )
        
        # Total readings in selected period
        st.metric(
            label="📈 Total Readings",
            value=f"{len(df):,}",
            delta=f"{selected_range}"
        )
    else:
        st.metric("❄️ Minimum", "--°C")
        st.metric("📈 Total Readings", "0")

# Main chart
st.subheader(f"🌊 Temperature Trends")

# Add time range buttons for the main chart
st.markdown("**Quick Time Range Selection:**")
chart_col1, chart_col2, chart_col3, chart_col4, chart_col5 = st.columns(5)

with chart_col1:
    if st.button("📅 Last Day", key="chart_day"):
        st.session_state.chart_hours = 24
with chart_col2:
    if st.button("📅 Last Week", key="chart_week"):
        st.session_state.chart_hours = 168
with chart_col3:
    if st.button("📅 Last Month", key="chart_month"):
        st.session_state.chart_hours = 720
with chart_col4:
    if st.button("📅 Last 3 Months", key="chart_3months"):
        st.session_state.chart_hours = 2160
with chart_col5:
    if st.button("📅 All Data", key="chart_all"):
        st.session_state.chart_hours = None

# Initialize chart time range if not set
if 'chart_hours' not in st.session_state:
    st.session_state.chart_hours = 168  # Default to last week

# Load data for the chart (separate from sidebar selection)
@st.cache_data(ttl=60)
def load_chart_data(chart_hours):
    try:
        if chart_hours is None:  # All data
            response = supabase.table('water_temperature').select("*").order('timestamp', desc=True).execute()
        else:
            start_time = datetime.now() - timedelta(hours=chart_hours)
            start_time_str = start_time.isoformat()
            response = supabase.table('water_temperature').select("*").gte('timestamp', start_time_str).order('timestamp', desc=True).execute()
        
        if response.data:
            chart_df = pd.DataFrame(response.data)
            chart_df['timestamp'] = pd.to_datetime(chart_df['timestamp'])
            return chart_df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading chart data: {str(e)}")
        return pd.DataFrame()

# Load chart data
chart_df = load_chart_data(st.session_state.chart_hours)

# Display current chart time range
chart_range_names = {
    24: "Last Day",
    168: "Last Week", 
    720: "Last Month",
    2160: "Last 3 Months",
    None: "All Data"
}
current_range = chart_range_names.get(st.session_state.chart_hours, "Custom")
st.markdown(f"*Showing: **{current_range}** ({len(chart_df):,} readings)*")

if not chart_df.empty:
    # Create beautiful plotly chart
    fig = go.Figure()
    
    # Add temperature line
    fig.add_trace(go.Scatter(
        x=chart_df['timestamp'],
        y=chart_df['temperature'],
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
    
    # Add cold water swimming temperature bands
    # Based on outdoor swimming temperature experiences
    fig.add_hrect(y0=0, y1=6, fillcolor="darkblue", opacity=0.1, line_width=0, annotation_text="Baltic (0-6°C)", annotation_position="right")
    fig.add_hrect(y0=6, y1=11, fillcolor="blue", opacity=0.1, line_width=0, annotation_text="Freezing (6-11°C)", annotation_position="right")
    fig.add_hrect(y0=12, y1=16, fillcolor="lightblue", opacity=0.1, line_width=0, annotation_text="Fresh (12-16°C)", annotation_position="right")
    fig.add_hrect(y0=17, y1=20, fillcolor="lightgreen", opacity=0.1, line_width=0, annotation_text="Summer (17-20°C)", annotation_position="right")
    fig.add_hrect(y0=21, y1=30, fillcolor="orange", opacity=0.1, line_width=0, annotation_text="Warm (21°C+)", annotation_position="right")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add note about temperature bands
    st.info("🏊 **Cold Water Swimming Guide**: The temperature bands shown above reflect how open water swimmers typically experience different water temperatures. While not strictly scientific, these ranges are based on anecdotal experiences from the swimming community.")
    
    # Additional charts in columns
    st.markdown("---")
    st.subheader(f"📈 Additional Analysis - {selected_range}")
    st.markdown("*The charts below use the time range selected in the sidebar*")
    
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
        st.subheader("📈 Daily Temperature Pattern")
        
        # Extract hour from timestamp and calculate average temperature by hour
        df['hour'] = df['timestamp'].dt.hour
        hourly_avg = df.groupby('hour')['temperature'].mean().reset_index()
        
        fig_hourly = px.line(
            hourly_avg, 
            x='hour', 
            y='temperature',
            title="Average Temperature by Hour of Day",
            color_discrete_sequence=['#ffa726']
        )
        fig_hourly.update_layout(
            xaxis_title="Hour of Day",
            yaxis_title="Average Temperature (°C)",
            plot_bgcolor='rgba(0,0,0,0)',
            height=300
        )
        st.plotly_chart(fig_hourly, use_container_width=True)

else:
    st.info(f"📭 No data available for the selected chart time range ({current_range})")
    st.markdown("**Try selecting a different time range above**")

# Data download section
st.subheader("💾 Download Historical Data")

download_col1, download_col2, download_col3 = st.columns(3)

with download_col1:
    if not df.empty:
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📄 Download as CSV",
            data=csv_data,
            file_name=f"stromness_water_temp_{selected_range.lower().replace(' ', '_')}.csv",
            mime="text/csv"
        )

with download_col2:
    if not df.empty:
        json_data = df.to_json(orient='records', date_format='iso')
        st.download_button(
            label="📋 Download as JSON", 
            data=json_data,
            file_name=f"stromness_water_temp_{selected_range.lower().replace(' ', '_')}.json",
            mime="application/json"
        )

with download_col3:
    # Custom date range download
    st.markdown("**Custom Range:**")
    if st.button("📅 Select Custom Dates"):
        st.session_state.show_date_picker = True

if st.session_state.get('show_date_picker', False):
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    if st.button("Download Custom Range"):
        if hours_back is None:  # All data selected
            custom_df = load_temperature_data(None)
        else:
            custom_df = load_temperature_data((datetime.now() - datetime.combine(start_date, datetime.min.time())).total_seconds() / 3600)
        
        # Filter by date range
        mask = (custom_df['timestamp'] >= pd.to_datetime(start_date)) & (custom_df['timestamp'] <= pd.to_datetime(end_date))
        custom_df = custom_df.loc[mask]
        
        if not custom_df.empty:
            custom_csv = custom_df.to_csv(index=False)
            st.download_button(
                label="📄 Download Custom CSV",
                data=custom_csv,
                file_name=f"stromness_water_temp_{start_date}_to_{end_date}.csv",
                mime="text/csv"
            )

# About the Project Section
st.markdown("---")
st.markdown('<div class="project-info">', unsafe_allow_html=True)
st.markdown("## 🌊 About This Project")

st.markdown("""
Through the project the youth group helped to design the buoy and its digital technology. They built a housing for inside the museum to display the data. They also spent time with artist **Jenny Pope**, learning about how to focus on their own wellbeing, fostering resilience in the face of the climate crisis through creativity. Finally the group took part in a snorkel at the Museum with **Kraken Diving** to see what marine life lives on their doorstep and to deploy the monitoring buoy.

**Stromness Museum** is the museum of the Orkney Natural History Society. Its founding President in 1837 was the Rev Dr **Charles Clouston**, who was a dedicated long term weather recorder for the county. It is in this tradition that we are now creating a set of present day sea temperature records for Orkney.

Charles Clouston wrote a paper *"An explanation of the popular weather prognostics of Scotland on scientific principles."* which can be read online here: [https://babel.hathitrust.org/cgi/pt?id=hvd.hxcr4m&seq=7](https://babel.hathitrust.org/cgi/pt?id=hvd.hxcr4m&seq=7)

The **West Mainland Youth Achievement Group** are an awards based youth group run in Stromness for ages 10+. The group love taking part in activities and community events while working towards Dynamic Youth or Youth Achievement Awards. Through this project the group worked towards a **Dynamic Youth Award**.

Sea swimming and snorkelling are popular pastimes in Orkney. Check out the [Orkney Snorkel Trail](https://scottishwildlifetrust.org.uk/wp-content/uploads/2024/08/202407_Orkney-snorkel-trail_04-ONLINE.pdf) from the Scottish Wildlife Trust.
""")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### [🏛️ Stromness Museum](https://stromnessmuseum.org.uk)")
with col2:
    st.markdown("### [🌐 Tern360](https://www.tern360.com)")
with col3:
    st.markdown("### [🤿 Kraken Diving](https://www.krakendiving.co.uk)")

st.markdown("*Special thanks to the West Mainland Youth Achievement Group, Jenny Pope, and all the young people who made this project possible!*")
st.markdown('</div>', unsafe_allow_html=True)

# Safe Cold Water Swimming Section
st.markdown("---")
st.markdown("## 🏊 Safe Cold Water Swimming")

st.markdown("""
**Cold water temperature varies hugely, and while this isn't scientific, anecdotally, open water swimmers experience it in these bands:**

### Temperature Bands

**0-6°C: BALTIC** 🧊  
Jumping in is likely to impair breathing in the uninitiated, as breath comes in big jolting gasps. Water has bite, skin smarts and burns. This is winter swimming. Limbs soon become weak – 25 metres can be an achievement. The joy is the cold water high: pure exhilaration and rush of endorphins.

**6-11°C: FREEZING** ❄️  
Much like baltic, but not quite so painful, or breathtaking.

**12-16°C: FRESH** 💙  
At this temperature triathlons start operating. In a wetsuit you may find you can swim comfortably for a while. Outside of one, the water is fresh, doable for the brave.

**17-20°C: SUMMER SWIMMING** ☀️  
Lakes and more mature rivers reach this temperature over summer, during hot spells. Still fresh on entry, but comfortable picnic lazy-hazy summer swimming.

**21°C+: WARM** 🌡️  
On rare occasions when waters reach these temperatures, there's an odd sense that something's missing – the cold water 'tang'.

### ⚠️ Cold Water Safety Risks

When embracing cold water please be aware of the following:

- **Cold Water Shock**: Sudden immersion causes sharp intake of breath, increased breathing rate and blood pressure
- **Swim Failure**: Reduced blood flow to limbs can weaken arms and legs to a point you can't swim
- **Afterdrop**: You'll be coldest 10 minutes after exiting as blood returns to your skin
- **Hypothermia**: Drop in core body temperature leading to shivering, loss of consciousness

**Safety Tips:**
- Stay close to shore
- Wear a wetsuit for longer swims
- Exit if you start shivering or limbs weaken
- Have warm clothes and drinks ready
- Never swim alone in cold water
- Acclimatise gradually

*Learn more about [How to Acclimatise To Cold Water](https://outdoorswimmingsociety.com/)*
""")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🌊 <strong>Stromness Museum Water Monitoring System</strong> 🌊</p>
    <p>Real-time data from LoRa-enabled buoy • Updated every few minutes</p>
    <p><em>Empowering young people through marine science and technology</em></p>
</div>
""", unsafe_allow_html=True)

# Status bar
with st.container():
    status_col1, status_col2, status_col3, status_col4 = st.columns(4)
    
    with status_col1:
        if latest_reading and pd.to_datetime(latest_reading['timestamp']).replace(tzinfo=None) > datetime.now() - timedelta(minutes=10):
            st.success("🟢 Buoy Online")
        else:
            st.error("🔴 Buoy Offline")
    
    with status_col2:
        if not df.empty:
            st.info(f"📊 {len(df):,} readings")
        else:
            st.warning("📊 No data")
    
    with status_col3:
        current_time = datetime.now().strftime("%H:%M:%S")
        st.info(f"🕐 {current_time}")
    
    with status_col4:
        if latest_reading:
            st.success("📡 LoRa Active")
        else:
            st.error("❌ NO SIGNAL")

# Debug information (only show if no data)
if df.empty:
    st.markdown("---")
    with st.expander("🔧 Debug Information"):
        st.write("**Troubleshooting steps:**")
        st.write("1. Check if Arduino is connected to WiFi")
        st.write("2. Verify Supabase credentials are correct")  
        st.write("3. Check Supabase table for data")
        
        # Show connection test
        if st.button("Test Supabase Connection"):
            try:
                test_response = supabase.table('water_temperature').select("count").execute()
                st.success(f"✅ Connection successful! Table exists.")
            except Exception as e:
                st.error(f"❌ Connection failed: {str(e)}")

# Final spacing
st.markdown("<br>", unsafe_allow_html=True)

# Auto-refresh at the very end
if auto_refresh:
    # This will automatically refresh the page every 30 seconds
    st.markdown("""
    <script>
    setTimeout(function(){
        window.location.reload(1);
    }, 30000);
    </script>
    """, unsafe_allow_html=True)