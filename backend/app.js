import Express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

dotenv.config();

const app = Express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(Express.json());

app.get('/', (req, res) => {
  res.send('Crypto Trading Agent Backend is running');
});

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
