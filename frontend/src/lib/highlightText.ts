/**
 * Client-side text highlighting utilities for semantic search results.
 *
 * For keyword search, the backend returns pre-highlighted HTML via
 * ts_headline(). For semantic search, we highlight query words that
 * appear literally in the chunk text as a best-effort approximation.
 */

/**
 * Common English stop words to exclude from highlighting.
 * These appear too frequently to be meaningful highlights.
 */
const STOP_WORDS = new Set([
  'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
  'of', 'with', 'by', 'from', 'is', 'it', 'as', 'be', 'was', 'are',
  'were', 'been', 'has', 'have', 'had', 'do', 'does', 'did', 'will',
  'would', 'could', 'should', 'may', 'might', 'can', 'shall', 'not',
  'no', 'so', 'if', 'then', 'than', 'that', 'this', 'these', 'those',
  'what', 'which', 'who', 'whom', 'how', 'when', 'where', 'why',
  'i', 'me', 'my', 'we', 'us', 'our', 'you', 'your', 'he', 'him',
  'his', 'she', 'her', 'they', 'them', 'their', 'its', 'am', 'about',
  'up', 'out', 'just', 'also', 'very', 'all', 'any', 'each', 'every',
])

/**
 * Apply a simple suffix-stripping stem to a word.
 *
 * This is a lightweight approximation — it strips common English
 * suffixes so that e.g. "running" → "run", "overwhelmed" → "overwhelm".
 * It's intentionally simple to avoid adding a library dependency.
 */
function simpleStem(word: string): string {
  const lower = word.toLowerCase()
  if (lower.length <= 3) return lower

  // Order matters — try longest suffixes first
  const suffixes = [
    'ingly', 'ation', 'ment', 'ness', 'ting',
    'able', 'ible', 'ally', 'ful', 'ous', 'ive', 'less',
    'ing', 'ied', 'ies', 'ely', 'ion',
    'ed', 'er', 'ly', 'es', 'en',
    's',
  ]

  for (const suffix of suffixes) {
    if (lower.endsWith(suffix) && lower.length - suffix.length >= 3) {
      return lower.slice(0, lower.length - suffix.length)
    }
  }
  return lower
}

/**
 * Build highlighted HTML for semantic search results.
 *
 * Splits the query into individual words, filters out stop words,
 * stems each word, then wraps matching words in the text with `<mark>` tags.
 *
 * @param text   - The raw chunk text to highlight.
 * @param query  - The user's search query.
 * @returns HTML string with `<mark>` tags around matching words.
 */
export function highlightSemanticMatches(text: string, query: string): string {
  const queryWords = query
    .toLowerCase()
    .split(/\s+/)
    .filter((w) => w.length > 0 && !STOP_WORDS.has(w))

  if (queryWords.length === 0) return escapeHtml(text)

  // Build stems for each query word
  const stems = queryWords.map(simpleStem)

  // Build a regex pattern that matches any word whose stem matches a query stem.
  // We match whole words and check the stem in the replacer function.
  const pattern = /[a-zA-Z'\u2019]+/g

  let result = ''
  let lastIndex = 0

  for (const match of text.matchAll(pattern)) {
    const word = match[0]
    const matchIndex = match.index
    const wordStem = simpleStem(word)

    // Append text before this word (escaped)
    result += escapeHtml(text.slice(lastIndex, matchIndex))

    // Check if this word's stem matches any query word stem
    const isMatch = stems.some(
      (stem) => wordStem === stem || wordStem.startsWith(stem) || stem.startsWith(wordStem),
    )

    if (isMatch) {
      result += `<mark>${escapeHtml(word)}</mark>`
    } else {
      result += escapeHtml(word)
    }

    lastIndex = matchIndex + word.length
  }

  // Append any remaining text after the last word
  result += escapeHtml(text.slice(lastIndex))

  return result
}

/**
 * Escape HTML special characters to prevent XSS when rendering as innerHTML.
 */
function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

/**
 * Sanitize highlighted HTML from ts_headline() to only allow <mark> tags.
 *
 * The backend's ts_headline() returns text with <mark>...</mark> tags.
 * This function strips all HTML except <mark> and </mark> to prevent XSS.
 *
 * @param html - The highlighted HTML string from the backend.
 * @returns Sanitized HTML string with only <mark> tags preserved.
 */
export function sanitizeHighlightedHtml(html: string): string {
  // First, escape everything
  const escaped = escapeHtml(html)
  // Then restore only <mark> and </mark> tags
  return escaped
    .replace(/&lt;mark&gt;/g, '<mark>')
    .replace(/&lt;\/mark&gt;/g, '</mark>')
}
