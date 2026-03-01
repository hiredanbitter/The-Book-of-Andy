# GitHub Issues — Podcast Transcript Search App
# Created with Claude
---

---

## EPIC 1: Project Setup & Infrastructure

---

### TICKET 1.1 — Project Scaffolding, Root README & Architecture Document

**User Story**
As a developer,
I want a well-structured monorepo with a root-level README and architecture document,
So that any developer or AI agent can quickly understand the project structure, stack, and data flow before touching any code.

**Context**
Stack: React (Vite) for the frontend, Python FastAPI for the backend, Supabase for PostgreSQL + pgvector + Storage + Google OAuth, OpenAI Embeddings API. Frontend deploys to Vercel, backend deploys to Render or Railway.

**Tasks**
- Initialize a monorepo with `/frontend` and `/backend` directories
- Scaffold the React frontend using Vite
- Scaffold the Python FastAPI backend with a basic app entry point
- Create a root-level `README.md` (see acceptance criteria for required content)
- Create a root-level `ARCHITECTURE.md` (see acceptance criteria for required content)
- Create a `.gitignore` appropriate for the stack
- Create a root-level `.env.example` documenting all required environment variables

**Acceptance Criteria**

Scenario: Root README exists and is informative
Given: A developer or AI agent clones the repository
When: They open the root `README.md`
Then: They can find the project description, tech stack, directory structure, instructions for running the frontend and backend locally, and links to `ARCHITECTURE.md`

Scenario: Architecture document describes the full system
Given: A developer or AI agent opens `ARCHITECTURE.md`
When: They read it
Then: They find a description of each component (React frontend, FastAPI backend, Supabase, OpenAI API), a data flow narrative from transcript ingestion through to search results, and a diagram or written description of how services connect

Scenario: Frontend scaffolding works
Given: A developer runs the frontend setup instructions
When: They run `npm install` and `npm run dev` inside `/frontend`
Then: A default Vite + React app loads in the browser without errors

Scenario: Backend scaffolding works
Given: A developer runs the backend setup instructions
When: They run the FastAPI app locally
Then: The app starts without errors and a health check endpoint returns a 200 response

**Standing README Instruction**
As part of completing this ticket, create or update the `README.md` in any directory you create or modify. Each README should describe the purpose of the directory, key files and their roles, and any important implementation decisions made.

---

### TICKET 1.2 — Supabase Project Setup

**User Story**
As a developer,
I want a fully configured Supabase project with the required database schema, storage bucket, and auth settings,
So that all other features have a reliable data and auth foundation to build on.

**Tasks**
- Create a Supabase project
- Enable the `pgvector` extension in the Supabase database
- Create the following tables (see schema notes below):
  - `podcasts` — podcast-level metadata
  - `episodes` — episode-level metadata linked to a podcast
  - `transcript_chunks` — individual chunks of transcript text with embeddings and timestamps
  - `bookmarks` — user-saved chunks linked to a user and a chunk
- Create a Supabase Storage bucket for raw transcript text files
- Enable Google OAuth in Supabase Auth settings
- Document all environment variables in `.env.example`

**Schema Notes**
- `podcasts`: id, name, created_at
- `episodes`: id, podcast_id (FK), title, episode_number, publication_date, description, transcript_file_url, created_at
- `transcript_chunks`: id, episode_id (FK), chunk_text, speaker_label, start_timestamp, end_timestamp, embedding (vector), chunk_index, created_at
- `bookmarks`: id, user_id (FK), chunk_id (FK), created_at

**Acceptance Criteria**

Scenario: Database tables exist with correct schema
Given: The Supabase project is configured
When: A developer inspects the database
Then: All four tables exist with the correct columns, foreign keys, and data types

Scenario: pgvector extension is enabled
Given: The Supabase project is configured
When: A developer runs a vector similarity query
Then: The query executes without errors

Scenario: Storage bucket exists
Given: The Supabase project is configured
When: A developer navigates to Supabase Storage
Then: A bucket for transcript files exists and is accessible to the backend service role

Scenario: Google OAuth is enabled
Given: The Supabase project is configured
When: A developer navigates to Supabase Auth settings
Then: Google is listed as an enabled provider with client ID and secret configured

**Standing README Instruction**
As part of completing this ticket, create or update the `README.md` in any directory you create or modify. Each README should describe the purpose of the directory, key files and their roles, and any important implementation decisions made.

---

---

