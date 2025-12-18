import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from execution.executor import TradingExecutor

executor = TradingExecutor()

print("=== CLOSE TRADE ===\n")

# Posizioni attuali
print("--- Current Positions ---")
positions = executor.get_positions()
for pos in positions:
    print(f"  {pos['coin']}: {pos['side']} {pos['size']} @ ${pos['entry_price']:,.2f}")
    print(f"  Unrealized PnL: ${pos['unrealized_pnl']:.2f}")

# Chiudi posizione BTC
print("\n--- Closing BTC position ---")
result = executor.close_position("BTC")
print(f"Result: {result}")

# Verifica
print("\n--- Positions after close ---")
positions = executor.get_positions()
if positions:
    for pos in positions:
        print(f"  {pos['coin']}: {pos['side']} {pos['size']}")
else:
    print("  No open positions ✅")

# Balance finale
balance = executor.get_balance()
print(f"\nFinal Balance: ${balance['balance']:,.2f}")