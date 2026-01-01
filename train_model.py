"""
Smart Meme Coin - XGBoost Model Training Script
This script trains a robust XGBoost model on cryptocurrency data
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
import xgboost as xgb
import pickle
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("SMART MEME COIN - XGBOOST MODEL TRAINING")
print("="*80)

# ========================
# 1. DATA LOADING
# ========================
print("\n[Step 1/7] Loading data files...")
try:
    # Load both CSV files
    df_coingecko = pd.read_csv('model_ready_coingecko.csv')
    print(f"✓ Loaded model_ready_coingecko.csv: {df_coingecko.shape[0]} rows, {df_coingecko.shape[1]} columns")
    
    df_fast = pd.read_csv('model_ready_fast.csv')
    print(f"✓ Loaded model_ready_fast.csv: {df_fast.shape[0]} rows, {df_fast.shape[1]} columns")
    
except Exception as e:
    print(f"✗ Error loading data: {e}")
    exit(1)

# ========================
# 2. DATA PREPROCESSING
# ========================
print("\n[Step 2/7] Preprocessing data...")

# Combine both datasets
df = pd.concat([df_coingecko, df_fast], axis=0, ignore_index=True)
print(f"✓ Combined dataset: {df.shape[0]} rows, {df.shape[1]} columns")

# Display label distribution
print("\n📊 Label Distribution:")
print(df['label'].value_counts())
print(f"\nLabel percentages:\n{df['label'].value_counts(normalize=True) * 100}")

# Separate features and target
# Exclude non-feature columns
exclude_cols = ['label', 'contract_address', 'timestamp']
feature_cols = [col for col in df.columns if col not in exclude_cols]

X = df[feature_cols].copy()
y = df['label'].copy()

print(f"\n✓ Features: {len(feature_cols)} columns")
print(f"✓ Target: {y.nunique()} classes ({y.unique()})")

# Encode target labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)
print(f"\n✓ Encoded labels: {dict(zip(label_encoder.classes_, range(len(label_encoder.classes_))))}")

# Handle missing values
if X.isnull().sum().sum() > 0:
    print(f"\n⚠ Found {X.isnull().sum().sum()} missing values, filling with median...")
    X = X.fillna(X.median())
    print("✓ Missing values handled")

# Handle infinite values
inf_mask = np.isinf(X.select_dtypes(include=[np.number])).any(axis=1)
if inf_mask.sum() > 0:
    print(f"⚠ Found {inf_mask.sum()} rows with infinite values, replacing...")
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median())
    print("✓ Infinite values handled")

# ========================
# 3. TRAIN-TEST SPLIT
# ========================
print("\n[Step 3/7] Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, 
    test_size=0.2, 
    random_state=42,
    stratify=y_encoded
)

print(f"✓ Training set: {X_train.shape[0]} samples")
print(f"✓ Test set: {X_test.shape[0]} samples")

# ========================
# 4. MODEL TRAINING
# ========================
print("\n[Step 4/7] Training XGBoost model...")

# Define XGBoost parameters
params = {
    'objective': 'multi:softmax',
    'num_class': len(label_encoder.classes_),
    'max_depth': 8,
    'learning_rate': 0.1,
    'n_estimators': 300,
    'min_child_weight': 1,
    'gamma': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'reg_alpha': 0.1,
    'reg_lambda': 1.0,
    'random_state': 42,
    'tree_method': 'hist',
    'eval_metric': 'mlogloss',
    'early_stopping_rounds': 50
}

print("\n📋 Model Parameters:")
for key, value in params.items():
    print(f"  {key}: {value}")

# Create and train model with validation
model = xgb.XGBClassifier(**params)

# Use evaluation set for early stopping
eval_set = [(X_train, y_train), (X_test, y_test)]

print("\n🚀 Training in progress...")
model.fit(
    X_train, y_train,
    eval_set=eval_set,
    verbose=50
)

print("\n✓ Model training completed!")

# ========================
# 5. MODEL EVALUATION
# ========================
print("\n[Step 5/7] Evaluating model performance...")

# Predictions
y_train_pred = model.predict(X_train)
y_test_pred = model.predict(X_test)

# Accuracy
train_accuracy = accuracy_score(y_train, y_train_pred)
test_accuracy = accuracy_score(y_test, y_test_pred)

print(f"\n📊 Model Performance:")
print(f"  Training Accuracy: {train_accuracy*100:.2f}%")
print(f"  Test Accuracy: {test_accuracy*100:.2f}%")

# F1 Score
train_f1 = f1_score(y_train, y_train_pred, average='weighted')
test_f1 = f1_score(y_test, y_test_pred, average='weighted')

print(f"  Training F1 Score: {train_f1:.4f}")
print(f"  Test F1 Score: {test_f1:.4f}")

# Classification Report
print("\n📝 Classification Report (Test Set):")
print(classification_report(
    y_test, y_test_pred, 
    target_names=label_encoder.classes_,
    digits=4
))

# Confusion Matrix
print("\n🎯 Confusion Matrix (Test Set):")
cm = confusion_matrix(y_test, y_test_pred)
print(cm)

# Feature Importance
print("\n⭐ Top 20 Important Features:")
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(feature_importance.head(20).to_string(index=False))

# ========================
# 6. CROSS-VALIDATION
# ========================
print("\n[Step 6/7] Performing cross-validation...")
# Create a new model without early stopping for CV
cv_model = xgb.XGBClassifier(
    objective='multi:softmax',
    num_class=len(label_encoder.classes_),
    max_depth=8,
    learning_rate=0.1,
    n_estimators=200,
    min_child_weight=1,
    gamma=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=1.0,
    random_state=42,
    tree_method='hist'
)
cv_scores = cross_val_score(cv_model, X_train, y_train, cv=5, scoring='accuracy')
print(f"✓ 5-Fold CV Accuracy: {cv_scores.mean()*100:.2f}% (+/- {cv_scores.std()*100:.2f}%)")

# ========================
# 7. MODEL SAVING
# ========================
print("\n[Step 7/7] Saving model and metadata...")

# Create model package with all information
model_package = {
    'model': model,
    'label_encoder': label_encoder,
    'feature_columns': feature_cols,
    'training_info': {
        'train_samples': X_train.shape[0],
        'test_samples': X_test.shape[0],
        'num_features': len(feature_cols),
        'num_classes': len(label_encoder.classes_),
        'class_names': label_encoder.classes_.tolist(),
        'class_mapping': dict(zip(label_encoder.classes_, range(len(label_encoder.classes_)))),
        'train_accuracy': float(train_accuracy),
        'test_accuracy': float(test_accuracy),
        'train_f1': float(train_f1),
        'test_f1': float(test_f1),
        'cv_mean_accuracy': float(cv_scores.mean()),
        'cv_std_accuracy': float(cv_scores.std()),
        'model_params': params,
        'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'best_iteration': model.best_iteration if hasattr(model, 'best_iteration') else None,
    },
    'feature_importance': feature_importance.to_dict('records'),
    'confusion_matrix': cm.tolist()
}

# Save as pickle file
pickle_filename = 'smart_meme_coin_model.pkl'
with open(pickle_filename, 'wb') as f:
    pickle.dump(model_package, f, protocol=pickle.HIGHEST_PROTOCOL)
print(f"✓ Model saved as: {pickle_filename}")

# Save model in XGBoost format using get_booster()
try:
    xgb_filename = 'smart_meme_coin_xgboost.ubj'
    model.get_booster().save_model(xgb_filename)
    print(f"✓ XGBoost booster saved as: {xgb_filename}")
except Exception as e:
    print(f"⚠ Could not save XGBoost format: {e}")

# Save metadata as JSON
metadata_filename = 'model_metadata.json'
metadata = {k: v for k, v in model_package['training_info'].items() if k != 'model_params'}
metadata['model_params'] = {k: str(v) for k, v in params.items()}
metadata['feature_importance_top20'] = feature_importance.head(20).to_dict('records')

with open(metadata_filename, 'w') as f:
    json.dump(metadata, f, indent=2)
print(f"✓ Metadata saved as: {metadata_filename}")

# Save label encoder
label_encoder_filename = 'label_encoder.pkl'
with open(label_encoder_filename, 'wb') as f:
    pickle.dump(label_encoder, f)
print(f"✓ Label encoder saved as: {label_encoder_filename}")

# ========================
# SUMMARY
# ========================
print("\n" + "="*80)
print("✅ MODEL TRAINING COMPLETED SUCCESSFULLY!")
print("="*80)

print(f"""
📦 Output Files Created:
   1. {pickle_filename} - Complete model package (recommended for loading)
   2. {xgb_filename} - XGBoost booster in UBJ format
   3. {metadata_filename} - Training metadata and metrics
   4. {label_encoder_filename} - Label encoder for predictions

📊 Final Model Stats:
   • Training Accuracy: {train_accuracy*100:.2f}%
   • Test Accuracy: {test_accuracy*100:.2f}%
   • Cross-validation Accuracy: {cv_scores.mean()*100:.2f}%
   • Number of Features: {len(feature_cols)}
   • Number of Classes: {len(label_encoder.classes_)}
   • Classes: {', '.join(label_encoder.classes_)}

💾 To load and use the model:
   
   import pickle
   
   # Load complete model package
   with open('{pickle_filename}', 'rb') as f:
       model_package = pickle.load(f)
   
   model = model_package['model']
   label_encoder = model_package['label_encoder']
   feature_columns = model_package['feature_columns']
   
   # Make predictions
   predictions = model.predict(X_new)
   predicted_labels = label_encoder.inverse_transform(predictions)
""")

print("="*80)
print("🎉 Happy Trading!")
print("="*80)
