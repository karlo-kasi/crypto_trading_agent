# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered cryptocurrency trading system with three main components:
- **Python Agent** (`agent_ai/`): LLM-based trading decisions using Claude API, executes on Hyperliquid exchange
- **Node.js Backend** (`backend/`): REST API for frontend dashboard
- **Shared Database**: SQL Server for trades, decisions, and statistics

## Commands

### Python Agent
```bash
cd agent_ai
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py  # Interactive CLI: run once, run loop, show status
```

### Node.js Backend
```bash
cd backend
npm install
npm run dev     # Watch mode (development)
npm start       # Production
```

### Test Individual Services
```bash
python agent/trading_agent.py
python services/technical_analysis.py
python services/news_service.py
python execution/close_trade.py  # Close all open positions
```

## Architecture

### Data Flow
```
ContextBuilder → TradingAgent (Claude LLM) → TradingExecutor → Hyperliquid
     ↓                    ↓                        ↓
 Market Data         Decision JSON            Order Execution
     ↓                    ↓                        ↓
 Technical +          TradeLogger ←──────────────────┘
 Sentiment                ↓
                    SQL Server DB
                         ↑
                   Node.js API (read-only)
```

### Key Services (Python)

| Service | Location | Purpose |
|---------|----------|---------|
| `TradingAgent` | `agent/trading_agent.py` | Claude API integration, returns JSON decisions |
| `TechnicalAnalysisService` | `services/technical_analysis.py` | RSI, MACD, EMA, Bollinger, ATR, Pivots |
| `HyperliquidClient` | `services/hyperliquid_client.py` | Exchange API wrapper |
| `NewsService` | `services/news_service.py` | CryptoPanic news + sentiment |
| `SentimentService` | `services/sentiment_service.py` | Fear & Greed Index |
| `ContextBuilder` | `services/context_builder.py` | Orchestrates all data sources |
| `TradingExecutor` | `execution/executor.py` | Position sizing, order execution |
| `TradeLogger` | `database/trade_logger.py` | SQLAlchemy ORM for persistence |

### API Endpoints (Node.js)

| Endpoint | Description |
|----------|-------------|
| `GET /api/balance/initial` | Starting balance |
| `GET /api/balance/current` | Current balance + stats |
| `GET /api/trades/recent` | Last 10 trades |
| `GET /api/trades` | All trades with cumulative balance |
| `GET /api/stats/daily` | Daily performance |

## Database Schema

Main tables in SQL Server:
- `trades`: Position history (coin, direction, entry/exit, PnL, result)
- `decisions`: LLM decisions with context_json and analysis_json
- `candles`: Historical OHLCV data
- `daily_stats`: Aggregated daily performance

## Environment Variables

```bash
# Database (SQL Server / LocalDB)
DB_SERVER=(localdb)\MSSQLLocalDB
DB_NAME=trading_db

# Hyperliquid Exchange
HL_TESTNET=true
HL_ACCOUNT_ADDRESS=0x...
HL_PRIVATE_KEY=0x...

# AI
ANTHROPIC_API_KEY=sk-ant-...

# News
CRYPTOPANIC_API_KEY=...

# Trading Limits
MAX_POSITION_SIZE_PCT=20
DEFAULT_LEVERAGE=3
TRADING_COINS=BTC,ETH,SOL
```

## Key Patterns

**Position Sizing**: `size_coins = (balance * size_pct * leverage) / price`

**LLM Response Format**: Agent returns JSON with `{decision, coin, confidence, size_pct, leverage, sl_pct, tp_pct, reasoning}`

**Risk Management**: SL/TP orders placed immediately after position open. All decisions logged before execution.

**Service Separation**: Python writes to DB, Node.js only reads. Single source of truth in SQL Server.
