import './Pagination.css'

interface PaginationProps {
  page: number
  totalPages: number
  total: number
  loading: boolean
  onPageChange: (page: number) => void
}

export function Pagination({
  page,
  totalPages,
  total,
  loading,
  onPageChange,
}: PaginationProps) {
  if (totalPages <= 1) return null

  return (
    <nav className="pagination" aria-label="Search results pagination">
      <button
        className="pagination-button"
        disabled={page <= 1 || loading}
        onClick={() => onPageChange(page - 1)}
        aria-label="Previous page"
      >
        &larr; Previous
      </button>

      <span className="pagination-info">
        Page {page} of {totalPages}
        <span className="pagination-total"> ({total} results)</span>
      </span>

      <button
        className="pagination-button"
        disabled={page >= totalPages || loading}
        onClick={() => onPageChange(page + 1)}
        aria-label="Next page"
      >
        Next &rarr;
      </button>
    </nav>
  )
}
