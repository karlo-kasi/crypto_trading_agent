import { Router } from 'express';
import tradingController from '../controllers/tradingController.js';

const router = Router();

// Balance endpoints
router.get('/balance/initial', tradingController.getInitialBalance);
router.get('/balance/current', tradingController.getCurrentBalance);

// Trades endpoints
router.get('/trades/recent', tradingController.getRecentTrades);
router.get('/trades', tradingController.getAllTrades);

// Stats endpoints
router.get('/stats/daily', tradingController.getDailyStats);

export default router;
