#!/usr/bin/env python3
"""
Quick Start: Train ML Model and Extract Arduino Parameters
Run: python3 quick_train.py
"""

import sys
import os

# Check if required packages are installed
try:
    import pandas as pd
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
except ImportError:
    print("❌ Missing dependencies! Install them with:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

print("🚀 Starting ML Model Training...")
print("="*60)

# Load data
try:
    healthy_data = pd.read_csv('data/healthy_data.csv')
    creep_data = pd.read_csv('data/creep_data.csv')
    print(f"✅ Loaded {len(healthy_data)} healthy samples")
    print(f"✅ Loaded {len(creep_data)} creep samples")
except FileNotFoundError as e:
    print(f"❌ Error: {e}")
    print("   Make sure data/healthy_data.csv and data/creep_data.csv exist")
    sys.exit(1)

# Combine and prepare
data = pd.concat([healthy_data, creep_data], ignore_index=True)
X = data[['nozzle_temp', 'bed_temp', 'current', 'vib_per_min']]
y = (data['status'] == 'creep').astype(int)

# Train
print("\n🔄 Training Random Forest Classifier...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
model = RandomForestClassifier(n_estimators=10, max_depth=5, random_state=42)
model.fit(X_scaled, y)

# Evaluate
from sklearn.metrics import accuracy_score
y_pred = model.predict(X_scaled)
accuracy = accuracy_score(y, y_pred)
print(f"📊 Training Accuracy: {accuracy:.2%}")

# Arduino Parameters
print("\n" + "="*60)
print("📱 ARDUINO PARAMETERS (for normalization)")
print("="*60)
print("\n✏️  Update these in src/test_with_ml.cpp:")
print("\nconst float norm_mean[4] = {")
for i, val in enumerate(scaler.mean_):
    print(f"  {val:.2f},  // {X.columns[i]}")
print("};")

print("\nconst float norm_std[4] = {")
for i, val in enumerate(scaler.scale_):
    print(f"  {val:.4f},  // {X.columns[i]}")
print("};")

# Feature importance
print("\n" + "="*60)
print("🎯 FEATURE IMPORTANCE")
print("="*60)
for feature, importance in zip(X.columns, model.feature_importances_):
    print(f"  {feature:12s}: {importance*100:5.1f}%")

# Simple thresholds
print("\n" + "="*60)
print("📋 CURRENT THRESHOLD RULES")
print("="*60)
print(f"Healthy rule (all must be true):")
print(f"  • nozzle_temp < 225.0")
print(f"  • bed_temp < 70.0")
print(f"  • current < 1.8")
print(f"  • vib_per_min < 70")
print(f"\nCreep rule (any one can be true):")
print(f"  • nozzle_temp > 235.0")
print(f"  • bed_temp > 72.0")
print(f"  • current > 2.5")
print(f"  • vib_per_min > 90")

print("\n✅ Model training complete!")
print("\n📝 Next steps:")
print("   1. Update Arduino parameters in src/test_with_ml.cpp (copy from above)")
print("   2. Connect your Arduino Micro")
print("   3. Run: platformio run --target upload")
print("   4. Monitor with Serial Monitor at 9600 baud")
