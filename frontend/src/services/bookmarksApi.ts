/**
 * API client for bookmark endpoints.
 *
 * Calls POST /bookmarks and GET /bookmarks on the FastAPI backend.
 * All bookmark endpoints require an authenticated Supabase session token.
 */

import { API_BASE_URL } from '../config'

export interface BookmarkResponseItem {
  bookmark_id: string
  chunk_id: string
  chunk_text: string
  speaker_label: string
  start_timestamp: string
  end_timestamp: string
  chunk_index: number
  episode_id: string
  episode_title: string
  episode_number: number | null
  podcast_name: string
  publication_date: string | null
  created_at: string
}

interface BookmarkListResponse {
  bookmarks: BookmarkResponseItem[]
}

/**
 * Fetch all bookmarks for the authenticated user.
 *
 * @param accessToken - The Supabase JWT session token.
 * @returns Array of bookmark objects.
 */
export async function fetchBookmarks(
  accessToken: string,
): Promise<BookmarkResponseItem[]> {
  const response = await fetch(`${API_BASE_URL}/bookmarks`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Failed to fetch bookmarks (${response.status}): ${body}`)
  }

  const data = (await response.json()) as BookmarkListResponse
  return data.bookmarks
}

/**
 * Create a bookmark for a specific transcript chunk.
 *
 * @param accessToken - The Supabase JWT session token.
 * @param chunkId - UUID of the transcript chunk to bookmark.
 * @returns The created bookmark object.
 * @throws {BookmarkLimitError} If the user has reached the 100 bookmark limit.
 */
export async function createBookmark(
  accessToken: string,
  chunkId: string,
): Promise<BookmarkResponseItem> {
  const response = await fetch(`${API_BASE_URL}/bookmarks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ chunk_id: chunkId }),
  })

  if (response.status === 400) {
    const data = (await response.json()) as { detail: string }
    throw new BookmarkLimitError(data.detail)
  }

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Failed to create bookmark (${response.status}): ${body}`)
  }

  return (await response.json()) as BookmarkResponseItem
}

/**
 * Delete a bookmark by its ID.
 *
 * @param accessToken - The Supabase JWT session token.
 * @param bookmarkId - UUID of the bookmark to delete.
 */
export async function deleteBookmark(
  accessToken: string,
  bookmarkId: string,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/bookmarks/${bookmarkId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Failed to delete bookmark (${response.status}): ${body}`)
  }
}

/**
 * Custom error class for when the bookmark limit is reached.
 */
export class BookmarkLimitError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'BookmarkLimitError'
  }
}
