import { useEffect, useState, useRef } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import './TranscriptPage.css'

interface TranscriptChunk {
  chunk_id: string
  chunk_index: number
  chunk_text: string
  speaker_label: string
  start_timestamp: string
  end_timestamp: string
}

interface EpisodeMetadata {
  episode_id: string
  episode_title: string
  episode_number: number | null
  podcast_name: string
  publication_date: string | null
  description: string | null
}

interface TranscriptResponse {
  episode: EpisodeMetadata
  chunks: TranscriptChunk[]
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string || 'http://localhost:8000'

export function TranscriptPage() {
  const { episodeId } = useParams<{ episodeId: string }>()
  const [searchParams] = useSearchParams()
  const highlightChunkId = searchParams.get('chunk')

  const [data, setData] = useState<TranscriptResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const highlightRef = useRef<HTMLDivElement | null>(null)
  const hasScrolled = useRef(false)

  useEffect(() => {
    if (!episodeId) return

    const fetchTranscript = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await fetch(
          `${API_BASE_URL}/episodes/${encodeURIComponent(episodeId)}/transcript`
        )
        if (!response.ok) {
          if (response.status === 404) {
            setError('Episode not found.')
          } else {
            setError('Failed to load transcript. Please try again later.')
          }
          return
        }
        const json: TranscriptResponse = await response.json()
        setData(json)
      } catch {
        setError('Failed to load transcript. Please try again later.')
      } finally {
        setLoading(false)
      }
    }

    fetchTranscript()
  }, [episodeId])

  // Scroll to highlighted chunk after data loads
  useEffect(() => {
    if (data && highlightChunkId && highlightRef.current && !hasScrolled.current) {
      hasScrolled.current = true
      // Small delay to ensure DOM is fully rendered
      setTimeout(() => {
        highlightRef.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'center',
        })
      }, 100)
    }
  }, [data, highlightChunkId])

  if (loading) {
    return (
      <div className="transcript-page">
        <div className="transcript-loading">Loading transcript...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="transcript-page">
        <div className="transcript-error">{error}</div>
      </div>
    )
  }

  if (!data) {
    return null
  }

  const { episode, chunks } = data

  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return ''
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    } catch {
      return dateStr
    }
  }

  return (
    <div className="transcript-page">
      {/* Episode Metadata */}
      <section className="episode-metadata">
        <div className="episode-meta-label">{episode.podcast_name}</div>
        <h1 className="episode-title">{episode.episode_title}</h1>
        <div className="episode-meta-details">
          {episode.episode_number != null && (
            <span className="episode-number">
              Episode {episode.episode_number}
            </span>
          )}
          {episode.publication_date && (
            <span className="episode-date">
              {formatDate(episode.publication_date)}
            </span>
          )}
        </div>
        {episode.description && (
          <p className="episode-description">{episode.description}</p>
        )}
      </section>

      {/* Transcript */}
      <section className="transcript-body">
        {chunks.length === 0 ? (
          <p className="transcript-empty">
            No transcript available for this episode yet.
          </p>
        ) : (
          chunks.map((chunk) => {
            const isHighlighted = chunk.chunk_id === highlightChunkId
            return (
              <div
                key={chunk.chunk_id}
                ref={isHighlighted ? highlightRef : undefined}
                className={`transcript-chunk${isHighlighted ? ' transcript-chunk--highlighted' : ''}`}
              >
                <div className="chunk-header">
                  <span className="chunk-speaker">{chunk.speaker_label}</span>
                  <span className="chunk-timestamp">{chunk.start_timestamp}</span>
                </div>
                <div className="chunk-text">{chunk.chunk_text}</div>
              </div>
            )
          })
        )}
      </section>
    </div>
  )
}
