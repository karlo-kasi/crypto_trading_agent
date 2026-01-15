import time
from datetime import datetime

from agent.trading_agent import TradingAgent
from execution.executor import TradingExecutor
from services.context_builder import ContextBuilder
from database.trade_logger import TradeLogger
from agent.config.settings import settings


class TradingBot:
    def __init__(self):
        print("🤖 Initializing Trading Bot...")
        self.agent = TradingAgent()
        self.executor = TradingExecutor()
        self.context_builder = ContextBuilder()
        self.logger = TradeLogger()
        self.running = False
    
    def show_status(self):
        """Mostra stato attuale"""
        print("\n" + "=" * 50)
        print("📊 PORTFOLIO STATUS")
        print("=" * 50)
        
        balance = self.executor.get_balance()
        print(f"Balance: ${balance.get('balance', 0):,.2f}")
        print(f"Available: ${balance.get('available', 0):,.2f}")
        
        positions = self.executor.get_positions()
        if positions:
            print("\n📈 Open Positions:")
            for pos in positions:
                pnl = pos['unrealized_pnl']
                emoji = "🟢" if pnl >= 0 else "🔴"
                print(f"  {pos['coin']}: {pos['side']} {pos['size']} @ ${pos['entry_price']:,.2f}")
                print(f"    {emoji} PnL: ${pnl:.2f}")
        else:
            print("\n📭 No open positions")
        
        # Mostra stats dal DB
        stats = self.logger.get_stats()
        if stats.get("total_trades", 0) > 0:
            print(f"\n📈 Trading Stats:")
            print(f"  Total Trades: {stats['total_trades']}")
            print(f"  Win Rate: {stats['win_rate']}%")
            print(f"  Total PnL: ${stats['total_pnl_usd']:.2f}")
    
    def run_once(self, auto_execute: bool = False):
        """Esegue un ciclo di analisi e trading"""
        print("\n" + "=" * 50)
        print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        self.show_status()
        
        # Analisi LLM
        print("\n🧠 LLM analyzing market...")
        
        # Costruisci context
        context = self.context_builder.build_context(["BTC", "ETH"])
        decision = self.agent.get_trading_decision(["BTC", "ETH"])
        
        print("\n" + "-" * 30)
        print("💡 LLM DECISION:")
        print("-" * 30)
        print(f"Action: {decision.get('decision')}")
        print(f"Coin: {decision.get('coin')}")
        print(f"Confidence: {decision.get('confidence', 0) * 100:.0f}%")
        
        if decision.get('decision') != "HOLD":
            print(f"Size: {decision.get('size_pct')}%")
            print(f"Leverage: {decision.get('leverage')}x")
            print(f"Stop Loss: {decision.get('stop_loss_pct')}%")
            print(f"Take Profit: {decision.get('take_profit_pct')}%")
        
        print(f"\n📝 Reasoning: {decision.get('reasoning')}")
        
        # Salva decisione nel DB
        decision_id = self.logger.log_decision(context=context, decision=decision)
        print(f"\n💾 Decision saved to DB (ID: {decision_id})")
        
        # Esegui trade
        if decision.get('decision') == "HOLD":
            print("\n⏸️ No trade - HOLD")
            return
        
        if auto_execute:
            execute = True
        else:
            print("\n" + "=" * 50)
            response = input("Execute trade? (yes/no): ").strip().lower()
            execute = response == "yes"
        
        if execute:
            print("\n⚡ Executing trade...")
            result = self.executor.execute_decision(decision)
            
            if result.get("trade", {}).get("success"):
                trade = result["trade"]
                print("✅ Trade executed successfully!")
                print(f"  {trade['side']} {trade['coin']}")
                print(f"  Size: {trade['size']}")
                print(f"  Price: ${trade['price']:,.2f}")
                
                # Calcola size_usd
                size_usd = trade['size'] * trade['price'] / trade['leverage']
                
                # Calcola SL/TP prices
                sl_pct = decision.get('stop_loss_pct', 3) / 100
                tp_pct = decision.get('take_profit_pct', 6) / 100
                
                if trade['side'] == "LONG":
                    sl_price = trade['price'] * (1 - sl_pct)
                    tp_price = trade['price'] * (1 + tp_pct)
                else:
                    sl_price = trade['price'] * (1 + sl_pct)
                    tp_price = trade['price'] * (1 - tp_pct)
                
                # Salva trade nel DB
                trade_id = self.logger.log_trade_open(
                    coin=trade['coin'],
                    direction=trade['side'],
                    entry_price=trade['price'],
                    size=trade['size'],
                    size_usd=size_usd,
                    leverage=trade['leverage'],
                    sl_price=sl_price,
                    tp_price=tp_price,
                    decision_id=decision_id
                )
                print(f"💾 Trade saved to DB (ID: {trade_id})")
                
            else:
                print(f"❌ Trade failed: {result}")
            
            self.show_status()
        else:
            print("\n❌ Trade cancelled")
    
    def run_loop(self, interval_minutes: int = 60):
        """Esegue il bot in loop"""
        print("\n" + "=" * 50)
        print(f"🔄 STARTING AUTO-TRADING LOOP")
        print(f"   Interval: {interval_minutes} minutes")
        print("   Press Ctrl+C to stop")
        print("=" * 50)
        
        self.running = True
        
        while self.running:
            try:
                self.run_once(auto_execute=False)
                
                print(f"\n⏳ Next analysis in {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\n\n🛑 Stopping bot...")
                self.running = False
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Retrying in 60 seconds...")
                time.sleep(60)
        
        self.logger.close()
        print("👋 Bot stopped")


def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║           🤖 CRYPTO TRADING BOT v1.0                      ║
    ║           AI-Powered Trading on Hyperliquid               ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    print("Choose mode:")
    print("  1. Run once (single analysis)")
    print("  2. Run loop (continuous trading)")
    print("  3. Show status only")
    print("  4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    bot = TradingBot()
    
    if choice == "1":
        bot.run_once(auto_execute=False)
    elif choice == "2":
        interval = input("Interval in minutes (default 60): ").strip()
        interval = int(interval) if interval else 60
        bot.run_loop(interval_minutes=interval)
    elif choice == "3":
        bot.show_status()
    elif choice == "4":
        print("👋 Bye!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()