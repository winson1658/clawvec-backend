/**
 * api/lib/response.js
 *
 * Standardised HTTP response helpers.
 *
 * Every endpoint returns the same envelope shape so clients can write
 * one generic error-handling layer:
 *
 *   // Success
 *   { success: true,  data: <payload>, meta?: { page, total, ... } }
 *
 *   // Error
 *   { success: false, error: { code, message, details? } }
 */

// ─── Success helpers ─────────────────────────────────────────────────────────

/**
 * sendOk — 200 with a data payload.
 *
 * @param {import('http').ServerResponse} res
 * @param {unknown} data
 * @param {{ meta?: object }} [opts]
 */
export function sendOk(res, data, { meta } = {}) {
  const body = { success: true, data };
  if (meta) body.meta = meta;
  return res.status(200).json(body);
}

/**
 * sendCreated — 201 for newly created resources.
 *
 * @param {import('http').ServerResponse} res
 * @param {unknown} data
 */
export function sendCreated(res, data) {
  return res.status(201).json({ success: true, data });
}

/**
 * sendNoContent — 204 when there is nothing to return (e.g. DELETE).
 */
export function sendNoContent(res) {
  return res.status(204).end();
}

// ─── Error helpers ────────────────────────────────────────────────────────────

/**
 * Canonical error codes used across the API.
 * Keeping them in one place makes i18n and client-side handling predictable.
 */
export const ErrorCode = Object.freeze({
  VALIDATION_ERROR:   'VALIDATION_ERROR',
  NOT_FOUND:          'NOT_FOUND',
  UNAUTHORIZED:       'UNAUTHORIZED',
  FORBIDDEN:          'FORBIDDEN',
  CONFLICT:           'CONFLICT',
  RATE_LIMITED:       'RATE_LIMITED',
  INTERNAL_ERROR:     'INTERNAL_ERROR',
  METHOD_NOT_ALLOWED: 'METHOD_NOT_ALLOWED',
});

/**
 * sendError — generic error sender.
 *
 * @param {import('http').ServerResponse} res
 * @param {number} status
 * @param {string} code     - one of ErrorCode
 * @param {string} message  - human-readable description
 * @param {unknown} [details]
 */
export function sendError(res, status, code, message, details) {
  const body = { success: false, error: { code, message } };
  if (details !== undefined) body.error.details = details;
  return res.status(status).json(body);
}

// Convenience shortcuts ──────────────────────────────────────────────────────

export const sendBadRequest = (res, message, details) =>
  sendError(res, 400, ErrorCode.VALIDATION_ERROR, message, details);

export const sendUnauthorized = (res, message = 'Unauthorized') =>
  sendError(res, 401, ErrorCode.UNAUTHORIZED, message);

export const sendForbidden = (res, message = 'Forbidden') =>
  sendError(res, 403, ErrorCode.FORBIDDEN, message);

export const sendNotFound = (res, resource = 'Resource') =>
  sendError(res, 404, ErrorCode.NOT_FOUND, `${resource} not found`);

export const sendConflict = (res, message) =>
  sendError(res, 409, ErrorCode.CONFLICT, message);

export const sendMethodNotAllowed = (res, allowed) => {
  res.setHeader('Allow', allowed.join(', '));
  return sendError(res, 405, ErrorCode.METHOD_NOT_ALLOWED, 'Method not allowed');
};

export const sendInternalError = (res, err, requestId) => {
  // Never expose raw stack traces in production.
  console.error({ requestId, error: err?.message, stack: err?.stack });
  return sendError(
    res,
    500,
    ErrorCode.INTERNAL_ERROR,
    'An unexpected error occurred',
    process.env.NODE_ENV !== 'production' ? err?.message : undefined
  );
};
