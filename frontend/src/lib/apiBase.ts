/**
 * Runtime API base URL resolution.
 *
 * Priority:
 * 1. Build-time ``VITE_API_URL`` (set via Docker build-arg or Railway build var)
 * 2. Runtime ``window.__API_URL__`` (injected via config.js by nginx at container start)
 * 3. Same-origin (empty string) — for Docker Compose with nginx proxy
 */

declare global {
  interface Window {
    __API_URL__?: string;
  }
}

export function getApiBaseUrl(): string {
  const viteUrl = import.meta.env.VITE_API_URL;
  if (viteUrl) return viteUrl;

  if (typeof window !== "undefined" && window.__API_URL__) {
    return window.__API_URL__;
  }

  // Same-origin: nginx proxies /api/ to the backend (Docker Compose)
  return "";
}
