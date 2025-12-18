import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import ta
from typing import Dict, Any
from services.hyperliquid_client import HyperliquidClient


class TechnicalAnalysisService:
    def __init__(self):
        self.client = HyperliquidClient(use_mainnet_for_data=True)
    
    def get_indicators(self, coin: str, interval: str = "1h", limit: int = 100) -> Dict[str, Any]:
        """Calcola tutti gli indicatori tecnici per una coin"""
        
        # Prendi candele
        candles = self.client.get_candles(coin, interval, limit)
        
        if not candles:
            return {"error": "No candles data"}
        
        # Converti in DataFrame
        df = pd.DataFrame(candles)
        df['o'] = df['o'].astype(float)
        df['h'] = df['h'].astype(float)
        df['l'] = df['l'].astype(float)
        df['c'] = df['c'].astype(float)
        df['v'] = df['v'].astype(float)
        
        # Calcola indicatori
        result = {
            "coin": coin,
            "interval": interval,
            "price": float(df['c'].iloc[-1]),
            "indicators": {}
        }
        
        # RSI (14)
        rsi = ta.momentum.RSIIndicator(df['c'], window=14)
        rsi_value = rsi.rsi().iloc[-1]
        result["indicators"]["rsi"] = {
            "value": round(rsi_value, 2),
            "signal": self._rsi_signal(rsi_value)
        }
        
        # MACD
        macd = ta.trend.MACD(df['c'])
        macd_line = macd.macd().iloc[-1]
        signal_line = macd.macd_signal().iloc[-1]
        result["indicators"]["macd"] = {
            "macd": round(macd_line, 2),
            "signal": round(signal_line, 2),
            "histogram": round(macd_line - signal_line, 2),
            "trend": "BULLISH" if macd_line > signal_line else "BEARISH"
        }
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df['c'], window=20, window_dev=2)
        bb_upper = bb.bollinger_hband().iloc[-1]
        bb_lower = bb.bollinger_lband().iloc[-1]
        bb_middle = bb.bollinger_mavg().iloc[-1]
        price = float(df['c'].iloc[-1])
        
        # Posizione nel canale (0 = lower, 1 = upper)
        bb_position = (price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5
        
        result["indicators"]["bollinger"] = {
            "upper": round(bb_upper, 2),
            "middle": round(bb_middle, 2),
            "lower": round(bb_lower, 2),
            "position": round(bb_position, 2)
        }
        
        # EMA
        ema_20 = ta.trend.EMAIndicator(df['c'], window=20).ema_indicator().iloc[-1]
        ema_50 = ta.trend.EMAIndicator(df['c'], window=50).ema_indicator().iloc[-1]
        result["indicators"]["ema"] = {
            "ema_20": round(ema_20, 2),
            "ema_50": round(ema_50, 2),
            "trend": "BULLISH" if price > ema_20 > ema_50 else "BEARISH" if price < ema_20 < ema_50 else "NEUTRAL"
        }
        
        # ATR (volatilità)
        atr = ta.volatility.AverageTrueRange(df['h'], df['l'], df['c'], window=14)
        atr_value = atr.average_true_range().iloc[-1]
        atr_pct = (atr_value / price) * 100
        result["indicators"]["atr"] = {
            "value": round(atr_value, 2),
            "percent": round(atr_pct, 2),
            "volatility": "HIGH" if atr_pct > 3 else "MEDIUM" if atr_pct > 1.5 else "LOW"
        }
        
        # Pivot Points (dal daily)
        daily_candles = self.client.get_candles(coin, "1d", 2)
        if daily_candles:
            yesterday = daily_candles[-2] if len(daily_candles) > 1 else daily_candles[-1]
            h = float(yesterday['h'])
            l = float(yesterday['l'])
            c = float(yesterday['c'])
            
            pivot = (h + l + c) / 3
            r1 = 2 * pivot - l
            s1 = 2 * pivot - h
            r2 = pivot + (h - l)
            s2 = pivot - (h - l)
            
            result["indicators"]["pivots"] = {
                "pivot": round(pivot, 2),
                "r1": round(r1, 2),
                "r2": round(r2, 2),
                "s1": round(s1, 2),
                "s2": round(s2, 2),
                "position": self._pivot_position(price, pivot, r1, s1)
            }
        
        # Trend complessivo
        result["trend"] = self._calculate_trend(result["indicators"])
        
        return result
    
    def _rsi_signal(self, rsi: float) -> str:
        if rsi >= 70:
            return "OVERBOUGHT"
        elif rsi <= 30:
            return "OVERSOLD"
        elif rsi >= 60:
            return "BULLISH"
        elif rsi <= 40:
            return "BEARISH"
        return "NEUTRAL"
    
    def _pivot_position(self, price: float, pivot: float, r1: float, s1: float) -> str:
        if price > r1:
            return "ABOVE_R1"
        elif price > pivot:
            return "BETWEEN_P_R1"
        elif price > s1:
            return "BETWEEN_S1_P"
        else:
            return "BELOW_S1"
    
    def _calculate_trend(self, indicators: dict) -> str:
        bullish = 0
        bearish = 0
        
        # RSI
        rsi_signal = indicators.get("rsi", {}).get("signal", "")
        if rsi_signal in ["BULLISH", "OVERSOLD"]:
            bullish += 1
        elif rsi_signal in ["BEARISH", "OVERBOUGHT"]:
            bearish += 1
        
        # MACD
        if indicators.get("macd", {}).get("trend") == "BULLISH":
            bullish += 1
        else:
            bearish += 1
        
        # EMA
        ema_trend = indicators.get("ema", {}).get("trend", "")
        if ema_trend == "BULLISH":
            bullish += 1
        elif ema_trend == "BEARISH":
            bearish += 1
        
        if bullish > bearish:
            return "BULLISH"
        elif bearish > bullish:
            return "BEARISH"
        return "NEUTRAL"


# Test
if __name__ == "__main__":
    ta_service = TechnicalAnalysisService()
    
    print("=== Technical Analysis Test ===\n")
    
    for coin in ["BTC", "ETH"]:
        print(f"--- {coin} ---")
        data = ta_service.get_indicators(coin, "1h", 100)
        
        print(f"Price: ${data['price']:,.2f}")
        print(f"Trend: {data['trend']}")
        print(f"RSI: {data['indicators']['rsi']['value']} ({data['indicators']['rsi']['signal']})")
        print(f"MACD: {data['indicators']['macd']['trend']}")
        print(f"EMA Trend: {data['indicators']['ema']['trend']}")
        print(f"Volatility: {data['indicators']['atr']['volatility']} ({data['indicators']['atr']['percent']}%)")
        if 'pivots' in data['indicators']:
            print(f"Pivot Position: {data['indicators']['pivots']['position']}")
        print()