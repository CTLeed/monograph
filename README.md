# Monograph

A production-quality static website for *Monograph*, a weekly editorial
newsletter that profiles one software product each Tuesday.

Built as plain HTML, CSS, and a tiny amount of vanilla JavaScript — no
framework, no build step, no client-side router, no tracker, no
third-party analytics. It deploys to any static host.

---

## Running locally

Any static file server will do. From this directory:

```bash
python3 -m http.server 8080
# or
npx serve .
```

Then open `http://localhost:8080`. The homepage is `index.html`.

> The subscribe form posts to `/api/subscribe`. With no real endpoint
> wired, the client JS treats a network failure as a simulated success
> so the UX works during local development. See
> `api/subscribe.example.js` for a reference implementation.

---

## File map

```
monograph/
├── index.html                # Homepage
├── about.html                # About the publication
├── pricing.html              # Subscribe / pricing
├── archive.html              # Every issue
├── 404.html                  # Not-found page
├── issues/
│   ├── 024-linear.html       # "The Cult of Craft"
│   ├── 023-arc.html          # "Re-imagining the Tab"
│   ├── 022-raycast.html      # "The Keyboard as Interface"
│   ├── 021-things.html       # "Seventeen Years of No"
│   ├── 020-figma.html        # "The Multiplayer Bet"
│   └── 019-notion.html       # "The Lego Problem"
├── assets/
│   ├── css/main.css          # All styles
│   └── js/
│       ├── main.js           # Reveal-on-scroll + footer year
│       └── signup.js         # Form validation + submit
├── api/
│   └── subscribe.example.js  # Reference server handler (NOT served)
├── robots.txt
└── README.md                 # This file
```

Every HTML file is fully self-contained — no includes, no partials.

---

## Security posture

Security is the first priority for this site. The following controls are
in place; the deploy checklist below explains how to lift the ones that
require server co-operation.

### Content Security Policy

Every page ships a strict CSP via `<meta http-equiv>`:

```
default-src 'self';
style-src   'self' https://fonts.googleapis.com;
font-src    'self' https://fonts.gstatic.com;
img-src     'self' data:;
script-src  'self';
connect-src 'self';
frame-ancestors 'none';
base-uri    'self';
form-action 'self';
object-src  'none';
upgrade-insecure-requests
```

- **No inline scripts anywhere.** All JavaScript lives in
  `assets/js/*.js` and is loaded with `defer`.
- **No inline event handlers** (`onclick=`, etc.).
- **No third-party scripts, analytics, or trackers.** The only
  cross-origin assets are Google Fonts CSS and font files, both
  restricted to their specific hosts.
- **`frame-ancestors 'none'`** prevents clickjacking.
- **`object-src 'none'`** prevents legacy plugin embeds.
- **`form-action 'self'`** prevents form hijacking to other origins.

### Other headers (meta-level)

- `<meta name="referrer" content="strict-origin-when-cross-origin">`
  — minimises referrer leakage.
- `<meta http-equiv="Content-Security-Policy" ...>` — on every page.
- All outbound links use `rel="noopener noreferrer"`.

### Headers that should be set at the edge

Meta-tag CSP works but real HTTP headers are stronger. Configure the
host (Netlify `_headers`, Cloudflare Pages `_headers`, nginx, etc.) to
emit these as response headers on every page:

```
Content-Security-Policy: default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'; upgrade-insecure-requests
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), interest-cohort=()
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-origin
```

### Subscribe form

- Submitted as `application/json` to a same-origin endpoint.
- Honeypot field named `website` — if filled, the server returns 200
  without writing anything, so bots do not adapt.
- Client-side throttle: 1 submit / 3 seconds / page load.
- Strict email regex on both client and server; 254-char length cap.
- `credentials: 'same-origin'`, `redirect: 'error'`, 8-second abort.
- Status messages are written only with `textContent`. User input
  is never interpolated into `innerHTML`.
- Server must re-validate everything and implement real rate limiting,
  double-opt-in, and minimal logging — see `api/subscribe.example.js`.

### Data

- The site stores nothing about visitors. No cookies are set; no
  `localStorage` is used.
- The subscribe form collects only an email address, transmitted over
  HTTPS to the operator-controlled endpoint.
- No third-party embeds, iframes, images, or scripts run in the page.

### What this project deliberately does NOT do

- No service worker. No offline cache. No PWA shell. (Each of these
  is a supply-chain vector if compromised and offers little value
  here.)
- No WebAssembly.
- No telemetry, ever.
- No "read-more" gates, no prompts, no pop-ups.

---

## Accessibility

- Skip-to-content link on every page.
- Semantic landmarks: `<header role="banner">`, `<main>`,
  `<footer role="contentinfo">`, `<article>`, `<nav aria-label>`.
- All interactive elements have focus-visible outlines.
- `aria-current="page"` on active nav items.
- `aria-live="polite"` on form status messages.
- `prefers-reduced-motion: reduce` disables reveal/blink animations.
- Colour contrast meets WCAG AA throughout the default palette.
- Typography scales fluidly with `clamp()` for mobile legibility.

---

## Deployment

This is a plain static site. Any of the following hosts work with no
configuration beyond the headers recipe above:

### Netlify / Cloudflare Pages / Vercel (static)

1. Drag-drop the `monograph/` folder or point the host at the repo.
2. Create a `_headers` file (Netlify / Pages) or `vercel.json` matching
   the recipe in the "Headers that should be set at the edge" section.
3. Wire an edge function at `/api/subscribe` using
   `api/subscribe.example.js` as a starting point.

### nginx / Caddy

Serve the directory with directory-listing off, HTTPS forced, and the
headers recipe applied. Point `/api/subscribe` at your handler.

### S3 + CloudFront

Set the `index.html` default document, create a 404-routing rule to
`/404.html`, and add a Lambda@Edge / CloudFront Function that appends
the security headers.

---

## Typography & colour

- Display: **Instrument Serif** (Google Fonts)
- Body: **Newsreader** (Google Fonts)
- Mono / metadata: **JetBrains Mono** (Google Fonts)

Palette is defined as CSS custom properties in `assets/css/main.css`
(`--paper`, `--ink`, `--accent`, etc.). Adjust tokens to retheme the
entire site.

If you want to self-host the fonts (to remove the two cross-origin
allowances from the CSP), download the three families, place them
under `assets/fonts/`, rewrite the `<link rel="stylesheet">` to a
local CSS file that declares `@font-face`, and tighten the CSP to
`style-src 'self'; font-src 'self'`.

---

## Licence

All text content in the issue essays is fictional editorial prose
written for demonstration purposes. Real companies are named; the
quoted essays are not real journalism and should not be represented
as such.

Code: do whatever you like with it.
