// Base URL for all API calls.
//
// In production the frontend is served behind nginx, which proxies /api/* to
// the backend and strips the prefix — so a relative base keeps requests
// same-origin and works on any host or IP without a rebuild.
// In dev, vite.config.js proxies /api to the local backend the same way.
export const API_URL = import.meta.env.VITE_API_URL ?? '/api'
