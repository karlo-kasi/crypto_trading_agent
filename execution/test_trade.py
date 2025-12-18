import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from execution.executor import TradingExecutor

executor = TradingExecutor()

print("=== TEST TRADE ===\n")

# Verifica balance
balance = executor.get_balance()
print(f"Balance: ${balance['balance']:,.2f}")
print(f"Available: ${balance['available']:,.2f}")

# Prezzo BTC
btc_price = executor.get_price("BTC")
print(f"BTC Price: ${btc_price:,.2f}")

# Apri una piccola posizione LONG
print("\n--- Opening LONG position on BTC ---")
result = executor.open_position(
    coin="BTC",
    is_buy=True,      # LONG
    size=0.001,       # 0.001 BTC (~$88)
    leverage=2,
    slippage=0.01
)

print(f"Result: {result}")

# Verifica posizioni
print("\n--- Positions after trade ---")
positions = executor.get_positions()
for pos in positions:
    print(f"  {pos['coin']}: {pos['side']} {pos['size']} @ ${pos['entry_price']:,.2f}")