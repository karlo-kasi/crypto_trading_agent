import Express, { Router } from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import tradingRoutes from './routes/tradingRoutes.js';
import { getConnection } from './config/database.js';

dotenv.config();

const app = Express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(Express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    message: 'Crypto Trading Agent Backend is running',
  });
});

// Routes
app.use('/api', tradingRoutes);

// Initialize database connection and start server
async function startServer() {
  try {
    await getConnection();
    app.listen(PORT, () => {
      console.log(`Server is running on http://localhost:${PORT}`);
    });
  } catch (error) {
    console.error('Failed to connect to database:', error);
    process.exit(1);
  }
}

startServer();
