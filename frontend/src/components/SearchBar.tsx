import type { FormEvent } from 'react'
import type { SearchMode } from '../types/search'
import './SearchBar.css'

interface SearchBarProps {
  query: string
  onQueryChange: (q: string) => void
  mode: SearchMode
  onModeChange: (m: SearchMode) => void
  onSubmit: () => void
  loading: boolean
}

export function SearchBar({
  query,
  onQueryChange,
  mode,
  onModeChange,
  onSubmit,
  loading,
}: SearchBarProps) {
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      onSubmit()
    }
  }

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <div className="search-input-wrapper">
        <input
          type="text"
          className="search-input"
          placeholder="Search podcast transcripts..."
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          disabled={loading}
          aria-label="Search query"
        />
        <button
          type="submit"
          className="search-submit"
          disabled={loading || !query.trim()}
          aria-label="Search"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      <div className="search-toggle" role="radiogroup" aria-label="Search mode">
        <button
          type="button"
          role="radio"
          aria-checked={mode === 'keyword'}
          className={`toggle-button ${mode === 'keyword' ? 'active' : ''}`}
          onClick={() => onModeChange('keyword')}
        >
          Keyword
        </button>
        <button
          type="button"
          role="radio"
          aria-checked={mode === 'semantic'}
          className={`toggle-button ${mode === 'semantic' ? 'active' : ''}`}
          onClick={() => onModeChange('semantic')}
        >
          Semantic
        </button>
      </div>
    </form>
  )
}
