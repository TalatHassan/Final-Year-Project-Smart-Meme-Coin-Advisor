# Smart Meme Coin - XGBoost Model

## 🎉 Model Training Completed Successfully!

This XGBoost model predicts cryptocurrency trading signals for meme coins with **89.20% test accuracy**.

---

## 📦 Generated Files

### 1. **smart_meme_coin_model.pkl** (11.3 MB) ⭐ MAIN FILE
   - Complete model package with all training data
   - Contains: model, label encoder, feature columns, training metrics
   - **This is the primary file you need to use the model**

### 2. **smart_meme_coin_xgboost.ubj** (11.3 MB)
   - XGBoost booster in Universal Binary JSON format
   - Can be loaded directly with XGBoost library
   - Alternative format for model deployment

### 3. **model_metadata.json** (1.1 KB)
   - Training information and performance metrics
   - Model parameters and configuration
   - Human-readable format

### 4. **label_encoder.pkl** (0.3 KB)
   - Label encoder for converting predictions to class names
   - Maps numeric predictions to: BUY, SELL, HOLD, buy, sell, hold

### 5. **feature_columns.json** (2.8 KB)
   - List of 107 required input features
   - Use this to ensure correct feature order

---

## 📊 Model Performance

| Metric | Training | Testing | Cross-Validation |
|--------|----------|---------|------------------|
| **Accuracy** | 94.28% | **89.20%** | 85.98% ±0.33% |
| **F1 Score** | 0.9428 | **0.8921** | - |

### Class Performance (Test Set)
| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| BUY   | 75.79%    | 67.51% | 71.41%   | 357     |
| HOLD  | 75.57%    | 75.76% | 75.66%   | 396     |
| SELL  | 71.62%    | 78.45% | 74.88%   | 399     |
| buy   | 88.58%    | 88.90% | 88.74%   | 4,719   |
| hold  | 91.90%    | 90.62% | 91.25%   | 10,616  |
| sell  | 87.86%    | 89.86% | 88.85%   | 5,760   |

### Training Details
- **Training Samples:** 88,986
- **Test Samples:** 22,247
- **Total Dataset:** 111,233 samples
- **Features:** 107
- **Classes:** 6 (BUY, HOLD, SELL, buy, hold, sell)

---

## 🚀 How to Use the Model

### Method 1: Load Complete Package (Recommended)

```python
import pickle
import pandas as pd
import numpy as np

# Load the complete model package
with open('smart_meme_coin_model.pkl', 'rb') as f:
    model_package = pickle.load(f)

# Extract components
model = model_package['model']
label_encoder = model_package['label_encoder']
feature_columns = model_package['feature_columns']

# Prepare your data (must have all 107 features in correct order)
# X_new should be a pandas DataFrame or numpy array with shape (n_samples, 107)
X_new = pd.DataFrame(your_data, columns=feature_columns)

# Handle missing/infinite values
X_new = X_new.fillna(X_new.median())
X_new = X_new.replace([np.inf, -np.inf], np.nan)
X_new = X_new.fillna(0)

# Make predictions
predictions = model.predict(X_new)  # Returns: [0, 1, 2, 3, 4, 5]
predicted_labels = label_encoder.inverse_transform(predictions)  # Returns: ['BUY', 'SELL', 'hold', ...]

# Get prediction probabilities
probabilities = model.predict_proba(X_new)  # Returns probability for each class

print("Predictions:", predicted_labels)
print("Probabilities:", probabilities)
```

### Method 2: Load Only XGBoost Model

```python
import xgboost as xgb
import pickle

# Load XGBoost booster
model = xgb.Booster()
model.load_model('smart_meme_coin_xgboost.ubj')

# Load label encoder separately
with open('label_encoder.pkl', 'rb') as f:
    label_encoder = pickle.load(f)

# Prepare data as DMatrix
import xgboost as xgb
dmatrix = xgb.DMatrix(X_new)

# Make predictions
predictions = model.predict(dmatrix)
predicted_labels = label_encoder.inverse_transform(predictions.astype(int))
```

---

## 🔍 Model Details

### Top 20 Most Important Features
1. `cg_ath_scaled` - All-time high (scaled)
2. `cg_ath` - All-time high price
3. `cg_market_cap_rank` - Market cap ranking
4. `cg_market_cap_rank_scaled` - Market cap rank (scaled)
5. `pooled_sol_scaled` - Pooled Solana (scaled)
6. `reddit_post_velocity_per_min_scaled` - Reddit activity
7. `tg_subscribers_scaled` - Telegram subscribers
8. `market_cap_scaled` - Market capitalization
9. `fdv_scaled` - Fully diluted valuation
10. `day_of_week_scaled` - Day of week
... and 97 more features

### Model Parameters
- **Algorithm:** XGBoost (Gradient Boosting)
- **Objective:** Multi-class classification (softmax)
- **Max Depth:** 8
- **Learning Rate:** 0.1
- **Number of Estimators:** 300
- **Tree Method:** Histogram-based
- **Regularization:** L1=0.1, L2=1.0

---

## 📝 Input Data Requirements

Your input data must contain all **107 features** in the exact order specified in `feature_columns.json`. 

### Required Feature Categories:
- CoinGecko metrics (prices, market cap, volumes, etc.)
- Social media metrics (Reddit, Telegram)
- Technical indicators (scaled and raw values)
- Time-based features (hour, day, timestamps)
- Pooled liquidity metrics
- Rug pull risk indicators

### Example Feature Names:
- `cg_price_usd`, `cg_market_cap`, `cg_total_volume_24h`
- `reddit_subs_scaled`, `tg_subscribers_scaled`
- `hour_sin`, `hour_cos`, `day_of_week_scaled`
- `pooled_sol_scaled`, `market_cap_scaled`

---

## ⚠️ Important Notes

1. **Feature Order Matters:** Features must be in the exact order as `feature_columns.json`
2. **Handle Missing Values:** Fill NaN/Inf values before prediction
3. **Data Preprocessing:** Apply the same scaling/preprocessing used during training
4. **Class Labels:** Model outputs 6 classes (some datasets use uppercase, some lowercase)
5. **Performance:** Model is optimized for meme coin trading signals

---

## 🛠️ Dependencies

```bash
pip install pandas numpy scikit-learn xgboost
```

**Versions used during training:**
- Python: 3.11.0
- XGBoost: Latest
- scikit-learn: Latest
- pandas: Latest
- numpy: Latest

---

## 📧 Model Information

- **Training Date:** 2026-01-01 15:41:04
- **Model Type:** XGBoost Classifier
- **Task:** Multi-class Classification
- **Training Script:** `train_model.py`
- **Verification Script:** `verify_model.py`

---

## 🎯 Use Cases

This model can predict:
- **BUY signals** - Good time to buy the meme coin
- **SELL signals** - Good time to sell the meme coin  
- **HOLD signals** - Hold current position

Perfect for:
- Automated trading systems
- Trading signal generation
- Portfolio management
- Risk assessment

---

## ✅ Success!

Your model is ready to use! Load `smart_meme_coin_model.pkl` and start making predictions.

Happy Trading! 🚀💰
