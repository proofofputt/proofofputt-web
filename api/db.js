
import pg from 'pg';

const { Pool } = pg;

let pool;

export function getDb() {
  if (!pool) {
    const connectionString = process.env.DATABASE_URL;
    pool = new Pool({
      connectionString,
    });
  }
  return pool;
}