## EPIC 2: Transcript Ingestion

---

### TICKET 2.1 — Transcript Chunking & Embedding Pipeline

**User Story**
As an admin,
I want to drop a plain text transcript file into Supabase Storage and trigger a backend pipeline that chunks and embeds it,
So that the transcript becomes searchable by both keyword and semantic search.

**Context**
Transcript files are plain text with lines in the following format:
`[0:00:16 - 0:00:30] SPEAKER_01: transcript text here`

Chunking strategy: sliding window with overlap. Group lines into chunks of approximately 8–10 lines, with each chunk overlapping the previous by 4–5 lines. Chunk size and overlap should be configurable parameters (not hardcoded) so they can be tuned later.

Each chunk should be stored with:
- The raw chunk text
- The speaker label of the first line in the chunk
- The start timestamp of the first line in the chunk
- The end timestamp of the last line in the chunk
- The embedding vector (generated via OpenAI Embeddings API)
- The chunk index (position in the episode)
- A reference to the parent episode

**Tasks**
- Write a parser that reads the plain text transcript format and extracts lines with speaker label, start timestamp, end timestamp, and text
- Implement the sliding window chunking logic with configurable chunk size and overlap
- Integrate with the OpenAI Embeddings API to generate a vector for each chunk
- Store each chunk in the `transcript_chunks` table in Supabase
- Write a script that can be run manually, accepting an episode ID and transcript file path as arguments
- Handle errors gracefully (e.g. malformed lines, API failures) and log them clearly

**Acceptance Criteria**

Scenario: Parser correctly extracts lines
Given: A valid transcript text file
When: The parser processes it
Then: Each line is correctly extracted with its speaker label, start timestamp, end timestamp, and text

Scenario: Chunking produces overlapping groups
Given: A parsed list of transcript lines
When: The chunking algorithm runs with default settings
Then: Chunks are groups of ~8–10 lines and each chunk shares ~4–5 lines with the previous chunk

Scenario: Embeddings are generated and stored
Given: A chunked transcript
When: The pipeline runs to completion
Then: Each chunk exists in the `transcript_chunks` table with a non-null embedding vector, correct timestamps, speaker label, and chunk index

Scenario: Malformed lines are handled gracefully
Given: A transcript file containing one or more lines that don't match the expected format
When: The parser processes the file
Then: Malformed lines are skipped and logged, and the pipeline continues processing the remaining lines

Scenario: Script is runnable from the command line
Given: A valid episode ID and transcript file path
When: The script is run
Then: The pipeline completes and a success message with chunk count is printed to the console

**Standing README Instruction**
As part of completing this ticket, create or update the `README.md` in any directory you create or modify. Each README should describe the purpose of the directory, key files and their roles, and any important implementation decisions made.

---

### TICKET 2.2 — Episode Metadata Storage

**User Story**
As an admin,
I want to record episode metadata in the database when I ingest a new transcript,
So that search results and transcript pages can display accurate episode information.

**Context**
Episode metadata includes: podcast name, episode title, episode number, publication date, description, and the URL of the raw transcript file in Supabase Storage. The podcast must exist in the `podcasts` table before an episode can be created. For MVP, this is managed manually or via a script — there is no admin UI.

**Tasks**
- Create a script or CLI command to insert a new podcast into the `podcasts` table if it doesn't already exist
- Create a script or CLI command to insert a new episode into the `episodes` table with all required metadata fields and the transcript file URL
- Integrate episode creation with the ingestion pipeline from Ticket 2.1 so that running the pipeline requires an episode to exist first (or creates one as part of the process)

**Acceptance Criteria**

Scenario: Podcast is created if it doesn't exist
Given: A podcast name that is not yet in the database
When: The admin runs the podcast creation script
Then: A new record appears in the `podcasts` table with the correct name

Scenario: Episode metadata is stored correctly
Given: A valid podcast ID and all required episode metadata fields
When: The admin runs the episode creation script
Then: A new record appears in the `episodes` table with all fields populated correctly and a valid transcript file URL

Scenario: Ingestion pipeline references a valid episode
Given: An episode record exists in the database
When: The ingestion pipeline script is run with that episode's ID
Then: All generated chunks are correctly linked to that episode via `episode_id`

**Standing README Instruction**
As part of completing this ticket, create or update the `README.md` in any directory you create or modify. Each README should describe the purpose of the directory, key files and their roles, and any important implementation decisions made.

