// Single point of truth for base-path-aware URLs (GitHub Pages subpath).
// specs/codex-site.md: never hardcode root-relative links — always use url().
const base = import.meta.env.BASE_URL.replace(/\/$/, '');

export function url(path: string): string {
  return `${base}${path.startsWith('/') ? path : `/${path}`}`;
}
