import { useEffect, useRef } from 'react'
import './Toast.css'

interface ToastProps {
  /** Message to display in the toast. */
  message: string
  /** Label for the action button (e.g. "Undo"). */
  actionLabel?: string
  /** Callback when the action button is clicked. */
  onAction?: () => void
  /** Callback when the toast is dismissed (by timeout or manual close). */
  onDismiss: () => void
  /** Duration in milliseconds before auto-dismiss. Defaults to 5000. */
  duration?: number
}

/**
 * A lightweight toast notification that appears at the bottom of the viewport.
 * Supports an optional action button (e.g. "Undo") and auto-dismisses after
 * a configurable duration.
 */
export function Toast({
  message,
  actionLabel,
  onAction,
  onDismiss,
  duration = 5000,
}: ToastProps) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    timerRef.current = setTimeout(onDismiss, duration)
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
    }
  }, [onDismiss, duration])

  const handleAction = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }
    onAction?.()
    onDismiss()
  }

  return (
    <div className="toast" role="status" aria-live="polite">
      <span className="toast-message">{message}</span>
      {actionLabel && onAction && (
        <button
          type="button"
          className="toast-action"
          onClick={handleAction}
        >
          {actionLabel}
        </button>
      )}
      <button
        type="button"
        className="toast-close"
        onClick={onDismiss}
        aria-label="Dismiss"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>
  )
}
