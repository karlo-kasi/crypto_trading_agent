from sqlalchemy import (
    Column, Integer, Float, String, DateTime, Text,
    ForeignKey, Boolean, Index, Enum as SQLEnum
)

from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class TradeDirection(enum.Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    
class TradeResult(enum.Enum): 
    WIN = "WIN"
    LOSS = "LOSS"
    BREAKEVEN = "BREAKEVEN"
    OPEN = "OPEN"

class ExitReason(enum.Enum):
    TAKE_PROFIT = "TP"
    STOP_LOSS = "SL"
    MANUAL = "MANUAL"
    SIGNAL = "SIGNAL"
    LIQUIDATION = "LIQUIDATION"       
    

class Trade(Base):
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    timestamp_open = Column(DateTime, nullable=False, index=True)
    timestamp_close = Column(DateTime, nullable=True)

    coin = Column(String(10), nullable=False, index=True)
    direction = Column(SQLEnum(TradeDirection), nullable=False)

    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    sl_price = Column(Float, nullable=True)
    tp_price = Column(Float, nullable=True)

    size = Column(Float, nullable=False)
    size_usd = Column(Float, nullable=True)
    leverage = Column(Integer, default=1)

    pnl_usd = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)
    fees_paid = Column(Float, default=0)
    result = Column(SQLEnum(TradeResult), default=TradeResult.OPEN)
    exit_reason = Column(SQLEnum(ExitReason), nullable=True)

    decision = relationship("Decision", back_populates="trade", uselist=False)

    def __repr__(self):
        return f"<Trade {self.id}: {self.coin} {self.direction.value}>"


class Decision(Base):
    __tablename__ = 'decisions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(Integer, ForeignKey('trades.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    context_json = Column(Text, nullable=False)
    analysis_json = Column(Text, nullable=True)
    confluence_score = Column(Float, nullable=True)
    risk_assessment = Column(String(10), nullable=True)
    reason = Column(Text, nullable=True)

    operation = Column(String(10), nullable=True)
    was_executed = Column(Boolean, default=False)

    trade = relationship("Trade", back_populates="decision")

    def __repr__(self):
        return f"<Decision {self.id}: {self.operation}>"


class Candle(Base):
    __tablename__ = 'candles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    coin = Column(String(10), nullable=False, index=True)
    timeframe = Column(String(5), nullable=False)

    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    __table_args__ = (
        Index('ix_candles_coin_tf_ts', 'coin', 'timeframe', 'timestamp'),
    )


class MarketSnapshot(Base):
    __tablename__ = 'market_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    snapshot_json = Column(Text, nullable=False)
    btc_price = Column(Float, nullable=True)
    fear_greed = Column(Integer, nullable=True)


class DailyStats(Base):
    __tablename__ = 'daily_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, unique=True, index=True)
    total_trades = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    pnl_usd = Column(Float, default=0)
    win_rate = Column(Float, nullable=True)
    max_drawdown = Column(Float, default=0)    