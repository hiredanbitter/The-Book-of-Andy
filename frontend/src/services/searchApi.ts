/**
 * API client for the search endpoints.
 *
 * Calls GET /search/keyword and GET /search/semantic on the FastAPI backend
 * and returns typed responses.
 */

import { API_BASE_URL, DEFAULT_PAGE_SIZE } from '../config'
import type { SearchMode, SearchResponse } from '../types/search'

/**
 * Perform a search against the backend.
 *
 * @param query - The user's search text.
 * @param mode  - 'keyword' or 'semantic'.
 * @param page  - 1-based page number (keyword search only; ignored for semantic).
 * @param pageSize - Results per page (keyword search only; ignored for semantic).
 * @returns The parsed SearchResponse from the API.
 * @throws {Error} If the API returns a non-OK status.
 */
export async function fetchSearchResults(
  query: string,
  mode: SearchMode,
  page: number = 1,
  pageSize: number = DEFAULT_PAGE_SIZE,
): Promise<SearchResponse> {
  const endpoint = mode === 'keyword' ? 'keyword' : 'semantic'

  const params = new URLSearchParams({ q: query })
  if (mode === 'keyword') {
    params.set('page', String(page))
    params.set('page_size', String(pageSize))
  }

  const url = `${API_BASE_URL}/search/${endpoint}?${params.toString()}`

  const response = await fetch(url)

  if (!response.ok) {
    const body = await response.text()
    throw new Error(
      `Search request failed (${response.status}): ${body}`,
    )
  }

  return (await response.json()) as SearchResponse
}