---

---

## EPIC 3: Search

---

### TICKET 3.1 — Keyword Search API Endpoint

**User Story**
As a user,
I want to search podcast transcripts using keywords,
So that I can find episodes and moments that contain specific words or phrases.

**Context**
Keyword search should match against the `chunk_text` field in the `transcript_chunks` table using PostgreSQL full-text search. Results should include the matching chunk plus the 2 lines immediately before and 2 lines immediately after it (retrieved by chunk_index). Results should be paginated with a configurable page size. Each result should include: chunk text, context lines, speaker label, start timestamp, end timestamp, episode title, episode number, podcast name, and publication date.

**Tasks**
- Create a `GET /search/keyword` endpoint in FastAPI
- Accept query parameters: `q` (search term), `page` (default 1), `page_size` (default 10)
- Implement full-text search against `chunk_text` using PostgreSQL
- For each matching chunk, retrieve the 2 preceding and 2 following chunks by `chunk_index` within the same episode
- Return paginated results with all required metadata fields
- Return total result count alongside results to support pagination UI

**Acceptance Criteria**

Scenario: Keyword search returns relevant results
Given: The database contains ingested transcript chunks
When: A user queries `GET /search/keyword?q=burnout`
Then: The response includes chunks containing the word "burnout" with correct metadata and context lines

Scenario: Results are paginated
Given: A search query that matches more results than the page size
When: The user requests page 2
Then: The response returns the correct second page of results and includes total result count

Scenario: Context lines are included
Given: A matching chunk that has at least 2 chunks before and after it in the same episode
When: The search result is returned
Then: The result includes the 2 preceding and 2 following chunks as context

Scenario: No results returns empty array
Given: A search term that matches nothing
When: The endpoint is called
Then: The response returns an empty results array and a total count of 0

**Standing README Instruction**
As part of completing this ticket, create or update the `README.md` in any directory you create or modify. Each README should describe the purpose of the directory, key files and their roles, and any important implementation decisions made.

---

### TICKET 3.2 — Semantic Search API Endpoint

**User Story**
As a user,
I want to search podcast transcripts using natural language,
So that I can find conceptually relevant moments even when my search terms don't exactly match the transcript text.

**Context**
Semantic search works by embedding the user's query using the OpenAI Embeddings API and then finding the most similar chunk vectors in the database using pgvector's cosine similarity. Results should follow the same shape as keyword search results: matching chunk, 2 lines of context before and after, and all episode metadata. Results should be paginated with a configurable page size.

**Tasks**
- Create a `GET /search/semantic` endpoint in FastAPI
- Accept query parameters: `q` (search term), `page` (default 1), `page_size` (default 10)
- Embed the query using the OpenAI Embeddings API
- Query `transcript_chunks` using pgvector cosine similarity to find the closest matching chunks
- For each matching chunk, retrieve the 2 preceding and 2 following chunks by `chunk_index` within the same episode
- Return paginated results with all required metadata fields and total result count

**Acceptance Criteria**

Scenario: Semantic search surfaces conceptually related results
Given: The database contains ingested transcript chunks about topics like workload and work-life balance
When: A user queries `GET /search/semantic?q=burnout`
Then: The response includes chunks related to burnout, workload, and work-life balance even if those exact words are not in the chunk text

Scenario: Results are paginated
Given: A semantic search query that matches many chunks
When: The user requests page 2
Then: The response returns the correct second page of results and includes total result count

Scenario: Context lines are included
Given: A matching chunk that has at least 2 chunks before and after it in the same episode
When: The search result is returned
Then: The result includes the 2 preceding and 2 following chunks as context

Scenario: OpenAI API failure is handled gracefully
Given: The OpenAI API is unavailable
When: A semantic search request is made
Then: The endpoint returns a 503 error with a clear error message

**Standing README Instruction**
As part of completing this ticket, create or update the `README.md` in any directory you create or modify. Each README should describe the purpose of the directory, key files and their roles, and any important implementation decisions made.

---

### TICKET 3.3 — Search UI (Homepage & Results Page)

**User Story**
As a user,
I want a clean search interface with a keyword/semantic toggle and paginated results,
So that I can quickly find relevant podcast moments using the search mode that suits my needs.

