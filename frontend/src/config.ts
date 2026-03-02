/**
 * Application configuration.
 *
 * Values are read from environment variables at build time (Vite injects
 * `import.meta.env.VITE_*` variables).  Sensible defaults are provided so the
 * app can run in development without a `.env` file for non-critical settings.
 */

/** Base URL of the FastAPI backend (no trailing slash). */
export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000'

/** Default number of search results per page. */
export const DEFAULT_PAGE_SIZE: number =
  Number(import.meta.env.VITE_DEFAULT_PAGE_SIZE) || 10
