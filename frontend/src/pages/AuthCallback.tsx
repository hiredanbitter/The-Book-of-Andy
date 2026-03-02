import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'

const CALLBACK_TIMEOUT_MS = 10_000

export function AuthCallback() {
  const navigate = useNavigate()
  const [error, setError] = useState(false)

  useEffect(() => {
    // Supabase automatically handles the OAuth callback by reading the
    // URL hash/query params. We just need to wait for the session to be
    // established and then redirect the user back to the page they came from.
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_IN') {
        const returnTo = sessionStorage.getItem('auth_return_to') ?? '/'
        sessionStorage.removeItem('auth_return_to')
        navigate(returnTo, { replace: true })
      }
    })

    // If sign-in doesn't complete within the timeout, show an error
    const timeout = setTimeout(() => {
      setError(true)
    }, CALLBACK_TIMEOUT_MS)

    return () => {
      subscription.unsubscribe()
      clearTimeout(timeout)
    }
  }, [navigate])

  if (error) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '60vh', gap: '1rem' }}>
        <p>Sign in could not be completed. Please try again.</p>
        <a href="/" style={{ color: '#646cff' }}>Return to home</a>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
      <p>Completing sign in...</p>
    </div>
  )
}
