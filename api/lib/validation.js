/**
 * api/lib/validation.js
 *
 * Lightweight, dependency-free schema validation for request bodies / query params.
 *
 * Design goals:
 *  - Zero runtime dependencies (no zod/joi) so the lambda cold-start stays fast.
 *  - Type-safe enough to catch the most common bugs at the boundary.
 *  - Returns structured errors that sendBadRequest() can pass straight to the client.
 *
 * Usage:
 *   import { validate, rules } from '../lib/validation.js';
 *
 *   const schema = {
 *     email:    [rules.required, rules.email],
 *     password: [rules.required, rules.minLength(8)],
 *     age:      [rules.optional, rules.integer, rules.min(0)],
 *   };
 *
 *   const { data, errors } = validate(req.body, schema);
 *   if (errors) return sendBadRequest(res, 'Validation failed', errors);
 */

// ─── Rule primitives ─────────────────────────────────────────────────────────

/**
 * @typedef {(value: unknown, field: string) => string | null} Rule
 * A Rule returns an error message string on failure, or null on success.
 */

export const rules = {
  // Presence
  required: (v, field) =>
    v === undefined || v === null || v === ''
      ? `${field} is required`
      : null,

  optional: () => null, // always passes; use as first rule to mark optional fields

  // Types
  string: (v, field) =>
    v !== undefined && typeof v !== 'string' ? `${field} must be a string` : null,

  integer: (v, field) =>
    v !== undefined && (!Number.isInteger(Number(v)) || isNaN(Number(v)))
      ? `${field} must be an integer`
      : null,

  boolean: (v, field) =>
    v !== undefined && typeof v !== 'boolean' ? `${field} must be a boolean` : null,

  // String constraints
  email: (v, field) => {
    if (v === undefined || v === null) return null;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(v))
      ? null
      : `${field} must be a valid email address`;
  },

  url: (v, field) => {
    if (v === undefined || v === null) return null;
    try {
      new URL(String(v));
      return null;
    } catch {
      return `${field} must be a valid URL`;
    }
  },

  uuid: (v, field) => {
    if (v === undefined || v === null) return null;
    return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(String(v))
      ? null
      : `${field} must be a valid UUID`;
  },

  // Numeric / length constraints (factory functions)
  minLength: (min) => (v, field) =>
    v !== undefined && String(v).length < min
      ? `${field} must be at least ${min} characters`
      : null,

  maxLength: (max) => (v, field) =>
    v !== undefined && String(v).length > max
      ? `${field} must be at most ${max} characters`
      : null,

  min: (minimum) => (v, field) =>
    v !== undefined && Number(v) < minimum
      ? `${field} must be at least ${minimum}`
      : null,

  max: (maximum) => (v, field) =>
    v !== undefined && Number(v) > maximum
      ? `${field} must be at most ${maximum}`
      : null,

  // Enum
  oneOf: (choices) => (v, field) =>
    v !== undefined && !choices.includes(v)
      ? `${field} must be one of: ${choices.join(', ')}`
      : null,
};

// ─── validate() ──────────────────────────────────────────────────────────────

/**
 * @typedef {{ [field: string]: Rule[] }} Schema
 * @typedef {{ data: object, errors: null } | { data: null, errors: object }} ValidationResult
 */

/**
 * validate — runs each field through its rule chain and collects all errors.
 *
 * @param {unknown} input   - req.body, req.query, etc.
 * @param {Schema}  schema
 * @returns {ValidationResult}
 */
export function validate(input, schema) {
  const source = (input && typeof input === 'object') ? input : {};
  const errors = {};
  const data = {};

  for (const [field, fieldRules] of Object.entries(schema)) {
    const value = source[field];
    const isOptional = fieldRules[0] === rules.optional;

    // Skip optional fields that are absent
    if (isOptional && (value === undefined || value === null)) {
      continue;
    }

    const fieldErrors = [];
    for (const rule of fieldRules) {
      const error = rule(value, field);
      if (error) fieldErrors.push(error);
    }

    if (fieldErrors.length > 0) {
      errors[field] = fieldErrors;
    } else {
      data[field] = value;
    }
  }

  if (Object.keys(errors).length > 0) {
    return { data: null, errors };
  }

  return { data, errors: null };
}

// ─── parseBody() ─────────────────────────────────────────────────────────────

/**
 * parseBody — reads and JSON-parses req.body safely.
 * Vercel already parses JSON bodies; this is a guard for edge cases
 * (e.g. body sent as a raw string by some clients).
 *
 * @param {import('http').IncomingMessage} req
 * @returns {unknown}
 */
export function parseBody(req) {
  if (req.body && typeof req.body === 'object') return req.body;
  if (typeof req.body === 'string') {
    try {
      return JSON.parse(req.body);
    } catch {
      return null;
    }
  }
  return null;
}
