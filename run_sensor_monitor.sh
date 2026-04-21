#!/bin/bash

# Quick start script for Sensor Monitor
# Run this to start the sensor data collection server on localhost:5001

echo "🚀 Starting Sensor Monitor Web Server..."
echo ""

# Check if Python virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Check if model files exist
if [ ! -f "model/model.pkl" ] || [ ! -f "model/scaler.pkl" ]; then
    echo "⚠️  Model files not found. Training model..."
    python ml_train.py
fi

echo ""
echo "✅ All set! Starting server..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Dashboard: http://localhost:5001"
echo "📊 API: http://localhost:5001/api/sensor-data"
echo "📈 Status: http://localhost:5001/api/status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⏱️  Sensor readings: Every 10 seconds"
echo "📡 Data source: Auto-detected (Arduino or Mock)"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server
python sensor_monitor.py
