import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import eth_account
from eth_account.signers.local import LocalAccount
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants
from typing import Dict, Any, Optional

from config.settings import settings


class TradingExecutor:
    def __init__(self):
        self.testnet = settings.hyperliquid.testnet
        
        if self.testnet:
            self.base_url = constants.TESTNET_API_URL
        else:
            self.base_url = constants.MAINNET_API_URL
        
        self.account = None
        self.exchange = None
        self.info = Info(base_url=self.base_url, skip_ws=True)
        
        self._setup_account()
    
    def _setup_account(self):
        private_key = settings.hyperliquid.private_key
        
        if not private_key:
            print("[WARNING] No private key configured - read-only mode")
            return
        
        try:
            if not private_key.startswith("0x"):
                private_key = "0x" + private_key
            
            self.account = eth_account.Account.from_key(private_key)
            self.exchange = Exchange(
                self.account,
                base_url=self.base_url
            )
            print(f"[OK] Account configured: {self.account.address}")
        except Exception as e:
            print(f"[ERROR] Error setting up account: {e}")
    
    def get_balance(self):
        if not settings.hyperliquid.account_address:
            return {"error": "No account address configured"}
        
        try:
            user_state = self.info.user_state(settings.hyperliquid.account_address)
            
            return {
                "balance": float(user_state.get("marginSummary", {}).get("accountValue", 0)),
                "available": float(user_state.get("withdrawable", 0)),
                "positions": user_state.get("assetPositions", [])
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_positions(self):
        if not settings.hyperliquid.account_address:
            return []
        
        try:
            user_state = self.info.user_state(settings.hyperliquid.account_address)
            positions = []
            
            for pos in user_state.get("assetPositions", []):
                position = pos.get("position", {})
                size = float(position.get("szi", 0))
                
                if size != 0:
                    positions.append({
                        "coin": position.get("coin"),
                        "size": size,
                        "entry_price": float(position.get("entryPx", 0)),
                        "unrealized_pnl": float(position.get("unrealizedPnl", 0)),
                        "leverage": float(position.get("leverage", {}).get("value", 1)),
                        "side": "LONG" if size > 0 else "SHORT"
                    })
            
            return positions
        except Exception as e:
            print(f"Error getting positions: {e}")
            return []
    
    def get_price(self, coin):
        all_mids = self.info.all_mids()
        return float(all_mids.get(coin, 0))
    
    def set_leverage(self, coin, leverage, is_cross=False):
        if not self.exchange:
            print("[ERROR] Exchange not configured")
            return False
        
        try:
            self.exchange.update_leverage(
                leverage=leverage,
                name=coin,
                is_cross=is_cross
            )
            print(f"[OK] Leverage set to {leverage}x for {coin}")
            return True
        except Exception as e:
            print(f"[ERROR] Error setting leverage: {e}")
            return False
    
    def open_position(self, coin, is_buy, size, leverage=3, slippage=0.01):
        if not self.exchange:
            return {"error": "Exchange not configured"}
        
        try:
            self.set_leverage(coin, leverage)
            
            result = self.exchange.market_open(
                name=coin,
                is_buy=is_buy,
                sz=size,
                px=None,
                slippage=slippage
            )
            
            status = result.get("response", {}).get("data", {}).get("statuses", [{}])[0]
            
            if "filled" in status:
                fill = status["filled"]
                return {
                    "success": True,
                    "side": "LONG" if is_buy else "SHORT",
                    "coin": coin,
                    "size": size,
                    "price": float(fill.get("avgPx", 0)),
                    "order_id": fill.get("oid"),
                    "leverage": leverage
                }
            else:
                return {
                    "success": False,
                    "error": status.get("error", "Unknown error"),
                    "raw": result
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def close_position(self, coin, slippage=0.03):
        if not self.exchange:
            return {"error": "Exchange not configured"}
        
        try:
            positions = self.get_positions()
            position = None
            for pos in positions:
                if pos["coin"] == coin:
                    position = pos
                    break
            
            if not position:
                return {"error": f"No open position for {coin}"}
            
            size = abs(position["size"])
            is_buy = position["side"] == "SHORT"
            
            result = self.exchange.market_open(
                name=coin,
                is_buy=is_buy,
                sz=size,
                px=None,
                slippage=slippage
            )
            
            return {"success": True, "coin": coin, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def place_stop_loss(self, coin, is_buy, size, trigger_price):
        if not self.exchange:
            return {"success": False, "error": "Exchange not configured"}
        
        try:
            price = float(trigger_price)
            
            result = self.exchange.order(
                name=coin,
                is_buy=is_buy,
                sz=size,
                limit_px=price,
                order_type={
                    "trigger": {
                        "triggerPx": price,
                        "isMarket": True,
                        "tpsl": "sl"
                    }
                },
                reduce_only=True
            )
            
            print(f"[OK] Stop Loss placed at {price:,.2f} USD")
            return {"success": True, "price": price, "result": result}
        except Exception as e:
            print(f"[ERROR] Error placing SL: {e}")
            return {"success": False, "error": str(e)}
    
    def place_take_profit(self, coin, is_buy, size, trigger_price):
        if not self.exchange:
            return {"success": False, "error": "Exchange not configured"}
        
        try:
            price = float(trigger_price)
            
            result = self.exchange.order(
                name=coin,
                is_buy=is_buy,
                sz=size,
                limit_px=price,
                order_type={
                    "trigger": {
                        "triggerPx": price,
                        "isMarket": True,
                        "tpsl": "tp"
                    }
                },
                reduce_only=True
            )
            
            print(f"[OK] Take Profit placed at {price:,.2f} USD")
            return {"success": True, "price": price, "result": result}
        except Exception as e:
            print(f"[ERROR] Error placing TP: {e}")
            return {"success": False, "error": str(e)}
    
    def execute_decision(self, decision):
        action = decision.get("decision", "HOLD")
        
        if action == "HOLD":
            return {"action": "HOLD", "message": "No trade executed"}
        
        coin = decision.get("coin")
        if not coin:
            return {"error": "No coin specified"}
        
        balance = self.get_balance()
        if "error" in balance:
            return balance
        
        size_pct = min(float(decision.get("size_pct", 3)), settings.trading.max_position_size_pct)
        size_usd = (balance["available"] * size_pct) / 100
        
        price = self.get_price(coin)
        if price == 0:
            return {"error": f"Could not get price for {coin}"}
        
        leverage = int(decision.get("leverage", settings.trading.default_leverage))
        size_coins = (size_usd * leverage) / price
        
        if coin == "BTC":
            size_coins = round(size_coins, 5)
        else:
            size_coins = round(size_coins, 4)
        
        result = {
            "action": action,
            "coin": coin,
            "size_pct": size_pct,
            "size_usd": size_usd
        }
        
        # OPEN LONG
        if action == "OPEN_LONG":
            trade_result = self.open_position(
                coin=coin,
                is_buy=True,
                size=size_coins,
                leverage=leverage
            )
            result["trade"] = trade_result
            
            if trade_result.get("success"):
                entry_price = float(trade_result["price"])
                sl_pct = float(decision.get("stop_loss_pct", 3)) / 100
                tp_pct = float(decision.get("take_profit_pct", 6)) / 100
                
                sl_price = round(entry_price * (1 - sl_pct), 1)
                tp_price = round(entry_price * (1 + tp_pct), 1)
                
                sl_result = self.place_stop_loss(coin, False, size_coins, sl_price)
                result["stop_loss"] = sl_result
                
                tp_result = self.place_take_profit(coin, False, size_coins, tp_price)
                result["take_profit"] = tp_result
        
        # OPEN SHORT
        elif action == "OPEN_SHORT":
            trade_result = self.open_position(
                coin=coin,
                is_buy=False,
                size=size_coins,
                leverage=leverage
            )
            result["trade"] = trade_result
            
            if trade_result.get("success"):
                entry_price = float(trade_result["price"])
                sl_pct = float(decision.get("stop_loss_pct", 3)) / 100
                tp_pct = float(decision.get("take_profit_pct", 6)) / 100
                
                sl_price = round(entry_price * (1 + sl_pct), 1)
                tp_price = round(entry_price * (1 - tp_pct), 1)
                
                sl_result = self.place_stop_loss(coin, True, size_coins, sl_price)
                result["stop_loss"] = sl_result
                
                tp_result = self.place_take_profit(coin, True, size_coins, tp_price)
                result["take_profit"] = tp_result
        
        # CLOSE
        elif action == "CLOSE":
            result["trade"] = self.close_position(coin)
        
        return result


if __name__ == "__main__":
    print("=== Trading Executor Test ===\n")
    
    executor = TradingExecutor()
    
    print("--- Balance ---")
    balance = executor.get_balance()
    print(f"Balance: ${balance.get('balance', 0):,.2f}")
    
    print("\n--- Positions ---")
    positions = executor.get_positions()
    if positions:
        for pos in positions:
            print(f"  {pos['coin']}: {pos['side']} {pos['size']} @ ${pos['entry_price']:,.2f}")
    else:
        print("  No open positions")
    
    print(f"\n--- Settings ---")
    print(f"Max Position Size: {settings.trading.max_position_size_pct}%")