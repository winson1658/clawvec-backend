# api/lib — Shared Utilities for Vercel Serverless Functions

This directory contains all shared logic for the `/api` layer.
Route files import from here; they never duplicate cross-cutting concerns.

---

## File Overview

| File | Responsibility |
|---|---|
| `middleware.js` | CORS, JWT auth, rate-limiting, request logging |
| `withMiddleware.js` | Compose middleware onto a handler; pre-built stacks |
| `database.js` | Serverless-safe connection pool, `withDb`, `withTransaction`, `query` |
| `response.js` | Uniform success/error envelope + convenience senders |
| `validation.js` | Zero-dependency schema validation for bodies & query params |

---

## Architecture Pattern

```
api/
├── lib/                    ← shared utilities (never exported as routes)
│   ├── middleware.js
│   ├── withMiddleware.js
│   ├── database.js
│   ├── response.js
│   └── validation.js
│
├── auth/
│   ├── register.js         → POST /api/auth/register
│   ├── login.js            → POST /api/auth/login
│   └── ai-verification/
│       └── status.js       → GET  /api/auth/ai-verification/status
│
└── users/
    └── [id].js             → GET  /api/users/:id
```

---

## Middleware Composition

```js
// Every route follows the same three-line pattern:
import { withMiddleware, publicStack }  from '../lib/withMiddleware.js';

async function handler(req, res) { /* pure business logic */ }

export default withMiddleware(publicStack, handler);
```

### Available stacks

| Stack | Middleware included |
|---|---|
| `publicStack` | logging → CORS → rate-limit (60 req/min) |
| `privateStack` | publicStack + JWT auth (mandatory) |
| `adminStack` | logging → CORS → rate-limit (20 req/min) + JWT auth |

Custom stacks are just arrays:

```js
import { corsMiddleware, authMiddleware } from '../lib/middleware.js';

export default withMiddleware(
  [corsMiddleware(), authMiddleware({ optional: true })],
  handler
);
```

---

## Database Usage

```js
import { query, withDb, withTransaction } from '../lib/database.js';

// Single query
const { rows } = await query('SELECT * FROM users WHERE id = $1', [id]);

// Manual client lifecycle
const result = await withDb(async (db) => {
  const { rows } = await db.query('...', [...]);
  return rows[0];
});

// Transaction (auto COMMIT / ROLLBACK)
await withTransaction(async (db) => {
  await db.query('INSERT INTO orders ...', [...]);
  await db.query('UPDATE inventory ...', [...]);
});
```

**Connection pool** is cached on the module variable so warm lambda
invocations reuse the same pool (max 3 connections per instance).

---

## Validation

```js
import { validate, rules, parseBody } from '../lib/validation.js';

const schema = {
  email:    [rules.required, rules.email],
  password: [rules.required, rules.minLength(8)],
  age:      [rules.optional, rules.integer, rules.min(0)],
};

const { data, errors } = validate(parseBody(req), schema);
if (errors) return sendBadRequest(res, 'Validation failed', errors);
```

---

## Response Envelope

All responses share the same shape so the frontend can handle them uniformly:

```jsonc
// Success
{ "success": true, "data": { ... }, "meta": { ... } }

// Error
{ "success": false, "error": { "code": "VALIDATION_ERROR", "message": "...", "details": { ... } } }
```

---

## Vercel Serverless Best Practices (Summary)

1. **Re-use warm connections** — module-level singletons for DB pools and Redis clients.
2. **Keep bundles small** — import only what each route needs; avoid barrel re-exports of heavy libraries.
3. **Set `maxDuration`** — configure per-route timeouts in `vercel.json` to avoid runaway functions.
4. **External connection pooling** — use PgBouncer or Supabase Pooler in `transaction` mode for high traffic.
5. **Environment variables** — never hard-code secrets; always read from `process.env`.
6. **Always return** — every code path must call `res.end()` / `res.json()` or the function will time out.
7. **Structured logging** — emit JSON logs so Vercel's log drain can parse them.
