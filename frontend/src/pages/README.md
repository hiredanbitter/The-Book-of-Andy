# Pages

React page components mapped to routes in `App.tsx`.

## Key Files

- **`HomePage.tsx`** — Landing page with the search bar and search results. Mounted at `/`.
- **`AuthCallback.tsx`** — Handles the OAuth redirect callback after Google sign-in. Mounted at `/auth/callback`.
- **`TranscriptPage.tsx`** — Transcript detail page showing full episode transcript with metadata. Mounted at `/episodes/:episodeId/transcript`.
- **`TranscriptPage.css`** — Styles for the transcript detail page including episode metadata, chunk rendering, highlight styling, and responsive breakpoints.

## TranscriptPage Implementation Decisions

- **Chunk highlight via query parameter**: The page reads a `?chunk=<chunk_id>` query parameter to identify which chunk to highlight and scroll to. This allows search result cards to link directly to a specific moment in the transcript.
- **Scroll behavior**: Uses `scrollIntoView({ behavior: 'smooth', block: 'center' })` with a small delay to ensure the DOM has rendered before scrolling.
- **Speaker labels and timestamps**: Speaker labels are rendered in bold; timestamps in a subtle gray, matching the spec.
- **Highlighted chunk**: Uses a yellow-tinted background with a left border accent for the matched chunk.
- **Responsive design**: A mobile breakpoint at 640px adjusts padding, font sizes, and metadata layout for small screens.
