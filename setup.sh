#!/bin/bash

# 🚀 ML-Based 3D Printer Health Monitoring - Setup Script
# This script sets up the Python environment and trains the ML model

set -e

echo "🔧 Setting up ML Environment..."
echo "================================"

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "✅ Activating virtual environment..."
source venv/bin/activate

echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Environment setup complete!"
echo ""
echo "🤖 Training ML Model..."
echo "========================"
python3 quick_train.py

echo ""
echo "🎯 Next Steps:"
echo "=============="
echo "1. Review the Arduino parameters printed above"
echo "2. Update src/test_with_ml.cpp with new parameters if needed"
echo "3. Connect your Arduino Micro via USB"
echo "4. Upload code with: platformio run --target upload"
echo "5. Monitor results in Serial Monitor (9600 baud)"
echo ""
echo "📚 Documentation:"
echo "   - README_ML_SETUP.md - Complete project guide"
echo "   - CALIBRATION_GUIDE.md - Sensor calibration instructions"
echo ""
