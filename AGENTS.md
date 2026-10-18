# AGENTS.md — Base44 sandbox notes

Non-obvious findings for running this repo in the Base44 sandbox.

## What this app is
A Persian (RTL) single-page marketing site for "پارسیک" (Parsik), a printing &
advertising agency in Bandar Abbas. Plain Flask serving static files, no
database, no external services, no secrets required.

## Run
- `docker compose -f docker-compose.base44.yml up -d --build`
- Web entry: port 3000 (host) → 5000 (Flask, `PORT` env).
- `FLASK_DEBUG=1` in compose enables Flask's reloader; the original default
  (Procfile/`debug=False`) is preserved when the variable is unset.

## Structure
- `index.html` — single page (hero, services, process, portfolio, about, contact)
- `assets/css/style.css` — design system (crimson/orange/champagne on cream)
- `assets/js/main.js` — header scroll state, mobile menu, scroll-spy, reveal,
  counters, portfolio filter, contact form
- `app.py` — static server + `POST /api/contact` (appends to `contacts.json`,
  git-ignored)

## Verify
- `curl http://localhost:3000/` → the page HTML (200)
- Preview: hero renders over the photo, header turns orange after scroll,
  portfolio filter works, contact form shows the success message.

## Quirks
- The header bar is intentionally `direction: ltr` (logo left, phone right)
  inside an RTL page, per the brand spec.
- Unsplash CDN images are downloaded into `assets/img/` (checked into the
  repo) so the preview never depends on runtime network access.
- Original BandarAbbas chatbot files (`food.json`, `places.json`, `shops.json`,
  `stays.json`) are leftovers from the base repo and unused by the site.
