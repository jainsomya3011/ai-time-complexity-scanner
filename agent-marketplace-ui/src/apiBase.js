/**
 * Marketplace (auth, agents, buy, use). In dev, Vite proxies /api → Flask :7000.
 * Override with VITE_MARKETPLACE_URL e.g. http://127.0.0.1:7000 for preview builds.
 */
export const MARKETPLACE_API =
  import.meta.env.VITE_MARKETPLACE_URL?.replace(/\/$/, "") ??
  (import.meta.env.DEV ? "/api" : "http://127.0.0.1:7000");
