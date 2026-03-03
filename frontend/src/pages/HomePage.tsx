import { useCallback, useState } from 'react'
import { SearchBar } from '../components/SearchBar'
import { SearchResultCard } from '../components/SearchResultCard'
import { ScrollToTop } from '../components/ScrollToTop'
import { Pagination } from '../components/Pagination'
import { Toast } from '../components/Toast'
import { useSearch } from '../hooks/useSearch'
import { useBookmarks } from '../hooks/useBookmarks'
import { useAuth } from '../hooks/useAuth'
import './HomePage.css'

export function HomePage() {
  const {
    query,
    setQuery,
    mode,
    setMode,
    loading,
    error,
    results,
    total,
    page,
    totalPages,
    hasSearched,
    search,
    goToPage,
  } = useSearch()

  const { user } = useAuth()
  const isLoggedIn = !!user
  const { bookmarkedChunkIds, saveBookmark, removeBookmark, undoRemoveBookmark } =
    useBookmarks()

  // Toast state for bookmark removal undo
  const [toast, setToast] = useState<{ chunkId: string } | null>(null)

  const handleBookmarkRemoved = useCallback((chunkId: string) => {
    setToast({ chunkId })
  }, [])

  const handleUndoRemove = useCallback(() => {
    if (toast) {
      undoRemoveBookmark(toast.chunkId)
    }
  }, [toast, undoRemoveBookmark])

  const handleToastDismiss = useCallback(() => {
    setToast(null)
  }, [])

  return (
    <div className={`home-page ${hasSearched ? 'has-results' : ''}`}>
      <div className="search-section">
        <h1 className="search-title">Podcast Transcript Search</h1>
        <p className="search-subtitle">
          Search podcast transcripts using keyword or semantic search.
        </p>
        <SearchBar
          query={query}
          onQueryChange={setQuery}
          mode={mode}
          onModeChange={setMode}
          onSubmit={search}
          loading={loading}
        />
      </div>

      {/* Loading state */}
      {loading && (
        <div className="search-status">
          <p className="loading-message">Searching...</p>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="search-status">
          <p className="error-message">{error}</p>
        </div>
      )}

      {/* Results */}
      {!loading && !error && results.length > 0 && (
        <div className="results-section">
          <p className="results-count">
            {mode === 'semantic'
              ? `Showing the top ${total} result${total !== 1 ? 's' : ''}`
              : `${total} result${total !== 1 ? 's' : ''} found`}
          </p>
          <div className="results-list">
            {results.map((result) => (
              <SearchResultCard
                key={result.chunk_id}
                result={result}
                isLoggedIn={isLoggedIn}
                isBookmarked={bookmarkedChunkIds.has(result.chunk_id)}
                onBookmark={saveBookmark}
                onRemoveBookmark={removeBookmark}
                onBookmarkRemoved={handleBookmarkRemoved}
              />
            ))}
          </div>
          {mode === 'keyword' && (
            <Pagination
              page={page}
              totalPages={totalPages}
              total={total}
              loading={loading}
              onPageChange={goToPage}
            />
          )}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && hasSearched && results.length === 0 && (
        <div className="search-status">
          <p className="empty-message">
            No results found. Try a different search term or switch search modes.
          </p>
        </div>
      )}

      {/* Toast notification for bookmark removal with undo */}
      {toast && (
        <Toast
          message="Bookmark removed"
          actionLabel="Undo"
          onAction={handleUndoRemove}
          onDismiss={handleToastDismiss}
        />
      )}

      <ScrollToTop />
    </div>
  )
}
