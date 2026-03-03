# Components

Reusable UI components shared across pages.

## Key Files

- **`SearchResultCard.tsx`** — Renders a single search result as a card with context lines, matching chunk, episode metadata, and a bookmark button. The bookmark button adapts its behavior based on authentication state (tooltip for logged-out users, save/loading/saved states for logged-in users).
- **`SearchResultCard.css`** — Styles for the search result card including context lines, match highlighting, metadata rows, bookmark button, tooltip, spinner, and inline error message.
- **`SearchBar.tsx`** — Search input with keyword/semantic mode toggle and submit button.
- **`SearchBar.css`** — Styles for the search bar component.
- **`BookmarkCard.tsx`** — Renders a single bookmark as a card matching the search result card format, with a delete button (confirm/cancel) instead of a bookmark button. Links to the transcript detail page in a new tab.
- **`BookmarkCard.css`** — Styles for the bookmark card including delete button, confirmation UI, spinner, and inline error message.
- **`Header.tsx`** — App header with logo link, bookmarks link (for logged-in users), auth status, and sign-in/sign-out button.
- **`Header.css`** — Styles for the app header.
- **`Pagination.tsx`** — Page navigation controls for keyword search results.
- **`Pagination.css`** — Styles for the pagination component.

## Bookmark Button Implementation Decisions

- **Positioned absolutely** in the top-right corner of each result card to avoid interfering with the card's link behavior.
- **Event propagation**: The bookmark button calls `preventDefault()` and `stopPropagation()` on click to prevent the parent `<a>` tag from navigating.
- **SVG icons**: Uses inline SVGs for the bookmark icon — outlined when unsaved, filled when saved — to avoid external icon library dependencies.
- **Tooltip for logged-out users**: Shown on hover via React state rather than CSS-only `:hover` to keep it conditional on auth state.
- **Inline error message**: Displayed below the button when the bookmark limit (100) is reached, styled as a subtle red notification.
- **Loading spinner**: A pure CSS spinner animation displayed while the `POST /bookmarks` API call is in flight.

## Delete Button Implementation Decisions (BookmarkCard)

- **Two-step confirmation**: Clicking the trash icon replaces it with "Delete" and "Cancel" buttons to prevent accidental deletions.
- **Optimistic removal**: On successful deletion the card is removed from the parent's state immediately without a full page reload.
- **Event propagation**: Like the bookmark button, the delete button calls `preventDefault()` and `stopPropagation()` to avoid triggering the card's link navigation.