**Context**
The homepage is a centered search bar with a keyword/semantic toggle. After submitting a search, results are displayed on the same page below the search bar. Each result card displays: matching chunk text (with context lines visually distinguished), podcast name, episode title, episode number, publication date, speaker label, and timestamp. Clicking a result opens the transcript detail page in a new tab, anchored to the matching chunk. Pagination controls allow navigating between pages. Page size is configurable (the default value should be defined in a config or environment variable).

**Tasks**
- Build the homepage with a centered search bar and keyword/semantic toggle
- On search submission, call the appropriate API endpoint based on the selected mode
- Display results as cards below the search bar, each showing all required metadata
- Visually distinguish the matching chunk text from the surrounding context lines (e.g. highlight or bold the match)
- Each result card links to the transcript detail page in a new tab with the correct anchor
- Implement pagination controls (previous/next, page number display)
- Show a "no results found" state when the search returns empty
- Show a loading state while the API call is in progress

**Acceptance Criteria**

Scenario: User performs a keyword search
Given: A user is on the homepage
When: They type a search term, select keyword mode, and submit
Then: Result cards appear below the search bar with matching chunks, context, and all metadata fields

Scenario: User performs a semantic search
Given: A user is on the homepage
When: They type a search term, select semantic mode, and submit
Then: Result cards appear with semantically relevant chunks and all metadata fields

Scenario: Matching chunk is visually distinguished from context
Given: A result card is displayed
When: The user views it
Then: The matching chunk text is visually distinct from the 2 context lines above and below it

Scenario: Clicking a result opens the transcript page
Given: A result card is displayed
When: The user clicks it
Then: The transcript detail page opens in a new tab scrolled to and highlighting the matching chunk

Scenario: Pagination works correctly
Given: A search with more results than the page size
When: The user clicks the next page button
Then: The next page of results is loaded and displayed

Scenario: Empty state is shown when no results found
Given: A search term that matches nothing
When: The search completes
Then: A friendly "no results found" message is displayed

**Standing README Instruction**
As part of completing this ticket, create or update the `README.md` in any directory you create or modify. Each README should describe the purpose of the directory, key files and their roles, and any important implementation decisions made.

---

---

## EPIC 4: Transcript Detail Page

---

### TICKET 4.1 — Transcript Detail Page

**User Story**
As a user,
I want to view the full transcript of an episode in a readable format, scrolled to and highlighting the section I found in search,
So that I can read the full context of a moment I discovered through search.

**Context**
The transcript detail page is accessed by clicking a search result. It opens in a new tab. The URL should include a reference to the specific chunk so the page can scroll to and highlight it on load. Episode metadata is displayed at the top. The transcript is rendered from the stored chunks. Speaker labels are styled in bold, timestamps are styled in subtle gray. The matching chunk is visually highlighted (e.g. yellow background).

**Tasks**
- Create a `GET /episodes/:id/transcript` API endpoint that returns all chunks for an episode in order, along with episode metadata
- Build the transcript detail page in React
- Display episode metadata (podcast name, episode title, episode number, publication date, description) at the top of the page
- Render the full transcript with styled speaker labels (bold) and timestamps (subtle gray)
- Accept a chunk ID in the URL (e.g. as a query parameter or hash) and on page load scroll to that chunk and apply a highlight style
- Ensure the page is readable on both desktop and mobile

**Acceptance Criteria**

Scenario: Full transcript is rendered
Given: A user navigates to a transcript detail page
When: The page loads
Then: The full transcript is displayed in chronological order with all speaker labels and timestamps visible

Scenario: Speaker labels and timestamps are styled correctly
Given: The transcript detail page is loaded
When: The user views the transcript
Then: Speaker labels appear in bold and timestamps appear in a subtle gray color

Scenario: Episode metadata is displayed at the top
Given: The transcript detail page is loaded
When: The user views the top of the page
Then: The podcast name, episode title, episode number, publication date, and description are all visible

Scenario: Matching chunk is highlighted and scrolled to
Given: The page URL contains a chunk ID reference
When: The page finishes loading
Then: The page has scrolled to the matching chunk and it is visually highlighted

Scenario: Page is readable on mobile
Given: A user opens the transcript detail page on a mobile device
When: They view the page
Then: The transcript and metadata are legible and no content is clipped or overflowing

**Standing README Instruction**
As part of completing this ticket, create or update the `README.md` in any directory you create or modify. Each README should describe the purpose of the directory, key files and their roles, and any important implementation decisions made.

---

---

## EPIC 5: Authentication

---

### TICKET 5.1 — Google OAuth Integration

