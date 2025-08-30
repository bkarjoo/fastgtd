# JS Modules Layout (Scaffold)

- `main.js`: App entrypoint. Imports legacy code for now.
- `auth.js`: Login/logout, token management. (TBD)
- `nodes.js`: Node CRUD, render, state. (TBD)
- `ui.js`: UI state, dark mode, navigation. (TBD)
- `drag-drop.js`: Touch drag & drop. (TBD)
- `chat.js`: Chat panel + AI calls. (TBD)
- `state.js`: Shared config and runtime state. (TBD)

Gradually move functions from `static/mobile-app.js` here. Bind public functions to `window` in `main.js` to preserve inline handlers during transition.

