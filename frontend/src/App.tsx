import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { Header } from './components/Header'
import { AuthCallback } from './pages/AuthCallback'
import { HomePage } from './pages/HomePage'
import { TranscriptPage } from './pages/TranscriptPage'
import { BookmarksPage } from './pages/BookmarksPage'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Header />
        <main>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/auth/callback" element={<AuthCallback />} />
            <Route path="/episodes/:episodeId/transcript" element={<TranscriptPage />} />
            <Route path="/bookmarks" element={<BookmarksPage />} />
          </Routes>
        </main>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
