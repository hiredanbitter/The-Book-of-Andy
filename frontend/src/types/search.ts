/**
 * TypeScript types mirroring the backend search API response shapes.
 */

export interface ContextChunk {
  chunk_index: number
  chunk_text: string
  speaker_label: string
  start_timestamp: string
  end_timestamp: string
}

export interface SearchResult {
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
  context_before: ContextChunk[]
  context_after: ContextChunk[]
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
  page: number
  page_size: number
}

export type SearchMode = 'keyword' | 'semantic'
