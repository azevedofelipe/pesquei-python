import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Proxies API calls to the FastAPI dev server (fastapi dev main.py, port
// 8000) so the browser only ever talks to one origin (this Vite server) —
// no CORS setup needed. Add a new prefix here any time a new router with a
// different top-level path is added to main.py.
//
// Regex keys (not plain string prefixes) on purpose: a plain '/lure' key
// prefix-matches '/lures' too, which silently swallowed the frontend's own
// /lures route into the backend proxy (404, since the API has no such
// path). Anchoring with (/|$) means "/lure" or "/lure/..." only.
const backendTarget = 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '^/auth(/|$)': backendTarget,
      '^/catch(/|$)': backendTarget,
      '^/lure(/|$)': backendTarget,
      '^/user(/|$)': backendTarget,
    },
  },
})
