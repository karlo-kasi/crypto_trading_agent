import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from execution.executor import TradingExecutor

executor = TradingExecutor()

print("=== CLOSE ALL TRADES ===\n")

# Posizioni attuali
print("--- Current Positions ---")
positions = executor.get_positions()

if not positions:
    print("  No open positions")
else:
    for pos in positions:
        print(f"  {pos['coin']}: {pos['side']} {pos['size']} @ ${pos['entry_price']:,.2f}")
        print(f"    Unrealized PnL: ${pos['unrealized_pnl']:.2f}")

    # Chiudi tutte le posizioni
    print("\n--- Closing All Positions ---")
    for pos in positions:
        coin = pos['coin']
        print(f"Closing {coin}...")
        result = executor.close_position(coin)
        if result.get("success"):
            print(f"  [OK] {coin} closed")
        else:
            print(f"  [ERROR] {coin}: {result.get('error')}")

# Verifica
print("\n--- Positions After Close ---")
positions = executor.get_positions()
if positions:
    for pos in positions:
        print(f"  {pos['coin']}: {pos['side']} {pos['size']}")
else:
    print("  No open positions")

# Balance finale
balance = executor.get_balance()
print(f"\nFinal Balance: ${balance['balance']:,.2f}")