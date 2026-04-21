# Email templates

Plain-text templates for the Mailjet workflow. Copy each into Mailjet's
campaign/template editor when needed. Placeholders use `{{NAME}}` style
so you can either hardcode on send or use Mailjet variables.

## Files

- `welcome-free.txt` — sent to new free-tier subscribers
- `welcome-member.txt` — sent manually after a new Member payment lands in Stripe
- `welcome-patron.txt` — sent manually after a new Patron payment lands in Stripe
- `weekly-issue.txt` — template for the Tuesday broadcast

## Placeholders common to the weekly

- `{{VOLUME}}` — e.g. `III`
- `{{ISSUE_NUM}}` — e.g. `25`
- `{{PUBLISH_DATE}}` — e.g. `21 April 2026`
- `{{ISSUE_TITLE}}` — the essay title
- `{{DEK}}` — one-sentence summary beneath the title
- `{{SUBJECT}}` — the product being profiled
- `{{READ_TIME}}` — minutes
- `{{BODY}}` — the essay text itself (plain text — HTML version goes in a different template)
- `{{ISSUE_URL}}` — canonical URL of the issue page on the site
- `{{NEXT_WEEK_TEASE}}` — one-line teaser for the following week

## Fixed footer fields

- `[your postal address]` — replace with your CAN-SPAM-compliant address.
  See `../README.md` in the root for why this is required.
- `[contact email]` — use your personal address (or a dedicated alias)
  until you have a domain. The site currently hardcodes
  `editor@monograph.press`, which is non-functional; see root README.

## Subject-line conventions

- Welcome emails: a short declarative phrase (`You are on the list.`).
- Weekly issues: `№ 25 — The Cult of Craft` (the issue number, em-dash, title).

The consistency is the point — readers should recognize the shape before
they read the sender.
