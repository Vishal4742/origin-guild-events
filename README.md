# Origin Guild Events

Live page behind the printed QR. To add or change an event, edit `events.json` and push, or add a Luma profile id to `HOSTS` / a site to `SITES` in `fetch_events.py`. A cron workflow re-fetches every 3 days. Nothing else needs to change.

Each entry: `id` (Luma slug), `evt` (Luma event id, from the page source), `title`, `start`/`end` (ISO, UTC), `where`, `hosts`, `desc`, `cover` (image file in this repo), `url`, `approval`.
