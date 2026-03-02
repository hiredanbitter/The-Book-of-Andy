import { SearchBar } from '../components/SearchBar'
import { SearchResultCard } from '../components/SearchResultCard'
import { Pagination } from '../components/Pagination'
import { useSearch } from '../hooks/useSearch'
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
            {total} result{total !== 1 ? 's' : ''} found
          </p>
          <div className="results-list">
            {results.map((result) => (
              <SearchResultCard key={result.chunk_id} result={result} />
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
    </div>
  )
}
