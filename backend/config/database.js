import sql from 'mssql';


const config = {
  server: process.env.DB_SERVER || '(localdb)\\MSSQLLocalDB',
  database: process.env.DB_NAME || 'trading_db',
  options: {
    encrypt: false,
    trustServerCertificate: true,
    enableArithAbort: true,
  },
  pool: {
    max: 10,
    min: 0,
    idleTimeoutMillis: 30000,
  },
};

let pool = null;

export async function getConnection() {
  if (!pool) {
    pool = await sql.connect(config);
    console.log('Database connected successfully');
  }
  return pool;
}

export async function closeConnection() {
  if (pool) {
    await pool.close();
    pool = null;
  }
}

export default { getConnection, closeConnection };
