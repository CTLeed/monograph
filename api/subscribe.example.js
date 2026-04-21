/* Monograph — example /api/subscribe handler.
 *
 * This file is NOT served by the static site. It exists as a reference
 * implementation you can adapt to whichever runtime you deploy behind a
 * static host (Cloudflare Workers, Netlify Functions, Vercel Functions,
 * AWS Lambda, a small Express server, etc.).
 *
 * Security checklist the handler must enforce (the browser cannot be
 * trusted to enforce any of these):
 *
 *   1. HTTPS only. The static host should already redirect; the handler
 *      should reject any plain-HTTP request it still receives.
 *   2. Method whitelist: POST only. Everything else returns 405.
 *   3. Content-type check: require application/json; reject form-encoded
 *      payloads to reduce the attack surface of accidental CSRF, and to
 *      force same-origin fetch() usage.
 *   4. Origin / Referer check: require the Origin header to match your
 *      canonical domain list. Drop on mismatch.
 *   5. Body size cap: hard cap at 2 KiB. Larger = reject.
 *   6. Strict email validation server-side (do not trust the client).
 *   7. Honeypot check: if the "website" field is non-empty, return 200
 *      to avoid signalling to the bot, but do not write anything.
 *   8. Per-IP rate limiting: recommend 5 requests / 10 minutes. Use a
 *      durable KV / Redis / Turnstile challenge.
 *   9. Double-opt-in: store the address as pending, email a confirmation
 *      link. Do not add to the active list until the user clicks it.
 *  10. No third-party trackers in the confirmation email either.
 *  11. Log only what you need: timestamp + hashed email, no IP + PII
 *      in the same row.
 *  12. Return JSON only. No reflected user input in any response body.
 *
 * The example below is written for Cloudflare Workers but is portable.
 */

const EMAIL_RE = /^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$/;
const MAX_EMAIL_LEN = 254;
const MAX_BODY_BYTES = 2048;
const ALLOWED_ORIGINS = new Set([
  'https://monograph.press',
  'https://www.monograph.press'
]);

function json(status, body) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'no-referrer'
    }
  });
}

export default {
  async fetch(request, env) {
    if (request.method !== 'POST') {
      return json(405, { error: 'method_not_allowed' });
    }

    const origin = request.headers.get('origin') || '';
    if (!ALLOWED_ORIGINS.has(origin)) {
      return json(403, { error: 'forbidden_origin' });
    }

    const ct = request.headers.get('content-type') || '';
    if (!ct.toLowerCase().startsWith('application/json')) {
      return json(415, { error: 'unsupported_media_type' });
    }

    const len = Number(request.headers.get('content-length') || 0);
    if (len > MAX_BODY_BYTES) {
      return json(413, { error: 'payload_too_large' });
    }

    let payload;
    try {
      payload = await request.json();
    } catch (_) {
      return json(400, { error: 'invalid_json' });
    }

    if (!payload || typeof payload !== 'object') {
      return json(400, { error: 'invalid_body' });
    }

    // Honeypot — silently succeed so bots do not adapt.
    if (typeof payload.website === 'string' && payload.website.trim() !== '') {
      return json(200, { ok: true });
    }

    const email = typeof payload.email === 'string' ? payload.email.trim().toLowerCase() : '';
    if (!email || email.length > MAX_EMAIL_LEN || !EMAIL_RE.test(email)) {
      return json(400, { error: 'invalid_email' });
    }

    const source = typeof payload.source === 'string' && payload.source.length <= 32
      ? payload.source.replace(/[^a-z0-9_\-]/gi, '')
      : 'unknown';

    // --- Rate-limit (pseudo) ----------------------------------------------
    // const ip = request.headers.get('cf-connecting-ip') || 'anon';
    // const throttled = await env.RATELIMIT.hit(`sub:${ip}`, 5, 600);
    // if (throttled) return json(429, { error: 'rate_limited' });

    // --- Store as pending (pseudo) ----------------------------------------
    // const token = crypto.randomUUID();
    // await env.DB.exec(
    //   'INSERT INTO pending_subscribers (email, source, token, created_at) VALUES (?, ?, ?, ?)',
    //   [email, source, token, Date.now()]
    // );

    // --- Send double-opt-in mail (pseudo) ---------------------------------
    // await sendConfirmationEmail(email, `https://monograph.press/confirm?t=${token}`);

    return json(200, { ok: true });
  }
};
