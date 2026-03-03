import { useState } from 'react'
import type { SearchResult } from '../types/search'
import './SearchResultCard.css'

interface SearchResultCardProps {
  result: SearchResult
  /** Whether the current user is authenticated. */
  isLoggedIn: boolean
  /** Whether this chunk is already bookmarked by the current user. */
  isBookmarked: boolean
  /** Callback to save a bookmark. Returns success/error info. */
  onBookmark: (chunkId: string) => Promise<{ success: boolean; error?: string }>
  /** Callback to remove a bookmark. Returns success/error info. */
  onRemoveBookmark?: (chunkId: string) => Promise<{ success: boolean; error?: string }>
  /** Callback invoked when a bookmark is successfully removed (for toast/undo). */
  onBookmarkRemoved?: (chunkId: string) => void
}

/**
 * Formats a publication date string (ISO or similar) to a human-readable form.
 * Returns the raw string if parsing fails.
 */
function formatDate(dateStr: string | null): string {
  if (!dateStr) return ''
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return dateStr
  }
}

/**
 * Build the URL that will open the transcript detail page with the matching
 * chunk highlighted.  The chunk_id is passed as a query parameter so the
 * transcript page can scroll to it on load.
 */
function buildTranscriptUrl(result: SearchResult): string {
  return `/episodes/${result.episode_id}/transcript?chunk=${result.chunk_id}`
}

export function SearchResultCard({
  result,
  isLoggedIn,
  isBookmarked,
  onBookmark,
  onRemoveBookmark,
  onBookmarkRemoved,
}: SearchResultCardProps) {
  const transcriptUrl = buildTranscriptUrl(result)
  const [saving, setSaving] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [showTooltip, setShowTooltip] = useState(false)

  const handleBookmarkClick = async (e: React.MouseEvent) => {
    // Prevent the card link from navigating
    e.preventDefault()
    e.stopPropagation()

    if (saving) return

    if (!isLoggedIn) return

    if (isBookmarked && onRemoveBookmark) {
      // Remove bookmark
      setSaving(true)
      setErrorMsg(null)

      const removeResult = await onRemoveBookmark(result.chunk_id)

      setSaving(false)
      if (removeResult.success) {
        onBookmarkRemoved?.(result.chunk_id)
      } else if (removeResult.error) {
        setErrorMsg(removeResult.error)
      }
    } else if (!isBookmarked) {
      // Create bookmark
      setSaving(true)
      setErrorMsg(null)

      const bookmarkResult = await onBookmark(result.chunk_id)

      setSaving(false)
      if (!bookmarkResult.success && bookmarkResult.error) {
        setErrorMsg(bookmarkResult.error)
      }
    }
  }

  return (
    <a
      href={transcriptUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="result-card"
      aria-label={`View transcript: ${result.episode_title}`}
    >
      {/* ---- Bookmark button ---- */}
      <div className="bookmark-button-wrapper">
        <button
          type="button"
          className={`bookmark-button ${isBookmarked ? 'bookmarked' : ''} ${saving ? 'saving' : ''}`}
          onClick={handleBookmarkClick}
          onMouseEnter={() => !isLoggedIn && setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
          disabled={saving}
          aria-label={isBookmarked ? 'Remove bookmark' : 'Save bookmark'}
        >
          {saving ? (
            <span className="bookmark-spinner" aria-hidden="true" />
          ) : isBookmarked ? (
            <svg
              className="bookmark-icon"
              viewBox="0 0 24 24"
              fill="currentColor"
              aria-hidden="true"
            >
              <path d="M5 3a2 2 0 0 0-2 2v16l9-4 9 4V5a2 2 0 0 0-2-2H5z" />
            </svg>
          ) : (
            <svg
              className="bookmark-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              aria-hidden="true"
            >
              <path d="M5 3a2 2 0 0 0-2 2v16l9-4 9 4V5a2 2 0 0 0-2-2H5z" />
            </svg>
          )}
        </button>
        {showTooltip && !isLoggedIn && (
          <span className="bookmark-tooltip" role="tooltip">
            Log in to save bookmarks
          </span>
        )}
        {errorMsg && (
          <span className="bookmark-error">{errorMsg}</span>
        )}
      </div>

      {/* ---- Context before ---- */}
      {result.context_before.length > 0 && (
        <div className="context-lines context-before">
          {result.context_before.map((ctx) => (
            <p key={ctx.chunk_index} className="context-line">
              {ctx.chunk_text}
            </p>
          ))}
        </div>
      )}

      {/* ---- Matching chunk (highlighted) ---- */}
      <div className="match-chunk">
        <p className="match-text">{result.chunk_text}</p>
      </div>

      {/* ---- Context after ---- */}
      {result.context_after.length > 0 && (
        <div className="context-lines context-after">
          {result.context_after.map((ctx) => (
            <p key={ctx.chunk_index} className="context-line">
              {ctx.chunk_text}
            </p>
          ))}
        </div>
      )}

      {/* ---- Metadata ---- */}
      <div className="result-meta">
        <span className="meta-podcast">{result.podcast_name}</span>
        <span className="meta-separator">&middot;</span>
        <span className="meta-episode">
          {result.episode_number != null && `Ep. ${result.episode_number} — `}
          {result.episode_title}
        </span>
        {result.publication_date && (
          <>
            <span className="meta-separator">&middot;</span>
            <span className="meta-date">
              {formatDate(result.publication_date)}
            </span>
          </>
        )}
      </div>

      <div className="result-meta-secondary">
        <span className="meta-speaker">{result.speaker_label}</span>
        <span className="meta-separator">&middot;</span>
        <span className="meta-timestamp">
          {result.start_timestamp} &ndash; {result.end_timestamp}
        </span>
      </div>
    </a>
  )
}