**User Story**
As a user,
I want to sign in with my Google account,
So that I can access features that require authentication, like bookmarking search results.

**Context**
Authentication is handled via Supabase Auth with Google OAuth. There is a sign in / sign out button in the top right of the app on all pages. There are no intrusive modals or popups prompting users to log in. Auth state should persist across page refreshes.

**Tasks**
- Integrate Supabase Auth with Google OAuth in the React frontend
- Add a sign in / sign out button to the top right of the app header on all pages
- On sign in, redirect the user back to the page they were on
- Persist auth state across page refreshes using Supabase session management
- Expose the current user's session/auth state globally in the app (e.g. via context) so other components can react to it

**Acceptance Criteria**

Scenario: User signs in with Google
Given: A user is on any page and is not logged in
When: They click the sign in button and complete the Google OAuth flow
Then: They are returned to the page they were on and the button now shows their name or a sign out option

Scenario: User signs out
Given: A user is logged in
When: They click the sign out button
Then: Their session is cleared and the button returns to showing "Sign In"

Scenario: Auth state persists across refresh
Given: A user is logged in
When: They refresh the page
Then: They remain logged in without needing to re-authenticate

Scenario: Auth state is available to all components
Given: A user is logged in
When: Any component in the app needs to check auth state
Then: The current user's session is accessible without additional API calls

**Standing README Instruction**
As part of completing this ticket, create or update the `README.md` in any directory you create or modify. Each README should describe the purpose of the directory, key files and their roles, and any important implementation decisions made.

---

---

## EPIC 6: Bookmarks

---

### TICKET 6.1 — Bookmark API Endpoints

**User Story**
As a logged-in user,
I want to save, retrieve, and delete bookmarked transcript chunks via the API,
So that the frontend can offer a fully functional bookmarking experience.

**Context**
Bookmarks link a user to a specific transcript chunk. A user can have a maximum of 100 bookmarks. Bookmark endpoints must be authenticated — unauthenticated requests should return 401. The bookmark response shape should include the full chunk data and episode metadata so the frontend can render bookmark cards in the same format as search result cards.

**Tasks**
- Create a `POST /bookmarks` endpoint to save a bookmark (accepts chunk_id, requires auth)
- Create a `DELETE /bookmarks/:id` endpoint to delete a bookmark (requires auth, user must own the bookmark)
- Create a `GET /bookmarks` endpoint to retrieve all bookmarks for the authenticated user, including chunk text, speaker label, timestamps, and episode metadata
- Enforce a maximum of 100 bookmarks per user — return a 400 error with a clear message if the limit is reached
- Ensure all endpoints return 401 for unauthenticated requests

**Acceptance Criteria**

Scenario: Logged-in user saves a bookmark
Given: A user is authenticated and has fewer than 100 bookmarks
When: They call `POST /bookmarks` with a valid chunk ID
Then: The bookmark is saved and the response returns the new bookmark with full chunk and episode metadata

Scenario: Bookmark limit is enforced
Given: A user already has 100 bookmarks
When: They attempt to save another bookmark
Then: The API returns a 400 error with a message indicating the limit has been reached

Scenario: Logged-in user deletes a bookmark
Given: A user is authenticated and owns a bookmark
When: They call `DELETE /bookmarks/:id`
Then: The bookmark is deleted and the response returns a 200 success

Scenario: User cannot delete another user's bookmark
Given: A user is authenticated
When: They attempt to delete a bookmark they do not own
Then: The API returns a 403 error

Scenario: Unauthenticated request is rejected
Given: A request is made to any bookmark endpoint without a valid auth token
When: The request is received
Then: The API returns a 401 error

**Standing README Instruction**
As part of completing this ticket, create or update the `README.md` in any directory you create or modify. Each README should describe the purpose of the directory, key files and their roles, and any important implementation decisions made.

---

### TICKET 6.2 — Bookmark Button on Search Result Cards

**User Story**
As a user,
I want to see a bookmark button on every search result card,
So that I can save interesting moments if I'm logged in, and understand what the button does if I'm not.

**Context**
The bookmark button is visible to all users on every result card. For logged-out users, hovering over the button shows a tooltip explaining that they need to be logged in to use this feature. No modal or redirect should occur. For logged-in users, clicking the button saves the bookmark. If the chunk is already bookmarked, the button should reflect that saved state. If the bookmark limit is reached, display a friendly inline error message.

