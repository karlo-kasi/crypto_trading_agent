import { getConnection } from '../config/database.js';

export const tradingController = {
  // GET /api/balance/initial - Saldo iniziale
  async getInitialBalance(req, res) {
    try {
      const pool = await getConnection();

      // Prende il primo trade per calcolare il saldo iniziale
      // oppure puoi avere una tabella separata per il saldo iniziale
      const result = await pool.request().query(`
        SELECT TOP 1
          COALESCE(
            (SELECT SUM(size_usd) FROM trades WHERE result = 'OPEN') +
            (SELECT COALESCE(SUM(pnl_usd), 0) FROM trades WHERE result != 'OPEN'),
            0
          ) as initial_balance
        FROM trades
      `);

      // Se non ci sono trades, ritorna un valore di default
      // Puoi modificare questo per leggere da una config o tabella dedicata
      const initialBalance = result.recordset[0]?.initial_balance || 1000;

      res.json({
        success: true,
        data: {
          initial_balance: initialBalance,
        },
      });
    } catch (error) {
      console.error('Error getting initial balance:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to get initial balance',
      });
    }
  },

  // GET /api/balance/current - Saldo corrente
  async getCurrentBalance(req, res) {
    try {
      const pool = await getConnection();

      const result = await pool.request().query(`
        SELECT
          COALESCE(SUM(pnl_usd), 0) as total_pnl,
          COUNT(*) as total_trades,
          SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
          SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses
        FROM trades
        WHERE result != 'OPEN'
      `);

      const stats = result.recordset[0];
      // Saldo iniziale hardcoded - modifica se hai una tabella dedicata
      const initialBalance = 1000;
      const currentBalance = initialBalance + (stats.total_pnl || 0);

      res.json({
        success: true,
        data: {
          current_balance: currentBalance,
          total_pnl: stats.total_pnl || 0,
          total_trades: stats.total_trades || 0,
          wins: stats.wins || 0,
          losses: stats.losses || 0,
          win_rate: stats.total_trades > 0
            ? ((stats.wins / stats.total_trades) * 100).toFixed(1)
            : 0,
        },
      });
    } catch (error) {
      console.error('Error getting current balance:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to get current balance',
      });
    }
  },

  // GET /api/trades/recent - Ultime 10 operazioni
  async getRecentTrades(req, res) {
    try {
      const pool = await getConnection();

      const result = await pool.request().query(`
        SELECT TOP 10
          id,
          created_at,
          timestamp_open,
          timestamp_close,
          coin,
          direction,
          entry_price,
          exit_price,
          sl_price,
          tp_price,
          size,
          size_usd,
          leverage,
          pnl_usd,
          pnl_pct,
          fees_paid,
          result,
          exit_reason
        FROM trades
        ORDER BY created_at DESC
      `);

      res.json({
        success: true,
        data: result.recordset,
      });
    } catch (error) {
      console.error('Error getting recent trades:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to get recent trades',
      });
    }
  },

  // GET /api/trades - Tutte le operazioni (per il grafico)
  async getAllTrades(req, res) {
    try {
      const pool = await getConnection();

      const result = await pool.request().query(`
        SELECT
          id,
          created_at,
          timestamp_open,
          timestamp_close,
          coin,
          direction,
          entry_price,
          exit_price,
          size_usd,
          leverage,
          pnl_usd,
          pnl_pct,
          result,
          exit_reason
        FROM trades
        ORDER BY created_at ASC
      `);

      // Calcola il balance cumulativo per il grafico
      const initialBalance = 1000;
      let cumulativeBalance = initialBalance;

      const tradesWithBalance = result.recordset.map((trade) => {
        if (trade.pnl_usd && trade.result !== 'OPEN') {
          cumulativeBalance += trade.pnl_usd;
        }
        return {
          ...trade,
          cumulative_balance: cumulativeBalance,
        };
      });

      res.json({
        success: true,
        data: tradesWithBalance,
        summary: {
          initial_balance: initialBalance,
          final_balance: cumulativeBalance,
          total_trades: result.recordset.length,
        },
      });
    } catch (error) {
      console.error('Error getting all trades:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to get all trades',
      });
    }
  },

  // GET /api/stats/daily - Statistiche giornaliere (per grafici)
  async getDailyStats(req, res) {
    try {
      const pool = await getConnection();

      const result = await pool.request().query(`
        SELECT
          id,
          date,
          total_trades,
          wins,
          losses,
          pnl_usd,
          win_rate,
          max_drawdown
        FROM daily_stats
        ORDER BY date ASC
      `);

      res.json({
        success: true,
        data: result.recordset,
      });
    } catch (error) {
      console.error('Error getting daily stats:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to get daily stats',
      });
    }
  },
};

export default tradingController;
