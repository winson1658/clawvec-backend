/**
 * api/lib/middleware.js
 *
 * Composable middleware factory for Vercel Serverless Functions.
 * Provides CORS, authentication, rate-limiting, and logging as
 * individual middleware units that can be composed via withMiddleware().
 */

// ─── CORS ────────────────────────────────────────────────────────────────────

const DEFAULT_CORS_ORIGINS = (process.env.CORS_ORIGINS || '')
  .split(',')
  .map((o) => o.trim())
  .filter(Boolean);

/**
 * corsMiddleware — sets CORS headers and handles pre-flight OPTIONS requests.
 *
 * @param {string[]} [allowedOrigins] - Defaults to CORS_ORIGINS env var.
 */
export function corsMiddleware(allowedOrigins = DEFAULT_CORS_ORIGINS) {
  return async (req, res, next) => {
    const origin = req.headers.origin || '';
    const allowed =
      allowedOrigins.length === 0 || allowedOrigins.includes(origin)
        ? origin
        : allowedOrigins[0];

    res.setHeader('Access-Control-Allow-Origin', allowed || '*');
    res.setHeader('Access-Control-Allow-Credentials', 'true');
    res.setHeader(
      'Access-Control-Allow-Methods',
      'GET,POST,PUT,PATCH,DELETE,OPTIONS'
    );
    res.setHeader(
      'Access-Control-Allow-Headers',
      'Content-Type, Authorization, X-Request-ID'
    );

    if (req.method === 'OPTIONS') {
      res.status(204).end();
      return; // pre-flight handled — skip handler
    }

    return next();
  };
}

// ─── JWT Authentication ───────────────────────────────────────────────────────

import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || '';

/**
 * authMiddleware — verifies the Bearer token in the Authorization header.
 * Attaches the decoded payload to req.user on success.
 *
 * @param {{ optional?: boolean }} [opts]
 *   optional: when true, missing/invalid tokens are tolerated (req.user stays undefined).
 */
export function authMiddleware({ optional = false } = {}) {
  return async (req, res, next) => {
    const header = req.headers.authorization || '';
    const token = header.startsWith('Bearer ') ? header.slice(7) : null;

    if (!token) {
      if (optional) return next();
      return res.status(401).json({ error: 'Missing authorization token' });
    }

    try {
      req.user = jwt.verify(token, JWT_SECRET);
      return next();
    } catch (err) {
      if (optional) return next();
      const message =
        err.name === 'TokenExpiredError' ? 'Token expired' : 'Invalid token';
      return res.status(401).json({ error: message });
    }
  };
}

// ─── Rate Limiting ────────────────────────────────────────────────────────────

// In-memory store (per warm lambda instance).
// For production use Redis via api/lib/cache.js.
const rateLimitStore = new Map();

/**
 * rateLimitMiddleware — sliding-window rate limiter.
 *
 * @param {{ limit?: number; windowMs?: number }} [opts]
 */
export function rateLimitMiddleware({ limit = 100, windowMs = 60_000 } = {}) {
  return async (req, res, next) => {
    const key = req.headers['x-forwarded-for'] || req.socket?.remoteAddress || 'unknown';
    const now = Date.now();
    const windowStart = now - windowMs;

    // Retrieve and prune timestamps outside the current window
    const timestamps = (rateLimitStore.get(key) || []).filter(
      (t) => t > windowStart
    );
    timestamps.push(now);
    rateLimitStore.set(key, timestamps);

    const remaining = Math.max(0, limit - timestamps.length);
    res.setHeader('X-RateLimit-Limit', limit);
    res.setHeader('X-RateLimit-Remaining', remaining);
    res.setHeader('X-RateLimit-Reset', Math.ceil((windowStart + windowMs) / 1000));

    if (timestamps.length > limit) {
      return res.status(429).json({ error: 'Too many requests' });
    }

    return next();
  };
}

// ─── Request Logging ──────────────────────────────────────────────────────────

import { randomUUID } from 'crypto';

/**
 * loggingMiddleware — attaches a request ID and logs duration on completion.
 */
export function loggingMiddleware() {
  return async (req, res, next) => {
    const requestId = randomUUID();
    const start = Date.now();

    req.requestId = requestId;
    res.setHeader('X-Request-ID', requestId);

    // Patch res.end to measure total duration
    const originalEnd = res.end.bind(res);
    res.end = (...args) => {
      const duration = Date.now() - start;
      console.log(
        JSON.stringify({
          requestId,
          method: req.method,
          url: req.url,
          status: res.statusCode,
          durationMs: duration,
          ip: req.headers['x-forwarded-for'] || 'unknown',
        })
      );
      return originalEnd(...args);
    };

    return next();
  };
}
