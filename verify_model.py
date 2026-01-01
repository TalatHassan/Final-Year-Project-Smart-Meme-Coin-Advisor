"""
Verify and test the trained Smart Meme Coin model
"""

import pickle
import json
import pandas as pd
import numpy as np

print("="*80)
print("SMART MEME COIN - MODEL VERIFICATION")
print("="*80)

# Load the model package
print("\n📦 Loading model package...")
try:
    with open('smart_meme_coin_model.pkl', 'rb') as f:
        model_package = pickle.load(f)
    print("✓ Model package loaded successfully!")
except Exception as e:
    print(f"✗ Error loading model: {e}")
    exit(1)

# Extract components
model = model_package['model']
label_encoder = model_package['label_encoder']
feature_columns = model_package['feature_columns']
training_info = model_package['training_info']

# Display model information
print("\n📊 MODEL INFORMATION")
print("="*80)
print(f"Training Date: {training_info['training_date']}")
print(f"Number of Features: {training_info['num_features']}")
print(f"Number of Classes: {training_info['num_classes']}")
print(f"Class Names: {', '.join(training_info['class_names'])}")
print(f"\n🎯 PERFORMANCE METRICS")
print(f"Training Accuracy: {training_info['train_accuracy']*100:.2f}%")
print(f"Test Accuracy: {training_info['test_accuracy']*100:.2f}%")
print(f"Training F1 Score: {training_info['train_f1']:.4f}")
print(f"Test F1 Score: {training_info['test_f1']:.4f}")
print(f"Cross-validation Accuracy: {training_info['cv_mean_accuracy']*100:.2f}% (+/- {training_info['cv_std_accuracy']*100:.2f}%)")

# Save additional metadata files
print("\n💾 Creating additional output files...")

# Save metadata as JSON
metadata = {
    'model_info': {
        'type': 'XGBoost Classifier',
        'task': 'Multi-class Classification',
        'classes': training_info['class_names'],
        'num_features': training_info['num_features'],
        'training_date': training_info['training_date']
    },
    'performance': {
        'train_accuracy': training_info['train_accuracy'],
        'test_accuracy': training_info['test_accuracy'],
        'train_f1_score': training_info['train_f1'],
        'test_f1_score': training_info['test_f1'],
        'cv_mean_accuracy': training_info['cv_mean_accuracy'],
        'cv_std_accuracy': training_info['cv_std_accuracy']
    },
    'data_info': {
        'train_samples': training_info['train_samples'],
        'test_samples': training_info['test_samples']
    },
    'model_parameters': {k: str(v) for k, v in training_info['model_params'].items()}
}

with open('model_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
print("✓ model_metadata.json created")

# Save label encoder separately
with open('label_encoder.pkl', 'wb') as f:
    pickle.dump(label_encoder, f)
print("✓ label_encoder.pkl created")

# Save feature columns
with open('feature_columns.json', 'w') as f:
    json.dump(feature_columns, f, indent=2)
print("✓ feature_columns.json created")

# Save XGBoost booster
try:
    model.get_booster().save_model('smart_meme_coin_xgboost.ubj')
    print("✓ smart_meme_coin_xgboost.ubj created")
except Exception as e:
    print(f"⚠ Could not save XGBoost booster: {e}")

# Test predictions on sample data
print("\n🧪 Testing model predictions...")
print("\nLoading test data...")
df_test = pd.read_csv('model_ready_coingecko.csv')
print(f"✓ Loaded {len(df_test)} test samples")

# Prepare test features
exclude_cols = ['label', 'contract_address', 'timestamp']
X_test_sample = df_test[feature_columns].head(10)
X_test_sample = X_test_sample.fillna(X_test_sample.median())
X_test_sample = X_test_sample.replace([np.inf, -np.inf], np.nan)
X_test_sample = X_test_sample.fillna(X_test_sample.median())

# Make predictions
predictions = model.predict(X_test_sample)
predicted_labels = label_encoder.inverse_transform(predictions)
actual_labels = df_test['label'].head(10).values

print("\n📋 Sample Predictions:")
print("-" * 50)
for i in range(len(predicted_labels)):
    match = "✓" if predicted_labels[i] == actual_labels[i] else "✗"
    print(f"{match} Actual: {actual_labels[i]:<6} | Predicted: {predicted_labels[i]}")

print("\n" + "="*80)
print("✅ MODEL VERIFICATION COMPLETED!")
print("="*80)

print("""
📂 All Output Files:
   1. smart_meme_coin_model.pkl - Complete model package (11+ MB)
   2. model_metadata.json - Model information and metrics
   3. label_encoder.pkl - Label encoder for predictions
   4. feature_columns.json - List of required features
   5. smart_meme_coin_xgboost.ubj - XGBoost booster file

💡 Usage Example:
   
   import pickle
   import pandas as pd
   
   # Load model
   with open('smart_meme_coin_model.pkl', 'rb') as f:
       model_pkg = pickle.load(f)
   
   model = model_pkg['model']
   label_encoder = model_pkg['label_encoder']
   
   # Prepare your data with the required features
   predictions = model.predict(X_new)
   labels = label_encoder.inverse_transform(predictions)
   
   print("Predictions:", labels)
""")
