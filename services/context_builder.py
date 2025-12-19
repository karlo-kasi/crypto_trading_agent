import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime, timezone
from typing import Dict, Any, List
import json

from services.technical_analysis import TechnicalAnalysisService
from services.sentiment_service import SentimentService
from services.news_service import NewsService
from config.settings import settings


class ContextBuilder:
    def __init__(self):
        self.ta_service = TechnicalAnalysisService()
        self.sentiment_service = SentimentService()
        self.news_service = NewsService()
    
    def build_context(self, coins: List[str] = None) -> Dict[str, Any]:
        """Costruisce il context completo per l'LLM"""
        if coins is None:
            coins = settings.trading.trading_coins
        
        sentiment = self.sentiment_service.get_sentiment_summary()
        news = self.news_service.get_news_summary(coins)

        
        context = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "portfolio": self._get_portfolio(),
            "market": {},
            "sentiment": sentiment,
            "news": news,
            "risk_params": {
                "max_position_size_pct": settings.trading.max_position_size_pct,
                "max_total_exposure_pct": settings.trading.max_total_exposure_pct,
                "max_daily_loss_pct": settings.trading.max_daily_loss_pct,
                "default_leverage": settings.trading.default_leverage,
            }
        }
        
        for coin in coins:
            ta_data = self.ta_service.get_indicators(coin, "1h", 100)
            
            if "error" not in ta_data:
                context["market"][coin] = {
                    "price": ta_data["price"],
                    "trend": ta_data["trend"],
                    "indicators": ta_data["indicators"]
                }
        
        return context
    
    def _get_portfolio(self) -> Dict[str, Any]:
        """Portfolio attuale"""
        return {
            "balance_usd": 10000,
            "available_usd": 10000,
            "positions": [],
            "total_exposure_pct": 0
        }
    
    def build_prompt_context(self, coins: List[str] = None) -> str:
        """Converte il context in formato leggibile per l'LLM"""
        context = self.build_context(coins)
        sentiment = context['sentiment']
        news = context['news']
        
        prompt = f"""
=== MARKET CONTEXT ===
Timestamp: {context['timestamp']}

=== PORTFOLIO ===
Balance: ${context['portfolio']['balance_usd']:,.2f}
Available: ${context['portfolio']['available_usd']:,.2f}
Open Positions: {len(context['portfolio']['positions'])}
Total Exposure: {context['portfolio']['total_exposure_pct']}%

=== SENTIMENT ===
Fear & Greed Index: {sentiment['fear_greed']['value']} ({sentiment['fear_greed']['classification']})
Signal: {sentiment['overall_signal']}
Bias: {sentiment['overall_bias']}
Score: {sentiment['sentiment_score']}

=== NEWS ===
News Sentiment: {news.get('sentiment_summary', 'N/A')} (Bullish: {news.get('bullish_count', 0)}, Bearish: {news.get('bearish_count', 0)})
Recent Headlines:
"""
        for headline in news.get('headlines', [])[:5]:
            prompt += f"- {headline}\n"
        
        prompt += """
=== MARKET DATA ===
"""
        
        for coin, data in context['market'].items():
            prompt += f"""
--- {coin} ---
Price: ${data['price']:,.2f}
Overall Trend: {data['trend']}

Indicators:
- RSI(14): {data['indicators']['rsi']['value']} ({data['indicators']['rsi']['signal']})
- MACD: {data['indicators']['macd']['trend']} (MACD: {data['indicators']['macd']['macd']}, Signal: {data['indicators']['macd']['signal']})
- EMA: {data['indicators']['ema']['trend']} (EMA20: {data['indicators']['ema']['ema_20']:,.0f}, EMA50: {data['indicators']['ema']['ema_50']:,.0f})
- Bollinger Position: {data['indicators']['bollinger']['position']} (Upper: {data['indicators']['bollinger']['upper']:,.0f}, Lower: {data['indicators']['bollinger']['lower']:,.0f})
- ATR: {data['indicators']['atr']['percent']}% ({data['indicators']['atr']['volatility']} volatility)
"""
            if 'pivots' in data['indicators']:
                prompt += f"- Pivot Position: {data['indicators']['pivots']['position']} (P: {data['indicators']['pivots']['pivot']:,.0f}, R1: {data['indicators']['pivots']['r1']:,.0f}, S1: {data['indicators']['pivots']['s1']:,.0f})\n"
        
        prompt += f"""
=== RISK PARAMETERS ===
Max Position Size: {context['risk_params']['max_position_size_pct']}%
Max Total Exposure: {context['risk_params']['max_total_exposure_pct']}%
Max Daily Loss: {context['risk_params']['max_daily_loss_pct']}%
Default Leverage: {context['risk_params']['default_leverage']}x
"""
        
        return prompt


# Test
if __name__ == "__main__":
    builder = ContextBuilder()
    
    print("=== Context Builder Test ===\n")
    
    context = builder.build_context(["BTC", "ETH"])
    print("JSON Context Keys:", list(context.keys()))
    
    print("\n" + "="*50)
    print("PROMPT FOR LLM:")
    print("="*50)
    
    prompt = builder.build_prompt_context(["BTC", "ETH"])
    print(prompt)