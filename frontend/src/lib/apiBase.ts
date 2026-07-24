/**
 * Runtime API base URL resolution.
 *
 * Priority:
 * 1. Build-time ``VITE_API_URL`` (set via Docker build-arg or Railway build var)
 * 2. Same-origin (the React app and nginx proxy live on the same domain)
 *
 * When using Docker Compose, nginx proxies ``/api/`` to the backend
 * container automatically.  On Railway, ``BACKEND_URL`` is injected as an
 * nginx env var and the proxy target is set at runtime via ``envsubst``.
 */

export function getApiBaseUrl(): string {
  const viteUrl = import.meta.env.VITE_API_URL;
  if (viteUrl) return viteUrl;
  // Same-origin: nginx proxies /api/ to the backend
  return "";
}
