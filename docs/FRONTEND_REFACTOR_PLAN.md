# Frontend Refactor Plan (Phase 1)

This document tracks the staged modularization of the mobile UI.

## Current state
- Legacy entry: `static/mobile-app.js` (3k+ LOC)
- CSS: `static/mobile-styles.css`
- HTML page: `mobile_unified_nodes.html`

## Phase 1 (landed)
- New entrypoint: `static/js/main.js` importing the legacy file (no behavior change).
- CSS structure scaffolded under `static/css/` with `mobile.css` aggregating current styles.
- Template stubs added under `templates/` for future extraction.

## Phase 2 (next)
- Introduce `state.js` for shared config/auth/session state.
- Extract UI concerns (`initDarkMode`, `toggleDarkMode`, screen toggles) into `ui.js`.
- Extract auth (`login`, `logout`) into `auth.js`, wiring to `state.js` and `ui.js`.
- Bind necessary functions to `window` from module entry to support inline handlers.

## Phase 3
- Extract node CRUD, rendering, and tree state into `nodes.js`.
- Extract touch drag-and-drop into `drag-drop.js`.
- Extract chat panel logic into `chat.js`.

## Phase 4
- Replace inline HTML strings with `templates/` partials.
- Add simple templating helpers to render partials.

## Build setup (optional)
- Reintroduce Vite with a lightweight config to bundle `static/js/main.js` and `static/css/mobile.css` into `dist/` for production.
- Scripts: `dev`, `build`, `preview`.

This allows gradual migration with minimal risk while keeping the app functional.

