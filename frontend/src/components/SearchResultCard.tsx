import type { SearchResult } from '../types/search'
import './SearchResultCard.css'

interface SearchResultCardProps {
  result: SearchResult
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

export function SearchResultCard({ result }: SearchResultCardProps) {
  const transcriptUrl = buildTranscriptUrl(result)

  return (
    <a
      href={transcriptUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="result-card"
      aria-label={`View transcript: ${result.episode_title}`}
    >
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
