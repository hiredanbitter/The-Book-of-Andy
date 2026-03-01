# Frontend — Podcast Transcript Search App

React + TypeScript frontend built with Vite.

## Purpose

This directory contains the user-facing single-page application for searching podcast transcripts, viewing full episode transcripts, and managing bookmarks.

## Key Files

| File / Directory | Description |
|------------------|-------------|
| `src/` | Application source code (components, pages, hooks, etc.) |
| `src/App.tsx` | Root application component |
| `src/main.tsx` | Application entry point |
| `public/` | Static assets served as-is |
| `index.html` | HTML shell for the SPA |
| `vite.config.ts` | Vite build configuration |
| `tsconfig.json` | TypeScript configuration |
| `eslint.config.js` | ESLint configuration |
| `package.json` | Dependencies and scripts |

## Getting Started

```bash
npm install
npm run dev
```

Runs on [http://localhost:5173](http://localhost:5173) by default.

## Available Scripts

- `npm run dev` — Start the development server with hot reload
- `npm run build` — Build for production
- `npm run preview` — Preview the production build locally
- `npm run lint` — Run ESLint

## Implementation Decisions

- **Vite** was chosen over Create React App for faster builds and better developer experience.
- **TypeScript** is used throughout for type safety.
- The app communicates with the FastAPI backend via REST API calls. The backend URL is configured via the `VITE_API_BASE_URL` environment variable.
