/**
 * api/auth/register.js  →  POST /api/auth/register
 *
 * Demonstrates the recommended pattern for a public, write endpoint:
 *  1. Method guard
 *  2. Body validation
 *  3. Business logic (DB + hashing)
 *  4. Standardised response
 *
 * Notice how the handler itself has ZERO boilerplate — all cross-cutting
 * concerns (CORS, rate-limit, logging, error handling) live in withMiddleware.
 */

import bcrypt from 'bcryptjs';
import { withMiddleware, publicStack } from '../lib/withMiddleware.js';
import { withTransaction }             from '../lib/database.js';
import { validate, rules, parseBody }  from '../lib/validation.js';
import {
  sendCreated,
  sendBadRequest,
  sendConflict,
  sendMethodNotAllowed,
} from '../lib/response.js';

// ─── Validation schema ────────────────────────────────────────────────────────

const registerSchema = {
  email:    [rules.required, rules.email],
  password: [rules.required, rules.minLength(8), rules.maxLength(128)],
  name:     [rules.required, rules.minLength(2), rules.maxLength(100)],
};

// ─── Handler ──────────────────────────────────────────────────────────────────

async function handler(req, res) {
  if (req.method !== 'POST') {
    return sendMethodNotAllowed(res, ['POST']);
  }

  // 1. Parse + validate
  const body = parseBody(req);
  const { data, errors } = validate(body, registerSchema);
  if (errors) return sendBadRequest(res, 'Invalid registration data', errors);

  // 2. Business logic inside a transaction
  const user = await withTransaction(async (db) => {
    // Check for duplicate email
    const { rows: existing } = await db.query(
      'SELECT id FROM users WHERE email = $1 LIMIT 1',
      [data.email.toLowerCase()]
    );
    if (existing.length > 0) {
      // Throw a typed error so the catch block can differentiate
      const err = new Error('Email already registered');
      err.code = 'DUPLICATE_EMAIL';
      throw err;
    }

    // Hash password
    const passwordHash = await bcrypt.hash(data.password, 12);

    // Insert new user
    const { rows } = await db.query(
      `INSERT INTO users (email, password_hash, name, created_at)
       VALUES ($1, $2, $3, NOW())
       RETURNING id, email, name, created_at`,
      [data.email.toLowerCase(), passwordHash, data.name]
    );

    return rows[0];
  });

  // 3. Respond — never return the password hash
  return sendCreated(res, {
    id:        user.id,
    email:     user.email,
    name:      user.name,
    createdAt: user.created_at,
  });
}

// ─── Export ───────────────────────────────────────────────────────────────────

// withMiddleware catches DUPLICATE_EMAIL and re-maps it to 409;
// all other unexpected errors become 500.
export default withMiddleware(
  publicStack,
  async (req, res) => {
    try {
      return await handler(req, res);
    } catch (err) {
      if (err.code === 'DUPLICATE_EMAIL') {
        return sendConflict(res, 'Email already registered');
      }
      throw err; // bubble up to withMiddleware's top-level catch → 500
    }
  }
);
