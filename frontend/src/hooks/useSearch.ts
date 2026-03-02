/**
 * Custom hook that manages search state and API calls.
 */

import { useCallback, useState } from 'react'
import { fetchSearchResults } from '../services/searchApi'
import { DEFAULT_PAGE_SIZE } from '../config'
import type { SearchMode, SearchResponse, SearchResult } from '../types/search'

interface UseSearchReturn {
  /** Current search query text. */
  query: string
  setQuery: (q: string) => void
  /** Active search mode. */
  mode: SearchMode
  setMode: (m: SearchMode) => void
  /** Whether an API call is in flight. */
  loading: boolean
  /** Error message from the most recent failed request, if any. */
  error: string | null
  /** The result list for the current page. */
  results: SearchResult[]
  /** Total number of results across all pages. */
  total: number
  /** Current 1-based page number. */
  page: number
  /** Results per page. */
  pageSize: number
  /** Total number of pages. */
  totalPages: number
  /** Whether a search has been submitted at least once this session. */
  hasSearched: boolean
  /** Submit a search (resets to page 1). */
  search: () => Promise<void>
  /** Navigate to a specific page. */
  goToPage: (p: number) => Promise<void>
}

export function useSearch(): UseSearchReturn {
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState<SearchMode>('keyword')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<SearchResult[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(DEFAULT_PAGE_SIZE)
  const [hasSearched, setHasSearched] = useState(false)

  // Internal helper shared by search() and goToPage()
  const performSearch = useCallback(
    async (q: string, m: SearchMode, p: number, ps: number) => {
      if (!q.trim()) return
      setLoading(true)
      setError(null)
      try {
        const data: SearchResponse = await fetchSearchResults(q, m, p, ps)
        setResults(data.results)
        setTotal(data.total)
        setPage(data.page)
        setHasSearched(true)
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'An unexpected error occurred.'
        setError(message)
        setResults([])
        setTotal(0)
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  const search = useCallback(async () => {
    await performSearch(query, mode, 1, pageSize)
  }, [query, mode, pageSize, performSearch])

  const goToPage = useCallback(
    async (p: number) => {
      await performSearch(query, mode, p, pageSize)
    },
    [query, mode, pageSize, performSearch],
  )

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return {
    query,
    setQuery,
    mode,
    setMode,
    loading,
    error,
    results,
    total,
    page,
    pageSize,
    totalPages,
    hasSearched,
    search,
    goToPage,
  }
}
