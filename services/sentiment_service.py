import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from typing import Dict, Any


class SentimentService:
    """
    Servizio per il sentiment macro del mercato crypto.
    Attualmente usa il Fear & Greed Index.
    """

    def __init__(self):
        self.fear_greed_url = "https://api.alternative.me/fng/"

    def get_fear_greed_index(self) -> Dict[str, Any]:
        """
        Recupera Fear & Greed Index e lo normalizza
        per uso in trading / AI agent.
        """
        try:
            response = requests.get(self.fear_greed_url, timeout=10)
            response.raise_for_status()

            fg = response.json()["data"][0]
            value = int(fg["value"])

            return {
                "value": value,
                "classification": fg["value_classification"],
                "signal": self._fg_signal(value),
                "score": self._fg_score(value),
                "bias": self._trading_bias(value),
                "timestamp": int(fg["timestamp"]),
            }

        except Exception as e:
            # Fallback sicuro: il bot non deve mai crashare
            return {
                "value": None,
                "classification": "UNKNOWN",
                "signal": "NEUTRAL",
                "score": 0.0,
                "bias": "NONE",
                "error": str(e),
            }

    def _fg_signal(self, value: int) -> str:
        """
        Converte il valore numerico (0–100)
        in un segnale semantico.
        """
        if value <= 25:
            return "EXTREME_FEAR"
        elif value <= 45:
            return "FEAR"
        elif value <= 55:
            return "NEUTRAL"
        elif value <= 75:
            return "GREED"
        else:
            return "EXTREME_GREED"

    def _fg_score(self, value: int) -> float:
        """
        Normalizza il Fear & Greed Index in un range [-1, +1]

        -1  = paura estrema
         0  = neutro
        +1  = greed estremo
        """
        return round((value - 50) / 50, 2)

    def _trading_bias(self, value: int) -> str:
        """
        Bias direzionale suggerito dal sentiment.
        NON è un segnale di trading diretto.
        """
        if value <= 25:
            return "LONG"
        elif value >= 75:
            return "SHORT"
        else:
            return "NONE"

    def get_sentiment_summary(self) -> Dict[str, Any]:
        """
        Riassunto compatto del sentiment,
        utile per decision engine / LLM.
        """
        fg = self.get_fear_greed_index()

        return {
            "fear_greed": fg,
            "overall_signal": fg["signal"],
            "overall_bias": fg["bias"],
            "sentiment_score": fg["score"],
        }


# ==========================
# TEST MANUALE
# ==========================
if __name__ == "__main__":
    service = SentimentService()

    print("=== Sentiment Service Test ===\n")

    fg = service.get_fear_greed_index()

    print(f"Fear & Greed Value : {fg['value']}")
    print(f"Classification    : {fg['classification']}")
    print(f"Signal            : {fg['signal']}")
    print(f"Score             : {fg['score']}")
    print(f"Trading Bias      : {fg['bias']}")
