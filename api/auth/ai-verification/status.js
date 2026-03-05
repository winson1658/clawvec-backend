/**
 * api/auth/ai-verification/status.js  →  GET /api/auth/ai-verification/status
 *
 * Returns the AI-verification status for the authenticated user.
 *
 * Demonstrates:
 *  - privateStack (auth required)
 *  - Query-param validation
 *  - Reading req.user set by authMiddleware
 */

import { withMiddleware, privateStack } from '../../lib/withMiddleware.js';
import { query }                        from '../../lib/database.js';
import { validate, rules }              from '../../lib/validation.js';
import {
  sendOk,
  sendBadRequest,
  sendNotFound,
  sendMethodNotAllowed,
} from '../../lib/response.js';

// ─── Query-param schema ───────────────────────────────────────────────────────

const querySchema = {
  // Optional: client may request a specific verification session by ID.
  sessionId: [rules.optional, rules.uuid],
};

// ─── Handler ──────────────────────────────────────────────────────────────────

async function handler(req, res) {
  if (req.method !== 'GET') {
    return sendMethodNotAllowed(res, ['GET']);
  }

  // Validate optional query params
  const { data: params, errors } = validate(req.query, querySchema);
  if (errors) return sendBadRequest(res, 'Invalid query parameters', errors);

  // req.user is populated by authMiddleware
  const userId = req.user.sub;

  const sql = params?.sessionId
    ? `SELECT id, status, score, completed_at
         FROM ai_verifications
        WHERE user_id = $1 AND id = $2
        LIMIT 1`
    : `SELECT id, status, score, completed_at
         FROM ai_verifications
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 1`;

  const queryParams = params?.sessionId
    ? [userId, params.sessionId]
    : [userId];

  const { rows } = await query(sql, queryParams);

  if (rows.length === 0) {
    return sendNotFound(res, 'AI verification');
  }

  const record = rows[0];
  return sendOk(res, {
    sessionId:   record.id,
    status:      record.status,       // 'pending' | 'passed' | 'failed'
    score:       record.score,
    completedAt: record.completed_at,
  });
}

// ─── Export ───────────────────────────────────────────────────────────────────

export default withMiddleware(privateStack, handler);
