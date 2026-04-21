import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import joblib

# Load data
healthy_data = pd.read_csv('data/healthy_data.csv')
creep_data = pd.read_csv('data/creep_data.csv')

# Combine datasets
data = pd.concat([healthy_data, creep_data], ignore_index=True)

# Prepare features and labels
X = data[['nozzle_temp', 'bed_temp', 'current', 'vib_per_min']]
y = data['status']

# Convert labels to binary (0 = healthy, 1 = creep)
y_binary = (y == 'creep').astype(int)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y_binary, test_size=0.2, random_state=42)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train Random Forest
model = RandomForestClassifier(n_estimators=10, max_depth=5, random_state=42)
model.fit(X_train_scaled, y_train)

# Evaluate
y_pred = model.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy:.2%}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Save scaler and model
joblib.dump(scaler, 'model/scaler.pkl')
joblib.dump(model, 'model/model.pkl')

# Print model coefficients for Arduino implementation
print("\n" + "="*50)
print("ARDUINO PARAMETERS")
print("="*50)

# Get feature importance
print("\nFeature Importance:")
for feature, importance in zip(X.columns, model.feature_importances_):
    print(f"  {feature}: {importance:.4f}")

# Get mean and std for normalization (from scaler)
print("\nScaler Mean (use for normalization in Arduino):")
for feature, mean in zip(X.columns, scaler.mean_):
    print(f"  {feature}: {mean:.2f}")

print("\nScaler Std (use for normalization in Arduino):")
for feature, std in zip(X.columns, scaler.scale_):
    print(f"  {feature}: {std:.4f}")

# Generate simple rule-based classifier for Arduino
print("\n" + "="*50)
print("SIMPLE RULE-BASED THRESHOLDS (Alternative to ML)")
print("="*50)
print("""
For Arduino without ML library, use these simple rules:
- Healthy: nozzle_temp < 225 AND bed_temp < 70 AND current < 1.8 AND vib_per_min < 70
- Creep: nozzle_temp > 235 OR bed_temp > 72 OR current > 2.5 OR vib_per_min > 90
- Unknown: Between these bounds
""")
