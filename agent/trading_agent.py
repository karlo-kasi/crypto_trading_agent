import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
from anthropic import Anthropic
from typing import Dict, Any, Optional

from config.settings import settings
from services.context_builder import ContextBuilder


class TradingAgent:
    def __init__(self):
        self.client = Anthropic(api_key=settings.llm.anthropic_api_key)
        self.context_builder = ContextBuilder()
        self.model = "claude-sonnet-4-20250514"
    
    def get_trading_decision(self, coins: list = None) -> Dict[str, Any]:
        """Chiede all'LLM una decisione di trading"""
        
        # Costruisci context
        context_prompt = self.context_builder.build_prompt_context(coins)
        
        # System prompt
        system_prompt = """You are an expert cryptocurrency trading agent. Your job is to analyze market data and make trading decisions.

RULES:
1. Be conservative - only trade when there's high confluence
2. Always respect risk parameters
3. Never exceed max position size or exposure limits
4. Consider sentiment + technical indicators together
5. Explain your reasoning clearly

OUTPUT FORMAT (respond ONLY with this JSON):
{
    "decision": "OPEN_LONG" | "OPEN_SHORT" | "CLOSE" | "HOLD",
    "coin": "BTC" | "ETH" | null,
    "confidence": 0.0-1.0,
    "size_pct": 0-20,
    "leverage": 1-10,
    "stop_loss_pct": 1-5,
    "take_profit_pct": 2-10,
    "reasoning": "Brief explanation of why"
}

If no good opportunity exists, return decision: "HOLD" with reasoning."""

        # User prompt
        user_prompt = f"""{context_prompt}

Based on the above market context, what is your trading decision?
Respond ONLY with the JSON format specified."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                system=system_prompt
            )
            
            # Parse response
            response_text = response.content[0].text
            
            # Estrai JSON dalla risposta
            decision = self._parse_decision(response_text)
            decision["raw_response"] = response_text
            
            return decision
            
        except Exception as e:
            return {
                "decision": "HOLD",
                "error": str(e),
                "reasoning": f"Error getting decision: {e}"
            }
    
    def _parse_decision(self, response_text: str) -> Dict[str, Any]:
        """Parsa la risposta JSON dell'LLM"""
        try:
            # Cerca JSON nella risposta
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response_text[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "decision": "HOLD",
            "reasoning": "Could not parse LLM response",
            "raw": response_text
        }


# Test
if __name__ == "__main__":
    print("=== Trading Agent Test ===\n")
    
    # Verifica API key
    if not settings.llm.anthropic_api_key:
        print("❌ ANTHROPIC_API_KEY not set in .env!")
        print("Add your API key to .env file:")
        print("ANTHROPIC_API_KEY=sk-ant-...")
        exit()
    
    agent = TradingAgent()
    
    print("Analyzing market and getting decision...")
    print("(This may take a few seconds)\n")
    
    decision = agent.get_trading_decision(["BTC", "ETH"])
    
    print("="*50)
    print("LLM TRADING DECISION:")
    print("="*50)
    print(f"Decision: {decision.get('decision')}")
    print(f"Coin: {decision.get('coin')}")
    print(f"Confidence: {decision.get('confidence')}")
    print(f"Size: {decision.get('size_pct')}%")
    print(f"Leverage: {decision.get('leverage')}x")
    print(f"Stop Loss: {decision.get('stop_loss_pct')}%")
    print(f"Take Profit: {decision.get('take_profit_pct')}%")
    print(f"\nReasoning: {decision.get('reasoning')}")