"""
Smart Meme Coin Analyzer - Flask Backend
Complete API with model integration and live data scraping
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import json
import time
from scraper import CoinDataScraper

app = Flask(__name__)
CORS(app)

# Load trained model
print("Loading trained model...")
try:
    with open('smart_meme_coin_model.pkl', 'rb') as f:
        model_package = pickle.load(f)
    
    model = model_package['model']
    label_encoder = model_package['label_encoder']
    feature_columns = model_package['feature_columns']
    
    print("✓ Model loaded successfully!")
    print(f"✓ Classes: {label_encoder.classes_}")
    print(f"✓ Features: {len(feature_columns)}")
except Exception as e:
    print(f"✗ Error loading model: {e}")
    model = None

# Initialize scraper
scraper = CoinDataScraper()

@app.route('/')
def index():
    """Main coin analyzer page"""
    return render_template('index.html')

@app.route('/analyze')
def analyze():
    """Analysis results page"""
    return render_template('analyze.html')

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """
    API endpoint to analyze a coin by contract address
    Returns: coin data, prediction, and graph data
    """
    try:
        data = request.get_json()
        contract_address = data.get('contract_address', '').strip()
        
        if not contract_address:
            return jsonify({'error': 'Contract address is required'}), 400
        
        print(f"\n{'='*60}")
        print(f"Analyzing coin: {contract_address}")
        print(f"{'='*60}")
        
        # Step 1: Scrape live data from multiple sources
        print("\n[1/4] Scraping live data...")
        coin_data = scraper.scrape_all_data(contract_address)
        
        if coin_data.get('error'):
            return jsonify({
                'error': coin_data['error'],
                'message': 'Could not fetch coin data. Please check the contract address.'
            }), 404
        
        print(f"✓ Scraped data from {len(coin_data.get('sources', []))} sources")
        
        # Step 2: Get DexScreener graph data
        print("\n[2/4] Fetching live chart data...")
        graph_data = get_dexscreener_data(contract_address)
        
        # Step 3: Prepare features for model
        print("\n[3/4] Preparing features for model...")
        features_df = prepare_features(coin_data)
        
        # Step 4: Make prediction
        print("\n[4/4] Generating prediction...")
        prediction_result = make_prediction(features_df)
        
        # Prepare response
        response = {
            'success': True,
            'contract_address': contract_address,
            'coin_data': coin_data,
            'graph_data': graph_data,
            'prediction': prediction_result,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n✓ Analysis complete! Prediction: {prediction_result['signal']}")
        print(f"{'='*60}\n")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"\n✗ Error during analysis: {str(e)}")
        return jsonify({
            'error': 'Analysis failed',
            'message': str(e)
        }), 500

def get_dexscreener_data(contract_address):
    """
    Fetch live chart data from DexScreener API
    """
    try:
        # DexScreener API endpoint
        url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('pairs') and len(data['pairs']) > 0:
                pair = data['pairs'][0]  # Get first pair
                
                return {
                    'available': True,
                    'pair_address': pair.get('pairAddress'),
                    'dex': pair.get('dexId'),
                    'url': pair.get('url'),
                    'price_usd': pair.get('priceUsd'),
                    'price_change_24h': pair.get('priceChange', {}).get('h24'),
                    'volume_24h': pair.get('volume', {}).get('h24'),
                    'liquidity_usd': pair.get('liquidity', {}).get('usd'),
                    'chart_url': f"https://dexscreener.com/solana/{pair.get('pairAddress')}"
                }
        
        return {'available': False, 'message': 'No chart data available'}
        
    except Exception as e:
        print(f"Error fetching DexScreener data: {e}")
        return {'available': False, 'error': str(e)}

def prepare_features(coin_data):
    """
    Prepare features from scraped data for model prediction
    """
    try:
        # Create feature dictionary with all 107 features
        features = {}
        
        # Extract features from coin_data
        coingecko_data = coin_data.get('coingecko', {})
        dexscreener_data = coin_data.get('dexscreener', {})
        social_data = coin_data.get('social', {})
        
        # CoinGecko features
        features['cg_price_usd'] = float(coingecko_data.get('price_usd', 0))
        features['cg_market_cap'] = float(coingecko_data.get('market_cap', 0))
        features['cg_market_cap_rank'] = float(coingecko_data.get('market_cap_rank', 0))
        features['cg_fdv'] = float(coingecko_data.get('fdv', 0))
        features['cg_total_volume_24h'] = float(coingecko_data.get('volume_24h', 0))
        features['cg_high_24h'] = float(coingecko_data.get('high_24h', 0))
        features['cg_low_24h'] = float(coingecko_data.get('low_24h', 0))
        features['cg_price_change_pct_24h'] = float(coingecko_data.get('price_change_24h', 0))
        features['cg_ath'] = float(coingecko_data.get('ath', 0))
        features['cg_atl'] = float(coingecko_data.get('atl', 0))
        
        # DexScreener features
        features['pooled_sol_scaled'] = float(dexscreener_data.get('liquidity_usd', 0)) / 1000000
        features['market_cap_scaled'] = float(dexscreener_data.get('market_cap', 0)) / 1000000
        
        # Social features
        features['tg_subscribers_scaled'] = float(social_data.get('telegram_members', 0)) / 10000
        features['reddit_subs_scaled'] = float(social_data.get('reddit_subscribers', 0)) / 10000
        
        # Time-based features
        now = datetime.now()
        features['hour_of_day'] = now.hour
        features['day_of_week'] = now.weekday()
        features['hour_sin'] = np.sin(2 * np.pi * now.hour / 24)
        features['hour_cos'] = np.cos(2 * np.pi * now.hour / 24)
        features['dow_sin'] = np.sin(2 * np.pi * now.weekday() / 7)
        features['dow_cos'] = np.cos(2 * np.pi * now.weekday() / 7)
        
        # Fill remaining features with zeros or defaults
        for col in feature_columns:
            if col not in features:
                features[col] = 0.0
        
        # Create DataFrame with correct column order
        df = pd.DataFrame([features])[feature_columns]
        
        # Handle missing/infinite values
        df = df.fillna(0)
        df = df.replace([np.inf, -np.inf], 0)
        
        return df
        
    except Exception as e:
        print(f"Error preparing features: {e}")
        # Return zero-filled dataframe as fallback
        return pd.DataFrame(np.zeros((1, len(feature_columns))), columns=feature_columns)

def make_prediction(features_df):
    """
    Make BUY/SELL/HOLD prediction using trained model
    """
    try:
        if model is None:
            return {
                'signal': 'UNKNOWN',
                'confidence': 0.0,
                'probabilities': {},
                'error': 'Model not loaded'
            }
        
        # Make prediction
        prediction = model.predict(features_df)[0]
        probabilities = model.predict_proba(features_df)[0]
        
        # Get predicted label
        predicted_label = label_encoder.inverse_transform([prediction])[0]
        
        # Get confidence (probability of predicted class)
        confidence = float(probabilities[prediction]) * 100
        
        # Create probability dictionary
        prob_dict = {}
        for idx, class_name in enumerate(label_encoder.classes_):
            prob_dict[class_name] = float(probabilities[idx]) * 100
        
        # Normalize prediction to uppercase
        signal = predicted_label.upper()
        
        return {
            'signal': signal,
            'confidence': round(confidence, 2),
            'probabilities': prob_dict,
            'recommendation': get_recommendation(signal, confidence)
        }
        
    except Exception as e:
        print(f"Error making prediction: {e}")
        return {
            'signal': 'ERROR',
            'confidence': 0.0,
            'probabilities': {},
            'error': str(e)
        }

def get_recommendation(signal, confidence):
    """
    Generate human-readable recommendation
    """
    if confidence >= 80:
        strength = "Strong"
    elif confidence >= 60:
        strength = "Moderate"
    else:
        strength = "Weak"
    
    recommendations = {
        'BUY': f"{strength} buy signal. Consider entering a position.",
        'SELL': f"{strength} sell signal. Consider exiting or reducing position.",
        'HOLD': f"{strength} hold signal. Maintain current position."
    }
    
    return recommendations.get(signal, "Unable to generate recommendation.")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 SMART MEME COIN ANALYZER - BACKEND SERVER")
    print("="*60)
    print(f"✓ Model Status: {'Loaded' if model else 'Not Loaded'}")
    print(f"✓ Server starting on http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
