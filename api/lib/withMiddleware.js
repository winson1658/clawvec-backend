/**
 * api/lib/withMiddleware.js
 *
 * Higher-order function that wraps a Vercel route handler with an ordered
 * chain of middleware functions and top-level error handling.
 *
 * ─── Why this matters ────────────────────────────────────────────────────────
 * Vercel Serverless Functions export a plain `handler(req, res)`.  Without a
 * composition layer every file has to repeat:
 *   1. CORS headers
 *   2. Token verification
 *   3. Rate-limit checks
 *   4. try/catch → 500
 *
 * withMiddleware() lets each route declare *what* it needs instead of *how*:
 *
 *   export default withMiddleware(
 *     [cors(), rateLimit(), auth()],
 *     async (req, res) => { ... }
 *   );
 *
 * ─── Middleware contract ─────────────────────────────────────────────────────
 * Each middleware is an async function with the signature:
 *
 *   async (req, res, next) => void
 *
 * Calling next() advances to the next middleware (or the handler).
 * NOT calling next() (or calling res.end / res.json) short-circuits the chain.
 * ─────────────────────────────────────────────────────────────────────────────
 */

import { sendInternalError } from './response.js';

/**
 * withMiddleware — composes middleware onto a handler.
 *
 * @param {Function[]} middlewares  - Ordered list of middleware factories/instances.
 * @param {Function}   handler      - The actual route logic.
 * @returns {Function}              - Vercel-compatible `(req, res) => Promise<void>`.
 *
 * @example
 * // api/auth/register.js
 * import { withMiddleware }    from '../lib/withMiddleware.js';
 * import { corsMiddleware }    from '../lib/middleware.js';
 * import { rateLimitMiddleware } from '../lib/middleware.js';
 *
 * export default withMiddleware(
 *   [corsMiddleware(), rateLimitMiddleware()],
 *   async (req, res) => {
 *     res.json({ ok: true });
 *   }
 * );
 */
export function withMiddleware(middlewares, handler) {
  return async function composedHandler(req, res) {
    // Build a recursive runner over the middleware array.
    let index = 0;

    async function next() {
      if (res.writableEnded) return; // Response already sent — bail out.

      if (index < middlewares.length) {
        const mw = middlewares[index++];
        await mw(req, res, next);
      } else {
        // All middleware passed — invoke the actual handler.
        await handler(req, res);
      }
    }

    try {
      await next();
    } catch (err) {
      // Top-level safety net: log and return 500 without leaking internals.
      if (!res.writableEnded) {
        sendInternalError(res, err, req.requestId);
      }
    }
  };
}

// ─── Pre-built stacks ────────────────────────────────────────────────────────
//
// Export common middleware combinations so routes can just do:
//   import { publicStack, privateStack } from '../lib/withMiddleware.js';
//   export default withMiddleware(publicStack, handler);
//
// Adjust these to match your project's defaults.

import {
  corsMiddleware,
  rateLimitMiddleware,
  authMiddleware,
  loggingMiddleware,
} from './middleware.js';

/** publicStack — logging + CORS + rate-limiting (no auth required). */
export const publicStack = [
  loggingMiddleware(),
  corsMiddleware(),
  rateLimitMiddleware({ limit: 60, windowMs: 60_000 }),
];

/** privateStack — publicStack + mandatory JWT authentication. */
export const privateStack = [
  ...publicStack,
  authMiddleware(),
];

/** adminStack — stricter rate limit + mandatory auth. */
export const adminStack = [
  loggingMiddleware(),
  corsMiddleware(),
  rateLimitMiddleware({ limit: 20, windowMs: 60_000 }),
  authMiddleware(),
];
