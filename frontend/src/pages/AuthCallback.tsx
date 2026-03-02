import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'

export function AuthCallback() {
  const navigate = useNavigate()

  useEffect(() => {
    // Supabase automatically handles the OAuth callback by reading the
    // URL hash/query params. We just need to wait for the session to be
    // established and then redirect the user back to the page they came from.
    supabase.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_IN') {
        // Redirect to the page the user was on before sign-in,
        // falling back to home if not available.
        const returnTo = sessionStorage.getItem('auth_return_to') ?? '/'
        sessionStorage.removeItem('auth_return_to')
        navigate(returnTo, { replace: true })
      }
    })
  }, [navigate])

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
      <p>Completing sign in...</p>
    </div>
  )
}
