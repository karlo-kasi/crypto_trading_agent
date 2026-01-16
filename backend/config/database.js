import sql from 'mssql/msnodesqlv8.js';

const config = {
  database: process.env.DB_NAME || 'trading_db',
  connectionString: `Driver={ODBC Driver 17 for SQL Server};Server=(localdb)\\MSSQLLocalDB;Database=${process.env.DB_NAME || 'trading_db'};Trusted_Connection=yes;`,
};

let pool = null;

export async function connectDatabase() {
  try {
    if (!pool) {
      console.log('🔌 Connecting to LocalDB with Windows Authentication...');
      pool = await sql.connect(config);
      console.log('✅ Database connected successfully');
    }
    return pool;
  } catch (error) {
    console.error('❌ Database connection failed:', error.message);
    console.error('Full error:', error);
    throw error;
  }
}

export async function getConnection() {
  if (!pool) {
    await connectDatabase();
  }
  return pool;
}

export async function closeConnection() {
  try {
    if (pool) {
      await pool.close();
      pool = null;
      console.log('Database connection closed');
    }
  } catch (error) {
    console.error('Error closing database connection:', error);
  }
}

export default { connectDatabase, getConnection, closeConnection };