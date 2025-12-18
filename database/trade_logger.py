import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import Trade, Decision, TradeDirection, TradeResult, ExitReason


class TradeLogger:
    """Salva trades e decisioni nel database"""
    
    def __init__(self):
        self.db: Session = SessionLocal()
    
    def log_decision(
        self,
        context: Dict[str, Any],
        decision: Dict[str, Any],
        trade_id: Optional[int] = None
    ) -> int:
        """Salva una decisione dell'LLM"""
        db_decision = Decision(
            trade_id=trade_id,
            created_at=datetime.utcnow(),
            context_json=json.dumps(context),
            analysis_json=json.dumps(decision),
            confluence_score=decision.get("confidence"),
            reason=decision.get("reasoning"),
            operation=decision.get("decision"),
            was_executed=False
        )
        
        self.db.add(db_decision)
        self.db.commit()
        self.db.refresh(db_decision)
        
        return db_decision.id
    
    def log_trade_open(
        self,
        coin: str,
        direction: str,
        entry_price: float,
        size: float,
        size_usd: float,
        leverage: int,
        sl_price: Optional[float] = None,
        tp_price: Optional[float] = None,
        decision_id: Optional[int] = None
    ) -> int:
        """Salva un trade aperto"""
        trade_direction = TradeDirection.LONG if direction == "LONG" else TradeDirection.SHORT
        
        db_trade = Trade(
            created_at=datetime.utcnow(),
            timestamp_open=datetime.utcnow(),
            coin=coin,
            direction=trade_direction,
            entry_price=entry_price,
            size=size,
            size_usd=size_usd,
            leverage=leverage,
            sl_price=sl_price,
            tp_price=tp_price,
            result=TradeResult.OPEN
        )
        
        self.db.add(db_trade)
        self.db.commit()
        self.db.refresh(db_trade)
        
        # Collega decision al trade
        if decision_id:
            decision = self.db.query(Decision).filter(Decision.id == decision_id).first()
            if decision:
                decision.trade_id = db_trade.id
                decision.was_executed = True
                self.db.commit()
        
        return db_trade.id
    
    def log_trade_close(
        self,
        trade_id: int,
        exit_price: float,
        exit_reason: str = "MANUAL"
    ) -> bool:
        """Aggiorna un trade chiuso"""
        trade = self.db.query(Trade).filter(Trade.id == trade_id).first()
        
        if not trade:
            return False
        
        trade.timestamp_close = datetime.utcnow()
        trade.exit_price = exit_price
        
        # Calcola PnL
        if trade.direction == TradeDirection.LONG:
            pnl_pct = ((exit_price - trade.entry_price) / trade.entry_price) * 100 * trade.leverage
        else:
            pnl_pct = ((trade.entry_price - exit_price) / trade.entry_price) * 100 * trade.leverage
        
        pnl_usd = (pnl_pct / 100) * trade.size_usd
        
        trade.pnl_pct = round(pnl_pct, 2)
        trade.pnl_usd = round(pnl_usd, 2)
        
        # Risultato
        if pnl_usd > 0:
            trade.result = TradeResult.WIN
        elif pnl_usd < 0:
            trade.result = TradeResult.LOSS
        else:
            trade.result = TradeResult.BREAKEVEN
        
        # Exit reason
        reason_map = {
            "TP": ExitReason.TAKE_PROFIT,
            "SL": ExitReason.STOP_LOSS,
            "MANUAL": ExitReason.MANUAL,
            "SIGNAL": ExitReason.SIGNAL
        }
        trade.exit_reason = reason_map.get(exit_reason, ExitReason.MANUAL)
        
        self.db.commit()
        return True
    
    def get_open_trades(self) -> list:
        """Trade aperti"""
        trades = self.db.query(Trade).filter(Trade.result == TradeResult.OPEN).all()
        return [{"id": t.id, "coin": t.coin, "direction": t.direction.value, "entry_price": t.entry_price} for t in trades]
    
    def get_stats(self) -> Dict[str, Any]:
        """Statistiche trading"""
        trades = self.db.query(Trade).filter(Trade.result != TradeResult.OPEN).all()
        
        if not trades:
            return {"total_trades": 0}
        
        wins = [t for t in trades if t.result == TradeResult.WIN]
        total_pnl = sum(t.pnl_usd or 0 for t in trades)
        
        return {
            "total_trades": len(trades),
            "wins": len(wins),
            "losses": len(trades) - len(wins),
            "win_rate": round(len(wins) / len(trades) * 100, 1),
            "total_pnl_usd": round(total_pnl, 2)
        }
    
    def close(self):
        self.db.close()