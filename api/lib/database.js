/**
 * api/lib/database.js
 *
 * Serverless-safe database connection manager.
 *
 * Key principle: In Vercel Serverless Functions a new Node.js process can be
 * spun up for every request. Naively opening a new connection per invocation
 * exhausts the database's max-connection limit under load.
 *
 * Solution: cache the connection pool on the module-level variable so that
 * subsequent invocations inside the *same warm lambda* reuse it.  For true
 * serverless connection pooling (across cold starts) consider PgBouncer or
 * Supabase's built-in pooler.
 */

import { Pool } from 'pg';

// Module-level singleton — survives across warm invocations of the same lambda.
let pool = null;

/**
 * getPool — returns (and lazily creates) the shared connection pool.
 *
 * @returns {Pool}
 */
export function getPool() {
  if (!pool) {
    pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      // Keep idle connections alive without hogging slots.
      max: 3,               // conservative for serverless: 1–5 recommended
      idleTimeoutMillis: 10_000,
      connectionTimeoutMillis: 5_000,
      ssl:
        process.env.NODE_ENV === 'production'
          ? { rejectUnauthorized: false }
          : false,
    });

    pool.on('error', (err) => {
      console.error('Unexpected pool error', err);
      // Reset so next call re-initialises a healthy pool.
      pool = null;
    });
  }

  return pool;
}

/**
 * withDb — runs `callback(client)` inside a checked-out client, automatically
 * releasing it afterward (even on error).
 *
 * Usage:
 *   const user = await withDb(async (db) => {
 *     const { rows } = await db.query('SELECT * FROM users WHERE id = $1', [id]);
 *     return rows[0];
 *   });
 *
 * @template T
 * @param {(client: import('pg').PoolClient) => Promise<T>} callback
 * @returns {Promise<T>}
 */
export async function withDb(callback) {
  const client = await getPool().connect();
  try {
    return await callback(client);
  } finally {
    client.release();
  }
}

/**
 * withTransaction — wraps `callback` in a BEGIN / COMMIT / ROLLBACK block.
 *
 * Usage:
 *   await withTransaction(async (db) => {
 *     await db.query('INSERT INTO orders ...', [...]);
 *     await db.query('UPDATE inventory ...', [...]);
 *   });
 *
 * @template T
 * @param {(client: import('pg').PoolClient) => Promise<T>} callback
 * @returns {Promise<T>}
 */
export async function withTransaction(callback) {
  return withDb(async (client) => {
    await client.query('BEGIN');
    try {
      const result = await callback(client);
      await client.query('COMMIT');
      return result;
    } catch (err) {
      await client.query('ROLLBACK');
      throw err;
    }
  });
}

/**
 * query — convenience wrapper for one-off queries that don't need manual
 * client lifecycle management.
 *
 * @param {string} text
 * @param {any[]} [params]
 */
export async function query(text, params) {
  return getPool().query(text, params);
}
