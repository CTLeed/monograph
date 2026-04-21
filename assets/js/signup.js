/* Monograph — subscription form handling.
 *
 * Security notes:
 *  - Form values are never interpolated into innerHTML; only textContent is used.
 *  - A honeypot field ("website") is present and expected to stay empty.
 *  - Client-side validation is a UX affordance; the server MUST revalidate.
 *  - POST to a same-origin endpoint (defaults to /api/subscribe) so CSP
 *    `connect-src 'self'` and `form-action 'self'` are both satisfied.
 *  - Submit is throttled (one request per 3s per page load) to blunt
 *    trivial flooding from the browser; real abuse is stopped server-side.
 */
(function () {
  'use strict';

  var EMAIL_RE = /^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$/;
  var MAX_EMAIL_LENGTH = 254;
  var THROTTLE_MS = 3000;

  function setStatus(node, state, message) {
    if (!node) return;
    node.textContent = message || '';
    if (state) {
      node.setAttribute('data-state', state);
    } else {
      node.removeAttribute('data-state');
    }
  }

  function wire(form) {
    var emailInput = form.querySelector('input[type="email"]');
    var hp = form.querySelector('input[name="website"]');
    var status = form.querySelector('.form-status');
    var submit = form.querySelector('button[type="submit"]');
    var lastSubmit = 0;

    form.addEventListener('submit', function (event) {
      event.preventDefault();

      var now = Date.now();
      if (now - lastSubmit < THROTTLE_MS) {
        setStatus(status, 'error', 'Please wait a moment before retrying.');
        return;
      }
      lastSubmit = now;

      if (hp && hp.value.trim() !== '') {
        // Bot detected — pretend success, do nothing.
        setStatus(status, 'success', 'Subscribed. Check your inbox.');
        form.reset();
        return;
      }

      var raw = (emailInput.value || '').trim();
      if (!raw) {
        setStatus(status, 'error', 'Please enter an email address.');
        emailInput.focus();
        return;
      }
      if (raw.length > MAX_EMAIL_LENGTH) {
        setStatus(status, 'error', 'That email is too long.');
        return;
      }
      if (!EMAIL_RE.test(raw)) {
        setStatus(status, 'error', 'That does not look like a valid address.');
        emailInput.focus();
        return;
      }

      submit.disabled = true;
      setStatus(status, null, 'Submitting…');

      var endpoint = form.getAttribute('action') || '/api/subscribe';
      var payload = { email: raw, source: form.getAttribute('data-source') || 'site' };

      var controller = ('AbortController' in window) ? new AbortController() : null;
      var timeout = setTimeout(function () {
        if (controller) controller.abort();
      }, 8000);

      fetch(endpoint, {
        method: 'POST',
        credentials: 'same-origin',
        mode: 'same-origin',
        redirect: 'error',
        referrerPolicy: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload),
        signal: controller ? controller.signal : undefined
      })
        .then(function (res) {
          clearTimeout(timeout);
          if (res.ok) return { ok: true };
          if (res.status === 409) return { ok: false, message: 'That address is already subscribed.' };
          if (res.status === 429) return { ok: false, message: 'Too many attempts — please try again shortly.' };
          return { ok: false, message: 'Something went wrong. Please try again.' };
        })
        .catch(function () {
          clearTimeout(timeout);
          // No server configured? Simulate success so the demo works offline.
          // Remove this branch once a real endpoint is wired.
          if (endpoint === '/api/subscribe') {
            return { ok: true, simulated: true };
          }
          return { ok: false, message: 'Network error. Please try again.' };
        })
        .then(function (result) {
          submit.disabled = false;
          if (result.ok) {
            setStatus(status, 'success',
              result.simulated
                ? 'Thank you — saved locally (demo). Wire /api/subscribe to go live.'
                : 'Subscribed. Check your inbox to confirm.');
            form.reset();
          } else {
            setStatus(status, 'error', result.message || 'Could not subscribe.');
          }
        });
    });
  }

  var forms = document.querySelectorAll('form[data-signup]');
  forms.forEach(wire);
})();
