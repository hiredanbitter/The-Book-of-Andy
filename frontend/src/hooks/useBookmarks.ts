/**
 * Custom hook that manages bookmark state for search result cards.
 *
 * Fetches the user's existing bookmarks on mount (when authenticated) and
 * exposes helpers to check whether a chunk is bookmarked, create new
 * bookmarks, remove bookmarks, and undo removals.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useAuth } from './useAuth'
import {
  BookmarkLimitError,
  createBookmark,
  deleteBookmark,
  fetchBookmarks,
} from '../services/bookmarksApi'

interface UseBookmarksReturn {
  /** Set of chunk IDs that the current user has bookmarked. */
  bookmarkedChunkIds: Set<string>
  /**
   * Save a bookmark for the given chunk.
   * Returns an object indicating success or a limit-reached error message.
   */
  saveBookmark: (chunkId: string) => Promise<{ success: boolean; error?: string }>
  /**
   * Remove a bookmark for the given chunk.
   * Returns an object indicating success or an error message.
   */
  removeBookmark: (chunkId: string) => Promise<{ success: boolean; error?: string }>
  /**
   * Undo a recent bookmark removal by re-creating the bookmark.
   * Returns an object indicating success or an error message.
   */
  undoRemoveBookmark: (chunkId: string) => Promise<{ success: boolean; error?: string }>
}

const EMPTY_SET: Set<string> = new Set()

export function useBookmarks(): UseBookmarksReturn {
  const { session } = useAuth()
  const accessToken = session?.access_token ?? null

  // chunk_id -> bookmark_id mapping from the initial fetch
  const [fetchedBookmarkMap, setFetchedBookmarkMap] = useState<Map<string, string>>(
    new Map(),
  )
  // chunk_id -> bookmark_id mapping for bookmarks created locally this session
  const [localBookmarkMap, setLocalBookmarkMap] = useState<Map<string, string>>(
    new Map(),
  )
  // Set of chunk IDs that have been removed locally this session
  const [locallyRemoved, setLocallyRemoved] = useState<Set<string>>(new Set())

  const cancelledRef = useRef(false)

  // Fetch existing bookmarks when user is authenticated
  useEffect(() => {
    cancelledRef.current = false

    if (!accessToken) return

    fetchBookmarks(accessToken)
      .then((bookmarks) => {
        if (!cancelledRef.current) {
          const map = new Map<string, string>()
          for (const b of bookmarks) {
            map.set(b.chunk_id, b.bookmark_id)
          }
          setFetchedBookmarkMap(map)
        }
      })
      .catch(() => {
        // Silently ignore fetch errors -- bookmarks are not critical
      })

    return () => {
      cancelledRef.current = true
    }
  }, [accessToken])

  // Compute the combined bookmark_id lookup (fetched + locally added - locally removed)
  const bookmarkIdMap = useMemo(() => {
    if (!accessToken) return new Map<string, string>()
    const merged = new Map(fetchedBookmarkMap)
    for (const [chunkId, bookmarkId] of localBookmarkMap) {
      merged.set(chunkId, bookmarkId)
    }
    for (const chunkId of locallyRemoved) {
      merged.delete(chunkId)
    }
    return merged
  }, [accessToken, fetchedBookmarkMap, localBookmarkMap, locallyRemoved])

  // Derive the set of bookmarked chunk IDs from the map
  const bookmarkedChunkIds = useMemo(() => {
    if (!accessToken) return EMPTY_SET
    return new Set(bookmarkIdMap.keys())
  }, [accessToken, bookmarkIdMap])

  const saveBookmark = useCallback(
    async (chunkId: string): Promise<{ success: boolean; error?: string }> => {
      if (!accessToken) {
        return { success: false, error: 'Not authenticated' }
      }

      // Optimistically add to local state
      setLocallyRemoved((prev) => {
        const next = new Set(prev)
        next.delete(chunkId)
        return next
      })

      try {
        const bookmark = await createBookmark(accessToken, chunkId)
        setLocalBookmarkMap((prev) => {
          const next = new Map(prev)
          next.set(chunkId, bookmark.bookmark_id)
          return next
        })
        return { success: true }
      } catch (err) {
        if (err instanceof BookmarkLimitError) {
          return { success: false, error: err.message }
        }
        return {
          success: false,
          error: 'Failed to save bookmark. Please try again.',
        }
      }
    },
    [accessToken],
  )

  const removeBookmark = useCallback(
    async (chunkId: string): Promise<{ success: boolean; error?: string }> => {
      if (!accessToken) {
        return { success: false, error: 'Not authenticated' }
      }

      const bookmarkId = bookmarkIdMap.get(chunkId)
      if (!bookmarkId) {
        return { success: false, error: 'Bookmark not found' }
      }

      // Optimistically remove from local state
      setLocallyRemoved((prev) => new Set(prev).add(chunkId))

      try {
        await deleteBookmark(accessToken, bookmarkId)
        // Clean up the local bookmark map entry if it was a locally-created bookmark
        setLocalBookmarkMap((prev) => {
          if (prev.has(chunkId)) {
            const next = new Map(prev)
            next.delete(chunkId)
            return next
          }
          return prev
        })
        return { success: true }
      } catch (err) {
        // Revert optimistic removal on failure
        setLocallyRemoved((prev) => {
          const next = new Set(prev)
          next.delete(chunkId)
          return next
        })
        const message =
          err instanceof Error ? err.message : 'Failed to remove bookmark.'
        return { success: false, error: message }
      }
    },
    [accessToken, bookmarkIdMap],
  )

  const undoRemoveBookmark = useCallback(
    async (chunkId: string): Promise<{ success: boolean; error?: string }> => {
      if (!accessToken) {
        return { success: false, error: 'Not authenticated' }
      }

      // Optimistically restore in local state
      setLocallyRemoved((prev) => {
        const next = new Set(prev)
        next.delete(chunkId)
        return next
      })

      try {
        const bookmark = await createBookmark(accessToken, chunkId)
        // Store the new bookmark_id
        setLocalBookmarkMap((prev) => {
          const next = new Map(prev)
          next.set(chunkId, bookmark.bookmark_id)
          return next
        })
        return { success: true }
      } catch (err) {
        // Revert optimistic restore on failure
        setLocallyRemoved((prev) => new Set(prev).add(chunkId))
        if (err instanceof BookmarkLimitError) {
          return { success: false, error: err.message }
        }
        return {
          success: false,
          error: 'Failed to restore bookmark. Please try again.',
        }
      }
    },
    [accessToken],
  )

  return {
    bookmarkedChunkIds,
    saveBookmark,
    removeBookmark,
    undoRemoveBookmark,
  }
}
