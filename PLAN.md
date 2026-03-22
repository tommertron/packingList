# Packing List — Upgrade Plan

> Upgrading the existing Python packing list app to fit the coefficiencies apps hub.

---

## What This Becomes

A Railway-hosted web app living at `apps.coefficiencies.com/packing-list`. Keeps the core trip-builder UX but gets the coefficiencies design system, Clerk auth, Todoist OAuth, and export options.

---

## Design

- Apply `coefficiencies.css` for full design system alignment
- Warm amber accent, Lora + DM Sans fonts, cream/dark mode
- Match hub card style for nav and footer

---

## Auth Strategy

**No account wall upfront.** The app works fully anonymous. Auth only triggers at export:

- **Download as Markdown** — no auth needed
- **Download as JSON** — no auth needed
- **Send to Todoist** — triggers Clerk sign-up/login, then Todoist OAuth

---

## Infrastructure

- **Hosting:** Railway (same project as the app hub)
- **Auth:** Clerk (shared key across all hub apps)
- **Database:** Railway Postgres — store Todoist access token keyed to Clerk user ID
- **Current:** Python + standard library → keep or migrate as needed

---

## Key Changes from Current Version

| Current | Target |
|---------|--------|
| API key entered manually in Settings | Todoist OAuth via Clerk |
| No export options | MD / JSON / Todoist |
| No design system | `coefficiencies.css` |
| Local only | Railway deployed |
| No accounts | Clerk (optional, only for sync) |

---

## Pro Tier (later)

- Save custom list templates
- Reuse across trips

---

## Prompt for Claude

When resuming work on this app, here's the context:

- Existing app: Python 3, standard library, `server.py` serves `index.html`
- Packing data lives in `packing.json` (falls back to `packing.template.json`)
- Already has trip-builder UI with category/item filtering
- `coefficiencies.css` is now in this directory — apply it
- See `app-hub-plan.md` in `/home/tommertron/code/coefficienciesApps/` for the full hub context and auth/monetisation strategy
- This will be deployed on Railway as part of the coefficiencies apps hub
