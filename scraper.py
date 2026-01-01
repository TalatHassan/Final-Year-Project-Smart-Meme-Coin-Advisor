"""
Coin Data Scraper - Fetch live data from multiple sources
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time

class CoinDataScraper:
    """
    Scrapes cryptocurrency data from multiple sources
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_all_data(self, contract_address):
        """
        Scrape data from all available sources
        """
        try:
            print(f"Scraping data for: {contract_address}")
            
            data = {
                'contract_address': contract_address,
                'timestamp': datetime.now().isoformat(),
                'sources': []
            }
            
            # 1. DexScreener
            print("  → Scraping DexScreener...")
            dexscreener_data = self.scrape_dexscreener(contract_address)
            if dexscreener_data:
                data['dexscreener'] = dexscreener_data
                data['sources'].append('dexscreener')
            
            # 2. CoinGecko (if available)
            print("  → Scraping CoinGecko...")
            coingecko_data = self.scrape_coingecko(contract_address)
            if coingecko_data:
                data['coingecko'] = coingecko_data
                data['sources'].append('coingecko')
            
            # 3. Birdeye
            print("  → Scraping Birdeye...")
            birdeye_data = self.scrape_birdeye(contract_address)
            if birdeye_data:
                data['birdeye'] = birdeye_data
                data['sources'].append('birdeye')
            
            # 4. Social data
            print("  → Fetching social data...")
            social_data = self.get_social_data(contract_address)
            if social_data:
                data['social'] = social_data
                data['sources'].append('social')
            
            if len(data['sources']) == 0:
                return {'error': 'No data found for this contract address'}
            
            return data
            
        except Exception as e:
            print(f"Error in scrape_all_data: {e}")
            return {'error': str(e)}
    
    def scrape_dexscreener(self, contract_address):
        """
        Scrape DexScreener for real-time trading data
        """
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('pairs') and len(data['pairs']) > 0:
                    pair = data['pairs'][0]
                    
                    return {
                        'name': pair.get('baseToken', {}).get('name', 'Unknown'),
                        'symbol': pair.get('baseToken', {}).get('symbol', 'Unknown'),
                        'price_usd': pair.get('priceUsd', 0),
                        'price_change_24h': pair.get('priceChange', {}).get('h24', 0),
                        'price_change_6h': pair.get('priceChange', {}).get('h6', 0),
                        'price_change_1h': pair.get('priceChange', {}).get('h1', 0),
                        'volume_24h': pair.get('volume', {}).get('h24', 0),
                        'volume_6h': pair.get('volume', {}).get('h6', 0),
                        'liquidity_usd': pair.get('liquidity', {}).get('usd', 0),
                        'liquidity_base': pair.get('liquidity', {}).get('base', 0),
                        'liquidity_quote': pair.get('liquidity', {}).get('quote', 0),
                        'fdv': pair.get('fdv', 0),
                        'market_cap': pair.get('marketCap', 0),
                        'pair_address': pair.get('pairAddress', ''),
                        'pair_created_at': pair.get('pairCreatedAt', 0),
                        'dex_id': pair.get('dexId', ''),
                        'chain': pair.get('chainId', ''),
                        'txns_24h_buys': pair.get('txns', {}).get('h24', {}).get('buys', 0),
                        'txns_24h_sells': pair.get('txns', {}).get('h24', {}).get('sells', 0),
                        'url': pair.get('url', '')
                    }
            
            return None
            
        except Exception as e:
            print(f"Error scraping DexScreener: {e}")
            return None
    
    def scrape_coingecko(self, contract_address):
        """
        Scrape CoinGecko for additional coin data
        """
        try:
            # Try to find coin on Solana network
            search_url = f"https://api.coingecko.com/api/v3/coins/solana/contract/{contract_address}"
            
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                market_data = data.get('market_data', {})
                
                return {
                    'name': data.get('name', 'Unknown'),
                    'symbol': data.get('symbol', 'Unknown'),
                    'price_usd': market_data.get('current_price', {}).get('usd', 0),
                    'market_cap': market_data.get('market_cap', {}).get('usd', 0),
                    'market_cap_rank': data.get('market_cap_rank', 0),
                    'volume_24h': market_data.get('total_volume', {}).get('usd', 0),
                    'high_24h': market_data.get('high_24h', {}).get('usd', 0),
                    'low_24h': market_data.get('low_24h', {}).get('usd', 0),
                    'price_change_24h': market_data.get('price_change_percentage_24h', 0),
                    'price_change_7d': market_data.get('price_change_percentage_7d', 0),
                    'price_change_30d': market_data.get('price_change_percentage_30d', 0),
                    'ath': market_data.get('ath', {}).get('usd', 0),
                    'atl': market_data.get('atl', {}).get('usd', 0),
                    'ath_change_pct': market_data.get('ath_change_percentage', {}).get('usd', 0),
                    'atl_change_pct': market_data.get('atl_change_percentage', {}).get('usd', 0),
                    'circulating_supply': market_data.get('circulating_supply', 0),
                    'total_supply': market_data.get('total_supply', 0),
                    'max_supply': market_data.get('max_supply', 0),
                    'fdv': market_data.get('fully_diluted_valuation', {}).get('usd', 0)
                }
            
            return None
            
        except Exception as e:
            print(f"Error scraping CoinGecko: {e}")
            return None
    
    def scrape_birdeye(self, contract_address):
        """
        Scrape Birdeye for Solana token data
        """
        try:
            url = f"https://public-api.birdeye.so/public/token_overview?address={contract_address}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and data.get('data'):
                    token_data = data['data']
                    
                    return {
                        'name': token_data.get('name', 'Unknown'),
                        'symbol': token_data.get('symbol', 'Unknown'),
                        'price': token_data.get('price', 0),
                        'price_change_24h': token_data.get('priceChange24h', 0),
                        'volume_24h': token_data.get('volume24h', 0),
                        'liquidity': token_data.get('liquidity', 0),
                        'market_cap': token_data.get('mc', 0),
                        'holder_count': token_data.get('holder', 0),
                        'decimals': token_data.get('decimals', 9)
                    }
            
            return None
            
        except Exception as e:
            print(f"Error scraping Birdeye: {e}")
            return None
    
    def get_social_data(self, contract_address):
        """
        Get social media data (placeholder - would need API keys)
        """
        try:
            # This is a placeholder - in production you would:
            # 1. Query Telegram API for subscriber count
            # 2. Query Reddit API for subreddit subscribers
            # 3. Query Twitter API for follower count
            # 4. Analyze sentiment from social media posts
            
            return {
                'telegram_members': 0,
                'reddit_subscribers': 0,
                'twitter_followers': 0,
                'sentiment_score': 0.5,  # Neutral
                'reddit_posts_24h': 0,
                'twitter_mentions_24h': 0
            }
            
        except Exception as e:
            print(f"Error getting social data: {e}")
            return None

# Test function
if __name__ == "__main__":
    scraper = CoinDataScraper()
    
    # Test with a known Solana token
    test_address = "So11111111111111111111111111111111111111112"  # Wrapped SOL
    
    print(f"\nTesting scraper with: {test_address}\n")
    data = scraper.scrape_all_data(test_address)
    
    print("\n" + "="*60)
    print("SCRAPING RESULTS:")
    print("="*60)
    print(json.dumps(data, indent=2))