**Tasks**
- Add a bookmark button to each search result card
- For logged-out users: show a tooltip on hover with the message "Log in to save bookmarks" (or similar), clicking does nothing
- For logged-in users: clicking the button calls `POST /bookmarks` and toggles the button to a saved state
- If the chunk is already bookmarked, show the button in its saved state on page load
- If the API returns a 400 (limit reached), display a friendly inline error message near the button
- Button should have a loading state while the API call is in progress

**Acceptance Criteria**

Scenario: Logged-out user hovers over bookmark button
Given: A user is not logged in and search results are displayed
When: They hover over the bookmark button on a result card
Then: A tooltip appears explaining they must be logged in to bookmark

Scenario: Logged-out user clicks bookmark button
Given: A user is not logged in
When: They click the bookmark button
Then: Nothing happens beyond the tooltip — no redirect, no modal

Scenario: Logged-in user saves a bookmark
Given: A user is logged in and views a result card that is not yet bookmarked
When: They click the bookmark button
Then: The bookmark is saved and the button transitions to a saved/filled state

Scenario: Already bookmarked chunk shows saved state
Given: A user is logged in and has previously bookmarked a chunk
When: They see that chunk in search results
Then: The bookmark button is already in the saved state

Scenario: Bookmark limit message is shown
Given: A logged-in user has reached their 100 bookmark limit
When: They click the bookmark button on a result
Then: A friendly inline error message is displayed near the button

**Standing README Instruction**
As part of completing this ticket, create or update the `README.md` in any directory you create or modify. Each README should describe the purpose of the directory, key files and their roles, and any important implementation decisions made.

---

### TICKET 6.3 — Bookmarks Dashboard

**User Story**
As a logged-in user,
I want a dashboard where I can view and manage all my saved bookmarks,
So that I can revisit and organize the podcast moments I've found valuable.

**Context**
The bookmarks dashboard is only accessible to logged-in users. It displays all of the user's saved bookmarks as cards in the same format as search result cards (chunk text, context, podcast name, episode title, episode number, publication date, speaker label, timestamp). Each card links to the transcript detail page in a new tab. Each card has a delete button to remove the bookmark. The page should handle the empty state (no bookmarks yet) gracefully.

**Tasks**
- Create a `/bookmarks` route in the React app, accessible only to logged-in users (redirect to home if not authenticated)
- Fetch and display all bookmarks for the authenticated user using `GET /bookmarks`
- Render each bookmark as a card matching the search result card format
- Each card links to the transcript detail page in a new tab anchored to the correct chunk
- Add a delete button to each card that calls `DELETE /bookmarks/:id` and removes the card from the UI on success
- Handle empty state with a friendly message
- Add a link to the bookmarks dashboard in the app header for logged-in users

**Acceptance Criteria**

Scenario: Logged-in user navigates to bookmarks dashboard
Given: A user is logged in and has saved bookmarks
When: They navigate to `/bookmarks`
Then: All their saved bookmarks are displayed as cards with full chunk and episode metadata

Scenario: Logged-out user is redirected
Given: A user is not logged in
When: They navigate to `/bookmarks`
Then: They are redirected to the homepage

Scenario: User deletes a bookmark
Given: A user is on the bookmarks dashboard
When: They click the delete button on a bookmark card and confirm
Then: The bookmark is deleted from the API and the card is removed from the UI without a full page reload

Scenario: Empty state is shown
Given: A user is logged in but has no saved bookmarks
When: They navigate to `/bookmarks`
Then: A friendly message is shown explaining they have no bookmarks yet, with a prompt to search

Scenario: Clicking a bookmark card opens the transcript page
Given: A user is on the bookmarks dashboard
When: They click a bookmark card
Then: The transcript detail page opens in a new tab scrolled to and highlighting the correct chunk

Scenario: Bookmarks link is visible in the header
Given: A user is logged in
When: They view any page
Then: A link to the bookmarks dashboard is visible in the app header

**Standing README Instruction**
As part of completing this ticket, create or update the `README.md` in any directory you create or modify. Each README should describe the purpose of the directory, key files and their roles, and any important implementation decisions made.

---

---

*End of MVP GitHub Issues*

---

### Post-MVP Backlog (not yet ticketed)
- Audio/video timestamp jumping from search results and transcript page
- Browse and discovery experience (by podcast, recent episodes, etc.)
- Bookmark collections and personal notes
- Admin upload UI for transcript files and episode metadata
