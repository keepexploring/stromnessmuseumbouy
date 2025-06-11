# 🌊 Stromness Museum Water Monitoring Dashboard

A real-time water temperature monitoring system for Stromness Harbor, featuring a LoRa-enabled buoy and beautiful web dashboard.

![Dashboard Preview](https://img.shields.io/badge/status-live-brightgreen)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.32.0-FF4B4B)

## 🚀 Live Demo

Visit the live dashboard: [https://stromnessmuseumbouy.streamlit.app](https://stromnessmuseumbouy.streamlit.app)

## 📋 Features

- **Real-time Temperature Display** - Live water temperature with status indicators
- **Interactive Charts** - Time-series graphs with temperature zones
- **Historical Data** - View trends from 1 hour to 1 month
- **Data Export** - Download data as CSV or JSON
- **Auto-refresh** - Updates every 30 seconds
- **Mobile Responsive** - Works on all devices

## 🛠️ Technology Stack

- **Frontend**: Streamlit, Plotly
- **Backend**: Supabase (PostgreSQL)
- **Hardware**: Raspberry Pi Pico W + LoRa Module
- **Deployment**: Streamlit Cloud

## 📦 Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stromnessmuseumbouy.git
cd stromnessmuseumbouy

Create virtual environment:

bashpython -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies:

bashpip install -r requirements.txt

Create .env file:

bashcp .env.example .env
# Edit .env with your Supabase credentials

Run the app:

bashstreamlit run app.py
🔧 Configuration
Environment Variables
Create a .env file with:
SUPABASE_URL=your-project-url
SUPABASE_ANON_KEY=your-anon-key

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

Thank you to Stromness Museum for supporting the development of this project.

The Orkney community for testing and feedback

📞 Contact
Stromness Museum - info@stromnessmuseum.org.uk
