import { useState } from 'react'
import type { BookmarkResponseItem } from '../services/bookmarksApi'
import './BookmarkCard.css'

interface BookmarkCardProps {
  bookmark: BookmarkResponseItem
  onDelete: (bookmarkId: string) => Promise<{ success: boolean; error?: string }>
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
 * chunk highlighted.
 */
function buildTranscriptUrl(bookmark: BookmarkResponseItem): string {
  return `/episodes/${bookmark.episode_id}/transcript?chunk=${bookmark.chunk_id}`
}

export function BookmarkCard({ bookmark, onDelete }: BookmarkCardProps) {
  const transcriptUrl = buildTranscriptUrl(bookmark)
  const [deleting, setDeleting] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()

    if (deleting) return

    if (!confirmDelete) {
      setConfirmDelete(true)
      return
    }

    // User confirmed — proceed with deletion
    performDelete()
  }

  const handleCancelDelete = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setConfirmDelete(false)
    setErrorMsg(null)
  }

  const performDelete = async () => {
    setDeleting(true)
    setErrorMsg(null)

    const result = await onDelete(bookmark.bookmark_id)

    setDeleting(false)
    if (!result.success && result.error) {
      setErrorMsg(result.error)
      setConfirmDelete(false)
    }
    // On success the parent will remove this card from the list
  }

  return (
    <a
      href={transcriptUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="bookmark-card"
      aria-label={`View transcript: ${bookmark.episode_title}`}
    >
      {/* ---- Delete button ---- */}
      <div className="delete-button-wrapper">
        {confirmDelete ? (
          <div className="delete-confirm-group">
            <button
              type="button"
              className={`delete-confirm-button ${deleting ? 'deleting' : ''}`}
              onClick={handleDeleteClick}
              disabled={deleting}
              aria-label="Confirm delete bookmark"
            >
              {deleting ? (
                <span className="delete-spinner" aria-hidden="true" />
              ) : (
                'Delete'
              )}
            </button>
            <button
              type="button"
              className="delete-cancel-button"
              onClick={handleCancelDelete}
              disabled={deleting}
              aria-label="Cancel delete"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            type="button"
            className="delete-button"
            onClick={handleDeleteClick}
            aria-label="Delete bookmark"
          >
            <svg
              className="delete-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
              <path d="M10 11v6" />
              <path d="M14 11v6" />
              <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
            </svg>
          </button>
        )}
        {errorMsg && (
          <span className="delete-error">{errorMsg}</span>
        )}
      </div>

      {/* ---- Chunk text (highlighted) ---- */}
      <div className="match-chunk">
        <p className="match-text">{bookmark.chunk_text}</p>
      </div>

      {/* ---- Metadata ---- */}
      <div className="result-meta">
        <span className="meta-podcast">{bookmark.podcast_name}</span>
        <span className="meta-separator">&middot;</span>
        <span className="meta-episode">
          {bookmark.episode_number != null && `Ep. ${bookmark.episode_number} — `}
          {bookmark.episode_title}
        </span>
        {bookmark.publication_date && (
          <>
            <span className="meta-separator">&middot;</span>
            <span className="meta-date">
              {formatDate(bookmark.publication_date)}
            </span>
          </>
        )}
      </div>

      <div className="result-meta-secondary">
        <span className="meta-speaker">{bookmark.speaker_label}</span>
        <span className="meta-separator">&middot;</span>
        <span className="meta-timestamp">
          {bookmark.start_timestamp} &ndash; {bookmark.end_timestamp}
        </span>
      </div>
    </a>
  )
}
