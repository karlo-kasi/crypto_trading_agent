import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from hyperliquid.info import Info
from hyperliquid.utils import constants 
from config.settings import settings 
import time


class HyperliquidClient:
    def __init__(self, use_mainnet_for_data: bool = True):
        if use_mainnet_for_data:
            base_url = constants.MAINNET_API_URL
        else:
            base_url = constants.TESTNET_API_URL if settings.hyperliquid.testnet else constants.MAINNET_API_URL
        
        self.info = Info(base_url=base_url, skip_ws=True)
        
    def get_price(self, coin: str) -> float: 
        """Prezzo corrente di una coin"""
        all_mids = self.info.all_mids()
        return float(all_mids.get(coin, 0)) 
    
    def get_all_prices(self) -> dict:
        """Tutti i prezzi"""
        return {k: float(v) for k, v in self.info.all_mids().items()}  
    
    def get_candles(self, coin: str, interval: str = "1h", limit: int = 100) -> list:
        """
        Candele OHLCV
        interval: 1m, 5m, 15m, 1h, 4h, 1d
        """
        try:
            interval_ms = {
                "1m": 60 * 1000,
                "5m": 5 * 60 * 1000,
                "15m": 15 * 60 * 1000,
                "1h": 60 * 60 * 1000,
                "4h": 4 * 60 * 60 * 1000,
                "1d": 24 * 60 * 60 * 1000,
            }
            
            now = int(time.time() * 1000)
            start_time = now - (limit * interval_ms.get(interval, 60 * 60 * 1000))
            
            # Parametro corretto: name invece di coin
            candles = self.info.candles_snapshot(
                name=coin, 
                interval=interval, 
                startTime=start_time, 
                endTime=now
            )
            return candles
        except Exception as e:
            print(f"Error getting candles: {e}")
            return []
    
    def get_orderbook(self, coin: str) -> dict:
        """Order book L2"""
        return self.info.l2_snapshot(coin=coin)
    
    def get_funding_rate(self, coin: str) -> float:
        """Funding rate corrente"""
        meta = self.info.meta_and_asset_ctxs()
        for asset in meta[1]:
            if asset.get('name') == coin:
                return float(asset.get('funding', 0))
        return 0.0
    
    
# Test
if __name__ == "__main__":
    client = HyperliquidClient(use_mainnet_for_data=True)
    
    print("=== Hyperliquid Client Test ===\n")
    
    btc_price = client.get_price("BTC")
    print(f"BTC Price: ${btc_price:,.2f}")
    
    eth_price = client.get_price("ETH")
    print(f"ETH Price: ${eth_price:,.2f}")
    
    print("\n--- Last 5 BTC 1h candles ---")
    candles = client.get_candles("BTC", "1h", 5)
    
    if candles:
        for c in candles[-5:]:
            ts = time.strftime('%Y-%m-%d %H:%M', time.localtime(c['t'] / 1000))
            print(f"  {ts} | O: {float(c['o']):,.0f} | H: {float(c['h']):,.0f} | L: {float(c['l']):,.0f} | C: {float(c['c']):,.0f}")
    else:
        print("No candles returned")
    
    print("\n--- BTC Funding Rate ---")
    funding = client.get_funding_rate("BTC")
    print(f"Funding: {funding:.6f}")