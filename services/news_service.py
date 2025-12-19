import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from datetime import datetime, timezone
from typing import Dict, Any, List
from config.settings import settings


class NewsService:
    """Servizio per recuperare news crypto da CryptoPanic."""
    
    def __init__(self):
        self.api_key = settings.cryptopanic_api_key
        self.base_url = "https://cryptopanic.com/api/developer/v2"
    
    def get_news(
        self,
        currencies: List[str] = None,
        filter_type: str = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recupera le ultime news crypto.
        
        Args:
            currencies: Lista di coin (es. ["BTC", "ETH"])
            filter_type: "rising", "hot", "bullish", "bearish", "important"
            limit: Numero massimo di news
        """
        
        if not self.api_key:
            print("[WARNING] No CryptoPanic API key configured")
            return []
        
        try:
            url = f"{self.base_url}/posts/"
            params = {"auth_token": self.api_key}
            
            if currencies:
                params["currencies"] = ",".join(currencies)
            
            if filter_type:
                params["filter"] = filter_type
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            news_list = []
            
            for item in data.get("results", [])[:limit]:
                votes = item.get("votes", {})
                
                news_list.append({
                    "title": item.get("title", ""),
                    "source": item.get("source", {}).get("title", "Unknown"),
                    "url": item.get("url", ""),
                    "published_at": item.get("published_at", ""),
                    "sentiment": self._get_sentiment(votes),
                    "currencies": [c.get("code") for c in item.get("currencies", [])],
                    "votes_positive": votes.get("positive", 0),
                    "votes_negative": votes.get("negative", 0)
                })
            
            return news_list
            
        except Exception as e:
            print(f"[ERROR] Error fetching news: {e}")
            return []
    
    def _get_sentiment(self, votes: Dict) -> str:
        """Determina il sentiment della news"""
        positive = votes.get("positive", 0)
        negative = votes.get("negative", 0)
        
        if positive > negative + 2:
            return "BULLISH"
        elif negative > positive + 2:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def get_news_summary(self, currencies: List[str] = None) -> Dict[str, Any]:
        """Riassunto news per il trading bot."""
        news = self.get_news(currencies=currencies, limit=10)
        
        if not news:
            return {
                "total_news": 0,
                "sentiment_summary": "NEUTRAL",
                "headlines": []
            }
        
        bullish = sum(1 for n in news if n["sentiment"] == "BULLISH")
        bearish = sum(1 for n in news if n["sentiment"] == "BEARISH")
        
        if bullish > bearish + 2:
            overall = "BULLISH"
        elif bearish > bullish + 2:
            overall = "BEARISH"
        else:
            overall = "NEUTRAL"
        
        headlines = []
        for n in news[:5]:
            time_str = n["published_at"][:16].replace("T", " ") if n["published_at"] else ""
            headlines.append(f"{time_str} | {n['title']}")
        
        return {
            "total_news": len(news),
            "bullish_count": bullish,
            "bearish_count": bearish,
            "sentiment_summary": overall,
            "headlines": headlines
        }
    
    def format_for_prompt(self, currencies: List[str] = None) -> str:
        """Formatta le news per il prompt dell'LLM."""
        summary = self.get_news_summary(currencies)
        
        if summary["total_news"] == 0:
            return "<news>\nNo recent news available.\n</news>"
        
        output = "<news>\n"
        output += f"News Sentiment: {summary['sentiment_summary']} "
        output += f"(Bullish: {summary['bullish_count']}, Bearish: {summary['bearish_count']})\n\n"
        
        for headline in summary["headlines"]:
            output += f"{headline}\n"
        
        output += "</news>"
        
        return output


# Test
if __name__ == "__main__":
    print("=== News Service Test ===\n")
    
    service = NewsService()
    
    print("--- Fetching News ---")
    news = service.get_news(currencies=["BTC", "ETH"], limit=5)
    
    if news:
        for n in news:
            print(f"[{n['sentiment']}] {n['title'][:70]}...")
            print(f"   Source: {n['source']}")
            print()
    else:
        print("No news found")
    
    print("--- Summary ---")
    summary = service.get_news_summary(["BTC", "ETH"])
    print(f"Total: {summary['total_news']}")
    print(f"Sentiment: {summary['sentiment_summary']}")
    
    print("\n--- Formatted for LLM ---")
    print(service.format_for_prompt(["BTC", "ETH"]))