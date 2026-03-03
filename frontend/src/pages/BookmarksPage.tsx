import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { BookmarkCard } from '../components/BookmarkCard'
import type { BookmarkResponseItem } from '../services/bookmarksApi'
import { fetchBookmarks, deleteBookmark } from '../services/bookmarksApi'
import './BookmarksPage.css'

export function BookmarksPage() {
  const { user, session, loading: authLoading } = useAuth()
  const navigate = useNavigate()

  const [bookmarks, setBookmarks] = useState<BookmarkResponseItem[]>([])
  const [loading, setLoading] = useState(false)
  const [hasFetched, setHasFetched] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const accessToken = session?.access_token ?? null
  const cancelledRef = useRef(false)

  // Redirect to home if not authenticated (after auth finishes loading)
  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/', { replace: true })
    }
  }, [authLoading, user, navigate])

  const loadBookmarks = useCallback(async (token: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchBookmarks(token)
      if (!cancelledRef.current) {
        setBookmarks(data)
        setHasFetched(true)
      }
    } catch (err: unknown) {
      if (!cancelledRef.current) {
        const message =
          err instanceof Error ? err.message : 'Failed to load bookmarks.'
        setError(message)
        setHasFetched(true)
      }
    } finally {
      if (!cancelledRef.current) {
        setLoading(false)
      }
    }
  }, [])

  // Fetch bookmarks when authenticated
  useEffect(() => {
    cancelledRef.current = false
    if (accessToken) {
      loadBookmarks(accessToken)
    }
    return () => {
      cancelledRef.current = true
    }
  }, [accessToken, loadBookmarks])

  const handleDelete = useCallback(
    async (
      bookmarkId: string,
    ): Promise<{ success: boolean; error?: string }> => {
      const token = session?.access_token ?? null
      if (!token) {
        return { success: false, error: 'Not authenticated' }
      }

      try {
        await deleteBookmark(token, bookmarkId)
        setBookmarks((prev) => prev.filter((b) => b.bookmark_id !== bookmarkId))
        return { success: true }
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : 'Failed to delete bookmark.'
        return { success: false, error: message }
      }
    },
    [session],
  )

  // Show loading while auth is resolving or bookmarks haven't been fetched yet
  const showLoading = authLoading || loading || (!!accessToken && !hasFetched)

  // Don't render anything while auth is still loading
  if (authLoading) {
    return (
      <div className="bookmarks-page">
        <p className="bookmarks-loading">Loading...</p>
      </div>
    )
  }

  // User not authenticated — will be redirected by the effect above
  if (!user) {
    return null
  }

  return (
    <div className="bookmarks-page">
      <h1 className="bookmarks-title">My Bookmarks</h1>

      {/* Loading state */}
      {showLoading && (
        <p className="bookmarks-loading">Loading bookmarks...</p>
      )}

      {/* Error state */}
      {error && !showLoading && (
        <p className="bookmarks-error">{error}</p>
      )}

      {/* Bookmarks list */}
      {!showLoading && !error && bookmarks.length > 0 && (
        <div className="bookmarks-list">
          {bookmarks.map((bookmark) => (
            <BookmarkCard
              key={bookmark.bookmark_id}
              bookmark={bookmark}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!showLoading && !error && bookmarks.length === 0 && (
        <div className="bookmarks-empty">
          <p className="bookmarks-empty-title">No bookmarks yet</p>
          <p className="bookmarks-empty-text">
            Search for podcast transcripts and bookmark the moments you find
            valuable. Your saved bookmarks will appear here.
          </p>
          <Link to="/" className="bookmarks-search-link">
            Start searching
          </Link>
        </div>
      )}
    </div>
  )
}
